"""
Content-Based Filtering Recommendation Model
Recommends movies based on movie features (genres, overview, keywords)
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import MODELS_PATH, MODEL_CONFIG


class ContentBasedRecommender:
    """
    Content-based movie recommender using TF-IDF on movie features.
    Recommends similar movies based on genres, keywords, and overview text.
    """
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(
            max_features=MODEL_CONFIG['content_based']['n_features'],
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.movie_ids = None
        self.movie_features = None
        self.is_fitted = False
    
    def _create_feature_string(self, row):
        """Combine movie features into single string for TF-IDF"""
        features = []
        
        # Add genres (weighted by repetition)
        if row.get('genres'):
            genres = row['genres'] if isinstance(row['genres'], list) else []
            features.extend(genres * 3)  # Weight genres heavily
        
        # Add keywords
        if row.get('keywords'):
            keywords = row['keywords'] if isinstance(row['keywords'], list) else []
            features.extend(keywords * 2)
        
        # Add overview
        if row.get('overview'):
            features.append(str(row['overview']))
        
        return ' '.join(features).lower()
    
    def fit(self, movies_df):
        """
        Fit the model on movie data.
        
        Args:
            movies_df: DataFrame with columns [movie_id, genres, keywords, overview]
        """
        print("Training Content-Based Recommender...")
        
        # Store movie IDs
        self.movie_ids = movies_df['movie_id'].tolist()
        
        # Create feature strings
        self.movie_features = movies_df.apply(self._create_feature_string, axis=1)
        
        # Fit TF-IDF
        self.tfidf_matrix = self.tfidf.fit_transform(self.movie_features)
        
        self.is_fitted = True
        print(f"✓ Fitted on {len(self.movie_ids)} movies")
        print(f"  TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        return self
    
    def get_similar_movies(self, movie_id, n=10):
        """
        Get n most similar movies to a given movie.
        
        Args:
            movie_id: ID of the movie to find similar movies for
            n: Number of recommendations
            
        Returns:
            List of (movie_id, similarity_score) tuples
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        try:
            idx = self.movie_ids.index(movie_id)
        except ValueError:
            return []
        
        # Calculate similarity scores
        movie_vector = self.tfidf_matrix[idx]
        similarity_scores = cosine_similarity(movie_vector, self.tfidf_matrix)[0]
        
        # Get top N similar movies (excluding itself)
        similar_indices = similarity_scores.argsort()[::-1][1:n+1]
        
        results = [
            (self.movie_ids[i], float(similarity_scores[i]))
            for i in similar_indices
        ]
        
        return results
    
    def recommend_for_user(self, liked_movie_ids, n=10, exclude_ids=None):
        """
        Recommend movies based on user's liked movies.
        
        Args:
            liked_movie_ids: List of movie IDs the user liked
            n: Number of recommendations
            exclude_ids: Movie IDs to exclude (already seen)
            
        Returns:
            List of (movie_id, score, explanation) tuples
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if not liked_movie_ids:
            return []
        
        exclude_ids = set(exclude_ids or [])
        exclude_ids.update(liked_movie_ids)
        
        # Get valid liked movie indices
        liked_indices = []
        for mid in liked_movie_ids:
            try:
                liked_indices.append(self.movie_ids.index(mid))
            except ValueError:
                continue
        
        if not liked_indices:
            return []
        
        # Calculate average user profile from liked movies
        user_profile = self.tfidf_matrix[liked_indices].mean(axis=0)
        user_profile = np.asarray(user_profile).flatten()
        
        # Calculate similarity to all movies
        all_scores = cosine_similarity([user_profile], self.tfidf_matrix)[0]
        
        # Filter and sort
        recommendations = []
        for idx in all_scores.argsort()[::-1]:
            movie_id = self.movie_ids[idx]
            if movie_id not in exclude_ids:
                score = float(all_scores[idx])
                explanation = f"Similar to movies you've liked (content match: {score:.0%})"
                recommendations.append({
                    'movie_id': movie_id,
                    'score': score,
                    'algorithm': 'content_based',
                    'rank': len(recommendations) + 1,
                    'explanation': explanation
                })
                if len(recommendations) >= n:
                    break
        
        return recommendations
    
    def save(self, filename='content_based_model.pkl'):
        """Save model to disk"""
        filepath = MODELS_PATH / filename
        model_data = {
            'tfidf': self.tfidf,
            'tfidf_matrix': self.tfidf_matrix,
            'movie_ids': self.movie_ids,
            'is_fitted': self.is_fitted
        }
        joblib.dump(model_data, filepath)
        print(f"✓ Model saved to {filepath}")
    
    def load(self, filename='content_based_model.pkl'):
        """Load model from disk"""
        filepath = MODELS_PATH / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Model not found: {filepath}")
        
        model_data = joblib.load(filepath)
        self.tfidf = model_data['tfidf']
        self.tfidf_matrix = model_data['tfidf_matrix']
        self.movie_ids = model_data['movie_ids']
        self.is_fitted = model_data['is_fitted']
        print(f"✓ Model loaded from {filepath}")


# Test
if __name__ == "__main__":
    # Test with sample data
    sample_data = pd.DataFrame({
        'movie_id': [1, 2, 3, 4, 5],
        'genres': [['Action', 'Sci-Fi'], ['Comedy'], ['Action'], ['Sci-Fi'], ['Comedy', 'Romance']],
        'keywords': [['space', 'aliens'], ['funny'], ['hero'], ['future'], ['love']],
        'overview': [
            'A space adventure with aliens',
            'A funny comedy about friends',
            'A hero saves the world',
            'A journey to the future',
            'A romantic comedy'
        ]
    })
    
    model = ContentBasedRecommender()
    model.fit(sample_data)
    
    print("\nSimilar to movie 1:")
    for mid, score in model.get_similar_movies(1, n=3):
        print(f"  Movie {mid}: {score:.3f}")
    
    print("\nRecommendations based on liking movies 1 and 4:")
    recs = model.recommend_for_user([1, 4], n=3, exclude_ids=[1, 4])
    for r in recs:
        print(f"  Movie {r['movie_id']}: {r['score']:.3f}")

