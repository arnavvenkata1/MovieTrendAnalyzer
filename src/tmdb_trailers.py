import requests
import os
import urllib.parse
from functools import lru_cache

TMDB_API_KEY = os.environ.get('TMDB_API_KEY', 'fbcab977af26578c4a273d037a4f2655')
BASE_URL = "https://api.themoviedb.org/3"


@lru_cache(maxsize=500)
def get_trailer_url(movie_id: int) -> str:
    try:
        response = requests.get(
            f"{BASE_URL}/movie/{movie_id}/videos",
            params={'api_key': TMDB_API_KEY, 'language': 'en-US'},
            timeout=5
        )
        
        if response.status_code != 200:
            return ""
        
        data = response.json()
        videos = data.get('results', [])
        
        priority_order = ['Trailer', 'Teaser', 'Clip', 'Featurette']
        
        for video_type in priority_order:
            for video in videos:
                if (video.get('site') == 'YouTube' and 
                    video.get('type') == video_type and
                    video.get('official', True)):
                    return f"https://www.youtube.com/watch?v={video['key']}"
        
        for video in videos:
            if video.get('site') == 'YouTube':
                return f"https://www.youtube.com/watch?v={video['key']}"
        
        return ""
        
    except Exception as e:
        return ""


def get_youtube_search_url(title: str, year: int = None) -> str:
    search_query = f"{title}"
    if year:
        search_query += f" {year}"
    search_query += " official trailer"
    
    encoded_query = urllib.parse.quote(search_query)
    return f"https://www.youtube.com/results?search_query={encoded_query}"


def get_trailer_or_search(movie_id: int, title: str, year: int = None) -> tuple:
    trailer_url = get_trailer_url(movie_id)
    
    if trailer_url:
        return trailer_url, True
    else:
        return get_youtube_search_url(title, year), False


if __name__ == "__main__":
    test_movies = [
        (19995, "Avatar", 2009),
        (157336, "Interstellar", 2014),
        (911430, "F1", 2025),
        (693134, "Dune: Part Two", 2024),
    ]
    
    print("Testing TMDB Trailer Fetcher")
    print("=" * 50)
    
    for movie_id, title, year in test_movies:
        url, is_direct = get_trailer_or_search(movie_id, title, year)
        status = "Direct" if is_direct else "Search"
        print(f"{status} {title}: {url[:50]}...")
