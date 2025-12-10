"""
Download Full TMDB Dataset
Downloads the complete TMDB movie database with 45,000+ movies

This uses the "The Movies Dataset" from Kaggle which includes:
- 45,000+ movies
- Full metadata (genres, keywords, cast, crew)
- Multiple languages
- User ratings
"""

import os
import sys
import json
import gzip
import urllib.request
from pathlib import Path
from datetime import datetime

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))


def download_kaggle_movies_dataset():
    """Download the full movies dataset from Kaggle"""
    print("=" * 60)
    print("DOWNLOADING FULL TMDB DATASET")
    print("=" * 60)
    
    data_dir = Path(__file__).parent.parent / 'data' / 'raw'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nThis script will download 'The Movies Dataset' from Kaggle")
    print("which contains 45,000+ movies with full metadata.\n")
    
    # Check if kagglehub is available
    try:
        import kagglehub
        
        print("[1] Downloading from Kaggle...")
        print("    Dataset: rounakbanik/the-movies-dataset")
        
        # Download the dataset
        path = kagglehub.dataset_download("rounakbanik/the-movies-dataset")
        
        print(f"    Downloaded to: {path}")
        
        # Copy files to our data directory
        import shutil
        
        files_to_copy = [
            'movies_metadata.csv',  # Main movie data - 45K movies
            'credits.csv',          # Cast and crew
            'keywords.csv',         # Keywords for each movie
            'ratings.csv',          # User ratings (26M ratings!)
            'links.csv',            # IMDB and TMDB IDs
        ]
        
        print("\n[2] Copying files to project...")
        
        for filename in files_to_copy:
            src = Path(path) / filename
            dst = data_dir / filename
            
            if src.exists():
                shutil.copy(src, dst)
                size_mb = dst.stat().st_size / (1024 * 1024)
                print(f"    ✓ {filename} ({size_mb:.1f} MB)")
            else:
                print(f"    ✗ {filename} not found")
        
        return True
        
    except ImportError:
        print("kagglehub not installed. Installing...")
        os.system("pip install kagglehub --quiet")
        print("Please run this script again.")
        return False
    except Exception as e:
        print(f"Error downloading from Kaggle: {e}")
        print("\nAlternative: Manual download")
        print("1. Go to: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset")
        print("2. Download and extract to: data/raw/")
        return False


def process_movies_metadata():
    """Process the downloaded movies_metadata.csv into our format"""
    print("\n" + "=" * 60)
    print("PROCESSING MOVIE DATA")
    print("=" * 60)
    
    import pandas as pd
    import ast
    
    data_dir = Path(__file__).parent.parent / 'data' / 'raw'
    output_dir = Path(__file__).parent.parent / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    movies_file = data_dir / 'movies_metadata.csv'
    
    if not movies_file.exists():
        print(f"✗ movies_metadata.csv not found in {data_dir}")
        return False
    
    print("\n[1] Loading movies_metadata.csv...")
    
    # Load with error handling for bad rows
    df = pd.read_csv(
        movies_file, 
        low_memory=False,
        on_bad_lines='skip'
    )
    
    print(f"    Loaded {len(df)} rows")
    
    print("\n[2] Cleaning data...")
    
    # Filter to only movies with valid IDs
    df = df[df['id'].apply(lambda x: str(x).isdigit())]
    df['id'] = df['id'].astype(int)
    
    # Parse JSON columns
    def safe_parse_json(val):
        if pd.isna(val):
            return []
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [item.get('name', '') for item in parsed if isinstance(item, dict)]
            return []
        except:
            return []
    
    print("    Parsing genres...")
    df['genres_list'] = df['genres'].apply(safe_parse_json)
    
    print("    Parsing production countries...")
    df['countries'] = df['production_countries'].apply(safe_parse_json)
    
    print("    Parsing spoken languages...")
    df['languages'] = df['spoken_languages'].apply(safe_parse_json)
    
    # Filter valid movies
    print("\n[3] Filtering valid movies...")
    
    # Must have title, release date, and at least one genre
    df = df[
        (df['title'].notna()) & 
        (df['title'].str.len() > 0) &
        (df['release_date'].notna()) &
        (df['genres_list'].apply(len) > 0)
    ]
    
    # Extract year
    df['release_year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
    df = df[df['release_year'].notna()]
    df['release_year'] = df['release_year'].astype(int)
    
    print(f"    {len(df)} valid movies after filtering")
    
    # Select and rename columns
    print("\n[4] Creating output format...")
    
    output_df = pd.DataFrame({
        'movie_id': df['id'],
        'title': df['title'],
        'original_title': df['original_title'],
        'release_year': df['release_year'],
        'genres': df['genres_list'],
        'overview': df['overview'].fillna(''),
        'vote_average': pd.to_numeric(df['vote_average'], errors='coerce').fillna(0),
        'vote_count': pd.to_numeric(df['vote_count'], errors='coerce').fillna(0),
        'popularity': pd.to_numeric(df['popularity'], errors='coerce').fillna(0),
        'runtime': pd.to_numeric(df['runtime'], errors='coerce').fillna(0),
        'original_language': df['original_language'],
        'languages': df['languages'],
        'countries': df['countries'],
        'tagline': df['tagline'].fillna(''),
        'budget': pd.to_numeric(df['budget'], errors='coerce').fillna(0),
        'revenue': pd.to_numeric(df['revenue'], errors='coerce').fillna(0),
    })
    
    # Sort by popularity
    output_df = output_df.sort_values('popularity', ascending=False)
    
    print(f"    Final dataset: {len(output_df)} movies")
    
    # Save to CSV
    print("\n[5] Saving processed data...")
    
    csv_path = output_dir / 'full_movies_dataset.csv'
    output_df.to_csv(csv_path, index=False)
    print(f"    ✓ Saved CSV: {csv_path}")
    
    # Also save as JSON for the app (top 5000 for performance)
    print("\n[6] Creating JSON for app (top 5000 movies)...")
    
    top_movies = output_df.head(5000)
    
    json_data = []
    for _, row in top_movies.iterrows():
        json_data.append({
            'movie_id': int(row['movie_id']),
            'title': row['title'],
            'original_title': row['original_title'],
            'release_year': int(row['release_year']),
            'genres': row['genres'] if isinstance(row['genres'], list) else [],
            'overview': row['overview'][:500] if row['overview'] else '',
            'vote_average': float(row['vote_average']),
            'vote_count': int(row['vote_count']),
            'runtime': int(row['runtime']) if row['runtime'] > 0 else None,
            'original_language': row['original_language'],
            'tagline': row['tagline'][:200] if row['tagline'] else '',
        })
    
    json_path = output_dir / 'sample_movies.json'
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"    ✓ Saved JSON: {json_path}")
    
    # Stats
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    
    print(f"\n📊 Total movies: {len(output_df):,}")
    print(f"📅 Year range: {output_df['release_year'].min()} - {output_df['release_year'].max()}")
    print(f"🌍 Languages: {output_df['original_language'].nunique()}")
    print(f"⭐ Average rating: {output_df['vote_average'].mean():.2f}")
    
    # Genre breakdown
    all_genres = []
    for genres in output_df['genres']:
        if isinstance(genres, list):
            all_genres.extend(genres)
    
    from collections import Counter
    genre_counts = Counter(all_genres)
    
    print(f"\n🎭 Top genres:")
    for genre, count in genre_counts.most_common(10):
        print(f"    {genre}: {count:,}")
    
    # Language breakdown
    lang_counts = output_df['original_language'].value_counts()
    print(f"\n🗣️ Top languages:")
    for lang, count in lang_counts.head(10).items():
        print(f"    {lang}: {count:,}")
    
    return True


def process_keywords():
    """Process keywords.csv and merge with movies"""
    print("\n" + "=" * 60)
    print("PROCESSING KEYWORDS")
    print("=" * 60)
    
    import pandas as pd
    import ast
    
    data_dir = Path(__file__).parent.parent / 'data' / 'raw'
    
    keywords_file = data_dir / 'keywords.csv'
    
    if not keywords_file.exists():
        print("Keywords file not found, skipping...")
        return {}
    
    print("[1] Loading keywords.csv...")
    
    df = pd.read_csv(keywords_file)
    print(f"    Loaded {len(df)} rows")
    
    def parse_keywords(val):
        try:
            parsed = ast.literal_eval(val)
            return [k.get('name', '') for k in parsed if isinstance(k, dict)]
        except:
            return []
    
    print("[2] Parsing keywords...")
    df['keywords_list'] = df['keywords'].apply(parse_keywords)
    
    # Create dict mapping movie_id to keywords
    keywords_dict = dict(zip(df['id'], df['keywords_list']))
    
    print(f"    ✓ Processed keywords for {len(keywords_dict)} movies")
    
    return keywords_dict


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("FULL TMDB DATASET DOWNLOADER")
    print("=" * 60)
    print("\nThis will download ~45,000 movies from Kaggle's")
    print("'The Movies Dataset' and process them for CineSwipe.\n")
    
    # Download
    success = download_kaggle_movies_dataset()
    
    if not success:
        print("\n❌ Download failed. Please try manual download.")
        return False
    
    # Process
    success = process_movies_metadata()
    
    if not success:
        print("\n❌ Processing failed.")
        return False
    
    # Process keywords
    process_keywords()
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print("\nYour dataset now includes 45,000+ movies!")
    print("\nNext steps:")
    print("  1. Retrain ML models: python src/train_models_offline.py")
    print("  2. Restart the app: streamlit run app/main.py")
    
    return True


if __name__ == "__main__":
    main()

