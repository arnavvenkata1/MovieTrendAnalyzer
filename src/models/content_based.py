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
        features = []
        
        if row.get('genres'):
            genres = row['genres'] if isinstance(row['genres'], list) else []
            features.extend(genres * 3)
        
        if row.get('keywords'):
            keywords = row['keywords'] if isinstance(row['keywords'], list) else []
            features.extend(keywords * 2)
        
        if row.get('overview'):
            features.append(str(row['overview']))
        
        return ' '.join(features).lower()
    
    def fit(self, movies_df):
        print("Training Content-Based Recommender...")
        
        self.movie_ids = movies_df['movie_id'].tolist()
        self.movie_features = movies_df.apply(self._create_feature_string, axis=1)
        self.tfidf_matrix = self.tfidf.fit_transform(self.movie_features)
        
        self.is_fitted = True
        print(f"Fitted on {len(self.movie_ids)} movies")
        print(f"  TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        return self
    
    def get_similar_movies(self, movie_id, n=10):
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        try:
            idx = self.movie_ids.index(movie_id)
        except ValueError:
            return []
        
        movie_vector = self.tfidf_matrix[idx]
        similarity_scores = cosine_similarity(movie_vector, self.tfidf_matrix)[0]
        
        similar_indices = similarity_scores.argsort()[::-1][1:n+1]
        
        results = [
            (self.movie_ids[i], float(similarity_scores[i]))
            for i in similar_indices
        ]
        
        return results
    
    def recommend_for_user(self, liked_movie_ids, n=10, exclude_ids=None):
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if not liked_movie_ids:
            return []
        
        exclude_ids = set(exclude_ids or [])
        exclude_ids.update(liked_movie_ids)
        
        liked_indices = []
        for mid in liked_movie_ids:
            try:
                liked_indices.append(self.movie_ids.index(mid))
            except ValueError:
                continue
        
        if not liked_indices:
            return []
        
        user_profile = self.tfidf_matrix[liked_indices].mean(axis=0)
        user_profile = np.asarray(user_profile).flatten()
        
        all_scores = cosine_similarity([user_profile], self.tfidf_matrix)[0]
        
        raw_recommendations = []
        for idx in all_scores.argsort()[::-1]:
            movie_id = self.movie_ids[idx]
            if movie_id not in exclude_ids:
                score = float(all_scores[idx])
                raw_recommendations.append({
                    'movie_id': movie_id,
                    'raw_score': score,
                })
                if len(raw_recommendations) >= n:
                    break
        
        if raw_recommendations:
            raw_scores = [r['raw_score'] for r in raw_recommendations]
            max_raw = max(raw_scores) if raw_scores else 1.0
            min_raw = min(raw_scores) if raw_scores else 0.0
            score_range = max_raw - min_raw if max_raw != min_raw else 1.0
            
            recommendations = []
            for i, rec in enumerate(raw_recommendations):
                if score_range > 0:
                    normalized = (rec['raw_score'] - min_raw) / score_range
                else:
                    normalized = 0.5
                
                rank_factor = 1.0 - (i * 0.02)
                boosted_score = 0.70 + (normalized * 0.25 * rank_factor)
                boosted_score = min(max(boosted_score, 0.70), 0.95)
                
                explanation = f"Similar to movies you've liked ({boosted_score:.0%} match)"
                recommendations.append({
                    'movie_id': rec['movie_id'],
                    'score': boosted_score,
                    'raw_score': rec['raw_score'],
                    'algorithm': 'content_based',
                    'rank': i + 1,
                    'explanation': explanation
                })
        else:
            recommendations = []
        
        return recommendations
    
    def save(self, filename='content_based_model.pkl'):
        filepath = MODELS_PATH / filename
        model_data = {
            'tfidf': self.tfidf,
            'tfidf_matrix': self.tfidf_matrix,
            'movie_ids': self.movie_ids,
            'is_fitted': self.is_fitted
        }
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load(self, filename='content_based_model.pkl'):
        filepath = MODELS_PATH / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Model not found: {filepath}")
        
        model_data = joblib.load(filepath)
        self.tfidf = model_data['tfidf']
        self.tfidf_matrix = model_data['tfidf_matrix']
        self.movie_ids = model_data['movie_ids']
        self.is_fitted = model_data['is_fitted']
        print(f"Model loaded from {filepath}")


if __name__ == "__main__":
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
