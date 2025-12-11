# CineSwipe 🎬

A movie recommendation system with a Tinder-style swipe interface. Swipe right to like, left to pass, and get personalized movie recommendations powered by machine learning.

## Features

- **Swipe Interface**: Discover movies through intuitive swipe gestures
- **Letterboxd Import**: Import your existing ratings to skip onboarding
- **Smart Recommendations**: Hybrid ML model combining content-based and collaborative filtering
- **Trailer Integration**: Watch trailers directly from movie cards
- **Analytics Dashboard**: Track your movie preferences and swipe history
- **My Movies**: View all your liked and passed movies

## Tech Stack

- **Frontend**: Streamlit
- **Database**: PostgreSQL (structured data), MongoDB (session logs)
- **ML**: scikit-learn (TF-IDF, k-NN, cosine similarity)
- **APIs**: TMDB API (trailers, metadata)
- **Data**: Kaggle TMDB 5000 Movies Dataset

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
streamlit run app/main.py
```

The app will open at `http://localhost:8501`

### 3. Start Using

1. Choose signup method: Manual onboarding OR Letterboxd import
2. Swipe through movies (👍 Like, 👎 Pass, ⏭️ Skip)
3. Get personalized recommendations after 3+ likes
4. View analytics and your movie history

## Project Structure

```
MovieTrendAnalyzer/
├── app/
│   └── main.py              # Streamlit application
├── src/
│   ├── models/
│   │   ├── content_based.py # TF-IDF similarity model
│   │   ├── collaborative.py # User-based k-NN model
│   │   └── hybrid.py        # Combined recommendation engine
│   ├── letterboxd_import.py # Letterboxd RSS integration
│   └── tmdb_trailers.py     # TMDB API for trailers
├── config/
│   └── settings.py          # Configuration settings
├── data/
│   ├── raw/                 # Original datasets
│   └── processed/           # Cleaned data and JSON
├── models/
│   └── saved/               # Trained ML models
├── database/
│   ├── postgres_schema.sql  # PostgreSQL schema
│   └── mongo_schema.md      # MongoDB collections
└── requirements.txt
```

## Database Setup (Optional)

The app works offline using JSON data. For full database features:

**PostgreSQL**:
```bash
createdb cineswipe
psql cineswipe < database/postgres_schema.sql
```

**MongoDB**:
```bash
mongod --dbpath /data/db
```

Update credentials in `config/settings.py`.

## Train ML Models

Models are pre-trained, but to retrain:

```bash
python src/train_models_offline.py
```

## Authors

- Anish Shah
- Arnav Venkata

CS210 Data Management Project
