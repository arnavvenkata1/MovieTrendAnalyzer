"""
Data Cleaning Module
Handles cleaning of raw movie data from Kaggle dataset

Author: Anish Shah
Date: December 9, 2024
"""

import pandas as pd
import numpy as np
import json
from typing import List, Optional


class DataCleaner:
    """
    Handles cleaning operations on raw movie data
    """
    
    @staticmethod
    def parse_json_column(json_str, key='name'):
        """
        Parse JSON string column to extract values
        
        Args:
            json_str: JSON string (may be malformed)
            key: Key to extract from each JSON object
            
        Returns:
            List of extracted values
        """
        if pd.isna(json_str) or json_str == '':
            return []
        
        try:
            # Try to parse as proper JSON
            items = json.loads(json_str)
            if isinstance(items, list):
                return [item[key] for item in items if isinstance(item, dict) and key in item]
            return []
        except json.JSONDecodeError:
            # Try to fix common JSON issues (single quotes, etc.)
            try:
                items = json.loads(json_str.replace("'", '"'))
                if isinstance(items, list):
                    return [item[key] for item in items if isinstance(item, dict) and key in item]
            except:
                pass
            return []
        except Exception:
            return []
    
    @staticmethod
    def clean_text_column(series: pd.Series, fill_na: str = '') -> pd.Series:
        """
        Clean text columns
        
        Args:
            series: Pandas Series with text data
            fill_na: Value to fill NaN with
            
        Returns:
            Cleaned Series
        """
        cleaned = series.fillna(fill_na)
        # Remove extra whitespace
        cleaned = cleaned.str.strip()
        # Replace multiple spaces with single space
        cleaned = cleaned.str.replace(r'\s+', ' ', regex=True)
        return cleaned
    
    @staticmethod
    def clean_numeric_column(series: pd.Series, fill_na: float = 0.0) -> pd.Series:
        """
        Clean numeric columns
        
        Args:
            series: Pandas Series with numeric data
            fill_na: Value to fill NaN with
            
        Returns:
            Cleaned Series as numeric type
        """
        return pd.to_numeric(series, errors='coerce').fillna(fill_na)
    
    @staticmethod
    def clean_datetime_column(series: pd.Series) -> pd.Series:
        """
        Clean datetime columns
        
        Args:
            series: Pandas Series with date/datetime data
            
        Returns:
            Series converted to datetime
        """
        return pd.to_datetime(series, errors='coerce')
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = 'fill') -> pd.DataFrame:
        """
        Handle missing values in dataframe
        
        Args:
            df: Input dataframe
            strategy: 'fill' (fill with defaults) or 'drop' (drop rows)
            
        Returns:
            Cleaned dataframe
        """
        if strategy == 'drop':
            # Drop rows where critical columns are missing
            critical_cols = ['title', 'genres', 'overview']
            return df.dropna(subset=[col for col in critical_cols if col in df.columns])
        else:
            # Fill strategy (default)
            df_clean = df.copy()
            # Fill text columns with empty string
            text_cols = ['overview', 'title']
            for col in text_cols:
                if col in df_clean.columns:
                    df_clean[col] = DataCleaner.clean_text_column(df_clean[col])
            return df_clean
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove duplicate records
        
        Args:
            df: Input dataframe
            subset: Columns to check for duplicates (default: all columns)
            
        Returns:
            Dataframe with duplicates removed
        """
        if subset is None:
            subset = ['id'] if 'id' in df.columns else None
        
        return df.drop_duplicates(subset=subset, keep='first')
    
    @staticmethod
    def validate_movie_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate movie data and filter invalid records
        
        Args:
            df: Input dataframe
            
        Returns:
            Validated dataframe with invalid records removed
        """
        initial_count = len(df)
        
        # Remove rows with missing titles
        df = df[df['title'].notna() & (df['title'] != '')]
        
        # Remove rows with missing genres (empty lists)
        if 'genres_list' in df.columns:
            df = df[df['genres_list'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
        
        # Remove rows with very short overviews (likely incomplete data)
        if 'overview' in df.columns:
            df = df[df['overview'].str.len() > 10]
        
        removed = initial_count - len(df)
        if removed > 0:
            print(f"  ⚠ Removed {removed} invalid records during validation")
        
        return df

