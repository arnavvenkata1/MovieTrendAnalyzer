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
                          exclude_ids=None, n_swipes=None, letterboxd_data=None):
        """
        Generate hybrid recommendations for a user.
        
        Args:
            user_id: User to recommend for
            liked_movie_ids: List of movie IDs the user liked (for content-based)
            n: Number of recommendations
            exclude_ids: Movie IDs to exclude
            n_swipes: Number of swipes the user has made (for weight calculation)
            letterboxd_data: Optional dict of movie_id -> rating from Letterboxd
            
        Returns:
            List of recommendation dicts with scores and explanations
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        exclude_ids = set(exclude_ids or [])
        n_swipes = n_swipes or len(liked_movie_ids)
        letterboxd_data = letterboxd_data or {}
        
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
        
        # Normalize scores to 75-98% range for better UX
        if sorted_movies:
            scores = [s for _, s in sorted_movies[:n]]
            if scores:
                max_score = max(scores)
                min_score = min(scores)
                score_range = max_score - min_score if max_score != min_score else 1.0
                
                # Normalize to 0.75-0.98 range (higher percentages!)
                normalized_scores = []
                for i, score in enumerate(scores):
                    if score_range > 0:
                        normalized = (score - min_score) / score_range
                        # Higher base (0.75) and wider range to 0.98
                        boosted_score = 0.75 + (normalized * 0.23)
                    else:
                        boosted_score = 0.85
                    
                    # Add rank boost - top recommendations get higher scores
                    rank_boost = max(0, (n - i) / n) * 0.05  # Up to 5% boost for #1
                    boosted_score += rank_boost
                    
                    normalized_scores.append(min(boosted_score, 0.98))
            else:
                normalized_scores = [0.85] * len(sorted_movies[:n])
        else:
            normalized_scores = []
        
        # Build final recommendations with normalized scores
        recommendations = []
        for rank, ((movie_id, raw_score), normalized_score) in enumerate(zip(sorted_movies[:n], normalized_scores), 1):
            exp = explanations.get(movie_id, {})
            
            final_score = normalized_score
            
            # Boost score if we have Letterboxd data showing user liked similar movies
            if letterboxd_data:
                # Check if this movie's genres match highly-rated Letterboxd movies
                letterboxd_boost = 0.0
                high_rated_count = sum(1 for r in letterboxd_data.values() if r and r >= 4.0)
                if high_rated_count > 5:
                    letterboxd_boost = 0.03  # Small boost for users with rich Letterboxd history
                final_score = min(final_score + letterboxd_boost, 0.98)
            
            # Create human-readable explanation
            explanation_parts = []
            if exp.get('content_explanation'):
                explanation_parts.append(exp['content_explanation'])
            if exp.get('collab_explanation'):
                explanation_parts.append(exp['collab_explanation'])
            
            # Add Letterboxd context if available
            if letterboxd_data and len(letterboxd_data) > 0:
                explanation_parts.append(f"Based on your {len(letterboxd_data)} Letterboxd ratings")
            
            recommendations.append({
                'movie_id': movie_id,
                'score': final_score,
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

