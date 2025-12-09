"""
Data Loader Module
Loads Kaggle CSV data and populates databases
"""

import pandas as pd
import json
import sys
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DATA_RAW_PATH, TMDB_IMAGE_BASE_URL
from src.utils.db_postgres import db as postgres_db
from src.utils.db_mongo import mongo_db


class DataLoader:
    """Loads movie data from Kaggle CSVs into databases"""
    
    def __init__(self):
        self.movies_df = None
        self.credits_df = None
        
    def load_csv_files(self):
        """Load all CSV files from data/raw"""
        print("\n[1] Loading CSV files...")
        
        # TMDB Movies
        movies_path = DATA_RAW_PATH / "tmdb_5000_movies.csv"
        if movies_path.exists():
            self.movies_df = pd.read_csv(movies_path, encoding='utf-8', encoding_errors='replace')
            print(f"  ✓ Loaded {len(self.movies_df)} movies from tmdb_5000_movies.csv")
        else:
            print(f"  ✗ File not found: {movies_path}")
            return False
        
        # TMDB Credits (optional - for cast/crew)
        credits_path = DATA_RAW_PATH / "tmdb_5000_credits.csv"
        if credits_path.exists():
            self.credits_df = pd.read_csv(credits_path, encoding='utf-8', encoding_errors='replace')
            print(f"  ✓ Loaded {len(self.credits_df)} credit records")
        
        return True
    
    def parse_json_column(self, json_str, key='name'):
        """Parse JSON string column to list of values"""
        if pd.isna(json_str):
            return []
        try:
            items = json.loads(json_str.replace("'", '"'))
            return [item[key] for item in items if key in item]
        except:
            return []
    
    def transform_movies(self):
        """Transform raw movie data"""
        print("\n[2] Transforming movie data...")
        
        df = self.movies_df.copy()
        
        # Parse genres
        df['genres_list'] = df['genres'].apply(lambda x: self.parse_json_column(x, 'name'))
        
        # Parse keywords
        df['keywords_list'] = df['keywords'].apply(lambda x: self.parse_json_column(x, 'name'))
        
        # Extract release year
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        df['release_year'] = df['release_date'].dt.year
        
        # Create poster URL
        # Note: TMDB poster_path format is like "/poster.jpg"
        # Full URL would need API access, so we'll store the path
        df['poster_url'] = df.apply(
            lambda row: f"{TMDB_IMAGE_BASE_URL}{row.get('poster_path', '')}" 
            if pd.notna(row.get('poster_path')) else None, 
            axis=1
        )
        
        # Clean up
        df['overview'] = df['overview'].fillna('')
        df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)
        df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
        df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce').fillna(0)
        df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(0)
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
        df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce').fillna(0)
        
        print(f"  ✓ Transformed {len(df)} movies")
        print(f"  ✓ Sample genres: {df['genres_list'].iloc[0]}")
        
        self.movies_df = df
        return df
    
    def load_to_postgres(self):
        """Load transformed data into PostgreSQL"""
        print("\n[3] Loading data into PostgreSQL...")
        
        if not postgres_db.connect():
            print("  ✗ Could not connect to PostgreSQL")
            return False
        
        df = self.movies_df
        loaded_count = 0
        
        with postgres_db.get_cursor() as cur:
            for _, row in tqdm(df.iterrows(), total=len(df), desc="  Inserting movies"):
                try:
                    cur.execute("""
                        INSERT INTO dim_movies (
                            tmdb_id, title, genres, overview, release_year, 
                            release_date, popularity, vote_average, vote_count,
                            budget, revenue, runtime, original_language,
                            poster_url, keywords
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (tmdb_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            vote_average = EXCLUDED.vote_average,
                            popularity = EXCLUDED.popularity
                        RETURNING movie_id
                    """, (
                        row['id'],
                        row['title'],
                        row['genres_list'],
                        row['overview'],
                        row['release_year'] if pd.notna(row['release_year']) else None,
                        row['release_date'] if pd.notna(row['release_date']) else None,
                        row['popularity'],
                        row['vote_average'],
                        int(row['vote_count']),
                        int(row['budget']),
                        int(row['revenue']),
                        int(row['runtime']) if row['runtime'] > 0 else None,
                        row['original_language'],
                        row['poster_url'],
                        row['keywords_list']
                    ))
                    loaded_count += 1
                except Exception as e:
                    print(f"\n  ⚠ Error inserting {row['title']}: {e}")
                    continue
            
            postgres_db.conn.commit()
        
        print(f"  ✓ Loaded {loaded_count} movies into PostgreSQL")
        return True
    
    def load_to_mongo(self):
        """Load raw data into MongoDB (data lake)"""
        print("\n[4] Loading raw data into MongoDB...")
        
        if not mongo_db.connect():
            print("  ✗ Could not connect to MongoDB")
            return False
        
        # Store raw records
        records = self.movies_df.to_dict('records')
        count = mongo_db.store_raw_kaggle_data('tmdb_5000_movies', records)
        
        print(f"  ✓ Stored {count} raw records in MongoDB")
        return True
    
    def run_full_load(self):
        """Execute full data loading pipeline"""
        print("=" * 60)
        print("CINESWIPE - DATA LOADER")
        print("=" * 60)
        
        # Load CSVs
        if not self.load_csv_files():
            print("✗ Failed to load CSV files")
            return False
        
        # Transform
        self.transform_movies()
        
        # Load to PostgreSQL
        self.load_to_postgres()
        
        # Load to MongoDB
        self.load_to_mongo()
        
        # Cleanup
        postgres_db.disconnect()
        mongo_db.disconnect()
        
        print("\n" + "=" * 60)
        print("DATA LOADING COMPLETE")
        print("=" * 60)
        
        return True


def main():
    loader = DataLoader()
    loader.run_full_load()


if __name__ == "__main__":
    main()

