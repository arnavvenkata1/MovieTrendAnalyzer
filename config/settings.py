"""
Configuration settings for Movie Trend Analyzer
Update these values with your actual database credentials
"""

import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "movie_trends"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

# MongoDB Configuration
MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST", "localhost"),
    "port": int(os.getenv("MONGO_PORT", "27017")),
    "database": os.getenv("MONGO_DB", "movie_trends_raw")
}

# MongoDB Connection String (for Atlas or local)
MONGO_URI = os.getenv(
    "MONGO_URI", 
    f"mongodb://{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"
)

# Data Paths
DATA_RAW_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
DATA_PROCESSED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

# Genre Keywords for Classification
GENRE_KEYWORDS = {
    "Horror": ["horror", "scary", "terrifying", "creepy", "spooky", "slasher", "haunted", "possessed"],
    "Comedy": ["comedy", "funny", "hilarious", "laugh", "humor", "comedic", "witty"],
    "Romance": ["romance", "love", "romantic", "relationship", "heartfelt", "dating"],
    "Sci-Fi": ["sci-fi", "scifi", "space", "alien", "future", "robot", "dystopian", "science fiction"],
    "Action": ["action", "fight", "explosion", "chase", "hero", "battle", "thriller"],
    "Drama": ["drama", "emotional", "intense", "powerful", "moving"],
    "Animation": ["animated", "animation", "cartoon", "pixar", "disney"],
    "Thriller": ["thriller", "suspense", "tense", "mystery", "psychological"]
}

# Model Configuration
MODEL_CONFIG = {
    "test_size": 0.2,
    "random_state": 42
}

