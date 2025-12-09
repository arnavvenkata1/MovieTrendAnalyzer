"""
Hybrid Recommendation Model
Combines content-based and collaborative filtering for better recommendations
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import MODEL_CONFIG
from src.models.content_based import ContentBasedRecommender
from src.models.collaborative import CollaborativeRecommender


class HybridRecommender:
    """
    Hybrid recommender that combines:
    - Content-based filtering (movie features)
    - Collaborative filtering (user behavior)
    
    Weights adapt based on user's interaction history.
    """
    
    def __init__(self, content_weight=None, collaborative_weight=None):
        self.content_model = ContentBasedRecommender()
        self.collaborative_model = CollaborativeRecommender()
        
        # Default weights from config
        self.content_weight = content_weight or MODEL_CONFIG['hybrid']['content_weight']
        self.collaborative_weight = collaborative_weight or MODEL_CONFIG['hybrid']['collaborative_weight']
        
        self.is_fitted = False
    
    def fit(self, movies_df, swipes_df=None):
        """
        Fit both models.
        
        Args:
            movies_df: Movie features for content-based model
            swipes_df: User swipes for collaborative model (optional)
        """
        print("=" * 50)
        print("Training Hybrid Recommender")
        print("=" * 50)
        
        # Fit content-based model
        self.content_model.fit(movies_df)
        
        # Fit collaborative model if we have swipe data
        if swipes_df is not None and len(swipes_df) > 0:
            self.collaborative_model.fit(swipes_df)
        else:
            print("  ⚠ No swipe data - collaborative filtering disabled")
        
        self.is_fitted = True
        return self
    
    def _calculate_weights(self, user_id, n_swipes):
        """
        Dynamically calculate weights based on user's interaction count.
        
        New users: Higher content weight (cold start)
        Active users: Higher collaborative weight
        """
        if n_swipes < 5:
            # Cold start - rely mostly on content
            return 0.9, 0.1
        elif n_swipes < 20:
            # Some data - balanced
            return 0.6, 0.4
        else:
            # Enough data - trust collaborative more
            return self.content_weight, self.collaborative_weight
    
    def recommend_for_user(self, user_id, liked_movie_ids, n=10, 
                          exclude_ids=None, n_swipes=None):
        """
        Generate hybrid recommendations for a user.
        
        Args:
            user_id: User to recommend for
            liked_movie_ids: List of movie IDs the user liked (for content-based)
            n: Number of recommendations
            exclude_ids: Movie IDs to exclude
            n_swipes: Number of swipes the user has made (for weight calculation)
            
        Returns:
            List of recommendation dicts with scores and explanations
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        exclude_ids = set(exclude_ids or [])
        n_swipes = n_swipes or len(liked_movie_ids)
        
        # Calculate dynamic weights
        content_w, collab_w = self._calculate_weights(user_id, n_swipes)
        
        # Get content-based recommendations
        content_recs = []
        if liked_movie_ids:
            content_recs = self.content_model.recommend_for_user(
                liked_movie_ids, n=n*2, exclude_ids=exclude_ids
            )
        
        # Get collaborative recommendations
        collab_recs = []
        if self.collaborative_model.is_fitted:
            collab_recs = self.collaborative_model.recommend_for_user(
                user_id, n=n*2, exclude_ids=exclude_ids
            )
        
        # Combine scores
        combined_scores = {}
        explanations = {}
        
        # Process content-based recommendations
        for rec in content_recs:
            movie_id = rec['movie_id']
            combined_scores[movie_id] = content_w * rec['score']
            explanations[movie_id] = {
                'content_score': rec['score'],
                'content_explanation': rec['explanation']
            }
        
        # Process collaborative recommendations
        for rec in collab_recs:
            movie_id = rec['movie_id']
            if movie_id in combined_scores:
                combined_scores[movie_id] += collab_w * rec['score']
                explanations[movie_id]['collab_score'] = rec['score']
                explanations[movie_id]['collab_explanation'] = rec['explanation']
            else:
                combined_scores[movie_id] = collab_w * rec['score']
                explanations[movie_id] = {
                    'collab_score': rec['score'],
                    'collab_explanation': rec['explanation']
                }
        
        # Sort by combined score
        sorted_movies = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build final recommendations
        recommendations = []
        for rank, (movie_id, score) in enumerate(sorted_movies[:n], 1):
            exp = explanations.get(movie_id, {})
            
            # Create human-readable explanation
            explanation_parts = []
            if exp.get('content_explanation'):
                explanation_parts.append(exp['content_explanation'])
            if exp.get('collab_explanation'):
                explanation_parts.append(exp['collab_explanation'])
            
            recommendations.append({
                'movie_id': movie_id,
                'score': min(score, 1.0),  # Cap at 1.0
                'algorithm': 'hybrid',
                'rank': rank,
                'explanation': ' | '.join(explanation_parts) if explanation_parts else 'Recommended for you',
                'weights_used': {'content': content_w, 'collaborative': collab_w},
                'component_scores': exp
            })
        
        return recommendations
    
    def recommend_for_new_user(self, preferences, n=10):
        """
        Generate recommendations for a new user based on onboarding preferences.
        
        Args:
            preferences: Dict with preferred_genres, mood, etc.
            n: Number of recommendations
            
        Returns:
            List of recommendation dicts
        """
        # For new users, we can only use content-based filtering
        # based on their stated preferences
        
        preferred_genres = preferences.get('preferred_genres', [])
        avoided_genres = preferences.get('avoided_genres', [])
        min_rating = preferences.get('min_rating', 6.0)
        
        # This is a simplified version - in production you'd query the database
        # For now, return empty and let the app handle it
        return []
    
    def save(self, prefix='hybrid'):
        """Save both models"""
        self.content_model.save(f'{prefix}_content.pkl')
        if self.collaborative_model.is_fitted:
            self.collaborative_model.save(f'{prefix}_collaborative.pkl')
    
    def load(self, prefix='hybrid'):
        """Load both models"""
        self.content_model.load(f'{prefix}_content.pkl')
        try:
            self.collaborative_model.load(f'{prefix}_collaborative.pkl')
        except FileNotFoundError:
            print("  ⚠ Collaborative model not found - content-only mode")
        self.is_fitted = True


# Test
if __name__ == "__main__":
    print("Testing Hybrid Recommender...")
    
    # Sample movies
    movies = pd.DataFrame({
        'movie_id': [1, 2, 3, 4, 5],
        'genres': [['Action', 'Sci-Fi'], ['Comedy'], ['Action'], ['Sci-Fi'], ['Comedy', 'Romance']],
        'keywords': [['space'], ['funny'], ['hero'], ['future'], ['love']],
        'overview': ['Space adventure', 'Funny movie', 'Hero saves day', 'Future story', 'Love story']
    })
    
    # Sample swipes
    swipes = pd.DataFrame({
        'user_id': [1, 1, 1, 2, 2, 2],
        'movie_id': [1, 2, 3, 1, 4, 5],
        'swipe_direction': ['right', 'left', 'right', 'right', 'right', 'left']
    })
    
    model = HybridRecommender()
    model.fit(movies, swipes)
    
    print("\nHybrid recommendations for user 1 (liked movies 1 & 3):")
    recs = model.recommend_for_user(
        user_id=1,
        liked_movie_ids=[1, 3],
        n=3,
        exclude_ids=[1, 2, 3]
    )
    for r in recs:
        print(f"  Movie {r['movie_id']}: {r['score']:.3f}")
        print(f"    Weights: {r['weights_used']}")

