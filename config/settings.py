"""
CineSwipe Configuration Settings
Update these values with your actual database credentials
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
MODELS_PATH = PROJECT_ROOT / "models" / "saved"

# Create directories if they don't exist
DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
MODELS_PATH.mkdir(parents=True, exist_ok=True)

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "cineswipe"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

# PostgreSQL connection string
POSTGRES_URI = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

# MongoDB Configuration  
MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST", "localhost"),
    "port": int(os.getenv("MONGO_PORT", "27017")),
    "database": os.getenv("MONGO_DB", "cineswipe_db")
}

# MongoDB connection string (for local or Atlas)
MONGO_URI = os.getenv(
    "MONGO_URI", 
    f"mongodb://{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"
)

# TMDB API (optional - for fetching poster images)
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Application Settings
APP_CONFIG = {
    "name": "CineSwipe",
    "version": "1.0.0",
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "movies_per_session": 20,       # How many movies to show per swipe session
    "min_swipes_for_recommendations": 10,  # Minimum swipes before personalized recs
}

# ML Model Settings
MODEL_CONFIG = {
    "content_based": {
        "n_features": 5000,         # TF-IDF features for overview text
        "n_recommendations": 20,
    },
    "collaborative": {
        "n_factors": 50,            # Matrix factorization factors
        "n_iterations": 20,
        "regularization": 0.1,
    },
    "hybrid": {
        "content_weight": 0.4,      # Weight for content-based
        "collaborative_weight": 0.6, # Weight for collaborative
    },
    "random_state": 42,
    "test_size": 0.2,
}

# Genre categories for onboarding
GENRE_OPTIONS = [
    "Action", "Adventure", "Animation", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "History",
    "Horror", "Music", "Mystery", "Romance", "Science Fiction",
    "Thriller", "War", "Western"
]

# Mood options for onboarding
MOOD_OPTIONS = [
    ("feel_good", "Feel-Good & Light", "🌈"),
    ("thrilling", "Thrilling & Exciting", "⚡"),
    ("thought_provoking", "Thought-Provoking", "🧠"),
    ("romantic", "Romantic", "❤️"),
    ("scary", "Scary & Intense", "😱"),
    ("funny", "Funny & Comedic", "😂"),
    ("inspiring", "Inspiring & Motivational", "✨"),
    ("nostalgic", "Classic & Nostalgic", "📽️"),
]

# Age group options
AGE_GROUPS = [
    "Under 18",
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55+",
]

# Decade options for movie preferences
DECADE_OPTIONS = [
    ("2020s", "2020s - Latest"),
    ("2010s", "2010s"),
    ("2000s", "2000s"),
    ("1990s", "1990s"),
    ("1980s", "1980s"),
    ("classic", "Classic (Before 1980)"),
    ("any", "Any Era"),
]

