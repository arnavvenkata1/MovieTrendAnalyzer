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
4. **Recommends movies** using a hybrid ML approach (content-based + collaborative filtering)
5. **Provides analytics** on user engagement, movie popularity, and recommendation performance

---

## ✨ Key Features

### 🎭 User Experience
- **Interactive Onboarding** - Quick preference questionnaire to personalize experience
- **Tinder-Style Swipe Interface** - Intuitive swipe gestures for movie discovery
- **Personalized Recommendations** - ML-powered suggestions based on your preferences and behavior
- **Real-Time Learning** - System learns from every swipe to improve recommendations

### 🤖 Machine Learning
- **Content-Based Filtering** - Uses TF-IDF on genres, keywords, and overviews
- **Collaborative Filtering** - K-Nearest Neighbors on user swipe patterns
- **Hybrid Model** - Combines both approaches with dynamic weighting
  - New users: Higher content weight (cold start problem solved)
  - Active users: Higher collaborative weight (better personalization)

### 📊 Analytics Dashboard
- **Platform Overview** - Total users, movies, swipes, and engagement metrics
- **Movie Analytics** - Top rated movies, genre distribution, decade analysis
- **User Analytics** - Engagement levels, preferences, most active users
- **Recommendation Analytics** - Algorithm performance, hit rates, top recommendations
- **Interactive Visualizations** - Plotly charts for data exploration

### 🗄️ Database Architecture
- **PostgreSQL** - Structured data (users, movies, swipes, recommendations)
- **MongoDB** - Flexible data (sessions, events, raw data lake)
- **Data Pipeline** - Automated cleaning and transformation

### 🔧 Data Processing
- **Data Cleaning Module** (`changing_data/`) - Robust data cleaning and validation
- **Data Transformation** - Feature engineering, categorization, derived metrics
- **Quality Assurance** - Missing value handling, duplicate removal, validation

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
| **Data Processing** | Pandas, NumPy |

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
│   ├── analytics_queries.sql    # Pre-built analytics queries
│   └── mongo_schema.md          # MongoDB collection docs
│
├── changing_data/               # Data cleaning & transformation
│   ├── data_cleaner.py         # Data cleaning operations
│   ├── data_transformer.py     # Data transformation pipeline
│   └── README.md               # Module documentation
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
├── scripts/
│   ├── download_kaggle_data.py  # Automated dataset download
│   └── train_models.py          # ML model training script
│
├── data/
│   ├── raw/                     # Kaggle CSV files
│   └── processed/               # Transformed data
│
├── models/
│   └── saved/                   # Trained ML models
│
└── docs/                        # Documentation
    ├── ANISH_SETUP_GUIDE.md     # Detailed setup instructions
    ├── SETUP_DOCUMENTATION.md   # Setup process documentation
    ├── APP_INTEGRATION_COMPLETE.md
    ├── DATA_CLEANING_TRANSFORMATION.md
    └── NEXT_STEPS_PLAN.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (local installation)
- MongoDB (local installation)
- Git

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
This automatically downloads the TMDB movie dataset from Kaggle.

### 4. Set Up Databases

**📖 For detailed setup instructions, see:** `docs/ANISH_SETUP_GUIDE.md`

**Quick PostgreSQL Setup:**
```bash
createdb cineswipe
psql -d cineswipe -f database/postgres_schema.sql
```

**Quick MongoDB Setup:**
```bash
# macOS (using Homebrew)
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

### 5. Configure Database Connection

Update `config/settings.py` with your database credentials:
```python
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "cineswipe",
    "user": "your_username",
    "password": ""
}
```

### 6. Load Data
```bash
python3 src/data_loader.py
```
This will:
- Clean and transform the raw data
- Load 4,800+ movies into PostgreSQL
- Store raw data in MongoDB

### 7. Train ML Models
```bash
python3 scripts/train_models.py
```
This trains the content-based and hybrid recommendation models.

### 8. Launch the App
```bash
streamlit run app/main.py
```

Open your browser to `http://localhost:8501` and start swiping! 🎬

---

## 🗄️ Database Architecture

### PostgreSQL (Structured Data)
- **dim_users** - User profiles and statistics
- **dim_movies** - Movie metadata from TMDB (4,800+ movies)
- **user_preferences** - Onboarding responses
- **fact_swipes** - Swipe history and interactions
- **fact_recommendations** - ML recommendations and performance
- **model_metrics** - Model performance tracking

**Pre-built Views:**
- `vw_user_engagement` - User activity metrics
- `vw_movie_popularity` - Movie approval rates
- `vw_genre_preferences` - Genre-based analytics
- `vw_algorithm_performance` - ML model performance

### MongoDB (Flexible Data)
- **user_sessions** - Detailed event tracking
- **recommendation_explanations** - Why movies were recommended
- **model_versions** - ML model metadata
- **raw_kaggle_data** - Data lake (original Kaggle data)

---

## 🤖 ML Models

### 1. Content-Based Filtering
- **Method:** TF-IDF vectorization on movie features
- **Features Used:** Genres, keywords, overview text
- **Use Case:** Cold start problem (new users, new movies)
- **Output:** Cosine similarity scores (0-1)

### 2. Collaborative Filtering  
- **Method:** K-Nearest Neighbors on user-item interactions
- **Features Used:** User swipe patterns
- **Use Case:** Active users with sufficient interaction history
- **Output:** Predicted preference scores

### 3. Hybrid Model
- **Approach:** Weighted combination of content-based + collaborative
- **Dynamic Weights:**
  - New users (< 5 swipes): 90% content, 10% collaborative
  - Moderate users (5-20 swipes): 60% content, 40% collaborative
  - Active users (20+ swipes): 40% content, 60% collaborative
- **Score Normalization:** Optimized to 65-95% match range for better UX
- **Output:** Normalized recommendation scores with explanations

---

## 📊 Analytics Dashboard

The analytics dashboard provides comprehensive insights across 4 tabs:

### 📈 Overview Tab
- Platform metrics (users, movies, swipes, like rate)
- Daily swipe activity trends
- Engagement overview

### 🎬 Movies Tab
- Top rated movies
- Genre distribution and popularity
- Movies by decade analysis
- Rating trends

### 👥 Users Tab
- User engagement levels (retention metrics)
- Genre preferences distribution
- Most active users leaderboard
- User behavior patterns

### 🤖 Recommendations Tab
- Algorithm performance comparison
- Recommendation hit rates
- Most recommended movies
- Success rate analysis

All visualizations are interactive using Plotly!

---

## 🔧 Data Processing Pipeline

### Data Cleaning (`changing_data/data_cleaner.py`)
- JSON parsing (handles malformed data)
- Missing value handling
- Duplicate removal
- Data validation
- Text/numeric/datetime normalization

### Data Transformation (`changing_data/data_transformer.py`)
- Feature extraction (genres, keywords, dates)
- Derived metrics (profit, ROI)
- Categorization (ratings, budget, runtime)
- Database preparation (PostgreSQL & MongoDB)

**Quality Improvements:**
- Removed invalid records
- Validated 4,799 movies
- Proper data type conversion
- Missing value strategies

---

## 📊 Key Metrics

| Metric | Description |
|--------|-------------|
| **Precision@K** | % of recommendations that were liked |
| **Hit Rate** | % of users who liked at least one rec |
| **Coverage** | % of movies that get recommended |
| **Diversity** | Genre diversity in recommendations |
| **Match Percentage** | Normalized recommendation confidence (65-95%) |

---

## 🎯 Project Requirements Met

✅ **Database Setup**
- PostgreSQL with 6 tables and 4 views
- MongoDB with flexible schema
- Full data loading pipeline

✅ **Data Cleaning & Transformation**
- Robust data cleaning module
- Feature engineering and transformation
- Quality assurance and validation

✅ **Machine Learning**
- Content-based filtering
- Collaborative filtering
- Hybrid recommendation system

✅ **Application**
- Streamlit web interface
- User onboarding and management
- Swipe interface
- Recommendations display
- Analytics dashboard

✅ **Analytics**
- User engagement metrics
- Movie popularity analysis
- Recommendation performance
- Interactive visualizations

---

## 👥 Team Contributions

### Anish Shah (dg branch)
- Database schema design and implementation
- PostgreSQL & MongoDB setup and configuration
- Data loading pipeline development
- Data cleaning and transformation modules (`changing_data/`)
- SQL analytics queries and views
- Streamlit app database integration
- Analytics dashboard development
- Comprehensive documentation

### Arnav Venkata (dev branch)
- ML recommendation models (content-based, collaborative, hybrid)
- Streamlit frontend development
- User interface design
- Model evaluation and optimization
- Model training scripts

---

## 📚 Documentation

- **`docs/ANISH_SETUP_GUIDE.md`** - Complete setup guide
- **`docs/SETUP_DOCUMENTATION.md`** - Setup process documentation
- **`docs/APP_INTEGRATION_COMPLETE.md`** - App integration details
- **`docs/DATA_CLEANING_TRANSFORMATION.md`** - Data processing documentation
- **`docs/NEXT_STEPS_PLAN.md`** - Future enhancements
- **`changing_data/README.md`** - Data processing module docs

---

## 🚧 Future Enhancements

- [ ] Movie poster display improvements
- [ ] Search and filter functionality
- [ ] User profile pages
- [ ] Social features (follow users, share recommendations)
- [ ] Advanced ML models (deep learning, matrix factorization)
- [ ] Real-time recommendation updates
- [ ] A/B testing framework

---

## 📄 License

This project is for educational purposes (CS210 Data Management Final Project at Duke University).

---

## 🙏 Acknowledgments

- **TMDB** for the movie dataset
- **Kaggle** for data hosting
- **CS210 course staff** for guidance and support

---

## 🤝 Contributing

This is a course project. For questions or issues, please open a GitHub issue.

---

**Last Updated:** December 9, 2024  
**Version:** 1.0.0  
**Status:** ✅ Complete and Fully Functional
