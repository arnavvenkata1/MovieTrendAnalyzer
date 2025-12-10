"""
Model Training Script for CineSwipe
Trains content-based and hybrid recommendation models using database data

Usage:
    python3 scripts/train_models.py

Author: Anish Shah
Date: December 9, 2024
"""

import sys
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.db_postgres import db as postgres_db
from src.models.content_based import ContentBasedRecommender
from src.models.hybrid import HybridRecommender
from config.settings import MODELS_PATH


def load_movies_from_database():
    """Load movie data from PostgreSQL database"""
    print("\n" + "=" * 60)
    print("LOADING MOVIE DATA FROM DATABASE")
    print("=" * 60)
    
    if not postgres_db.connect():
        print("✗ Failed to connect to PostgreSQL")
        return None
    
    print("\n[1] Querying movies from database...")
    
    # Query all movies with required fields
    query = """
        SELECT 
            movie_id,
            genres,
            keywords,
            overview,
            title,
            vote_average,
            popularity
        FROM dim_movies
        WHERE genres IS NOT NULL
        ORDER BY movie_id
    """
    
    movies = postgres_db.execute_query(query)
    
    if not movies:
        print("✗ No movies found in database")
        postgres_db.disconnect()
        return None
    
    print(f"✓ Loaded {len(movies)} movies from database")
    
    # Convert to DataFrame
    movies_df = pd.DataFrame(movies)
    
    # Ensure data types are correct
    print("\n[2] Processing movie data...")
    
    # Convert genres and keywords from list/array to list if needed
    # PostgreSQL arrays come as Python lists already, but let's ensure
    def ensure_list(val):
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            # Handle string representation of arrays
            import ast
            try:
                return ast.literal_eval(val)
            except:
                return []
        return []
    
    movies_df['genres'] = movies_df['genres'].apply(ensure_list)
    movies_df['keywords'] = movies_df['keywords'].apply(ensure_list)
    movies_df['overview'] = movies_df['overview'].fillna('')
    
    # Filter out movies with empty genres or overview
    initial_count = len(movies_df)
    movies_df = movies_df[
        (movies_df['genres'].apply(len) > 0) &
        (movies_df['overview'].str.len() > 0)
    ]
    
    removed = initial_count - len(movies_df)
    if removed > 0:
        print(f"  ⚠ Filtered out {removed} movies with missing data")
    
    print(f"✓ Ready to train on {len(movies_df)} movies")
    print(f"  Sample genres: {movies_df['genres'].iloc[0][:3] if len(movies_df) > 0 else 'N/A'}")
    
    postgres_db.disconnect()
    return movies_df


def load_swipes_from_database():
    """Load user swipe data from PostgreSQL database"""
    print("\n" + "=" * 60)
    print("LOADING SWIPE DATA FROM DATABASE")
    print("=" * 60)
    
    if not postgres_db.connect():
        print("✗ Failed to connect to PostgreSQL")
        return None
    
    print("\n[1] Querying swipes from database...")
    
    query = """
        SELECT 
            user_id,
            movie_id,
            swipe_direction
        FROM fact_swipes
        ORDER BY swipe_timestamp
    """
    
    swipes = postgres_db.execute_query(query)
    
    if not swipes:
        print("  ⚠ No swipe data found (this is expected for new installations)")
        print("  Collaborative filtering will be disabled until users start swiping")
        postgres_db.disconnect()
        return None
    
    print(f"✓ Loaded {len(swipes)} swipes from database")
    
    swipes_df = pd.DataFrame(swipes)
    
    # Check for minimum data requirements
    unique_users = swipes_df['user_id'].nunique()
    unique_movies = swipes_df['movie_id'].nunique()
    
    print(f"  Users: {unique_users}, Movies: {unique_movies}")
    
    if unique_users < 5:
        print("  ⚠ Warning: Very few users. Collaborative filtering may not work well.")
    
    postgres_db.disconnect()
    return swipes_df


def train_content_based_model(movies_df):
    """Train the content-based recommendation model"""
    print("\n" + "=" * 60)
    print("TRAINING CONTENT-BASED MODEL")
    print("=" * 60)
    
    try:
        model = ContentBasedRecommender()
        
        # Prepare data - only need movie_id, genres, keywords, overview
        training_data = movies_df[['movie_id', 'genres', 'keywords', 'overview']].copy()
        
        print(f"\n[1] Training on {len(training_data)} movies...")
        model.fit(training_data)
        
        print("\n[2] Saving model...")
        model.save('content_based_model.pkl')
        
        print("\n[3] Testing model...")
        # Test with first movie
        if len(training_data) > 0:
            test_movie_id = training_data['movie_id'].iloc[0]
            similar = model.get_similar_movies(test_movie_id, n=3)
            if similar:
                print(f"  ✓ Test: Similar movies to movie {test_movie_id}:")
                for mid, score in similar:
                    title = movies_df[movies_df['movie_id'] == mid]['title'].values[0] if len(movies_df[movies_df['movie_id'] == mid]) > 0 else f"Movie {mid}"
                    print(f"    - {title}: {score:.3f}")
        
        print("\n✅ Content-based model training complete!")
        return model
        
    except Exception as e:
        print(f"\n✗ Error training content-based model: {e}")
        import traceback
        traceback.print_exc()
        return None


def train_hybrid_model(movies_df, swipes_df=None):
    """Train the hybrid recommendation model"""
    print("\n" + "=" * 60)
    print("TRAINING HYBRID MODEL")
    print("=" * 60)
    
    try:
        model = HybridRecommender()
        
        # Prepare movie data
        training_data = movies_df[['movie_id', 'genres', 'keywords', 'overview']].copy()
        
        print(f"\n[1] Training on {len(training_data)} movies...")
        if swipes_df is not None and len(swipes_df) > 0:
            print(f"  Using {len(swipes_df)} swipes for collaborative component")
        else:
            print("  Collaborative component disabled (no swipe data)")
        
        model.fit(training_data, swipes_df=swipes_df)
        
        print("\n[2] Saving model...")
        model.save('hybrid')
        
        print("\n✅ Hybrid model training complete!")
        return model
        
    except Exception as e:
        print(f"\n✗ Error training hybrid model: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_model_files():
    """Verify that model files were created"""
    print("\n" + "=" * 60)
    print("VERIFYING MODEL FILES")
    print("=" * 60)
    
    models_to_check = [
        'content_based_model.pkl',
        'hybrid_content.pkl'
    ]
    
    all_exist = True
    for model_file in models_to_check:
        filepath = MODELS_PATH / model_file
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  ✓ {model_file} ({size_mb:.2f} MB)")
        else:
            print(f"  ✗ {model_file} - NOT FOUND")
            all_exist = False
    
    # Check for collaborative model (may not exist if no swipes)
    collab_file = MODELS_PATH / 'hybrid_collaborative.pkl'
    if collab_file.exists():
        size_mb = collab_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ hybrid_collaborative.pkl ({size_mb:.2f} MB)")
    else:
        print(f"  ⚠ hybrid_collaborative.pkl - Not created (no swipe data)")
    
    return all_exist


def main():
    """Main training function"""
    print("=" * 60)
    print("CINESWIPE - MODEL TRAINING")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Load movie data from PostgreSQL")
    print("  2. Train content-based recommendation model")
    print("  3. Train hybrid recommendation model")
    print("  4. Save models to disk")
    print("\n" + "=" * 60)
    
    # Ensure models directory exists
    MODELS_PATH.mkdir(parents=True, exist_ok=True)
    print(f"\nModels will be saved to: {MODELS_PATH}")
    
    # Load data
    movies_df = load_movies_from_database()
    if movies_df is None or len(movies_df) == 0:
        print("\n✗ Cannot proceed without movie data")
        return False
    
    swipes_df = load_swipes_from_database()
    
    # Train models
    content_model = train_content_based_model(movies_df)
    if content_model is None:
        print("\n✗ Failed to train content-based model")
        return False
    
    hybrid_model = train_hybrid_model(movies_df, swipes_df)
    if hybrid_model is None:
        print("\n✗ Failed to train hybrid model")
        return False
    
    # Verify
    verify_model_files()
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print("\n✅ Models are ready to use in the Streamlit app")
    print(f"📁 Models saved in: {MODELS_PATH}")
    print("\nNext steps:")
    print("  1. Test models in the Streamlit app")
    print("  2. Once users start swiping, retrain to enable collaborative filtering")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

