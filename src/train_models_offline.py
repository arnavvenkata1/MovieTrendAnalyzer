"""
Offline Model Training Script
Train recommendation models directly from CSV files (no database required)
Run with: python src/train_models_offline.py
"""

import pandas as pd
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_RAW_PATH, MODELS_PATH
from src.models.content_based import ContentBasedRecommender
from src.models.hybrid import HybridRecommender


def load_movies_from_csv():
    """Load and prepare movie data from CSV"""
    print("Loading movies from CSV...")
    
    csv_path = DATA_RAW_PATH / "tmdb_5000_movies.csv"
    if not csv_path.exists():
        print(f"✗ File not found: {csv_path}")
        print("  Please download from Kaggle and place in data/raw/")
        return None
    
    df = pd.read_csv(csv_path, encoding='utf-8', encoding_errors='replace')
    print(f"✓ Loaded {len(df)} movies")
    
    # Parse genres from JSON
    def parse_genres(genres_str):
        if pd.isna(genres_str):
            return []
        try:
            genres = json.loads(genres_str.replace("'", '"'))
            return [g['name'] for g in genres]
        except:
            return []
    
    # Parse keywords from JSON
    def parse_keywords(kw_str):
        if pd.isna(kw_str):
            return []
        try:
            keywords = json.loads(kw_str.replace("'", '"'))
            return [k['name'] for k in keywords[:10]]  # Limit to 10 keywords
        except:
            return []
    
    df['genres'] = df['genres'].apply(parse_genres)
    df['keywords'] = df['keywords'].apply(parse_keywords)
    df['overview'] = df['overview'].fillna('')
    df['movie_id'] = df['id']  # Use TMDB ID as movie_id
    
    print(f"✓ Parsed genres and keywords")
    print(f"  Sample genres: {df['genres'].iloc[0]}")
    
    return df


def train_content_based_model(movies_df):
    """Train the content-based recommendation model"""
    print("\n" + "=" * 50)
    print("TRAINING CONTENT-BASED MODEL")
    print("=" * 50)
    
    model = ContentBasedRecommender()
    model.fit(movies_df)
    
    # Test with a sample movie
    print("\nTesting model with 'Avatar' (ID: 19995)...")
    similar = model.get_similar_movies(19995, n=5)
    
    if similar:
        print("Similar movies to Avatar:")
        for movie_id, score in similar:
            title = movies_df[movies_df['movie_id'] == movie_id]['title'].values
            if len(title) > 0:
                print(f"  - {title[0]}: {score:.3f}")
    
    # Save model
    model.save('content_based_model.pkl')
    
    return model


def test_recommendations(model, movies_df):
    """Test generating recommendations"""
    print("\n" + "=" * 50)
    print("TESTING RECOMMENDATIONS")
    print("=" * 50)
    
    # Simulate a user who liked these movies (by TMDB ID)
    liked_movies = [
        19995,   # Avatar
        24428,   # The Avengers
        135397,  # Jurassic World
    ]
    
    print(f"\nUser liked:")
    for mid in liked_movies:
        title = movies_df[movies_df['movie_id'] == mid]['title'].values
        if len(title) > 0:
            print(f"  - {title[0]}")
    
    # Get recommendations
    recommendations = model.recommend_for_user(
        liked_movie_ids=liked_movies,
        n=10,
        exclude_ids=liked_movies
    )
    
    print(f"\nTop 10 Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        title = movies_df[movies_df['movie_id'] == rec['movie_id']]['title'].values
        if len(title) > 0:
            print(f"  {i}. {title[0]} (score: {rec['score']:.3f})")


def create_sample_movies_json(movies_df, n=50):
    """Create a JSON file with sample movies for the Streamlit app"""
    print("\n" + "=" * 50)
    print("CREATING SAMPLE MOVIES FOR APP")
    print("=" * 50)
    
    # Get top movies by popularity
    top_movies = movies_df.nlargest(n, 'popularity')
    
    sample_movies = []
    for _, row in top_movies.iterrows():
        sample_movies.append({
            'movie_id': int(row['movie_id']),
            'title': row['title'],
            'release_year': int(row['release_date'][:4]) if pd.notna(row.get('release_date')) else None,
            'genres': row['genres'],
            'vote_average': float(row['vote_average']) if pd.notna(row['vote_average']) else 0,
            'overview': row['overview'][:300] + '...' if len(str(row['overview'])) > 300 else row['overview'],
            'popularity': float(row['popularity']) if pd.notna(row['popularity']) else 0
        })
    
    # Save to JSON
    import json
    output_path = DATA_RAW_PATH.parent / 'processed' / 'sample_movies.json'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(sample_movies, f, indent=2)
    
    print(f"✓ Saved {len(sample_movies)} sample movies to {output_path}")
    
    return sample_movies


def main():
    print("=" * 60)
    print("CINESWIPE - OFFLINE MODEL TRAINING")
    print("=" * 60)
    
    # Load data
    movies_df = load_movies_from_csv()
    if movies_df is None:
        return
    
    # Train content-based model
    model = train_content_based_model(movies_df)
    
    # Test recommendations
    test_recommendations(model, movies_df)
    
    # Create sample movies for app
    create_sample_movies_json(movies_df, n=100)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nModels saved to: {MODELS_PATH}")
    print(f"Sample movies saved to: data/processed/sample_movies.json")
    print("\nYou can now run the Streamlit app:")
    print("  streamlit run app/main.py")


if __name__ == "__main__":
    main()

