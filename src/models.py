"""
Machine Learning Models Module
Implements trend prediction using scikit-learn
"""

import pandas as pd
import numpy as np
import os
import sys
import joblib
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.preprocessing import StandardScaler

from config.settings import MODEL_CONFIG, DATA_PROCESSED_PATH


class TrendPredictor:
    """
    Machine Learning models for predicting movie genre trends
    
    Tasks:
    1. Regression: Predict next-day engagement
    2. Classification: Predict if genre is RISING, DECLINING, or STABLE
    """
    
    def __init__(self):
        self.regression_model = None
        self.classification_model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    # =========================================================
    # FEATURE ENGINEERING
    # =========================================================
    
    def prepare_features(self, df):
        """
        Create features for ML models from daily trends data
        """
        print("\n[FEATURE ENGINEERING]")
        
        df = df.copy()
        df = df.sort_values(['genre', 'date'])
        
        # Lag features (previous day values)
        df['engagement_lag1'] = df.groupby('genre')['total_engagement'].shift(1)
        df['engagement_lag2'] = df.groupby('genre')['total_engagement'].shift(2)
        df['engagement_lag3'] = df.groupby('genre')['total_engagement'].shift(3)
        
        df['sentiment_lag1'] = df.groupby('genre')['avg_sentiment'].shift(1)
        df['reviews_lag1'] = df.groupby('genre')['total_reviews'].shift(1)
        
        # Rolling averages (7-day window)
        df['engagement_ma7'] = df.groupby('genre')['total_engagement'].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        df['sentiment_ma7'] = df.groupby('genre')['avg_sentiment'].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        
        # Velocity (momentum indicator)
        df['engagement_velocity'] = df.groupby('genre')['total_engagement'].pct_change() * 100
        
        # Day of week (some genres may trend on weekends)
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Create target variable for classification
        df['trend_direction'] = df['engagement_velocity'].apply(self._classify_trend)
        
        # Drop rows with NaN from lag features
        df = df.dropna(subset=['engagement_lag1', 'engagement_lag2'])
        
        print(f"✓ Created {len(df)} feature records")
        print(f"✓ Features: {df.columns.tolist()}")
        
        return df
    
    def _classify_trend(self, velocity):
        """Classify trend based on velocity percentage"""
        if pd.isna(velocity):
            return 'STABLE'
        if velocity > 10:  # More than 10% increase
            return 'RISING'
        elif velocity < -10:  # More than 10% decrease
            return 'DECLINING'
        else:
            return 'STABLE'
    
    # =========================================================
    # REGRESSION MODEL (Predict Engagement)
    # =========================================================
    
    def train_regression_model(self, df, target='total_engagement'):
        """
        Train regression model to predict next-day engagement
        """
        print("\n" + "=" * 50)
        print("TRAINING REGRESSION MODEL")
        print("=" * 50)
        
        # Define features
        self.feature_columns = [
            'engagement_lag1', 'engagement_lag2', 'engagement_lag3',
            'sentiment_lag1', 'reviews_lag1',
            'engagement_ma7', 'sentiment_ma7',
            'day_of_week', 'is_weekend'
        ]
        
        # Prepare data
        X = df[self.feature_columns].fillna(0)
        y = df[target]
        
        # Split data (temporal split - train on earlier data)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=MODEL_CONFIG['test_size'],
            random_state=MODEL_CONFIG['random_state'],
            shuffle=False  # Maintain temporal order
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train multiple models and compare
        models = {
            'Linear Regression': LinearRegression(),
            'Decision Tree': DecisionTreeRegressor(max_depth=10, random_state=42),
            'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        }
        
        best_model = None
        best_mae = float('inf')
        
        print("\n[Model Comparison]")
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            print(f"\n{name}:")
            print(f"  MAE:  {mae:.2f}")
            print(f"  RMSE: {rmse:.2f}")
            print(f"  R²:   {r2:.4f}")
            
            if mae < best_mae:
                best_mae = mae
                best_model = model
                self.regression_model = model
        
        print(f"\n✓ Best model selected: {type(best_model).__name__}")
        
        # Feature importance (if available)
        if hasattr(best_model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': best_model.feature_importances_
            }).sort_values('importance', ascending=False)
            print("\n[Feature Importance]")
            print(importance.to_string(index=False))
        
        return {
            'model': self.regression_model,
            'mae': best_mae,
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': self.regression_model.predict(X_test_scaled)
        }
    
    # =========================================================
    # CLASSIFICATION MODEL (Predict Trend Direction)
    # =========================================================
    
    def train_classification_model(self, df, target='trend_direction'):
        """
        Train classification model to predict if genre is RISING/DECLINING/STABLE
        """
        print("\n" + "=" * 50)
        print("TRAINING CLASSIFICATION MODEL")
        print("=" * 50)
        
        # Define features (same as regression)
        feature_cols = [
            'engagement_lag1', 'engagement_lag2',
            'sentiment_lag1', 'reviews_lag1',
            'engagement_ma7', 'sentiment_ma7',
            'is_weekend'
        ]
        
        # Prepare data
        X = df[feature_cols].fillna(0)
        y = df[target]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=MODEL_CONFIG['test_size'],
            random_state=MODEL_CONFIG['random_state'],
            stratify=y  # Maintain class balance
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models
        models = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
            'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        }
        
        best_model = None
        best_accuracy = 0
        
        print("\n[Model Comparison]")
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            print(f"\n{name}:")
            print(f"  Accuracy:  {accuracy:.4f}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            print(f"  F1 Score:  {f1:.4f}")
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = model
                self.classification_model = model
        
        print(f"\n✓ Best model selected: {type(best_model).__name__}")
        
        # Confusion Matrix
        y_pred_best = best_model.predict(X_test_scaled)
        print("\n[Classification Report]")
        print(classification_report(y_test, y_pred_best, zero_division=0))
        
        return {
            'model': self.classification_model,
            'accuracy': best_accuracy,
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': y_pred_best
        }
    
    # =========================================================
    # PREDICTION
    # =========================================================
    
    def predict_engagement(self, features_dict):
        """Predict engagement for new data point"""
        if self.regression_model is None:
            raise ValueError("Regression model not trained!")
        
        features = pd.DataFrame([features_dict])[self.feature_columns]
        features_scaled = self.scaler.transform(features)
        
        prediction = self.regression_model.predict(features_scaled)[0]
        return max(0, int(prediction))  # Engagement can't be negative
    
    def predict_trend(self, features_dict):
        """Predict trend direction for new data point"""
        if self.classification_model is None:
            raise ValueError("Classification model not trained!")
        
        feature_cols = ['engagement_lag1', 'engagement_lag2', 'sentiment_lag1', 
                       'reviews_lag1', 'engagement_ma7', 'sentiment_ma7', 'is_weekend']
        
        features = pd.DataFrame([features_dict])[feature_cols]
        features_scaled = self.scaler.transform(features)
        
        prediction = self.classification_model.predict(features_scaled)[0]
        probabilities = self.classification_model.predict_proba(features_scaled)[0]
        
        return {
            'prediction': prediction,
            'confidence': max(probabilities)
        }
    
    # =========================================================
    # SAVE/LOAD MODELS
    # =========================================================
    
    def save_models(self, output_dir=None):
        """Save trained models to disk"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        
        os.makedirs(output_dir, exist_ok=True)
        
        if self.regression_model:
            joblib.dump(self.regression_model, os.path.join(output_dir, 'regression_model.pkl'))
        if self.classification_model:
            joblib.dump(self.classification_model, os.path.join(output_dir, 'classification_model.pkl'))
        joblib.dump(self.scaler, os.path.join(output_dir, 'scaler.pkl'))
        
        print(f"✓ Models saved to {output_dir}")
    
    def load_models(self, model_dir=None):
        """Load trained models from disk"""
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        
        self.regression_model = joblib.load(os.path.join(model_dir, 'regression_model.pkl'))
        self.classification_model = joblib.load(os.path.join(model_dir, 'classification_model.pkl'))
        self.scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        
        print(f"✓ Models loaded from {model_dir}")


# =========================================================
# MAIN EXECUTION
# =========================================================

def main():
    """Train and evaluate models"""
    print("=" * 60)
    print("MOVIE TREND PREDICTOR - ML TRAINING")
    print("=" * 60)
    
    # Load processed daily trends
    trends_path = os.path.join(DATA_PROCESSED_PATH, 'daily_trends_processed.csv')
    
    if not os.path.exists(trends_path):
        print(f"✗ File not found: {trends_path}")
        print("Please run etl.py first to generate processed data.")
        return
    
    df = pd.read_csv(trends_path)
    print(f"✓ Loaded {len(df)} daily trend records")
    
    # Initialize predictor
    predictor = TrendPredictor()
    
    # Prepare features
    df_features = predictor.prepare_features(df)
    
    # Train models
    regression_results = predictor.train_regression_model(df_features)
    classification_results = predictor.train_classification_model(df_features)
    
    # Save models
    predictor.save_models()
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"\nRegression MAE: {regression_results['mae']:.2f}")
    print(f"Classification Accuracy: {classification_results['accuracy']:.4f}")


if __name__ == "__main__":
    main()

