"""
Letterboxd Import Module for CineSwipe
Imports user's movie ratings from their public Letterboxd profile via RSS

Usage:
    from src.letterboxd_import import LetterboxdImporter
    
    importer = LetterboxdImporter()
    movies = importer.get_user_ratings("username")
"""

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
    """Import user movie data from Letterboxd public profiles"""
    
    def __init__(self, tmdb_movies_path: str = None):
        """
        Initialize the importer
        
        Args:
            tmdb_movies_path: Path to TMDB movies CSV for matching
        """
        self.base_url = "https://letterboxd.com"
        self.tmdb_movies = None
        
        # Load TMDB movies for matching
        if tmdb_movies_path:
            self._load_tmdb_movies(tmdb_movies_path)
        else:
            # Try default path
            default_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
            if default_path.exists():
                self._load_tmdb_from_json(default_path)
    
    def _load_tmdb_movies(self, path: str):
        """Load TMDB movies from CSV"""
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
        """Load TMDB movies from JSON"""
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
        """
        Validate if a Letterboxd username exists and has public profile
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not username or len(username) < 2:
            return False, "Username too short"
        
        # Clean username
        username = username.strip().lower()
        
        # Try to fetch the profile RSS
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
        """
        Get user's rated films from their Letterboxd diary
        
        Args:
            username: Letterboxd username
            limit: Maximum number of films to fetch
            
        Returns:
            List of dicts with movie info and ratings
        """
        username = username.strip().lower()
        
        # Fetch rated films RSS
        ratings_url = f"{self.base_url}/{username}/films/ratings/rss/"
        diary_url = f"{self.base_url}/{username}/rss/"
        
        movies = []
        seen_titles = set()
        
        # Try ratings feed first
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
        
        # Also try diary feed for additional entries
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
        
        # Match with TMDB IDs
        matched_movies = self._match_with_tmdb(movies)
        
        return matched_movies[:limit]
    
    def _parse_rating_entry(self, entry) -> Optional[Dict]:
        """Parse a rating RSS entry"""
        try:
            title = entry.get('title', '')
            
            # Extract rating (stars) from title
            # Format: "Movie Title - ★★★★" or "Movie Title - ★★★½"
            stars = title.count('★')
            half_star = '½' in title
            rating = stars + (0.5 if half_star else 0)
            
            # Clean title
            clean_title = re.sub(r'\s*-\s*★.*$', '', title).strip()
            
            # Try to extract year from link
            link = entry.get('link', '')
            year_match = re.search(r'/film/[^/]+-(\d{4})/?', link)
            year = int(year_match.group(1)) if year_match else None
            
            return {
                'title': clean_title,
                'letterboxd_rating': rating,
                'year': year,
                'liked': rating >= 3.5,  # 3.5+ stars = liked
                'source': 'letterboxd_rating'
            }
        except Exception as e:
            return None
    
    def _parse_diary_entry(self, entry) -> Optional[Dict]:
        """Parse a diary RSS entry"""
        try:
            title = entry.get('title', '')
            
            # Extract rating from title if present
            stars = title.count('★')
            half_star = '½' in title
            rating = stars + (0.5 if half_star else 0) if stars > 0 else None
            
            # Clean title - remove date and rating
            clean_title = re.sub(r'\s*-\s*★.*$', '', title)
            clean_title = re.sub(r',\s*\d{4}\s*-\s*', '', clean_title).strip()
            
            # Try to extract year
            link = entry.get('link', '')
            year_match = re.search(r'/film/[^/]+-(\d{4})/?', link)
            year = int(year_match.group(1)) if year_match else None
            
            return {
                'title': clean_title,
                'letterboxd_rating': rating,
                'year': year,
                'liked': rating >= 3.5 if rating else True,  # If watched without rating, assume liked
                'source': 'letterboxd_diary'
            }
        except Exception as e:
            return None
    
    def _match_with_tmdb(self, movies: List[Dict]) -> List[Dict]:
        """Match Letterboxd movies with TMDB IDs"""
        if not self.tmdb_movies:
            return movies
        
        matched = []
        for movie in movies:
            title_lower = movie['title'].lower().strip()
            
            # Exact match first
            if title_lower in self.tmdb_movies:
                tmdb = self.tmdb_movies[title_lower]
                movie['movie_id'] = tmdb['movie_id']
                movie['tmdb_title'] = tmdb['title']
                movie['matched'] = True
                matched.append(movie)
                continue
            
            # Fuzzy match if available
            if fuzz:
                best_match = None
                best_score = 0
                
                for tmdb_title, tmdb_data in self.tmdb_movies.items():
                    score = fuzz.ratio(title_lower, tmdb_title)
                    if score > best_score and score >= 85:
                        best_score = score
                        best_match = tmdb_data
                
                if best_match:
                    movie['movie_id'] = best_match['movie_id']
                    movie['tmdb_title'] = best_match['title']
                    movie['match_score'] = best_score
                    movie['matched'] = True
                    matched.append(movie)
                    continue
            
            # No match found
            movie['matched'] = False
            matched.append(movie)
        
        return matched
    
    def get_liked_movie_ids(self, username: str) -> List[int]:
        """
        Get list of TMDB movie IDs that user liked (rated 3.5+ stars)
        
        Args:
            username: Letterboxd username
            
        Returns:
            List of TMDB movie IDs
        """
        movies = self.get_user_ratings(username)
        
        liked_ids = [
            m['movie_id'] 
            for m in movies 
            if m.get('liked') and m.get('matched') and m.get('movie_id')
        ]
        
        return liked_ids
    
    def get_disliked_movie_ids(self, username: str) -> List[int]:
        """
        Get list of TMDB movie IDs that user disliked (rated < 3 stars)
        
        Args:
            username: Letterboxd username
            
        Returns:
            List of TMDB movie IDs
        """
        movies = self.get_user_ratings(username)
        
        disliked_ids = [
            m['movie_id'] 
            for m in movies 
            if not m.get('liked') and m.get('matched') and m.get('movie_id')
            and m.get('letterboxd_rating') is not None
        ]
        
        return disliked_ids
    
    def get_genre_preferences(self, username: str) -> Dict[str, int]:
        """
        Analyze user's genre preferences from their ratings
        
        Returns:
            Dict mapping genre names to like counts
        """
        # This would require loading full movie data with genres
        # For now, return empty - can be implemented later
        return {}


def test_letterboxd_import():
    """Test the Letterboxd import functionality"""
    print("=" * 50)
    print("LETTERBOXD IMPORT TEST")
    print("=" * 50)
    
    importer = LetterboxdImporter()
    
    # Test with a known public profile (you can change this)
    test_username = "davidehrlich"  # A well-known film critic
    
    print(f"\nTesting with username: {test_username}")
    
    # Validate
    is_valid, msg = importer.validate_username(test_username)
    print(f"Valid: {is_valid} - {msg}")
    
    if is_valid:
        # Get ratings
        movies = importer.get_user_ratings(test_username, limit=10)
        print(f"\nFound {len(movies)} movies:")
        
        for m in movies[:5]:
            rating = m.get('letterboxd_rating', 'N/A')
            matched = '✓' if m.get('matched') else '✗'
            print(f"  {matched} {m['title']} - {rating}★ - {'Liked' if m.get('liked') else 'Passed'}")


if __name__ == "__main__":
    test_letterboxd_import()

