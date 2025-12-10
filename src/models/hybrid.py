import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import MODEL_CONFIG
from src.models.content_based import ContentBasedRecommender
from src.models.collaborative import CollaborativeRecommender


class HybridRecommender:
    
    def __init__(self, content_weight=None, collaborative_weight=None):
        self.content_model = ContentBasedRecommender()
        self.collaborative_model = CollaborativeRecommender()
        
        self.content_weight = content_weight or MODEL_CONFIG['hybrid']['content_weight']
        self.collaborative_weight = collaborative_weight or MODEL_CONFIG['hybrid']['collaborative_weight']
        
        self.is_fitted = False
    
    def fit(self, movies_df, swipes_df=None):
        print("=" * 50)
        print("Training Hybrid Recommender")
        print("=" * 50)
        
        self.content_model.fit(movies_df)
        
        if swipes_df is not None and len(swipes_df) > 0:
            self.collaborative_model.fit(swipes_df)
        else:
            print("  No swipe data - collaborative filtering disabled")
        
        self.is_fitted = True
        return self
    
    def _calculate_weights(self, user_id, n_swipes):
        if n_swipes < 5:
            return 0.9, 0.1
        elif n_swipes < 20:
            return 0.6, 0.4
        else:
            return self.content_weight, self.collaborative_weight
    
    def recommend_for_user(self, user_id, liked_movie_ids, n=10, 
                          exclude_ids=None, n_swipes=None, letterboxd_data=None):
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        exclude_ids = set(exclude_ids or [])
        n_swipes = n_swipes or len(liked_movie_ids)
        letterboxd_data = letterboxd_data or {}
        
        content_w, collab_w = self._calculate_weights(user_id, n_swipes)
        
        content_recs = []
        if liked_movie_ids:
            content_recs = self.content_model.recommend_for_user(
                liked_movie_ids, n=n*2, exclude_ids=exclude_ids
            )
        
        collab_recs = []
        if self.collaborative_model.is_fitted:
            collab_recs = self.collaborative_model.recommend_for_user(
                user_id, n=n*2, exclude_ids=exclude_ids
            )
        
        combined_scores = {}
        explanations = {}
        
        for rec in content_recs:
            movie_id = rec['movie_id']
            combined_scores[movie_id] = content_w * rec['score']
            explanations[movie_id] = {
                'content_score': rec['score'],
                'content_explanation': rec['explanation']
            }
        
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
        
        sorted_movies = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_movies:
            scores = [s for _, s in sorted_movies[:n]]
            if scores:
                max_score = max(scores)
                min_score = min(scores)
                score_range = max_score - min_score if max_score != min_score else 1.0
                
                normalized_scores = []
                for i, score in enumerate(scores):
                    if score_range > 0:
                        normalized = (score - min_score) / score_range
                        boosted_score = 0.75 + (normalized * 0.23)
                    else:
                        boosted_score = 0.85
                    
                    rank_boost = max(0, (n - i) / n) * 0.05
                    boosted_score += rank_boost
                    
                    normalized_scores.append(min(boosted_score, 0.98))
            else:
                normalized_scores = [0.85] * len(sorted_movies[:n])
        else:
            normalized_scores = []
        
        recommendations = []
        for rank, ((movie_id, raw_score), normalized_score) in enumerate(zip(sorted_movies[:n], normalized_scores), 1):
            exp = explanations.get(movie_id, {})
            
            final_score = normalized_score
            
            if letterboxd_data:
                letterboxd_boost = 0.0
                high_rated_count = sum(1 for r in letterboxd_data.values() if r and r >= 4.0)
                if high_rated_count > 5:
                    letterboxd_boost = 0.03
                final_score = min(final_score + letterboxd_boost, 0.98)
            
            explanation_parts = []
            if exp.get('content_explanation'):
                explanation_parts.append(exp['content_explanation'])
            if exp.get('collab_explanation'):
                explanation_parts.append(exp['collab_explanation'])
            
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
        preferred_genres = preferences.get('preferred_genres', [])
        avoided_genres = preferences.get('avoided_genres', [])
        min_rating = preferences.get('min_rating', 6.0)
        
        return []
    
    def save(self, prefix='hybrid'):
        self.content_model.save(f'{prefix}_content.pkl')
        if self.collaborative_model.is_fitted:
            self.collaborative_model.save(f'{prefix}_collaborative.pkl')
    
    def load(self, prefix='hybrid'):
        self.content_model.load(f'{prefix}_content.pkl')
        try:
            self.collaborative_model.load(f'{prefix}_collaborative.pkl')
        except FileNotFoundError:
            print("  Collaborative model not found - content-only mode")
        self.is_fitted = True


if __name__ == "__main__":
    print("Testing Hybrid Recommender...")
    
    movies = pd.DataFrame({
        'movie_id': [1, 2, 3, 4, 5],
        'genres': [['Action', 'Sci-Fi'], ['Comedy'], ['Action'], ['Sci-Fi'], ['Comedy', 'Romance']],
        'keywords': [['space'], ['funny'], ['hero'], ['future'], ['love']],
        'overview': ['Space adventure', 'Funny movie', 'Hero saves day', 'Future story', 'Love story']
    })
    
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
