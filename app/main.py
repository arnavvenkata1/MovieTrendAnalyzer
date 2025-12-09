"""
CineSwipe - Main Streamlit Application
Movie Recommendation System with Swipe Interface
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import APP_CONFIG, GENRE_OPTIONS, MOOD_OPTIONS, AGE_GROUPS, DECADE_OPTIONS

# Page configuration
st.set_page_config(
    page_title="CineSwipe 🎬",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    .main-header {
        font-family: 'Poppins', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #E50914 0%, #FF6B6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-family: 'Poppins', sans-serif;
        text-align: center;
        color: #888;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .movie-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    
    .movie-card:hover {
        transform: translateY(-5px);
    }
    
    .movie-title {
        font-family: 'Poppins', sans-serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: #fff;
        margin-bottom: 0.5rem;
    }
    
    .movie-year {
        color: #888;
        font-size: 1rem;
    }
    
    .genre-tag {
        display: inline-block;
        background: linear-gradient(135deg, #E50914 0%, #FF6B6B 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.8rem;
    }
    
    .rating-badge {
        background: #FFD700;
        color: #000;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        font-weight: 600;
    }
    
    .swipe-button {
        font-size: 3rem;
        padding: 1rem 2rem;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .swipe-left {
        background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
    }
    
    .swipe-right {
        background: linear-gradient(135deg, #00C851 0%, #007E33 100%);
    }
    
    .stat-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #E50914;
    }
    
    .stat-label {
        color: #888;
        font-size: 0.9rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'onboarding_complete' not in st.session_state:
        st.session_state.onboarding_complete = False
    if 'preferences' not in st.session_state:
        st.session_state.preferences = {}
    if 'current_movie_idx' not in st.session_state:
        st.session_state.current_movie_idx = 0
    if 'swipe_history' not in st.session_state:
        st.session_state.swipe_history = []
    if 'liked_movies' not in st.session_state:
        st.session_state.liked_movies = []
    if 'disliked_movies' not in st.session_state:
        st.session_state.disliked_movies = []
    if 'movies_to_show' not in st.session_state:
        st.session_state.movies_to_show = []


def show_landing_page():
    """Display landing page for new users"""
    st.markdown('<h1 class="main-header">🎬 CineSwipe</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Swipe your way to your next favorite movie</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### How it works:
        
        1. 📝 **Tell us your preferences** - Quick onboarding to understand your taste
        2. 🎬 **Swipe through movies** - Right for like, Left for pass
        3. ✨ **Get personalized recommendations** - Our AI learns what you love
        
        ---
        """)
        
        username = st.text_input("Enter a username to get started:", placeholder="movie_lover_123")
        
        if st.button("🚀 Start Discovering", type="primary", use_container_width=True):
            if username:
                st.session_state.user = {
                    'username': username,
                    'user_id': hash(username) % 10000  # Simple ID for demo
                }
                st.rerun()
            else:
                st.error("Please enter a username")


def show_onboarding():
    """Display onboarding questionnaire"""
    st.markdown('<h1 class="main-header">🎯 Let\'s Get to Know You</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Help us find movies you\'ll love</p>', unsafe_allow_html=True)
    
    with st.form("onboarding_form"):
        st.subheader("1. What genres do you enjoy? 🎭")
        preferred_genres = st.multiselect(
            "Select your favorite genres (pick at least 2):",
            options=GENRE_OPTIONS,
            default=["Action", "Comedy"]
        )
        
        st.subheader("2. Any genres you'd like to avoid? 🚫")
        avoided_genres = st.multiselect(
            "Select genres to exclude:",
            options=[g for g in GENRE_OPTIONS if g not in preferred_genres],
            default=[]
        )
        
        st.subheader("3. What's your mood today? 🎭")
        mood_cols = st.columns(4)
        mood_options_display = {m[0]: f"{m[2]} {m[1]}" for m in MOOD_OPTIONS}
        selected_mood = st.radio(
            "Select your mood:",
            options=[m[0] for m in MOOD_OPTIONS],
            format_func=lambda x: mood_options_display[x],
            horizontal=True
        )
        
        st.subheader("4. Preferred era of movies? 📅")
        decade_options_display = {d[0]: d[1] for d in DECADE_OPTIONS}
        preferred_decade = st.select_slider(
            "Slide to select:",
            options=[d[0] for d in DECADE_OPTIONS],
            value="2010s",
            format_func=lambda x: decade_options_display[x]
        )
        
        st.subheader("5. Minimum rating? ⭐")
        min_rating = st.slider(
            "Only show movies rated above:",
            min_value=5.0,
            max_value=9.0,
            value=6.5,
            step=0.5
        )
        
        st.subheader("6. Your age group? 👤")
        age_group = st.selectbox(
            "This helps us recommend age-appropriate content:",
            options=AGE_GROUPS,
            index=1
        )
        
        submitted = st.form_submit_button("🎬 Start Swiping!", type="primary", use_container_width=True)
        
        if submitted:
            if len(preferred_genres) < 2:
                st.error("Please select at least 2 favorite genres")
            else:
                st.session_state.preferences = {
                    'preferred_genres': preferred_genres,
                    'avoided_genres': avoided_genres,
                    'mood_preference': selected_mood,
                    'preferred_decade': preferred_decade,
                    'min_rating': min_rating,
                    'age_group': age_group
                }
                st.session_state.onboarding_complete = True
                st.rerun()


def load_sample_movies():
    """Load sample movies from JSON file or fall back to defaults"""
    import json
    
    # Try to load from generated JSON file
    json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
    
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                movies = json.load(f)
            # Shuffle for variety
            import random
            random.shuffle(movies)
            return movies[:50]  # Return 50 random movies per session
        except Exception as e:
            print(f"Error loading movies JSON: {e}")
    
    # Fallback to hardcoded sample if JSON doesn't exist
    sample_movies = [
        {
            'movie_id': 19995, 'title': 'Avatar', 'release_year': 2009,
            'genres': ['Action', 'Adventure', 'Fantasy', 'Science Fiction'],
            'vote_average': 7.2, 'overview': 'In the 22nd century, a paraplegic Marine is dispatched to the moon Pandora on a unique mission...'
        },
        {
            'movie_id': 285, 'title': 'Pirates of the Caribbean: At World\'s End', 'release_year': 2007,
            'genres': ['Adventure', 'Fantasy', 'Action'],
            'vote_average': 6.9, 'overview': 'Captain Barbossa, long believed to be dead, has come back to life...'
        },
        {
            'movie_id': 206647, 'title': 'Spectre', 'release_year': 2015,
            'genres': ['Action', 'Adventure', 'Crime'],
            'vote_average': 6.3, 'overview': 'A cryptic message from Bond\'s past sends him on a trail to uncover a sinister organization...'
        },
        {
            'movie_id': 49026, 'title': 'The Dark Knight Rises', 'release_year': 2012,
            'genres': ['Action', 'Crime', 'Drama', 'Thriller'],
            'vote_average': 7.6, 'overview': 'Following the death of District Attorney Harvey Dent, Batman assumes responsibility...'
        },
        {
            'movie_id': 49529, 'title': 'John Carter', 'release_year': 2012,
            'genres': ['Action', 'Adventure', 'Science Fiction'],
            'vote_average': 6.1, 'overview': 'John Carter, a Civil War veteran, is transported to Mars...'
        },
    ]
    return sample_movies


def show_swipe_interface():
    """Display the movie swiping interface"""
    st.markdown('<h1 class="main-header">🎬 Discover Movies</h1>', unsafe_allow_html=True)
    
    # Load movies if not loaded
    if not st.session_state.movies_to_show:
        st.session_state.movies_to_show = load_sample_movies()
    
    movies = st.session_state.movies_to_show
    idx = st.session_state.current_movie_idx
    
    # Stats sidebar
    with st.sidebar:
        st.markdown("### 📊 Your Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👍 Liked", len(st.session_state.liked_movies))
        with col2:
            st.metric("👎 Passed", len(st.session_state.disliked_movies))
        
        st.divider()
        st.markdown("### 🎯 Preferences")
        st.write(f"**Genres:** {', '.join(st.session_state.preferences.get('preferred_genres', []))}")
        st.write(f"**Mood:** {st.session_state.preferences.get('mood_preference', 'N/A')}")
        
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.current_movie_idx = 0
            st.session_state.liked_movies = []
            st.session_state.disliked_movies = []
            st.rerun()
    
    # Check if we have movies to show
    if idx >= len(movies):
        st.success("🎉 You've seen all available movies!")
        st.markdown("### Your Liked Movies:")
        for mid in st.session_state.liked_movies:
            movie = next((m for m in movies if m['movie_id'] == mid), None)
            if movie:
                st.write(f"- {movie['title']} ({movie['release_year']})")
        
        if st.button("🔄 Start Over", type="primary"):
            st.session_state.current_movie_idx = 0
            st.session_state.liked_movies = []
            st.session_state.disliked_movies = []
            st.rerun()
        return
    
    movie = movies[idx]
    
    # Movie card
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(f"""
        <div class="movie-card">
            <h2 class="movie-title">{movie['title']}</h2>
            <p class="movie-year">{movie['release_year']} • ⭐ {movie['vote_average']}/10</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Genre tags
        genre_html = ' '.join([f'<span class="genre-tag">{g}</span>' for g in movie['genres'][:4]])
        st.markdown(f'<div style="margin: 1rem 0;">{genre_html}</div>', unsafe_allow_html=True)
        
        # Overview
        st.markdown(f"**Overview:** {movie['overview'][:200]}...")
        
        # Swipe buttons
        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        
        with btn_col1:
            if st.button("👎 Pass", key="left", use_container_width=True):
                st.session_state.disliked_movies.append(movie['movie_id'])
                st.session_state.swipe_history.append({
                    'movie_id': movie['movie_id'],
                    'direction': 'left'
                })
                st.session_state.current_movie_idx += 1
                st.rerun()
        
        with btn_col2:
            if st.button("⏭️ Skip", key="skip", use_container_width=True):
                st.session_state.swipe_history.append({
                    'movie_id': movie['movie_id'],
                    'direction': 'skip'
                })
                st.session_state.current_movie_idx += 1
                st.rerun()
        
        with btn_col3:
            if st.button("👍 Like", key="right", use_container_width=True, type="primary"):
                st.session_state.liked_movies.append(movie['movie_id'])
                st.session_state.swipe_history.append({
                    'movie_id': movie['movie_id'],
                    'direction': 'right'
                })
                st.session_state.current_movie_idx += 1
                st.rerun()
        
        # Progress
        progress = (idx + 1) / len(movies)
        st.progress(progress, text=f"Movie {idx + 1} of {len(movies)}")


def show_recommendations():
    """Display personalized recommendations using ML model"""
    st.markdown('<h1 class="main-header">✨ Your Recommendations</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Based on your preferences and swipes</p>', unsafe_allow_html=True)
    
    if len(st.session_state.liked_movies) < 3:
        st.warning("👆 Swipe on at least 3 movies to get personalized recommendations!")
        st.info("Go to the Swipe tab and like at least 3 movies to unlock AI recommendations!")
        return
    
    # Try to load the trained ML model
    try:
        from src.models.content_based import ContentBasedRecommender
        import json
        
        model_path = Path(__file__).parent.parent / 'models' / 'saved' / 'content_based_model.pkl'
        json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
        
        if model_path.exists() and json_path.exists():
            # Load model
            model = ContentBasedRecommender()
            model.load('content_based_model.pkl')
            
            # Load movie data for titles
            with open(json_path, 'r') as f:
                all_movies = {m['movie_id']: m for m in json.load(f)}
            
            # Get recommendations based on liked movies
            liked_ids = st.session_state.liked_movies
            all_swiped = liked_ids + st.session_state.disliked_movies
            
            recommendations = model.recommend_for_user(
                liked_movie_ids=liked_ids,
                n=10,
                exclude_ids=all_swiped
            )
            
            if recommendations:
                st.success(f"🎯 Based on the {len(liked_ids)} movies you liked, here are our top picks!")
                
                for i, rec in enumerate(recommendations, 1):
                    movie = all_movies.get(rec['movie_id'], {})
                    title = movie.get('title', f"Movie {rec['movie_id']}")
                    year = movie.get('release_year', 'N/A')
                    genres = movie.get('genres', [])
                    overview = movie.get('overview', '')[:200]
                    
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"### {i}. {title} ({year})")
                            if genres:
                                st.caption(f"🎭 {', '.join(genres[:3])}")
                            st.write(f"{overview}..." if overview else "")
                            st.caption(f"💡 {rec.get('explanation', 'Similar to movies you liked')}")
                        with col2:
                            score_pct = min(rec['score'] * 100, 99)
                            st.metric("Match", f"{score_pct:.0f}%")
                        st.divider()
            else:
                st.info("Keep swiping to improve your recommendations!")
        else:
            st.warning("⚠️ ML model not found. Run `python src/train_models_offline.py` first!")
            
    except Exception as e:
        st.error(f"Error loading recommendations: {e}")
        # Fallback to simple recommendations
        st.info("Showing sample recommendations...")
        sample_recs = [
            {'title': 'Inception', 'year': 2010, 'score': 0.95, 'reason': 'Mind-bending thriller'},
            {'title': 'The Matrix', 'year': 1999, 'score': 0.92, 'reason': 'Sci-Fi classic'},
            {'title': 'Interstellar', 'year': 2014, 'score': 0.89, 'reason': 'Epic space adventure'},
        ]
        for i, rec in enumerate(sample_recs, 1):
            st.markdown(f"**{i}. {rec['title']}** ({rec['year']}) - {rec['reason']}")


def show_analytics_dashboard():
    """Display analytics dashboard with charts"""
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.markdown('<h1 class="main-header">📊 Your Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Insights from your movie preferences</p>', unsafe_allow_html=True)
    
    # Key metrics
    total_swipes = len(st.session_state.swipe_history)
    likes = len(st.session_state.liked_movies)
    dislikes = len(st.session_state.disliked_movies)
    like_rate = likes / max(total_swipes, 1) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Swipes", total_swipes)
    with col2:
        st.metric("Movies Liked 👍", likes)
    with col3:
        st.metric("Movies Passed 👎", dislikes)
    with col4:
        st.metric("Like Rate", f"{like_rate:.1f}%")
    
    st.divider()
    
    if total_swipes == 0:
        st.info("👆 Start swiping to see your analytics!")
        return
    
    # Load movie data for analysis
    try:
        import json
        json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
        
        if json_path.exists():
            with open(json_path, 'r') as f:
                all_movies = {m['movie_id']: m for m in json.load(f)}
            
            # Analyze liked movies by genre
            genre_counts = {}
            for movie_id in st.session_state.liked_movies:
                movie = all_movies.get(movie_id, {})
                for genre in movie.get('genres', []):
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎭 Your Favorite Genres")
                if genre_counts:
                    genre_df = pd.DataFrame([
                        {'Genre': k, 'Count': v} 
                        for k, v in sorted(genre_counts.items(), key=lambda x: -x[1])
                    ])
                    fig = px.bar(
                        genre_df, x='Genre', y='Count',
                        color='Count',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("Like some movies to see genre preferences!")
            
            with col2:
                st.subheader("📈 Swipe Distribution")
                if total_swipes > 0:
                    swipe_data = pd.DataFrame({
                        'Type': ['Liked 👍', 'Passed 👎'],
                        'Count': [likes, dislikes]
                    })
                    fig = px.pie(
                        swipe_data, values='Count', names='Type',
                        color_discrete_sequence=['#00C851', '#ff4444'],
                        hole=0.4
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Swipe history table
            st.subheader("📋 Your Swipe History")
            history_data = []
            for swipe in st.session_state.swipe_history[-20:]:  # Last 20
                movie = all_movies.get(swipe['movie_id'], {})
                history_data.append({
                    'Movie': movie.get('title', 'Unknown'),
                    'Year': movie.get('release_year', 'N/A'),
                    'Verdict': '👍 Liked' if swipe['direction'] == 'right' else '👎 Passed'
                })
            
            if history_data:
                st.dataframe(
                    pd.DataFrame(history_data),
                    use_container_width=True,
                    hide_index=True
                )
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        # Basic fallback
        st.write(f"You've made {total_swipes} swipes so far!")


def main():
    """Main application entry point"""
    init_session_state()
    
    # Navigation
    if st.session_state.user is None:
        show_landing_page()
    elif not st.session_state.onboarding_complete:
        show_onboarding()
    else:
        # Sidebar navigation
        page = st.sidebar.radio(
            "Navigate",
            ["🎬 Swipe", "✨ Recommendations", "📊 Analytics"],
            label_visibility="collapsed"
        )
        
        if page == "🎬 Swipe":
            show_swipe_interface()
        elif page == "✨ Recommendations":
            show_recommendations()
        elif page == "📊 Analytics":
            show_analytics_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666;">CineSwipe | CS210 Data Management | Anish Shah & Arnav Venkata</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

