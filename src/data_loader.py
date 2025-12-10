"""
Data Loader Module
Loads Kaggle CSV data and populates databases
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DATA_RAW_PATH
from src.utils.db_postgres import db as postgres_db
from src.utils.db_mongo import mongo_db
from changing_data.data_cleaner import DataCleaner
from changing_data.data_transformer import DataTransformer


class DataLoader:
    """Loads movie data from Kaggle CSVs into databases"""
    
    def __init__(self):
        self.movies_df = None
        self.credits_df = None
        self.cleaner = DataCleaner()
        self.transformer = DataTransformer()
        
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
    
    def clean_movies(self):
        """Clean raw movie data"""
        print("\n[2] Cleaning movie data...")
        
        df = self.movies_df.copy()
        
        # Handle missing values
        df = self.cleaner.handle_missing_values(df, strategy='fill')
        
        # Remove duplicates
        df = self.cleaner.remove_duplicates(df, subset=['id'])
        
        # Validate data
        df = self.cleaner.validate_movie_data(df)
        
        self.movies_df = df
        print(f"  ✓ Cleaned {len(df)} movies")
        return df
    
    def transform_movies(self):
        """Transform cleaned movie data"""
        print("\n[3] Transforming movie data...")
        
        # Use transformer to apply all transformations
        df_transformed = self.transformer.transform_movies(self.movies_df)
        
        self.movies_df = df_transformed
        return df_transformed
    
    def load_to_postgres(self):
        """Load transformed data into PostgreSQL"""
        print("\n[4] Loading data into PostgreSQL...")
        
        if not postgres_db.connect():
            print("  ✗ Could not connect to PostgreSQL")
            return False
        
        # Prepare data for PostgreSQL
        df = self.transformer.prepare_for_postgres(self.movies_df)
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
                        row.get('genres', row.get('genres_list', [])),
                        row['overview'],
                        row['release_year'] if pd.notna(row['release_year']) else None,
                        row['release_date'] if pd.notna(row['release_date']) else None,
                        row['popularity'],
                        row['vote_average'],
                        int(row['vote_count']),
                        int(row['budget']),
                        int(row['revenue']),
                        int(row['runtime']) if pd.notna(row['runtime']) and row['runtime'] > 0 else None,
                        row['original_language'],
                        row.get('poster_url'),
                        row.get('keywords', row.get('keywords_list', []))
                    ))
                    loaded_count += 1
                except Exception as e:
                    print(f"\n  ⚠ Error inserting {row.get('title', 'Unknown')}: {e}")
                    continue
            
            postgres_db.conn.commit()
        
        print(f"  ✓ Loaded {loaded_count} movies into PostgreSQL")
        return True
    
    def load_to_mongo(self):
        """Load raw data into MongoDB (data lake)"""
        print("\n[5] Loading raw data into MongoDB...")
        
        if not mongo_db.connect():
            print("  ✗ Could not connect to MongoDB")
            return False
        
        # Prepare data for MongoDB (handles NaT/NaN)
        df_mongo = self.transformer.prepare_for_mongo(self.movies_df)
        
        # Convert to dict records
        records = df_mongo.to_dict('records')
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
        
        # Clean data
        self.clean_movies()
        
        # Transform data
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

