import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
MODELS_PATH = PROJECT_ROOT / "models" / "saved"

DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
MODELS_PATH.mkdir(parents=True, exist_ok=True)

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "cineswipe"),
    "user": os.getenv("POSTGRES_USER", "anish"),
    "password": os.getenv("POSTGRES_PASSWORD", "")
}

POSTGRES_URI = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST", "localhost"),
    "port": int(os.getenv("MONGO_PORT", "27017")),
    "database": os.getenv("MONGO_DB", "cineswipe_db")
}

MONGO_URI = os.getenv(
    "MONGO_URI", 
    f"mongodb://{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"
)

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

APP_CONFIG = {
    "name": "CineSwipe",
    "version": "1.0.0",
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "movies_per_session": 20,
    "min_swipes_for_recommendations": 10,
}

MODEL_CONFIG = {
    "content_based": {
        "n_features": 5000,
        "n_recommendations": 20,
    },
    "collaborative": {
        "n_factors": 50,
        "n_iterations": 20,
        "regularization": 0.1,
    },
    "hybrid": {
        "content_weight": 0.4,
        "collaborative_weight": 0.6,
    },
    "random_state": 42,
    "test_size": 0.2,
}

GENRE_OPTIONS = [
    "Action", "Adventure", "Animation", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "History",
    "Horror", "Music", "Mystery", "Romance", "Science Fiction",
    "Thriller", "War", "Western"
]

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

AGE_GROUPS = [
    "Under 18",
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55+",
]

DECADE_OPTIONS = [
    ("2020s", "2020s - Latest"),
    ("2010s", "2010s"),
    ("2000s", "2000s"),
    ("1990s", "1990s"),
    ("1980s", "1980s"),
    ("classic", "Classic (Before 1980)"),
    ("any", "Any Era"),
]
