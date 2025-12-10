"""
Data Transformation Module
Handles transformation of cleaned movie data into analysis-ready format

Author: Anish Shah
Date: December 9, 2024
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from changing_data.data_cleaner import DataCleaner


class DataTransformer:
    """
    Handles transformation operations on cleaned movie data
    """
    
    def __init__(self):
        self.cleaner = DataCleaner()
    
    def transform_movies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw movie data into analysis-ready format
        
        Args:
            df: Raw movie dataframe from Kaggle CSV
            
        Returns:
            Transformed dataframe with all derived columns
        """
        print("\n[1] Parsing JSON columns...")
        # Parse genres from JSON
        df['genres_list'] = df['genres'].apply(
            lambda x: self.cleaner.parse_json_column(x, 'name')
        )
        
        # Parse keywords from JSON
        df['keywords_list'] = df['keywords'].apply(
            lambda x: self.cleaner.parse_json_column(x, 'name')
        )
        
        print("[2] Extracting date/time features...")
        # Extract release year from date
        df['release_date'] = self.cleaner.clean_datetime_column(df['release_date'])
        df['release_year'] = df['release_date'].dt.year
        
        # Extract decade
        df['decade'] = (df['release_year'] // 10) * 10
        
        print("[3] Creating derived features...")
        # Create poster URL
        df['poster_url'] = df.apply(self._create_poster_url, axis=1)
        
        # Calculate profit (revenue - budget)
        df['profit'] = df.apply(self._calculate_profit, axis=1)
        
        # Calculate ROI (return on investment)
        df['roi'] = df.apply(self._calculate_roi, axis=1)
        
        # Create genre count
        df['genre_count'] = df['genres_list'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        
        # Create keywords count
        df['keyword_count'] = df['keywords_list'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        
        print("[4] Cleaning numeric columns...")
        # Clean numeric columns
        numeric_cols = {
            'vote_average': 0.0,
            'vote_count': 0,
            'popularity': 0.0,
            'budget': 0,
            'revenue': 0,
            'runtime': None  # Keep as None if missing (can't assume 0)
        }
        
        for col, default in numeric_cols.items():
            if col in df.columns:
                if default is None:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                else:
                    df[col] = self.cleaner.clean_numeric_column(df[col], fill_na=default)
        
        print("[5] Cleaning text columns...")
        # Clean text columns
        if 'overview' in df.columns:
            df['overview'] = self.cleaner.clean_text_column(df['overview'])
        
        if 'title' in df.columns:
            df['title'] = self.cleaner.clean_text_column(df['title'])
        
        print("[6] Creating categorical features...")
        # Create rating category
        df['rating_category'] = df['vote_average'].apply(self._categorize_rating)
        
        # Create budget category
        df['budget_category'] = df['budget'].apply(self._categorize_budget)
        
        # Create runtime category
        df['runtime_category'] = df['runtime'].apply(self._categorize_runtime)
        
        print(f"  ✓ Transformed {len(df)} movies")
        if len(df) > 0:
            print(f"  ✓ Sample genres: {df['genres_list'].iloc[0][:3]}")
            print(f"  ✓ Date range: {df['release_year'].min()} - {df['release_year'].max()}")
        
        return df
    
    def _create_poster_url(self, row) -> Optional[str]:
        """Create full poster URL from poster_path"""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config.settings import TMDB_IMAGE_BASE_URL
        
        poster_path = row.get('poster_path')
        if pd.notna(poster_path) and poster_path != '':
            return f"{TMDB_IMAGE_BASE_URL}{poster_path}"
        return None
    
    def _calculate_profit(self, row) -> float:
        """Calculate profit (revenue - budget)"""
        revenue = row.get('revenue', 0) or 0
        budget = row.get('budget', 0) or 0
        return float(revenue - budget) if revenue > 0 and budget > 0 else None
    
    def _calculate_roi(self, row) -> Optional[float]:
        """Calculate ROI percentage"""
        revenue = row.get('revenue', 0) or 0
        budget = row.get('budget', 0) or 0
        
        if budget > 0 and revenue > 0:
            return ((revenue - budget) / budget) * 100
        return None
    
    def _categorize_rating(self, rating: float) -> str:
        """Categorize movie rating"""
        if pd.isna(rating):
            return 'Unknown'
        if rating >= 8.0:
            return 'Excellent'
        elif rating >= 7.0:
            return 'Very Good'
        elif rating >= 6.0:
            return 'Good'
        elif rating >= 5.0:
            return 'Average'
        else:
            return 'Below Average'
    
    def _categorize_budget(self, budget: float) -> str:
        """Categorize movie budget"""
        if pd.isna(budget) or budget == 0:
            return 'Unknown'
        budget_millions = budget / 1_000_000
        if budget_millions >= 100:
            return 'Blockbuster (100M+)'
        elif budget_millions >= 50:
            return 'Big Budget (50-100M)'
        elif budget_millions >= 20:
            return 'Mid Budget (20-50M)'
        elif budget_millions >= 5:
            return 'Low Budget (5-20M)'
        else:
            return 'Indie (<5M)'
    
    def _categorize_runtime(self, runtime: float) -> str:
        """Categorize movie runtime"""
        if pd.isna(runtime) or runtime == 0:
            return 'Unknown'
        if runtime >= 150:
            return 'Epic (150+ min)'
        elif runtime >= 120:
            return 'Long (120-150 min)'
        elif runtime >= 90:
            return 'Standard (90-120 min)'
        elif runtime >= 60:
            return 'Short (60-90 min)'
        else:
            return 'Very Short (<60 min)'
    
    def prepare_for_postgres(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare dataframe for PostgreSQL insertion
        
        Args:
            df: Transformed dataframe
            
        Returns:
            DataFrame ready for PostgreSQL
        """
        # Ensure required columns exist and are in correct format
        pg_df = df.copy()
        
        # Rename columns if needed
        if 'genres_list' in pg_df.columns:
            pg_df['genres'] = pg_df['genres_list']
        if 'keywords_list' in pg_df.columns:
            pg_df['keywords'] = pg_df['keywords_list']
        
        # Ensure data types are correct
        if 'release_year' in pg_df.columns:
            pg_df['release_year'] = pg_df['release_year'].astype('Int64')  # Nullable integer
        
        return pg_df
    
    def prepare_for_mongo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare dataframe for MongoDB insertion (handle NaT/NaN)
        
        Args:
            df: Transformed dataframe
            
        Returns:
            DataFrame ready for MongoDB (NaT/NaN replaced with None)
        """
        mongo_df = df.copy()
        
        # Replace NaT in datetime columns
        for col in mongo_df.select_dtypes(include=['datetime64']).columns:
            mongo_df[col] = mongo_df[col].replace({pd.NaT: None})
        
        # Replace NaN with None for MongoDB compatibility
        mongo_df = mongo_df.replace({np.nan: None, pd.NA: None})
        
        return mongo_df

