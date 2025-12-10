import feedparser
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from fuzzywuzzy import fuzz
except ImportError:
    fuzz = None


class LetterboxdImporter:
    
    def __init__(self, tmdb_movies_path: str = None):
        self.base_url = "https://letterboxd.com"
        self.tmdb_movies = None
        
        if tmdb_movies_path:
            self._load_tmdb_movies(tmdb_movies_path)
        else:
            default_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
            if default_path.exists():
                self._load_tmdb_from_json(default_path)
    
    def _load_tmdb_movies(self, path: str):
        try:
            import pandas as pd
            df = pd.read_csv(path)
            self.tmdb_movies = {}
            for _, row in df.iterrows():
                title = str(row.get('title', '')).lower().strip()
                self.tmdb_movies[title] = {
                    'movie_id': row.get('id', row.get('movie_id')),
                    'title': row.get('title'),
                    'release_year': row.get('release_year', str(row.get('release_date', ''))[:4])
                }
        except Exception as e:
            print(f"Error loading TMDB movies: {e}")
    
    def _load_tmdb_from_json(self, path: Path):
        try:
            with open(path, 'r') as f:
                movies = json.load(f)
            self.tmdb_movies = {}
            for movie in movies:
                title = str(movie.get('title', '')).lower().strip()
                self.tmdb_movies[title] = {
                    'movie_id': movie.get('movie_id'),
                    'title': movie.get('title'),
                    'release_year': movie.get('release_year')
                }
        except Exception as e:
            print(f"Error loading movies JSON: {e}")
    
    def validate_username(self, username: str) -> Tuple[bool, str]:
        if not username or len(username) < 2:
            return False, "Username too short"
        
        username = username.strip().lower()
        feed_url = f"{self.base_url}/{username}/rss/"
        
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and not feed.entries:
                return False, "Profile not found or is private"
            
            if len(feed.entries) == 0:
                return True, "Profile found but no recent activity"
            
            return True, f"Found {len(feed.entries)} recent diary entries"
            
        except Exception as e:
            return False, f"Error checking profile: {str(e)}"
    
    def get_user_ratings(self, username: str, limit: int = 100) -> List[Dict]:
        username = username.strip().lower()
        
        ratings_url = f"{self.base_url}/{username}/films/ratings/rss/"
        diary_url = f"{self.base_url}/{username}/rss/"
        
        movies = []
        seen_titles = set()
        
        try:
            feed = feedparser.parse(ratings_url)
            if feed.entries:
                for entry in feed.entries[:limit]:
                    movie = self._parse_rating_entry(entry)
                    if movie and movie['title'] not in seen_titles:
                        movies.append(movie)
                        seen_titles.add(movie['title'])
        except Exception as e:
            print(f"Error fetching ratings: {e}")
        
        try:
            feed = feedparser.parse(diary_url)
            if feed.entries:
                for entry in feed.entries[:limit]:
                    movie = self._parse_diary_entry(entry)
                    if movie and movie['title'] not in seen_titles:
                        movies.append(movie)
                        seen_titles.add(movie['title'])
        except Exception as e:
            print(f"Error fetching diary: {e}")
        
        matched_movies = self._match_with_tmdb(movies)
        
        return matched_movies[:limit]
    
    def _parse_rating_entry(self, entry) -> Optional[Dict]:
        try:
            title = entry.get('title', '')
            
            stars = title.count('★')
            half_star = '½' in title
            rating = stars + (0.5 if half_star else 0)
            
            clean_title = re.sub(r'\s*-\s*★.*$', '', title).strip()
            clean_title = re.sub(r',?\s*\d{4}\s*$', '', clean_title).strip()
            
            link = entry.get('link', '')
            year_match = re.search(r'/film/[^/]+-(\d{4})/?', link)
            year = int(year_match.group(1)) if year_match else None
            
            if not year:
                title_year = re.search(r',?\s*(\d{4})\s*$', title)
                year = int(title_year.group(1)) if title_year else None
            
            return {
                'title': clean_title,
                'letterboxd_rating': rating,
                'year': year,
                'liked': rating >= 3.5,
                'source': 'letterboxd_rating'
            }
        except Exception as e:
            return None
    
    def _parse_diary_entry(self, entry) -> Optional[Dict]:
        try:
            title = entry.get('title', '')
            
            stars = title.count('★')
            half_star = '½' in title
            rating = stars + (0.5 if half_star else 0) if stars > 0 else None
            
            title_year_match = re.search(r',\s*(\d{4})\s*-', title)
            year_from_title = int(title_year_match.group(1)) if title_year_match else None
            
            clean_title = re.sub(r'\s*-\s*★.*$', '', title)
            clean_title = re.sub(r',\s*\d{4}\s*(-|$)', '', clean_title).strip()
            clean_title = re.sub(r'\s+\d{4}\s*$', '', clean_title).strip()
            
            link = entry.get('link', '')
            year_match = re.search(r'/film/[^/]+-(\d{4})/?', link)
            year = int(year_match.group(1)) if year_match else year_from_title
            
            return {
                'title': clean_title,
                'letterboxd_rating': rating,
                'year': year,
                'liked': rating >= 3.5 if rating else True,
                'source': 'letterboxd_diary'
            }
        except Exception as e:
            return None
    
    def _match_with_tmdb(self, movies: List[Dict]) -> List[Dict]:
        if not self.tmdb_movies:
            return movies
        
        matched = []
        for movie in movies:
            raw_title = movie['title']
            title_lower = raw_title.lower().strip()
            
            title_lower = re.sub(r',?\s*\d{4}\s*$', '', title_lower).strip()
            title_lower = re.sub(r'\s*\(\d{4}\)\s*$', '', title_lower).strip()
            
            if title_lower in self.tmdb_movies:
                tmdb = self.tmdb_movies[title_lower]
                movie['movie_id'] = tmdb['movie_id']
                movie['tmdb_title'] = tmdb['title']
                movie['matched'] = True
                matched.append(movie)
                continue
            
            title_no_article = re.sub(r'^(the|a|an)\s+', '', title_lower)
            if title_no_article in self.tmdb_movies:
                tmdb = self.tmdb_movies[title_no_article]
                movie['movie_id'] = tmdb['movie_id']
                movie['tmdb_title'] = tmdb['title']
                movie['matched'] = True
                matched.append(movie)
                continue
            
            title_with_the = f"the {title_lower}"
            if title_with_the in self.tmdb_movies:
                tmdb = self.tmdb_movies[title_with_the]
                movie['movie_id'] = tmdb['movie_id']
                movie['tmdb_title'] = tmdb['title']
                movie['matched'] = True
                matched.append(movie)
                continue
            
            title_no_punct = re.sub(r'[^\w\s]', '', title_lower)
            if title_no_punct in self.tmdb_movies:
                tmdb = self.tmdb_movies[title_no_punct]
                movie['movie_id'] = tmdb['movie_id']
                movie['tmdb_title'] = tmdb['title']
                movie['matched'] = True
                matched.append(movie)
                continue
            
            if fuzz:
                best_match = None
                best_score = 0
                
                for tmdb_title, tmdb_data in self.tmdb_movies.items():
                    score1 = fuzz.ratio(title_lower, tmdb_title)
                    score2 = fuzz.ratio(title_no_article, tmdb_title)
                    score3 = fuzz.partial_ratio(title_lower, tmdb_title)
                    score = max(score1, score2, score3)
                    
                    if score > best_score and score >= 80:
                        best_score = score
                        best_match = tmdb_data
                
                if best_match:
                    movie['movie_id'] = best_match['movie_id']
                    movie['tmdb_title'] = best_match['title']
                    movie['match_score'] = best_score
                    movie['matched'] = True
                    matched.append(movie)
                    continue
            
            movie['matched'] = False
            matched.append(movie)
        
        return matched
    
    def get_liked_movie_ids(self, username: str) -> List[int]:
        movies = self.get_user_ratings(username)
        
        liked_ids = [
            m['movie_id'] 
            for m in movies 
            if m.get('liked') and m.get('matched') and m.get('movie_id')
        ]
        
        return liked_ids
    
    def get_disliked_movie_ids(self, username: str) -> List[int]:
        movies = self.get_user_ratings(username)
        
        disliked_ids = [
            m['movie_id'] 
            for m in movies 
            if not m.get('liked') and m.get('matched') and m.get('movie_id')
            and m.get('letterboxd_rating') is not None
        ]
        
        return disliked_ids
    
    def get_genre_preferences(self, username: str) -> Dict[str, int]:
        return {}


def test_letterboxd_import():
    print("=" * 50)
    print("LETTERBOXD IMPORT TEST")
    print("=" * 50)
    
    importer = LetterboxdImporter()
    
    test_username = "davidehrlich"
    
    print(f"\nTesting with username: {test_username}")
    
    is_valid, msg = importer.validate_username(test_username)
    print(f"Valid: {is_valid} - {msg}")
    
    if is_valid:
        movies = importer.get_user_ratings(test_username, limit=10)
        print(f"\nFound {len(movies)} movies:")
        
        for m in movies[:5]:
            rating = m.get('letterboxd_rating', 'N/A')
            matched = 'Y' if m.get('matched') else 'N'
            print(f"  {matched} {m['title']} - {rating} - {'Liked' if m.get('liked') else 'Passed'}")


if __name__ == "__main__":
    test_letterboxd_import()
