"""
TMDB API Fetcher - Get Latest Movies Including 2024-2025!
Fetches real-time movie data from The Movie Database API

To get your free API key:
1. Sign up at https://www.themoviedb.org/signup
2. Go to Settings → API → Request API Key
3. Copy your API key and paste below or set as env var

Usage:
    python scripts/fetch_tmdb_api.py
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# TMDB API Configuration
# Get your free key at: https://www.themoviedb.org/settings/api
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')

# If no env var, prompt for key
if not TMDB_API_KEY:
    print("=" * 60)
    print("TMDB API KEY REQUIRED")
    print("=" * 60)
    print("\nTo get a FREE API key:")
    print("1. Go to: https://www.themoviedb.org/signup")
    print("2. Create account (takes 30 seconds)")
    print("3. Go to: https://www.themoviedb.org/settings/api")
    print("4. Click 'Create' → 'Developer' → Fill form")
    print("5. Copy your API Key (v3 auth)")
    print()
    TMDB_API_KEY = input("Paste your TMDB API Key here: ").strip()
    
    if not TMDB_API_KEY:
        print("No API key provided. Exiting.")
        sys.exit(1)

BASE_URL = "https://api.themoviedb.org/3"


def fetch_movies_from_endpoint(endpoint: str, params: dict = None, max_pages: int = 10) -> list:
    """Fetch movies from a TMDB API endpoint"""
    all_movies = []
    
    if params is None:
        params = {}
    
    params['api_key'] = TMDB_API_KEY
    params['language'] = 'en-US'
    
    for page in range(1, max_pages + 1):
        params['page'] = page
        
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
            
            if response.status_code == 401:
                print("❌ Invalid API key! Please check your TMDB API key.")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            movies = data.get('results', [])
            if not movies:
                break
                
            all_movies.extend(movies)
            
            # Respect rate limits
            time.sleep(0.1)
            
            total_pages = data.get('total_pages', 1)
            if page >= total_pages:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    return all_movies


def fetch_movie_details(movie_id: int) -> dict:
    """Fetch detailed info for a single movie"""
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'append_to_response': 'keywords,credits'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/movie/{movie_id}", params=params)
        response.raise_for_status()
        return response.json()
    except:
        return None


def search_movie(title: str, year: int = None) -> dict:
    """Search for a specific movie by title"""
    params = {
        'api_key': TMDB_API_KEY,
        'query': title,
        'language': 'en-US'
    }
    if year:
        params['year'] = year
    
    try:
        response = requests.get(f"{BASE_URL}/search/movie", params=params)
        response.raise_for_status()
        results = response.json().get('results', [])
        return results[0] if results else None
    except:
        return None


def fetch_all_movies(target_count: int = 5000) -> list:
    """Fetch movies from multiple sources to get comprehensive coverage"""
    
    print("=" * 60)
    print("FETCHING MOVIES FROM TMDB API")
    print("=" * 60)
    
    all_movies = {}  # Use dict to avoid duplicates
    
    # 1. Popular movies (all time)
    print("\n[1/6] Fetching popular movies...")
    popular = fetch_movies_from_endpoint("movie/popular", max_pages=50)
    for m in popular:
        all_movies[m['id']] = m
    print(f"    ✓ {len(popular)} popular movies")
    
    # 2. Top rated movies
    print("\n[2/6] Fetching top rated movies...")
    top_rated = fetch_movies_from_endpoint("movie/top_rated", max_pages=50)
    for m in top_rated:
        all_movies[m['id']] = m
    print(f"    ✓ {len(top_rated)} top rated movies")
    
    # 3. Now playing (currently in theaters)
    print("\n[3/6] Fetching now playing...")
    now_playing = fetch_movies_from_endpoint("movie/now_playing", max_pages=10)
    for m in now_playing:
        all_movies[m['id']] = m
    print(f"    ✓ {len(now_playing)} now playing")
    
    # 4. Upcoming movies (including 2025!)
    print("\n[4/6] Fetching upcoming movies (2024-2025)...")
    upcoming = fetch_movies_from_endpoint("movie/upcoming", max_pages=20)
    for m in upcoming:
        all_movies[m['id']] = m
    print(f"    ✓ {len(upcoming)} upcoming movies")
    
    # 5. Discover recent years (2020-2025)
    print("\n[5/6] Fetching movies by year (2020-2025)...")
    for year in range(2020, 2026):
        print(f"    Fetching {year}...", end=" ")
        year_movies = fetch_movies_from_endpoint(
            "discover/movie",
            params={
                'primary_release_year': year,
                'sort_by': 'popularity.desc'
            },
            max_pages=20
        )
        for m in year_movies:
            all_movies[m['id']] = m
        print(f"{len(year_movies)} movies")
        time.sleep(0.2)
    
    # 6. Discover by genre to get variety
    print("\n[6/6] Fetching by genre for variety...")
    genres = {
        28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
        80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
        14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
        9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 53: "Thriller"
    }
    
    for genre_id, genre_name in genres.items():
        genre_movies = fetch_movies_from_endpoint(
            "discover/movie",
            params={
                'with_genres': genre_id,
                'sort_by': 'popularity.desc'
            },
            max_pages=10
        )
        for m in genre_movies:
            all_movies[m['id']] = m
        print(f"    {genre_name}: {len(genre_movies)}")
        time.sleep(0.1)
    
    print(f"\n📊 Total unique movies collected: {len(all_movies)}")
    
    return list(all_movies.values())


def process_movies(raw_movies: list) -> list:
    """Process raw TMDB movie data into our format"""
    
    print("\n" + "=" * 60)
    print("PROCESSING MOVIE DATA")
    print("=" * 60)
    
    # Genre ID mapping
    genre_map = {
        28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
        80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
        14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
        9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
        10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
    }
    
    processed = []
    
    for movie in raw_movies:
        try:
            # Extract release year
            release_date = movie.get('release_date', '')
            if not release_date:
                continue
            
            year = int(release_date[:4]) if len(release_date) >= 4 else None
            if not year:
                continue
            
            # Convert genre IDs to names
            genre_ids = movie.get('genre_ids', [])
            genres = [genre_map.get(gid, '') for gid in genre_ids if gid in genre_map]
            
            if not genres:
                continue
            
            # Build processed movie
            processed_movie = {
                'movie_id': movie['id'],
                'title': movie.get('title', ''),
                'original_title': movie.get('original_title', ''),
                'release_year': year,
                'release_date': release_date,
                'genres': genres,
                'overview': movie.get('overview', '')[:500] if movie.get('overview') else '',
                'vote_average': float(movie.get('vote_average', 0)),
                'vote_count': int(movie.get('vote_count', 0)),
                'popularity': float(movie.get('popularity', 0)),
                'original_language': movie.get('original_language', 'en'),
                'poster_path': movie.get('poster_path', ''),
                'backdrop_path': movie.get('backdrop_path', ''),
            }
            
            # Only include movies with titles
            if processed_movie['title']:
                processed.append(processed_movie)
                
        except Exception as e:
            continue
    
    # Sort by popularity
    processed.sort(key=lambda x: x['popularity'], reverse=True)
    
    print(f"✓ Processed {len(processed)} valid movies")
    
    return processed


def check_for_specific_movies(movies: list):
    """Check if specific 2024-2025 movies are in the dataset"""
    
    print("\n" + "=" * 60)
    print("CHECKING FOR 2024-2025 MOVIES")
    print("=" * 60)
    
    movies_to_check = [
        "F1",
        "Dune: Part Two", 
        "Oppenheimer",
        "Barbie",
        "The Batman",
        "Avatar: The Way of Water",
        "Spider-Man: Across the Spider-Verse",
        "Guardians of the Galaxy Vol. 3",
        "Mission: Impossible - Dead Reckoning",
        "Killers of the Flower Moon",
        "Poor Things",
        "The Holdovers",
        "Wonka",
        "Aquaman and the Lost Kingdom",
        "Napoleon",
        "Godzilla x Kong",
        "Kung Fu Panda 4",
        "Inside Out 2",
        "Deadpool 3",
        "Joker: Folie à Deux",
        "Gladiator 2",
        "Wicked",
        "Moana 2",
        "Mufasa: The Lion King",
    ]
    
    movie_titles = {m['title'].lower() for m in movies}
    movie_originals = {m.get('original_title', '').lower() for m in movies}
    all_titles = movie_titles | movie_originals
    
    found = []
    missing = []
    
    for check in movies_to_check:
        if check.lower() in all_titles:
            found.append(check)
        else:
            # Try partial match
            partial = any(check.lower() in t for t in all_titles)
            if partial:
                found.append(check)
            else:
                missing.append(check)
    
    print(f"\n✅ Found ({len(found)}):")
    for m in found:
        print(f"    • {m}")
    
    if missing:
        print(f"\n❌ Missing ({len(missing)}):")
        for m in missing:
            print(f"    • {m}")
        print("\n💡 Some upcoming movies may not be in TMDB yet.")
        print("   They'll appear as release dates get closer.")
    
    # Check year distribution
    print("\n📅 Movies by year:")
    year_counts = {}
    for m in movies:
        year = m.get('release_year', 0)
        year_counts[year] = year_counts.get(year, 0) + 1
    
    for year in sorted(year_counts.keys(), reverse=True)[:10]:
        print(f"    {year}: {year_counts[year]} movies")


def save_movies(movies: list):
    """Save processed movies to JSON"""
    
    output_dir = Path(__file__).parent.parent / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    json_path = output_dir / 'sample_movies.json'
    
    # Take top 5000 for the app
    top_movies = movies[:5000]
    
    with open(json_path, 'w') as f:
        json.dump(top_movies, f, indent=2)
    
    print(f"\n✓ Saved {len(top_movies)} movies to {json_path}")
    
    # Also save full dataset
    full_path = output_dir / 'full_movies_api.json'
    with open(full_path, 'w') as f:
        json.dump(movies, f, indent=2)
    
    print(f"✓ Saved full dataset ({len(movies)} movies) to {full_path}")


def main():
    """Main function"""
    
    print("\n" + "=" * 60)
    print("🎬 TMDB API MOVIE FETCHER")
    print("=" * 60)
    print("\nThis will fetch the LATEST movies including 2024-2025!")
    print("Including: F1, Dune 2, Oppenheimer, upcoming releases, etc.\n")
    
    # Test API key
    print("Testing API key...")
    test = search_movie("Inception")
    if not test:
        print("❌ API key test failed. Please check your key.")
        return False
    print("✓ API key valid!\n")
    
    # Fetch movies
    raw_movies = fetch_all_movies(target_count=5000)
    
    if not raw_movies:
        print("❌ No movies fetched. Check your API key and internet connection.")
        return False
    
    # Process
    processed = process_movies(raw_movies)
    
    # Check for specific movies
    check_for_specific_movies(processed)
    
    # Save
    save_movies(processed)
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print(f"\n🎬 Total movies: {len(processed)}")
    print("\nNext steps:")
    print("  1. Retrain models: python src/train_models_offline.py")
    print("  2. Restart app: streamlit run app/main.py")
    
    return True


if __name__ == "__main__":
    main()

