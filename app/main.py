import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import uuid
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import APP_CONFIG, GENRE_OPTIONS, MOOD_OPTIONS, AGE_GROUPS, DECADE_OPTIONS
from src.utils.db_postgres import db as postgres_db
from src.utils.db_mongo import mongo_db

st.set_page_config(
    page_title="CineSwipe 🎬",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
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
    if 'db_connected' not in st.session_state:
        st.session_state.db_connected = False
    if 'import_method' not in st.session_state:
        st.session_state.import_method = None
    if 'letterboxd_data' not in st.session_state:
        st.session_state.letterboxd_data = None
    if 'letterboxd_profile_viewed' not in st.session_state:
        st.session_state.letterboxd_profile_viewed = False


def show_landing_page():
    st.markdown('<h1 class="main-header">🎬 CineSwipe</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Swipe your way to your next favorite movie</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### How it works:
        
        1. 📝 **Tell us your preferences** - Quick onboarding OR import from Letterboxd
        2. 🎬 **Swipe through movies** - Right for like, Left for pass
        3. ✨ **Get personalized recommendations** - Our AI learns what you love
        
        ---
        """)
        
        signup_method = st.radio(
            "Choose how to get started:",
            ["✍️ New User (Manual Onboarding)", "📥 Import from Letterboxd"],
            horizontal=True
        )
        
        if signup_method == "✍️ New User (Manual Onboarding)":
            username = st.text_input("Enter a username to get started:", placeholder="movie_lover_123")
            
            if st.button("🚀 Start Discovering", type="primary", use_container_width=True):
                if username:
                    st.session_state.user = {
                        'username': username,
                        'user_id': hash(username) % 10000
                    }
                    st.session_state.import_method = 'manual'
                    st.rerun()
                else:
                    st.error("Please enter a username")
        
        else:
            st.markdown("""
            #### 📥 Import from Letterboxd
            Enter your **public** Letterboxd username to import your ratings.
            We'll use your movie history to personalize recommendations instantly!
            """)
            
            letterboxd_username = st.text_input(
                "Letterboxd Username:", 
                placeholder="your_letterboxd_username",
                help="Your Letterboxd profile must be public"
            )
            
            if st.button("🔍 Import My Ratings", type="primary", use_container_width=True):
                if letterboxd_username:
                    with st.spinner("Connecting to Letterboxd..."):
                        try:
                            from src.letterboxd_import import LetterboxdImporter
                            
                            importer = LetterboxdImporter()
                            is_valid, msg = importer.validate_username(letterboxd_username)
                            
                            if is_valid:
                                st.success(f"✅ Found profile! {msg}")
                                
                                with st.spinner("Importing your movie ratings..."):
                                    movies = importer.get_user_ratings(letterboxd_username, limit=50)
                                    
                                    if movies:
                                        liked = [m for m in movies if m.get('liked') and m.get('matched')]
                                        disliked = [m for m in movies if not m.get('liked') and m.get('matched')]
                                        
                                        st.success(f"🎬 Imported {len(liked)} liked and {len(disliked)} disliked movies!")
                                        
                                        st.session_state.user = {
                                            'username': letterboxd_username,
                                            'user_id': hash(letterboxd_username) % 10000
                                        }
                                        st.session_state.import_method = 'letterboxd'
                                        st.session_state.letterboxd_data = movies
                                        st.session_state.liked_movies = [m['movie_id'] for m in liked if m.get('movie_id')]
                                        st.session_state.disliked_movies = [m['movie_id'] for m in disliked if m.get('movie_id')]
                                        
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.warning("No rated movies found. Try manual onboarding instead.")
                            else:
                                st.error(f"❌ {msg}")
                                st.info("Make sure your Letterboxd profile is public and the username is correct.")
                        
                        except ImportError:
                            st.error("Letterboxd import not available. Please install: `pip install feedparser fuzzywuzzy`")
                        except Exception as e:
                            st.error(f"Error importing: {str(e)}")
                else:
                    st.error("Please enter your Letterboxd username")


def show_letterboxd_profile():
    st.markdown('<h1 class="main-header">📥 Your Letterboxd Profile</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Here\'s what we imported from your account</p>', unsafe_allow_html=True)
    
    letterboxd_data = st.session_state.letterboxd_data or []
    liked_movies = st.session_state.liked_movies or []
    disliked_movies = st.session_state.disliked_movies or []
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Imported", len(letterboxd_data))
    with col2:
        st.metric("👍 Liked", len(liked_movies))
    with col3:
        st.metric("👎 Disliked", len(disliked_movies))
    with col4:
        matched = len([m for m in letterboxd_data if m.get('matched')])
        st.metric("🔗 Matched to DB", matched)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎭 Your Favorite Genres")
        
        try:
            import json
            json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
            
            if json_path.exists():
                with open(json_path, 'r') as f:
                    all_movies = {m['movie_id']: m for m in json.load(f)}
                
                genre_counts = {}
                for movie_id in liked_movies:
                    movie = all_movies.get(movie_id, {})
                    for genre in movie.get('genres', []):
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
                
                if genre_counts:
                    sorted_genres = sorted(genre_counts.items(), key=lambda x: -x[1])
                    
                    genre_df = pd.DataFrame(sorted_genres[:8], columns=['Genre', 'Count'])
                    fig = px.bar(
                        genre_df, x='Genre', y='Count',
                        color='Count',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(
                        showlegend=False,
                        height=300,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    top_genres = [g[0] for g in sorted_genres[:5]]
                    st.session_state.preferences['preferred_genres'] = top_genres
                    
                    st.caption(f"**Top genres:** {', '.join(top_genres[:5])}")
                else:
                    st.info("No genre data available from matched movies")
        except Exception as e:
            st.warning(f"Could not analyze genres: {e}")
    
    with col2:
        st.subheader("⭐ Rating Distribution")
        
        ratings = [m.get('letterboxd_rating') for m in letterboxd_data if m.get('letterboxd_rating')]
        
        if ratings:
            rating_counts = {}
            for r in ratings:
                key = f"{r}★"
                rating_counts[key] = rating_counts.get(key, 0) + 1
            
            rating_df = pd.DataFrame([
                {'Rating': k, 'Count': v} 
                for k, v in sorted(rating_counts.items())
            ])
            
            fig = px.pie(
                rating_df, values='Count', names='Rating',
                color_discrete_sequence=px.colors.sequential.RdBu,
                hole=0.4
            )
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rating data available")
    
    st.divider()
    
    st.subheader("📋 Imported Movies")
    
    if letterboxd_data:
        display_data = []
        for m in letterboxd_data[:20]:
            rating = m.get('letterboxd_rating', 'N/A')
            status = '👍 Liked' if m.get('liked') else '👎 Passed'
            matched = '✅' if m.get('matched') else '❌'
            
            display_data.append({
                'Movie': m.get('title', 'Unknown'),
                'Rating': f"{rating}★" if rating != 'N/A' else 'N/A',
                'Status': status,
                'In Database': matched
            })
        
        st.dataframe(
            pd.DataFrame(display_data),
            use_container_width=True,
            hide_index=True
        )
        
        if len(letterboxd_data) > 20:
            st.caption(f"Showing 20 of {len(letterboxd_data)} imported movies")
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🎬 Ready to discover new movies?")
        st.markdown("We'll use your Letterboxd ratings to recommend movies you'll love!")
        
        if st.button("🚀 Start Swiping!", type="primary", use_container_width=True):
            st.session_state.letterboxd_profile_viewed = True
            st.session_state.onboarding_complete = True
            
            if not st.session_state.preferences:
                st.session_state.preferences = {
                    'preferred_genres': [],
                    'avoided_genres': [],
                    'preferred_decade': 'Any',
                    'mood_preference': 'Excited',
                    'min_rating': 6.0,
                    'age_group': '18-24'
                }
            
            st.rerun()
        
        st.caption("Or go back to change your account")
        if st.button("← Use Different Account", use_container_width=True):
            st.session_state.user = None
            st.session_state.letterboxd_data = None
            st.session_state.liked_movies = []
            st.session_state.disliked_movies = []
            st.session_state.import_method = None
            st.rerun()


def show_onboarding():
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
                
                if ensure_db_connection():
                    try:
                        if not st.session_state.username:
                            st.session_state.username = f"user_{uuid.uuid4().hex[:8]}"
                        
                        user = postgres_db.create_user(
                            username=st.session_state.username,
                            age_group=age_group
                        )
                        
                        if user:
                            st.session_state.user_id = user['user_id']
                            st.session_state.username = user['username']
                            
                            postgres_db.update_user_preferences(
                                user_id=st.session_state.user_id,
                                preferences={
                                    'preferred_genres': preferred_genres,
                                    'avoided_genres': avoided_genres,
                                    'preferred_decade': preferred_decade,
                                    'mood_preference': selected_mood,
                                    'min_rating': min_rating
                                }
                            )
                            
                            mongo_db.create_session(
                                user_id=st.session_state.user_id,
                                session_id=st.session_state.session_id
                            )
                            
                            st.success("✅ Profile created! Loading movies...")
                        else:
                            st.warning("⚠️ Could not create user profile, but continuing anyway...")
                    except Exception as e:
                        st.warning(f"⚠️ Database error: {e}. Continuing with local session...")
                
                st.session_state.onboarding_complete = True
                st.rerun()


def ensure_db_connection():
    if not st.session_state.db_connected:
        try:
            postgres_db.connect()
            mongo_db.connect()
            st.session_state.db_connected = True
            return True
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return False
    return True


def load_movies_from_database(user_id=None, limit=20):
    if not ensure_db_connection():
        return load_sample_movies_fallback()
    
    try:
        exclude_ids = []
        if user_id:
            exclude_ids = postgres_db.get_swiped_movie_ids(user_id)
        
        preferences = st.session_state.preferences if st.session_state.preferences else {}
        preferred_genres = preferences.get('preferred_genres', [])
        min_rating = preferences.get('min_rating', 6.0)
        
        if preferred_genres:
            movies = postgres_db.get_movies_by_genre(
                genres=preferred_genres,
                limit=limit * 2,
                exclude_ids=exclude_ids
            )
        else:
            movies = postgres_db.get_random_movies(
                limit=limit * 2,
                exclude_ids=exclude_ids,
                min_rating=min_rating
            )
        
        result_movies = []
        for movie in movies[:limit]:
            if movie.get('vote_average', 0) >= min_rating:
                genres = movie.get('genres', [])
                if isinstance(genres, str):
                    import ast
                    try:
                        genres = ast.literal_eval(genres)
                    except:
                        genres = []
                
                result_movies.append({
                    'movie_id': movie['movie_id'],
                    'title': movie['title'],
                    'release_year': movie.get('release_year'),
                    'genres': genres if isinstance(genres, list) else [],
                    'vote_average': float(movie.get('vote_average', 0)),
                    'overview': movie.get('overview', ''),
                    'poster_url': movie.get('poster_url', '')
                })
        
        if result_movies:
            return result_movies
        else:
            return load_sample_movies_fallback()
            
    except Exception as e:
        st.warning(f"Error loading movies from database: {e}. Using sample movies.")
        return load_sample_movies_fallback()


def record_swipe(movie_id, direction):
    if not st.session_state.user_id:
        return
    
    if not ensure_db_connection():
        return
    
    try:
        postgres_db.record_swipe(
            user_id=st.session_state.user_id,
            movie_id=movie_id,
            direction=direction,
            session_id=st.session_state.session_id
        )
        
        mongo_db.add_session_event(
            session_id=st.session_state.session_id,
            event_type='swipe',
            event_data={
                'movie_id': movie_id,
                'direction': direction
            }
        )
    except Exception as e:
        pass


def load_sample_movies_fallback():
    import json
    
    json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
    
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                movies = json.load(f)
            import random
            random.shuffle(movies)
            return movies[:50]
        except Exception as e:
            print(f"Error loading movies JSON: {e}")
    
    return [
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


def show_swipe_interface():
    st.markdown('<h1 class="main-header">🎬 Discover Movies</h1>', unsafe_allow_html=True)
    
    if not st.session_state.movies_to_show:
        st.session_state.movies_to_show = load_movies_from_database(
            user_id=st.session_state.user_id,
            limit=APP_CONFIG['movies_per_session']
        )
    
    movies = st.session_state.movies_to_show
    idx = st.session_state.current_movie_idx
    
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
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(f"""
        <div class="movie-card">
            <h2 class="movie-title">{movie['title']}</h2>
            <p class="movie-year">{movie['release_year']} • ⭐ {movie['vote_average']}/10</p>
        </div>
        """, unsafe_allow_html=True)
        
        genre_html = ' '.join([f'<span class="genre-tag">{g}</span>' for g in movie['genres'][:4]])
        st.markdown(f'<div style="margin: 1rem 0;">{genre_html}</div>', unsafe_allow_html=True)
        
        overview = movie.get('overview', '') or 'No description available.'
        if len(overview) > 150:
            st.markdown(f"**Overview:** {overview[:150]}...")
            with st.expander("📖 Read Full Overview"):
                st.write(overview)
        else:
            st.markdown(f"**Overview:** {overview}")
        
        import requests
        import urllib.parse
        
        trailer_url = None
        try:
            TMDB_API_KEY = 'fbcab977af26578c4a273d037a4f2655'
            response = requests.get(
                f"https://api.themoviedb.org/3/movie/{movie['movie_id']}/videos",
                params={'api_key': TMDB_API_KEY, 'language': 'en-US'},
                timeout=5
            )
            
            if response.status_code == 200:
                videos = response.json().get('results', [])
                for video_type in ['Trailer', 'Teaser']:
                    for video in videos:
                        if video.get('site') == 'YouTube' and video.get('type') == video_type:
                            trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
                            break
                    if trailer_url:
                        break
                
                if not trailer_url:
                    for video in videos:
                        if video.get('site') == 'YouTube':
                            trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
                            break
        except Exception as e:
            pass
        
        if trailer_url:
            st.link_button("🎬 Watch Trailer", trailer_url, use_container_width=True)
        else:
            search_query = urllib.parse.quote(f"{movie['title']} {movie.get('release_year', '')} official trailer")
            st.link_button("🔍 Find Trailer", f"https://www.youtube.com/results?search_query={search_query}", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        
        with btn_col1:
            if st.button("👎 Pass", key="left", use_container_width=True):
                record_swipe(movie['movie_id'], 'left')
                st.session_state.disliked_movies.append(movie['movie_id'])
                st.session_state.swipe_history.append({
                    'movie_id': movie['movie_id'],
                    'direction': 'left'
                })
                st.session_state.current_movie_idx += 1
                st.rerun()
        
        with btn_col2:
            if st.button("⏭️ Skip", key="skip", use_container_width=True):
                record_swipe(movie['movie_id'], 'skip')
                st.session_state.swipe_history.append({
                    'movie_id': movie['movie_id'],
                    'direction': 'skip'
                })
                st.session_state.current_movie_idx += 1
                st.rerun()
        
        with btn_col3:
            if st.button("👍 Like", key="right", use_container_width=True, type="primary"):
                record_swipe(movie['movie_id'], 'right')
                st.session_state.liked_movies.append(movie['movie_id'])
                st.session_state.swipe_history.append({
                    'movie_id': movie['movie_id'],
                    'direction': 'right'
                })
                st.session_state.current_movie_idx += 1
                st.rerun()
        
        progress = (idx + 1) / len(movies)
        st.progress(progress, text=f"Movie {idx + 1} of {len(movies)}")


def show_recommendations():
    st.markdown('<h1 class="main-header">✨ Your Recommendations</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Based on your preferences and swipes</p>', unsafe_allow_html=True)
    
    min_swipes = APP_CONFIG.get('min_swipes_for_recommendations', 3)
    if len(st.session_state.liked_movies) < min_swipes:
        st.warning(f"👆 Swipe on at least {min_swipes} movies to get personalized recommendations!")
        st.info("Go to the Swipe tab and like some movies to unlock AI recommendations!")
        return
    
    try:
        from src.models.hybrid import HybridRecommender
        
        with st.spinner("🤖 Generating personalized recommendations..."):
            model = HybridRecommender()
            model.load('hybrid')
            
            liked_movie_ids = st.session_state.liked_movies
            exclude_ids = list(set(st.session_state.liked_movies + st.session_state.disliked_movies))
            
            n_swipes = len(st.session_state.swipe_history)
            
            letterboxd_ratings = {}
            if st.session_state.letterboxd_data:
                for m in st.session_state.letterboxd_data:
                    if m.get('movie_id') and m.get('letterboxd_rating'):
                        letterboxd_ratings[m['movie_id']] = m['letterboxd_rating']
            
            recommendations = model.recommend_for_user(
                user_id=st.session_state.user_id,
                liked_movie_ids=liked_movie_ids,
                n=10,
                exclude_ids=exclude_ids,
                n_swipes=n_swipes,
                letterboxd_data=letterboxd_ratings
            )
            
            if not recommendations:
                st.warning("No recommendations available. Try liking more movies!")
                return
            
            if ensure_db_connection():
                movie_ids = [r['movie_id'] for r in recommendations]
                
                movie_details = {}
                for movie_id in movie_ids:
                    movie = postgres_db.get_movie(movie_id=movie_id)
                    if movie:
                        movie_details[movie_id] = movie
                
                st.success(f"🎯 Found {len(recommendations)} movies we think you'll love!")
                st.divider()
                
                for i, rec in enumerate(recommendations, 1):
                    movie_id = rec['movie_id']
                    movie = movie_details.get(movie_id, {})
                    
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            title = movie.get('title', f'Movie {movie_id}')
                            year = movie.get('release_year', 'N/A')
                            genres = movie.get('genres', [])
                            overview = movie.get('overview', '')
                            
                            st.markdown(f"### {i}. {title} ({year})")
                            if genres:
                                genre_tags = ' '.join([f'`{g}`' for g in genres[:3]])
                                st.markdown(genre_tags)
                            if overview:
                                st.caption(overview[:150] + '...' if len(overview) > 150 else overview)
                            st.caption(f"💡 {rec.get('explanation', 'Recommended for you')}")
                        with col2:
                            score = rec.get('score', 0)
                            st.metric("Match", f"{score*100:.0f}%")
                        st.divider()
                
                try:
                    postgres_db.save_recommendations(
                        user_id=st.session_state.user_id,
                        recommendations=recommendations
                    )
                except Exception as e:
                    pass
            else:
                st.warning("⚠️ Could not load movie details from database")
                
    except (FileNotFoundError, Exception) as e:
        try:
            from src.models.content_based import ContentBasedRecommender
            import json
            
            model_path = Path(__file__).parent.parent / 'models' / 'saved' / 'content_based_model.pkl'
            json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
            
            if model_path.exists() and json_path.exists():
                model = ContentBasedRecommender()
                model.load('content_based_model.pkl')
                
                with open(json_path, 'r') as f:
                    all_movies = {m['movie_id']: m for m in json.load(f)}
                
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
                
        except Exception as e2:
            st.error(f"Error loading recommendations: {e2}")
            st.info("Showing sample recommendations...")
            sample_recs = [
                {'title': 'Inception', 'year': 2010, 'score': 0.95, 'reason': 'Mind-bending thriller'},
                {'title': 'The Matrix', 'year': 1999, 'score': 0.92, 'reason': 'Sci-Fi classic'},
                {'title': 'Interstellar', 'year': 2014, 'score': 0.89, 'reason': 'Epic space adventure'},
            ]
            for i, rec in enumerate(sample_recs, 1):
                st.markdown(f"**{i}. {rec['title']}** ({rec['year']}) - {rec['reason']}")


def show_analytics_dashboard():
    st.markdown('<h1 class="main-header">📊 Your Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Insights from your movie preferences</p>', unsafe_allow_html=True)
    
    likes = len(st.session_state.liked_movies)
    dislikes = len(st.session_state.disliked_movies)
    manual_swipes = len(st.session_state.swipe_history)
    
    total_movies_rated = likes + dislikes
    
    like_rate = (likes / max(total_movies_rated, 1)) * 100
    
    letterboxd_count = len(st.session_state.letterboxd_data) if st.session_state.letterboxd_data else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if letterboxd_count > 0:
            st.metric("Total Rated", total_movies_rated, 
                     delta=f"+{letterboxd_count} from Letterboxd",
                     delta_color="normal")
        else:
            st.metric("Total Swiped", total_movies_rated)
    with col2:
        st.metric("Movies Liked 👍", likes)
    with col3:
        st.metric("Movies Passed 👎", dislikes)
    with col4:
        st.metric("Like Rate", f"{like_rate:.1f}%")
    
    st.divider()
    
    if total_movies_rated == 0:
        st.info("👆 Start swiping or import from Letterboxd to see your analytics!")
        return
    
    import json
    all_movies = {}
    
    json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                all_movies = {m['movie_id']: m for m in json.load(f)}
        except:
            pass
    
    if not all_movies:
        try:
            if ensure_db_connection():
                for movie_id in st.session_state.liked_movies + st.session_state.disliked_movies:
                    movie = postgres_db.get_movie(movie_id=movie_id)
                    if movie:
                        all_movies[movie_id] = movie
        except:
            pass
    
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
        if total_movies_rated > 0:
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
    
    st.subheader("📋 Your Swipe History")
    history_data = []
    for swipe in st.session_state.swipe_history[-20:]:
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
    
    if st.session_state.letterboxd_data:
        st.divider()
        st.subheader("📥 Your Letterboxd Import")
        
        lb_data = st.session_state.letterboxd_data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Imported Movies", len(lb_data))
        with col2:
            matched = len([m for m in lb_data if m.get('matched')])
            st.metric("Matched to DB", matched)
        with col3:
            avg_rating = sum(m.get('letterboxd_rating', 0) or 0 for m in lb_data) / max(len(lb_data), 1)
            st.metric("Avg Rating", f"{avg_rating:.1f}★")


def show_my_movies():
    st.markdown('<h1 class="main-header">📋 My Movies</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your movie history and preferences</p>', unsafe_allow_html=True)
    
    liked_movies = st.session_state.liked_movies
    disliked_movies = st.session_state.disliked_movies
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👍 Liked", len(liked_movies))
    with col2:
        st.metric("👎 Passed", len(disliked_movies))
    with col3:
        total = len(liked_movies) + len(disliked_movies)
        st.metric("📊 Total", total)
    
    st.divider()
    
    if total == 0:
        st.info("👆 Start swiping or import from Letterboxd to see your movies here!")
        return
    
    try:
        import json
        json_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_movies.json'
        
        all_movies = {}
        if json_path.exists():
            with open(json_path, 'r') as f:
                all_movies = {m['movie_id']: m for m in json.load(f)}
        
        tab1, tab2 = st.tabs(["👍 Liked Movies", "👎 Passed Movies"])
        
        with tab1:
            if liked_movies:
                st.subheader(f"Movies You Loved ({len(liked_movies)})")
                
                for i, movie_id in enumerate(liked_movies):
                    movie = all_movies.get(movie_id, {})
                    if movie:
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                title = movie.get('title', f'Movie {movie_id}')
                                year = movie.get('release_year', 'N/A')
                                genres = movie.get('genres', [])
                                rating = movie.get('vote_average', 0)
                                
                                st.markdown(f"### {title} ({year})")
                                if genres:
                                    st.caption(f"🎭 {', '.join(genres[:3])} • ⭐ {rating}/10")
                            
                            with col2:
                                import requests
                                trailer_btn_url = None
                                try:
                                    resp = requests.get(
                                        f"https://api.themoviedb.org/3/movie/{movie_id}/videos",
                                        params={'api_key': 'fbcab977af26578c4a273d037a4f2655'},
                                        timeout=3
                                    )
                                    if resp.status_code == 200:
                                        for v in resp.json().get('results', []):
                                            if v.get('site') == 'YouTube' and v.get('type') in ['Trailer', 'Teaser']:
                                                trailer_btn_url = f"https://www.youtube.com/watch?v={v['key']}"
                                                break
                                except:
                                    pass
                                
                                if trailer_btn_url:
                                    st.link_button("🎬 Trailer", trailer_btn_url)
                            
                            with col3:
                                st.markdown("👍")
                            
                            overview = movie.get('overview', '')
                            if overview:
                                with st.expander("📖 Overview"):
                                    st.write(overview)
                            
                            st.divider()
            else:
                st.info("No liked movies yet. Start swiping! 👆")
        
        with tab2:
            if disliked_movies:
                st.subheader(f"Movies You Passed ({len(disliked_movies)})")
                
                for i, movie_id in enumerate(disliked_movies):
                    movie = all_movies.get(movie_id, {})
                    if movie:
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                title = movie.get('title', f'Movie {movie_id}')
                                year = movie.get('release_year', 'N/A')
                                genres = movie.get('genres', [])
                                
                                st.markdown(f"**{title}** ({year})")
                                if genres:
                                    st.caption(f"🎭 {', '.join(genres[:3])}")
                            
                            with col2:
                                st.markdown("👎")
                            
                            st.divider()
            else:
                st.info("No passed movies yet.")
        
        if st.session_state.letterboxd_data:
            st.divider()
            st.subheader("📥 Imported from Letterboxd")
            
            lb_data = st.session_state.letterboxd_data
            matched = [m for m in lb_data if m.get('matched')]
            unmatched = [m for m in lb_data if not m.get('matched')]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Matched", len(matched))
            with col2:
                st.metric("Unmatched", len(unmatched))
            
            with st.expander(f"📋 View All Imported ({len(lb_data)} movies)"):
                import_data = []
                for m in lb_data[:50]:
                    rating = m.get('letterboxd_rating', 'N/A')
                    status = '👍' if m.get('liked') else '👎'
                    matched_status = '✅' if m.get('matched') else '❌'
                    import_data.append({
                        'Movie': m.get('title', 'Unknown'),
                        'Rating': f"{rating}★" if rating != 'N/A' else 'N/A',
                        'Verdict': status,
                        'Matched': matched_status
                    })
                
                st.dataframe(pd.DataFrame(import_data), use_container_width=True, hide_index=True)
                
                if len(lb_data) > 50:
                    st.caption(f"Showing 50 of {len(lb_data)} imported movies")
    
    except Exception as e:
        st.error(f"Error loading movies: {e}")


def main():
    init_session_state()
    
    if st.session_state.user is None:
        show_landing_page()
    elif st.session_state.import_method == 'letterboxd' and not st.session_state.letterboxd_profile_viewed:
        show_letterboxd_profile()
    elif not st.session_state.onboarding_complete:
        show_onboarding()
    else:
        page = st.sidebar.radio(
            "Navigate",
            ["🎬 Swipe", "✨ Recommendations", "📋 My Movies", "📊 Analytics"],
            label_visibility="collapsed"
        )
        
        if page == "🎬 Swipe":
            show_swipe_interface()
        elif page == "✨ Recommendations":
            show_recommendations()
        elif page == "📋 My Movies":
            show_my_movies()
        elif page == "📊 Analytics":
            show_analytics_dashboard()
    
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666;">CineSwipe | CS210 Data Management | Anish Shah & Arnav Venkata</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
