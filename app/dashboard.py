"""
Movie Trend Analyzer - Streamlit Dashboard
Interactive visualization of movie genre trends and predictions
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page configuration
st.set_page_config(
    page_title="Movie Trend Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #E50914;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stMetric > div {
        background-color: #262626;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load_data():
    """Load processed data files"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed')
    
    data = {}
    
    # Load Letterboxd processed
    letterboxd_path = os.path.join(data_dir, 'letterboxd_processed.csv')
    if os.path.exists(letterboxd_path):
        data['letterboxd'] = pd.read_csv(letterboxd_path)
        data['letterboxd']['review_date'] = pd.to_datetime(data['letterboxd']['review_date'], errors='coerce')
    
    # Load daily trends
    trends_path = os.path.join(data_dir, 'daily_trends_processed.csv')
    if os.path.exists(trends_path):
        data['daily_trends'] = pd.read_csv(trends_path)
        data['daily_trends']['date'] = pd.to_datetime(data['daily_trends']['date'], errors='coerce')
    
    # Load TMDB movies
    tmdb_path = os.path.join(data_dir, 'tmdb_movies_processed.csv')
    if os.path.exists(tmdb_path):
        data['tmdb'] = pd.read_csv(tmdb_path)
    
    return data


# =========================================================
# VISUALIZATION FUNCTIONS
# =========================================================

def plot_engagement_over_time(df, selected_genres):
    """Line chart of engagement over time by genre"""
    filtered = df[df['genre'].isin(selected_genres)]
    
    fig = px.line(
        filtered,
        x='date',
        y='total_engagement',
        color='genre',
        title='📈 Engagement Trends Over Time',
        labels={'total_engagement': 'Total Engagement', 'date': 'Date'},
        template='plotly_dark'
    )
    
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400
    )
    
    return fig


def plot_sentiment_heatmap(df):
    """Heatmap of average sentiment by genre and time"""
    pivot = df.pivot_table(
        values='avg_sentiment',
        index='genre',
        columns=pd.to_datetime(df['date']).dt.strftime('%Y-%m'),
        aggfunc='mean'
    )
    
    fig = px.imshow(
        pivot,
        title='🎭 Sentiment Heatmap by Genre',
        labels=dict(x='Month', y='Genre', color='Avg Sentiment'),
        color_continuous_scale='RdYlGn',
        template='plotly_dark'
    )
    
    fig.update_layout(height=400)
    
    return fig


def plot_genre_distribution(df):
    """Pie chart of review distribution by genre"""
    genre_counts = df['genre'].value_counts().head(10)
    
    fig = px.pie(
        values=genre_counts.values,
        names=genre_counts.index,
        title='🎥 Review Distribution by Genre',
        template='plotly_dark',
        hole=0.4
    )
    
    fig.update_layout(height=400)
    
    return fig


def plot_top_movies(df, n=10):
    """Bar chart of top movies by engagement"""
    top_movies = df.nlargest(n, 'like_count')[['movie_name', 'like_count', 'sentiment_compound']]
    
    fig = px.bar(
        top_movies,
        x='like_count',
        y='movie_name',
        orientation='h',
        title=f'🏆 Top {n} Movies by Likes',
        labels={'like_count': 'Total Likes', 'movie_name': 'Movie'},
        color='sentiment_compound',
        color_continuous_scale='RdYlGn',
        template='plotly_dark'
    )
    
    fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
    
    return fig


def plot_actual_vs_predicted(y_actual, y_pred):
    """Scatter plot of actual vs predicted values"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=y_actual,
        y=y_pred,
        mode='markers',
        name='Predictions',
        marker=dict(color='#E50914', size=8, opacity=0.6)
    ))
    
    # Perfect prediction line
    max_val = max(max(y_actual), max(y_pred))
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        name='Perfect Prediction',
        line=dict(color='white', dash='dash')
    ))
    
    fig.update_layout(
        title='🎯 Actual vs Predicted Engagement',
        xaxis_title='Actual Engagement',
        yaxis_title='Predicted Engagement',
        template='plotly_dark',
        height=400
    )
    
    return fig


# =========================================================
# MAIN APP
# =========================================================

def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 Movie Trend Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: gray;">Analyzing social media trends in movie genres | CS210 Final Project</p>', unsafe_allow_html=True)
    
    # Load data
    data = load_data()
    
    if not data:
        st.error("⚠️ No processed data found! Please run the ETL pipeline first:")
        st.code("python src/etl.py", language="bash")
        return
    
    # Sidebar
    st.sidebar.header("🎛️ Controls")
    
    if 'letterboxd' in data:
        available_genres = data['letterboxd']['genre'].dropna().unique().tolist()
        available_genres = [g for g in available_genres if g != 'Unknown'][:10]
        
        selected_genres = st.sidebar.multiselect(
            "Select Genres",
            options=available_genres,
            default=available_genres[:5] if len(available_genres) >= 5 else available_genres
        )
    else:
        selected_genres = []
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trends", "🎭 Sentiment", "🤖 Predictions"])
    
    # =====================
    # TAB 1: Overview
    # =====================
    with tab1:
        st.header("Dataset Overview")
        
        if 'letterboxd' in data:
            df = data['letterboxd']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Reviews", f"{len(df):,}")
            with col2:
                st.metric("Unique Movies", f"{df['movie_name'].nunique():,}")
            with col3:
                avg_sentiment = df['sentiment_compound'].mean()
                st.metric("Avg Sentiment", f"{avg_sentiment:.3f}")
            with col4:
                total_engagement = df['like_count'].sum()
                st.metric("Total Likes", f"{total_engagement:,}")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(plot_genre_distribution(df), use_container_width=True)
            
            with col2:
                st.plotly_chart(plot_top_movies(df), use_container_width=True)
    
    # =====================
    # TAB 2: Trends
    # =====================
    with tab2:
        st.header("Engagement Trends")
        
        if 'daily_trends' in data and selected_genres:
            df = data['daily_trends']
            
            st.plotly_chart(
                plot_engagement_over_time(df, selected_genres),
                use_container_width=True
            )
            
            # Genre comparison table
            st.subheader("📋 Genre Performance Summary")
            
            summary = df[df['genre'].isin(selected_genres)].groupby('genre').agg({
                'total_engagement': ['sum', 'mean'],
                'total_reviews': 'sum',
                'avg_sentiment': 'mean'
            }).round(2)
            
            summary.columns = ['Total Engagement', 'Avg Daily Engagement', 'Total Reviews', 'Avg Sentiment']
            summary = summary.sort_values('Total Engagement', ascending=False)
            
            st.dataframe(summary, use_container_width=True)
        else:
            st.info("Select genres from the sidebar to view trends.")
    
    # =====================
    # TAB 3: Sentiment
    # =====================
    with tab3:
        st.header("Sentiment Analysis")
        
        if 'daily_trends' in data:
            df = data['daily_trends']
            
            st.plotly_chart(plot_sentiment_heatmap(df), use_container_width=True)
            
            # Sentiment distribution by genre
            if 'letterboxd' in data:
                lb_df = data['letterboxd']
                
                fig = px.box(
                    lb_df[lb_df['genre'].isin(selected_genres)],
                    x='genre',
                    y='sentiment_compound',
                    color='genre',
                    title='📊 Sentiment Distribution by Genre',
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # =====================
    # TAB 4: Predictions
    # =====================
    with tab4:
        st.header("ML Predictions")
        
        st.info("🔮 **Prediction Engine**\n\nThis section shows model performance and allows you to make predictions.")
        
        # Check if models exist
        model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        
        if os.path.exists(os.path.join(model_dir, 'regression_model.pkl')):
            st.success("✅ Trained models found!")
            
            # Load metrics if available
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Regression Model")
                st.markdown("""
                - **Task**: Predict next-day engagement
                - **Algorithm**: Random Forest Regressor
                - **Features**: Lag values, moving averages, sentiment
                """)
            
            with col2:
                st.subheader("Classification Model")
                st.markdown("""
                - **Task**: Predict trend direction (RISING/DECLINING/STABLE)
                - **Algorithm**: Random Forest Classifier
                - **Features**: Same as regression
                """)
            
            # Prediction interface
            st.divider()
            st.subheader("🎯 Make a Prediction")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                engagement_lag1 = st.number_input("Yesterday's Engagement", value=1000, step=100)
                engagement_lag2 = st.number_input("2 Days Ago Engagement", value=900, step=100)
            
            with col2:
                sentiment_lag1 = st.slider("Yesterday's Sentiment", -1.0, 1.0, 0.5)
                reviews_lag1 = st.number_input("Yesterday's Review Count", value=50, step=10)
            
            with col3:
                is_weekend = st.checkbox("Is Weekend?")
                engagement_ma7 = st.number_input("7-Day Moving Avg", value=950, step=50)
            
            if st.button("Predict", type="primary"):
                st.success("📈 **Predicted Engagement**: ~1,100")
                st.success("📊 **Trend Direction**: RISING (85% confidence)")
                st.caption("*Note: Connect to trained models for real predictions*")
        
        else:
            st.warning("⚠️ No trained models found. Run the training script first:")
            st.code("python src/models.py", language="bash")
    
    # Footer
    st.divider()
    st.markdown("""
    <p style="text-align: center; color: gray;">
        Movie Trend Analyzer | CS210 Data Management | Anish Shah & Arnav Venkata
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

