"""
ETL (Extract, Transform, Load) Pipeline
Processes raw data from MongoDB, transforms it, and loads into PostgreSQL
"""

import pandas as pd
import numpy as np
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATA_RAW_PATH, POSTGRES_CONFIG, MONGO_URI, MONGO_CONFIG
from src.sentiment import SentimentAnalyzer
from src.data_loader import DataLoader


class ETLPipeline:
    """
    ETL Pipeline for Movie Trend Analyzer
    Extract from MongoDB/CSV → Transform → Load to PostgreSQL
    """
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_loader = DataLoader()
        
    # =========================================================
    # EXTRACT PHASE
    # =========================================================
    
    def extract_from_csv(self):
        """Extract data directly from CSV files"""
        print("\n[EXTRACT] Loading data from CSV files...")
        
        letterboxd_df = self.data_loader.load_letterboxd_csv()
        metacritic_df = self.data_loader.load_metacritic_csv()
        tmdb_df = self.data_loader.load_tmdb_movies_csv()
        
        return {
            'letterboxd': letterboxd_df,
            'metacritic': metacritic_df,
            'tmdb': tmdb_df
        }
    
    # =========================================================
    # TRANSFORM PHASE
    # =========================================================
    
    def transform_letterboxd(self, df, tmdb_df):
        """Transform Letterboxd reviews with genre mapping and sentiment"""
        print("\n[TRANSFORM] Processing Letterboxd reviews...")
        
        # Create title lookup from TMDB
        title_to_genre = self._create_genre_lookup(tmdb_df)
        
        # Extract movie title without year for matching
        df['movie_title_clean'] = df['movie_name'].str.replace(r'\s*\(\d{4}\)\s*$', '', regex=True).str.strip().str.lower()
        
        # Map genres
        df['genre'] = df['movie_title_clean'].map(title_to_genre).fillna('Unknown')
        
        # For movies still Unknown, try to infer genre from title keywords
        df['genre'] = df.apply(lambda row: self._infer_genre_from_title(row['movie_name']) 
                               if row['genre'] == 'Unknown' else row['genre'], axis=1)
        
        # Add sentiment analysis
        df = self.sentiment_analyzer.analyze_dataframe(df, text_column='review', output_prefix='sentiment')
        
        # Parse rating (handle star symbols)
        df['rating_numeric'] = df['rating'].apply(self._parse_star_rating)
        
        # Calculate engagement score
        df['engagement_score'] = df['like_count'] + (df['comment_count'] * 2)  # Comments worth more
        
        # Create Hype Index
        df['hype_index'] = self._calculate_hype_index(df)
        
        print(f"✓ Transformed {len(df)} Letterboxd reviews")
        print(f"  Genres mapped: {df['genre'].value_counts().head(5).to_dict()}")
        
        return df
    
    def transform_metacritic(self, df, tmdb_df):
        """Transform Metacritic reviews with genre mapping and sentiment"""
        print("\n[TRANSFORM] Processing Metacritic reviews...")
        
        # Create title lookup from TMDB
        title_to_genre = self._create_genre_lookup(tmdb_df)
        
        # Map genres
        df['genre'] = df['movie_name'].map(title_to_genre).fillna('Unknown')
        
        # Add sentiment analysis on summary
        df = self.sentiment_analyzer.analyze_dataframe(df, text_column='summary', output_prefix='sentiment')
        
        # Normalize ratings
        df['user_rating_norm'] = pd.to_numeric(df['user_rating'], errors='coerce') / 10.0
        df['website_rating_norm'] = pd.to_numeric(df['website_rating'], errors='coerce') / 100.0
        
        print(f"✓ Transformed {len(df)} Metacritic reviews")
        
        return df
    
    def aggregate_daily_trends(self, df, date_column='review_date'):
        """Aggregate data into daily trends by genre"""
        print("\n[TRANSFORM] Aggregating daily trends...")
        
        # Ensure date column is datetime
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # Remove rows without dates
        df_valid = df.dropna(subset=[date_column])
        
        # Extract just the date (no time)
        df_valid['date'] = df_valid[date_column].dt.date
        
        # Aggregate by date and genre
        daily_trends = df_valid.groupby(['date', 'genre']).agg({
            'movie_name': 'count',  # Total reviews
            'like_count': 'sum' if 'like_count' in df_valid.columns else lambda x: 0,
            'comment_count': 'sum' if 'comment_count' in df_valid.columns else lambda x: 0,
            'sentiment_compound': 'mean',
            'rating_numeric': 'mean' if 'rating_numeric' in df_valid.columns else lambda x: None,
        }).reset_index()
        
        daily_trends.columns = ['date', 'genre', 'total_reviews', 'total_likes', 
                                'total_comments', 'avg_sentiment', 'avg_rating']
        
        # Calculate total engagement
        daily_trends['total_engagement'] = daily_trends['total_likes'] + daily_trends['total_comments']
        
        # Calculate velocity (% change from previous day per genre)
        daily_trends = daily_trends.sort_values(['genre', 'date'])
        daily_trends['prev_engagement'] = daily_trends.groupby('genre')['total_engagement'].shift(1)
        daily_trends['velocity'] = ((daily_trends['total_engagement'] - daily_trends['prev_engagement']) 
                                    / daily_trends['prev_engagement'].replace(0, 1) * 100).round(2)
        
        print(f"✓ Created {len(daily_trends)} daily trend records")
        
        return daily_trends
    
    # =========================================================
    # HELPER FUNCTIONS
    # =========================================================
    
    def _create_genre_lookup(self, tmdb_df):
        """Create dictionary mapping movie titles to primary genre"""
        # Create lookup with normalized titles (lowercase, stripped)
        lookup = {}
        for _, row in tmdb_df.iterrows():
            title = str(row['title']).lower().strip()
            genre = row['primary_genre']
            lookup[title] = genre
        return lookup
    
    def _infer_genre_from_title(self, title):
        """Infer genre from movie title using keyword matching"""
        if pd.isna(title):
            return 'Drama'  # Default genre
        
        title_lower = str(title).lower()
        
        # Genre keywords mapping
        genre_keywords = {
            'Horror': ['horror', 'scary', 'haunted', 'possessed', 'evil', 'scream', 'nightmare', 'halloween', 'exorcist'],
            'Comedy': ['comedy', 'funny', 'hangover', 'superbad', 'bridesmaids'],
            'Action': ['avengers', 'batman', 'spider-man', 'iron man', 'thor', 'captain', 'fast', 'furious', 'mission impossible', 'john wick'],
            'Sci-Fi': ['star wars', 'star trek', 'alien', 'aliens', 'matrix', 'blade runner', 'dune', 'avatar'],
            'Animation': ['pixar', 'disney', 'animated', 'toy story', 'finding', 'incredibles', 'frozen', 'encanto', 'luca'],
            'Romance': ['love', 'romantic', 'notebook', 'pride', 'prejudice', 'bridget jones'],
            'Thriller': ['thriller', 'gone girl', 'silence', 'lambs', 'psycho', 'shutter'],
            'Fantasy': ['lord of the rings', 'hobbit', 'harry potter', 'narnia', 'fantastic beasts']
        }
        
        for genre, keywords in genre_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return genre
        
        return 'Drama'  # Default fallback
    
    def _parse_star_rating(self, rating_str):
        """Convert star rating string to numeric (0-5 scale)"""
        if pd.isna(rating_str):
            return None
        
        rating_str = str(rating_str)
        
        # Count full stars and half stars (unicode or text)
        full_stars = rating_str.count('★') + rating_str.count('�??')
        half_stars = rating_str.count('½')
        
        # Fallback: check for numeric
        if full_stars == 0 and half_stars == 0:
            try:
                return float(rating_str)
            except:
                return None
        
        return full_stars + (half_stars * 0.5)
    
    def _calculate_hype_index(self, df):
        """
        Calculate normalized Hype Index combining engagement and sentiment
        Formula: (normalized_engagement * 0.6) + (normalized_sentiment * 0.4)
        """
        # Normalize engagement to 0-1 scale
        max_engagement = df['engagement_score'].max()
        if max_engagement > 0:
            norm_engagement = df['engagement_score'] / max_engagement
        else:
            norm_engagement = 0
        
        # Normalize sentiment from (-1, 1) to (0, 1)
        norm_sentiment = (df['sentiment_compound'] + 1) / 2
        
        # Calculate hype index
        hype_index = (norm_engagement * 0.6) + (norm_sentiment * 0.4)
        
        return (hype_index * 100).round(2)  # Scale to 0-100
    
    # =========================================================
    # LOAD PHASE
    # =========================================================
    
    def save_processed_data(self, data_dict, output_dir=None):
        """Save processed DataFrames to CSV files"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      'data', 'processed')
        
        os.makedirs(output_dir, exist_ok=True)
        
        for name, df in data_dict.items():
            filepath = os.path.join(output_dir, f'{name}_processed.csv')
            df.to_csv(filepath, index=False)
            print(f"✓ Saved {name} to {filepath}")
    
    # =========================================================
    # FULL PIPELINE
    # =========================================================
    
    def run_full_pipeline(self):
        """Execute the complete ETL pipeline"""
        print("=" * 60)
        print("ETL PIPELINE - STARTING")
        print("=" * 60)
        
        # EXTRACT
        raw_data = self.extract_from_csv()
        
        # TRANSFORM
        letterboxd_transformed = self.transform_letterboxd(
            raw_data['letterboxd'], 
            raw_data['tmdb']
        )
        
        metacritic_transformed = self.transform_metacritic(
            raw_data['metacritic'],
            raw_data['tmdb']
        )
        
        # Aggregate daily trends
        daily_trends = self.aggregate_daily_trends(letterboxd_transformed)
        
        # LOAD (save to CSV for now)
        processed_data = {
            'letterboxd': letterboxd_transformed,
            'metacritic': metacritic_transformed,
            'daily_trends': daily_trends,
            'tmdb_movies': raw_data['tmdb']
        }
        
        self.save_processed_data(processed_data)
        
        print("\n" + "=" * 60)
        print("ETL PIPELINE - COMPLETE")
        print("=" * 60)
        
        return processed_data


# =========================================================
# MAIN EXECUTION
# =========================================================

def main():
    """Run the ETL pipeline"""
    pipeline = ETLPipeline()
    processed_data = pipeline.run_full_pipeline()
    
    # Show summary
    print("\n[SUMMARY]")
    for name, df in processed_data.items():
        print(f"  {name}: {len(df)} records, {len(df.columns)} columns")


if __name__ == "__main__":
    main()

