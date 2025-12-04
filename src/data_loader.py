"""
Data Loader Module
Loads CSV data into PostgreSQL (structured) and MongoDB (raw/unstructured)
"""

import pandas as pd
import json
import re
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATA_RAW_PATH, POSTGRES_CONFIG, MONGO_URI, MONGO_CONFIG
from tqdm import tqdm

# Database imports
try:
    import psycopg2
    from psycopg2.extras import execute_values
    from pymongo import MongoClient
except ImportError as e:
    print(f"Missing database driver: {e}")
    print("Run: pip install psycopg2-binary pymongo")


class DataLoader:
    """Handles loading data from CSVs into databases"""
    
    def __init__(self):
        self.pg_conn = None
        self.mongo_client = None
        self.mongo_db = None
        
    def connect_postgres(self):
        """Establish PostgreSQL connection"""
        try:
            self.pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
            print("✓ Connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"✗ PostgreSQL connection failed: {e}")
            return False
    
    def connect_mongo(self):
        """Establish MongoDB connection"""
        try:
            self.mongo_client = MongoClient(MONGO_URI)
            self.mongo_db = self.mongo_client[MONGO_CONFIG['database']]
            # Test connection
            self.mongo_client.server_info()
            print("✓ Connected to MongoDB")
            return True
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            return False
    
    def close_connections(self):
        """Close all database connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.mongo_client:
            self.mongo_client.close()
        print("Connections closed.")
    
    # =========================================================
    # CSV LOADING FUNCTIONS
    # =========================================================
    
    def load_letterboxd_csv(self):
        """Load Letterboxd reviews CSV into a DataFrame"""
        filepath = os.path.join(DATA_RAW_PATH, "letterboxd-reviews.csv")
        df = pd.read_csv(filepath, encoding='utf-8', encoding_errors='replace')
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Parse like_count (convert "22,446 likes" to integer)
        df['like_count'] = df['like_count'].apply(self._parse_like_count)
        
        # Parse comment_count
        df['comment_count'] = pd.to_numeric(df['comment_count'], errors='coerce').fillna(0).astype(int)
        
        # Parse review_date
        df['review_date'] = pd.to_datetime(df['review_date'], format='mixed', errors='coerce')
        
        # Add platform identifier
        df['platform'] = 'letterboxd'
        
        print(f"✓ Loaded {len(df)} Letterboxd reviews")
        return df
    
    def load_metacritic_csv(self):
        """Load Metacritic reviews CSV into a DataFrame"""
        filepath = os.path.join(DATA_RAW_PATH, "metacritic-reviews.csv")
        df = pd.read_csv(filepath, encoding='utf-8', encoding_errors='replace', on_bad_lines='skip')
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Parse release_date
        df['release_date'] = pd.to_datetime(df['release_date'], format='mixed', errors='coerce')
        
        # Add platform identifier
        df['platform'] = 'metacritic'
        
        print(f"✓ Loaded {len(df)} Metacritic reviews")
        return df
    
    def load_tmdb_movies_csv(self):
        """Load TMDB movies CSV with genre information"""
        filepath = os.path.join(DATA_RAW_PATH, "tmdb_5000_movies.csv")
        df = pd.read_csv(filepath, encoding='utf-8', encoding_errors='replace')
        
        # Parse genres from JSON string to list
        df['genres_list'] = df['genres'].apply(self._parse_genres_json)
        df['primary_genre'] = df['genres_list'].apply(lambda x: x[0] if x else 'Unknown')
        
        # Extract release year
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        df['release_year'] = df['release_date'].dt.year
        
        print(f"✓ Loaded {len(df)} TMDB movies")
        return df
    
    # =========================================================
    # HELPER FUNCTIONS
    # =========================================================
    
    def _parse_like_count(self, value):
        """Convert '22,446 likes' format to integer"""
        if pd.isna(value):
            return 0
        try:
            # Remove 'likes', commas, spaces, and convert to int
            cleaned = str(value).lower().replace('likes', '').replace('like', '')
            cleaned = cleaned.replace(',', '').replace(' ', '').strip()
            return int(float(cleaned)) if cleaned else 0
        except:
            return 0
    
    def _parse_genres_json(self, genres_str):
        """Parse TMDB genres JSON string to list of genre names"""
        if pd.isna(genres_str):
            return []
        try:
            genres = json.loads(genres_str.replace("'", '"'))
            return [g['name'] for g in genres]
        except:
            return []
    
    # =========================================================
    # DATABASE INSERTION FUNCTIONS
    # =========================================================
    
    def insert_raw_to_mongo(self, df, collection_name):
        """Insert raw DataFrame records into MongoDB"""
        if not self.mongo_db:
            print("MongoDB not connected!")
            return
        
        collection = self.mongo_db[collection_name]
        records = df.to_dict('records')
        
        # Convert datetime objects to strings for MongoDB
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        
        result = collection.insert_many(records)
        print(f"✓ Inserted {len(result.inserted_ids)} documents into MongoDB '{collection_name}'")
        return result.inserted_ids
    
    def insert_genres_to_postgres(self, genres_list):
        """Insert genres into dim_genres table"""
        if not self.pg_conn:
            print("PostgreSQL not connected!")
            return
        
        cursor = self.pg_conn.cursor()
        
        for genre in genres_list:
            cursor.execute("""
                INSERT INTO dim_genres (genre_name) 
                VALUES (%s) 
                ON CONFLICT (genre_name) DO NOTHING
            """, (genre,))
        
        self.pg_conn.commit()
        cursor.close()
        print(f"✓ Inserted {len(genres_list)} genres into PostgreSQL")
    
    def insert_movies_to_postgres(self, df):
        """Insert movies from TMDB into dim_movies table"""
        if not self.pg_conn:
            print("PostgreSQL not connected!")
            return
        
        cursor = self.pg_conn.cursor()
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Inserting movies"):
            # Get genre_id for primary genre
            cursor.execute(
                "SELECT genre_id FROM dim_genres WHERE genre_name = %s",
                (row['primary_genre'],)
            )
            result = cursor.fetchone()
            genre_id = result[0] if result else None
            
            cursor.execute("""
                INSERT INTO dim_movies (title, release_year, genre_id, tmdb_id, overview, popularity, vote_average, vote_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                row['title'],
                row['release_year'] if pd.notna(row['release_year']) else None,
                genre_id,
                row['id'],
                row['overview'] if pd.notna(row['overview']) else None,
                row['popularity'] if pd.notna(row['popularity']) else None,
                row['vote_average'] if pd.notna(row['vote_average']) else None,
                row['vote_count'] if pd.notna(row['vote_count']) else None
            ))
        
        self.pg_conn.commit()
        cursor.close()
        print(f"✓ Inserted movies into PostgreSQL")


# =========================================================
# MAIN EXECUTION
# =========================================================

def main():
    """Main function to load all data"""
    print("=" * 60)
    print("MOVIE TREND ANALYZER - DATA LOADER")
    print("=" * 60)
    
    loader = DataLoader()
    
    # Load CSVs into DataFrames
    print("\n[1/4] Loading CSV files...")
    letterboxd_df = loader.load_letterboxd_csv()
    metacritic_df = loader.load_metacritic_csv()
    tmdb_df = loader.load_tmdb_movies_csv()
    
    # Show sample data
    print("\n[Sample] Letterboxd columns:", letterboxd_df.columns.tolist())
    print("[Sample] TMDB genres found:", tmdb_df['primary_genre'].value_counts().head(10).to_dict())
    
    # Connect to databases
    print("\n[2/4] Connecting to databases...")
    pg_connected = loader.connect_postgres()
    mongo_connected = loader.connect_mongo()
    
    if mongo_connected:
        print("\n[3/4] Inserting raw data into MongoDB...")
        loader.insert_raw_to_mongo(letterboxd_df, 'letterboxd_raw')
        loader.insert_raw_to_mongo(metacritic_df, 'metacritic_raw')
        loader.insert_raw_to_mongo(tmdb_df, 'tmdb_movies_raw')
    
    if pg_connected:
        print("\n[4/4] Inserting structured data into PostgreSQL...")
        # Insert unique genres first
        all_genres = tmdb_df['genres_list'].explode().dropna().unique().tolist()
        loader.insert_genres_to_postgres(all_genres)
        
        # Insert movies
        loader.insert_movies_to_postgres(tmdb_df)
    
    # Cleanup
    loader.close_connections()
    
    print("\n" + "=" * 60)
    print("DATA LOADING COMPLETE")
    print("=" * 60)
    
    return letterboxd_df, metacritic_df, tmdb_df


if __name__ == "__main__":
    main()

