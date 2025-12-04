"""
Sentiment Analysis Module
Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) for sentiment scoring
"""

import pandas as pd
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SentimentAnalyzer:
    """Handles sentiment analysis using VADER"""
    
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        
        # Initialize VADER
        self.analyzer = SentimentIntensityAnalyzer()
        print("✓ VADER Sentiment Analyzer initialized")
    
    def clean_text(self, text):
        """Clean review text for analysis"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove special characters but keep punctuation (VADER uses it)
        text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of a single text
        Returns compound score (-1 to 1) and sentiment label
        """
        cleaned_text = self.clean_text(text)
        
        if not cleaned_text:
            return {
                'compound': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0,
                'label': 'neutral'
            }
        
        scores = self.analyzer.polarity_scores(cleaned_text)
        
        # Determine label based on compound score
        if scores['compound'] >= 0.05:
            label = 'positive'
        elif scores['compound'] <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'compound': scores['compound'],
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
            'label': label
        }
    
    def analyze_dataframe(self, df, text_column='review', output_prefix='sentiment'):
        """
        Analyze sentiment for entire DataFrame
        Adds new columns: {prefix}_compound, {prefix}_label
        """
        print(f"Analyzing sentiment for {len(df)} reviews...")
        
        # Analyze each row
        sentiments = df[text_column].apply(self.analyze_sentiment)
        
        # Extract compound score and label into new columns
        df[f'{output_prefix}_compound'] = sentiments.apply(lambda x: x['compound'])
        df[f'{output_prefix}_positive'] = sentiments.apply(lambda x: x['positive'])
        df[f'{output_prefix}_negative'] = sentiments.apply(lambda x: x['negative'])
        df[f'{output_prefix}_label'] = sentiments.apply(lambda x: x['label'])
        
        # Print summary statistics
        label_counts = df[f'{output_prefix}_label'].value_counts()
        print(f"\n✓ Sentiment Analysis Complete:")
        print(f"  Positive: {label_counts.get('positive', 0)} ({label_counts.get('positive', 0)/len(df)*100:.1f}%)")
        print(f"  Neutral:  {label_counts.get('neutral', 0)} ({label_counts.get('neutral', 0)/len(df)*100:.1f}%)")
        print(f"  Negative: {label_counts.get('negative', 0)} ({label_counts.get('negative', 0)/len(df)*100:.1f}%)")
        print(f"  Average Compound Score: {df[f'{output_prefix}_compound'].mean():.3f}")
        
        return df
    
    def get_sentiment_summary(self, df, group_by_column, sentiment_column='sentiment_compound'):
        """
        Get sentiment summary grouped by a column (e.g., genre, date)
        """
        summary = df.groupby(group_by_column).agg({
            sentiment_column: ['mean', 'std', 'count'],
        }).round(3)
        
        summary.columns = ['avg_sentiment', 'std_sentiment', 'count']
        summary = summary.sort_values('avg_sentiment', ascending=False)
        
        return summary


# =========================================================
# STANDALONE EXECUTION
# =========================================================

def main():
    """Test sentiment analysis on sample data"""
    print("=" * 60)
    print("SENTIMENT ANALYSIS MODULE - TEST")
    print("=" * 60)
    
    analyzer = SentimentAnalyzer()
    
    # Test with sample reviews
    test_reviews = [
        "This movie was absolutely incredible! Best film I've seen all year.",
        "Terrible waste of time. The plot made no sense and the acting was awful.",
        "It was okay, nothing special but not bad either.",
        "OMG this horror movie scared me so much! I loved every minute of it!!!",
        "Boring and predictable. Very disappointed.",
    ]
    
    print("\n[Test Results]")
    for review in test_reviews:
        result = analyzer.analyze_sentiment(review)
        print(f"\nReview: \"{review[:50]}...\"")
        print(f"  Compound Score: {result['compound']:.3f}")
        print(f"  Label: {result['label']}")


if __name__ == "__main__":
    main()

