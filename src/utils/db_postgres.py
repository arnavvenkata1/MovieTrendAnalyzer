"""
PostgreSQL Database Utilities
Handles all PostgreSQL connections and operations
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from contextlib import contextmanager
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import POSTGRES_CONFIG


class PostgresDB:
    """PostgreSQL database handler"""
    
    def __init__(self):
        self.config = POSTGRES_CONFIG
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.config)
            print(f"✓ Connected to PostgreSQL: {self.config['database']}")
            return True
        except Exception as e:
            print(f"✗ PostgreSQL connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("PostgreSQL connection closed.")
    
    @contextmanager
    def get_cursor(self, dict_cursor=False):
        """Context manager for database cursor"""
        if not self.conn:
            self.connect()
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = self.conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute a single query"""
        with self.get_cursor(dict_cursor=True) as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            return None
    
    def execute_many(self, query, data):
        """Execute query with multiple rows"""
        with self.get_cursor() as cur:
            execute_values(cur, query, data)
    
    # =========================================================
    # USER OPERATIONS
    # =========================================================
    
    def create_user(self, username, email=None, age_group=None):
        """Create a new user"""
        query = """
            INSERT INTO dim_users (username, email, age_group)
            VALUES (%s, %s, %s)
            RETURNING user_id, username, created_at
        """
        result = self.execute_query(query, (username, email, age_group))
        return result[0] if result else None
    
    def get_user(self, username=None, user_id=None):
        """Get user by username or user_id"""
        if username:
            query = "SELECT * FROM dim_users WHERE username = %s"
            result = self.execute_query(query, (username,))
        elif user_id:
            query = "SELECT * FROM dim_users WHERE user_id = %s"
            result = self.execute_query(query, (user_id,))
        else:
            return None
        return result[0] if result else None
    
    def update_user_preferences(self, user_id, preferences):
        """Update or insert user preferences"""
        query = """
            INSERT INTO user_preferences (user_id, preferred_genres, avoided_genres, 
                                         preferred_decade, mood_preference, min_rating)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                preferred_genres = EXCLUDED.preferred_genres,
                avoided_genres = EXCLUDED.avoided_genres,
                preferred_decade = EXCLUDED.preferred_decade,
                mood_preference = EXCLUDED.mood_preference,
                min_rating = EXCLUDED.min_rating,
                updated_at = CURRENT_TIMESTAMP
            RETURNING pref_id
        """
        result = self.execute_query(query, (
            user_id,
            preferences.get('preferred_genres', []),
            preferences.get('avoided_genres', []),
            preferences.get('preferred_decade'),
            preferences.get('mood_preference'),
            preferences.get('min_rating', 6.0)
        ))
        return result[0] if result else None
    
    def get_user_preferences(self, user_id):
        """Get user preferences"""
        query = "SELECT * FROM user_preferences WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    # =========================================================
    # MOVIE OPERATIONS
    # =========================================================
    
    def get_movie(self, movie_id=None, tmdb_id=None):
        """Get movie by movie_id or tmdb_id"""
        if movie_id:
            query = "SELECT * FROM dim_movies WHERE movie_id = %s"
            result = self.execute_query(query, (movie_id,))
        elif tmdb_id:
            query = "SELECT * FROM dim_movies WHERE tmdb_id = %s"
            result = self.execute_query(query, (tmdb_id,))
        else:
            return None
        return result[0] if result else None
    
    def get_random_movies(self, limit=20, exclude_ids=None, min_rating=6.0):
        """Get random movies for swiping"""
        if exclude_ids:
            query = """
                SELECT * FROM dim_movies 
                WHERE vote_average >= %s AND movie_id != ALL(%s)
                ORDER BY RANDOM() 
                LIMIT %s
            """
            return self.execute_query(query, (min_rating, exclude_ids, limit))
        else:
            query = """
                SELECT * FROM dim_movies 
                WHERE vote_average >= %s
                ORDER BY RANDOM() 
                LIMIT %s
            """
            return self.execute_query(query, (min_rating, limit))
    
    def get_movies_by_genre(self, genres, limit=20, exclude_ids=None):
        """Get movies matching genres"""
        if exclude_ids:
            query = """
                SELECT * FROM dim_movies 
                WHERE genres && %s AND movie_id != ALL(%s)
                ORDER BY popularity DESC 
                LIMIT %s
            """
            return self.execute_query(query, (genres, exclude_ids, limit))
        else:
            query = """
                SELECT * FROM dim_movies 
                WHERE genres && %s
                ORDER BY popularity DESC 
                LIMIT %s
            """
            return self.execute_query(query, (genres, limit))
    
    def get_total_movies(self):
        """Get total movie count"""
        query = "SELECT COUNT(*) as count FROM dim_movies"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    # =========================================================
    # SWIPE OPERATIONS
    # =========================================================
    
    def record_swipe(self, user_id, movie_id, direction, session_id=None, 
                     time_spent_ms=None, recommendation_source=None):
        """Record a user swipe"""
        query = """
            INSERT INTO fact_swipes (user_id, movie_id, swipe_direction, 
                                    session_id, time_spent_ms, recommendation_source)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, movie_id) DO UPDATE SET
                swipe_direction = EXCLUDED.swipe_direction,
                swipe_timestamp = CURRENT_TIMESTAMP
            RETURNING swipe_id
        """
        result = self.execute_query(query, (
            user_id, movie_id, direction, session_id, time_spent_ms, recommendation_source
        ))
        
        # Update user stats
        self._update_user_swipe_stats(user_id, direction)
        
        return result[0] if result else None
    
    def _update_user_swipe_stats(self, user_id, direction):
        """Update user's swipe statistics"""
        if direction == 'right':
            query = """
                UPDATE dim_users 
                SET total_swipes = total_swipes + 1,
                    total_right_swipes = total_right_swipes + 1,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """
        else:
            query = """
                UPDATE dim_users 
                SET total_swipes = total_swipes + 1,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """
        self.execute_query(query, (user_id,), fetch=False)
    
    def get_user_swipes(self, user_id, direction=None):
        """Get all swipes for a user"""
        if direction:
            query = """
                SELECT s.*, m.title, m.genres 
                FROM fact_swipes s
                JOIN dim_movies m ON s.movie_id = m.movie_id
                WHERE s.user_id = %s AND s.swipe_direction = %s
                ORDER BY s.swipe_timestamp DESC
            """
            return self.execute_query(query, (user_id, direction))
        else:
            query = """
                SELECT s.*, m.title, m.genres 
                FROM fact_swipes s
                JOIN dim_movies m ON s.movie_id = m.movie_id
                WHERE s.user_id = %s
                ORDER BY s.swipe_timestamp DESC
            """
            return self.execute_query(query, (user_id,))
    
    def get_swiped_movie_ids(self, user_id):
        """Get list of movie IDs user has already swiped on"""
        query = "SELECT movie_id FROM fact_swipes WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return [r['movie_id'] for r in result] if result else []
    
    # =========================================================
    # RECOMMENDATION OPERATIONS
    # =========================================================
    
    def save_recommendations(self, user_id, recommendations):
        """Save recommendations for a user"""
        query = """
            INSERT INTO fact_recommendations 
            (user_id, movie_id, score, rank_position, algorithm_used, explanation_text)
            VALUES %s
        """
        data = [
            (user_id, r['movie_id'], r['score'], r['rank'], 
             r['algorithm'], r.get('explanation', ''))
            for r in recommendations
        ]
        self.execute_many(query, data)
    
    def get_user_recommendations(self, user_id, limit=10):
        """Get recommendations for a user"""
        query = """
            SELECT r.*, m.title, m.genres, m.overview, m.vote_average, m.poster_url
            FROM fact_recommendations r
            JOIN dim_movies m ON r.movie_id = m.movie_id
            WHERE r.user_id = %s AND r.was_shown = FALSE
            ORDER BY r.score DESC
            LIMIT %s
        """
        return self.execute_query(query, (user_id, limit))
    
    # =========================================================
    # ANALYTICS QUERIES
    # =========================================================
    
    def get_genre_stats(self, user_id=None):
        """Get genre statistics (overall or per user)"""
        if user_id:
            query = """
                SELECT * FROM vw_genre_preferences 
                WHERE user_id = %s 
                ORDER BY likes DESC
            """
            return self.execute_query(query, (user_id,))
        else:
            query = """
                SELECT 
                    UNNEST(m.genres) as genre,
                    COUNT(*) as total_swipes,
                    SUM(CASE WHEN s.swipe_direction = 'right' THEN 1 ELSE 0 END) as likes
                FROM fact_swipes s
                JOIN dim_movies m ON s.movie_id = m.movie_id
                GROUP BY UNNEST(m.genres)
                ORDER BY likes DESC
            """
            return self.execute_query(query)
    
    def get_algorithm_performance(self):
        """Get algorithm performance metrics"""
        query = "SELECT * FROM vw_algorithm_performance"
        return self.execute_query(query)


# Singleton instance
db = PostgresDB()

