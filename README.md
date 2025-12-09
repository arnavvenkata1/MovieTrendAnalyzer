# 🎬 CineSwipe - Movie Recommendation System

**CS210 Data Management Final Project**  
**Authors:** Anish Shah & Arnav Venkata

A Tinder-style movie recommendation app that learns your preferences through swipes and provides personalized movie suggestions using hybrid machine learning.

---

## 🎯 Project Overview

CineSwipe is a full-stack movie recommendation system that:
1. **Onboards users** with preference questions (genres, mood, era)
2. **Shows movie cards** to swipe left (👎) or right (👍)
3. **Learns in real-time** from your swipes
4. **Recommends movies** using a hybrid ML approach

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎭 **Onboarding** | Quick preference questionnaire |
| 👆 **Swipe Interface** | Tinder-style movie discovery |
| 🤖 **Hybrid ML** | Content-based + Collaborative filtering |
| 📊 **Analytics** | Track your viewing patterns |
| 🗄️ **Hybrid Database** | PostgreSQL + MongoDB architecture |

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.10+ |
| **SQL Database** | PostgreSQL |
| **NoSQL Database** | MongoDB |
| **ML Framework** | Scikit-learn |
| **NLP** | TF-IDF Vectorization |
| **Frontend** | Streamlit |
| **Visualization** | Plotly |

---

## 📁 Project Structure

```
CineSwipe/
├── README.md
├── requirements.txt
├── .gitignore
│
├── config/
│   └── settings.py              # Configuration settings
│
├── database/
│   ├── postgres_schema.sql      # PostgreSQL tables & views
│   └── mongo_schema.md          # MongoDB collection docs
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py           # Load Kaggle CSVs → DBs
│   │
│   ├── models/
│   │   ├── content_based.py     # TF-IDF similarity model
│   │   ├── collaborative.py     # User-user KNN model
│   │   └── hybrid.py            # Combined recommendation
│   │
│   └── utils/
│       ├── db_postgres.py       # PostgreSQL operations
│       └── db_mongo.py          # MongoDB operations
│
├── app/
│   └── main.py                  # Streamlit application
│
├── data/
│   ├── raw/                     # Kaggle CSV files
│   └── processed/               # Transformed data
│
└── models/
    └── saved/                   # Trained ML models
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/arnavvenkata1/MovieTrendAnalyzer.git
cd MovieTrendAnalyzer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download Data
```bash
python3 scripts/download_kaggle_data.py
```

### 4. Set Up Databases
**📖 For detailed setup instructions, see:** `docs/ANISH_SETUP_GUIDE.md`

Quick setup:
```bash
# PostgreSQL
createdb cineswipe
psql -d cineswipe -f database/postgres_schema.sql

# MongoDB (see docs/MONGODB_SETUP_INSTRUCTIONS.md for details)
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

### 5. Load Data
```bash
python3 src/data_loader.py
```

### 6. Launch the App
```bash
streamlit run app/main.py
```

---

## 🗄️ Database Architecture

### PostgreSQL (Structured Data)
- **dim_users** - User profiles
- **dim_movies** - Movie metadata (from TMDB)
- **user_preferences** - Onboarding responses
- **fact_swipes** - Swipe history
- **fact_recommendations** - ML recommendations
- **model_metrics** - Model performance tracking

### MongoDB (Flexible Data)
- **user_sessions** - Detailed event tracking
- **recommendation_explanations** - Why we recommended
- **model_versions** - ML model metadata
- **raw_kaggle_data** - Data lake

---

## 🤖 ML Models

### 1. Content-Based Filtering
- Uses TF-IDF on movie genres, keywords, and overviews
- Recommends movies similar to ones you liked

### 2. Collaborative Filtering  
- Uses K-Nearest Neighbors on user swipe patterns
- Recommends movies liked by similar users

### 3. Hybrid Model
- Combines both approaches with dynamic weighting
- New users: Higher content weight (cold start)
- Active users: Higher collaborative weight

---

## 📊 Key Metrics

| Metric | Description |
|--------|-------------|
| **Precision@K** | % of recommendations that were liked |
| **Hit Rate** | % of users who liked at least one rec |
| **Coverage** | % of movies that get recommended |
| **Diversity** | Genre diversity in recommendations |

---

## 👥 Team Contributions

### Anish Shah (dg branch)
- Database schema design
- PostgreSQL & MongoDB setup
- Data loading pipeline
- SQL analytics queries

### Arnav Venkata (dev branch)
- ML recommendation models
- Streamlit frontend
- User interface design
- Model evaluation

---

## 📄 License

This project is for educational purposes (CS210 Final Project at Duke University).

---

## 🙏 Acknowledgments

- TMDB for the movie dataset
- Kaggle for data hosting
- CS210 course staff
