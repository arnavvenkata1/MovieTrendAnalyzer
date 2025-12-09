"""
Collaborative Filtering Recommendation Model
Recommends movies based on similar users' preferences
"""

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import MODELS_PATH, MODEL_CONFIG


class CollaborativeRecommender:
    """
    Collaborative filtering recommender using user-item interactions (swipes).
    Uses k-nearest neighbors to find similar users.
    """
    
    def __init__(self, n_neighbors=20):
        self.n_neighbors = n_neighbors
        self.user_item_matrix = None
        self.user_ids = None
        self.movie_ids = None
        self.model = None
        self.is_fitted = False
    
    def fit(self, swipes_df):
        """
        Fit the model on swipe data.
        
        Args:
            swipes_df: DataFrame with columns [user_id, movie_id, swipe_direction]
                      swipe_direction: 'right' = 1, 'left' = -1, 'skip' = 0
        """
        print("Training Collaborative Filtering Recommender...")
        
        # Convert swipe direction to numeric
        swipes_df = swipes_df.copy()
        swipes_df['rating'] = swipes_df['swipe_direction'].map({
            'right': 1,
            'superlike': 2,
            'left': -1,
            'skip': 0
        }).fillna(0)
        
        # Create pivot table (user-item matrix)
        self.user_item_matrix = swipes_df.pivot_table(
            index='user_id',
            columns='movie_id',
            values='rating',
            fill_value=0
        )
        
        self.user_ids = self.user_item_matrix.index.tolist()
        self.movie_ids = self.user_item_matrix.columns.tolist()
        
        # Convert to sparse matrix
        sparse_matrix = csr_matrix(self.user_item_matrix.values)
        
        # Fit KNN model
        self.model = NearestNeighbors(
            n_neighbors=min(self.n_neighbors, len(self.user_ids)),
            metric='cosine',
            algorithm='brute'
        )
        self.model.fit(sparse_matrix)
        
        self.is_fitted = True
        print(f"✓ Fitted on {len(self.user_ids)} users, {len(self.movie_ids)} movies")
        print(f"  Matrix shape: {self.user_item_matrix.shape}")
        print(f"  Sparsity: {(sparse_matrix.nnz / (sparse_matrix.shape[0] * sparse_matrix.shape[1]) * 100):.2f}%")
        
        return self
    
    def get_similar_users(self, user_id, n=10):
        """
        Find n most similar users to a given user.
        
        Args:
            user_id: ID of the user
            n: Number of similar users to find
            
        Returns:
            List of (user_id, similarity_score) tuples
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        try:
            user_idx = self.user_ids.index(user_id)
        except ValueError:
            return []
        
        user_vector = self.user_item_matrix.iloc[user_idx].values.reshape(1, -1)
        distances, indices = self.model.kneighbors(
            user_vector, 
            n_neighbors=min(n+1, len(self.user_ids))
        )
        
        # Convert distance to similarity (1 - distance for cosine)
        results = [
            (self.user_ids[indices[0][i]], 1 - distances[0][i])
            for i in range(1, len(indices[0]))  # Skip first (self)
        ]
        
        return results
    
    def recommend_for_user(self, user_id, n=10, exclude_ids=None):
        """
        Recommend movies for a user based on similar users' preferences.
        
        Args:
            user_id: User to recommend for
            n: Number of recommendations
            exclude_ids: Movie IDs to exclude (already seen)
            
        Returns:
            List of recommendation dicts
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        exclude_ids = set(exclude_ids or [])
        
        # Check if user exists
        if user_id not in self.user_ids:
            # Cold start - return popular movies
            print(f"  User {user_id} not in training data - using popularity fallback")
            return self._get_popular_movies(n, exclude_ids)
        
        # Get similar users
        similar_users = self.get_similar_users(user_id, n=self.n_neighbors)
        
        if not similar_users:
            return self._get_popular_movies(n, exclude_ids)
        
        # Aggregate ratings from similar users
        user_idx = self.user_ids.index(user_id)
        user_ratings = self.user_item_matrix.iloc[user_idx]
        
        # Movies the user hasn't rated
        unrated_movies = user_ratings[user_ratings == 0].index.tolist()
        unrated_movies = [m for m in unrated_movies if m not in exclude_ids]
        
        # Calculate predicted scores
        movie_scores = {}
        for movie_id in unrated_movies:
            score = 0
            weight_sum = 0
            
            for similar_user_id, similarity in similar_users:
                similar_user_idx = self.user_ids.index(similar_user_id)
                similar_rating = self.user_item_matrix.iloc[similar_user_idx][movie_id]
                
                if similar_rating != 0:
                    score += similarity * similar_rating
                    weight_sum += abs(similarity)
            
            if weight_sum > 0:
                movie_scores[movie_id] = score / weight_sum
        
        # Sort and return top N
        sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for rank, (movie_id, score) in enumerate(sorted_movies[:n], 1):
            # Normalize score to 0-1 range
            normalized_score = (score + 1) / 2  # Convert from [-1, 1] to [0, 1]
            recommendations.append({
                'movie_id': movie_id,
                'score': normalized_score,
                'algorithm': 'collaborative',
                'rank': rank,
                'explanation': f"Users similar to you liked this movie"
            })
        
        return recommendations
    
    def _get_popular_movies(self, n, exclude_ids):
        """Fallback: return most popular movies"""
        # Sum ratings for each movie
        movie_popularity = self.user_item_matrix.sum(axis=0)
        sorted_movies = movie_popularity.sort_values(ascending=False)
        
        recommendations = []
        for movie_id, score in sorted_movies.items():
            if movie_id not in exclude_ids:
                recommendations.append({
                    'movie_id': movie_id,
                    'score': min(score / 10, 1.0),  # Normalize
                    'algorithm': 'popular',
                    'rank': len(recommendations) + 1,
                    'explanation': 'Popular among all users'
                })
                if len(recommendations) >= n:
                    break
        
        return recommendations
    
    def save(self, filename='collaborative_model.pkl'):
        """Save model to disk"""
        filepath = MODELS_PATH / filename
        model_data = {
            'model': self.model,
            'user_item_matrix': self.user_item_matrix,
            'user_ids': self.user_ids,
            'movie_ids': self.movie_ids,
            'n_neighbors': self.n_neighbors,
            'is_fitted': self.is_fitted
        }
        joblib.dump(model_data, filepath)
        print(f"✓ Model saved to {filepath}")
    
    def load(self, filename='collaborative_model.pkl'):
        """Load model from disk"""
        filepath = MODELS_PATH / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Model not found: {filepath}")
        
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.user_item_matrix = model_data['user_item_matrix']
        self.user_ids = model_data['user_ids']
        self.movie_ids = model_data['movie_ids']
        self.n_neighbors = model_data['n_neighbors']
        self.is_fitted = model_data['is_fitted']
        print(f"✓ Model loaded from {filepath}")


# Test
if __name__ == "__main__":
    # Test with sample data
    sample_swipes = pd.DataFrame({
        'user_id': [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4],
        'movie_id': [1, 2, 3, 1, 2, 4, 1, 3, 4, 2, 3, 4],
        'swipe_direction': ['right', 'left', 'right', 'right', 'right', 'left',
                          'right', 'right', 'left', 'left', 'right', 'right']
    })
    
    model = CollaborativeRecommender(n_neighbors=3)
    model.fit(sample_swipes)
    
    print("\nSimilar users to user 1:")
    for uid, score in model.get_similar_users(1, n=2):
        print(f"  User {uid}: {score:.3f}")
    
    print("\nRecommendations for user 1:")
    recs = model.recommend_for_user(1, n=3, exclude_ids=[1, 2, 3])
    for r in recs:
        print(f"  Movie {r['movie_id']}: {r['score']:.3f} ({r['algorithm']})")

