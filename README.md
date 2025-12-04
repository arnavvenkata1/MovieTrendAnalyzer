# 🎬 Movie Trend Analyzer

**CS210 Data Management Final Project**  
**Authors:** Anish Shah & Arnav Venkata

A data-driven system that analyzes social media activity to identify and forecast emerging audience interests in movie genres.

---

## 📋 Project Overview

The Movie Trend Prediction System analyzes movie review data from **Letterboxd** and **Metacritic** to:
- Track engagement trends by genre over time
- Perform sentiment analysis on reviews
- Predict future genre popularity using machine learning

### Key Features
- **Hybrid Database Architecture**: PostgreSQL (structured) + MongoDB (unstructured)
- **ETL Pipeline**: Extract, Transform, Load workflow
- **Sentiment Analysis**: VADER-based NLP analysis
- **ML Models**: Regression and Classification for trend prediction
- **Interactive Dashboard**: Streamlit-based visualization

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| SQL Database | PostgreSQL |
| NoSQL Database | MongoDB |
| Data Processing | Pandas, NumPy |
| NLP | NLTK, VADER |
| Machine Learning | Scikit-learn |
| Visualization | Streamlit, Plotly |

---

## 📁 Project Structure

```
MovieTrendAnalyzer/
├── README.md
├── requirements.txt
├── config/
│   └── settings.py          # Database & app configuration
├── data/
│   ├── raw/                  # Original CSV files
│   │   ├── letterboxd-reviews.csv
│   │   ├── metacritic-reviews.csv
│   │   ├── tmdb_5000_movies.csv
│   │   └── tmdb_5000_credits.csv
│   └── processed/            # Transformed data
├── database/
│   └── schema.sql            # PostgreSQL schema
├── src/
│   ├── __init__.py
│   ├── data_loader.py        # Load CSV → Databases
│   ├── etl.py                # ETL Pipeline
│   ├── sentiment.py          # VADER sentiment analysis
│   └── models.py             # ML training & prediction
├── app/
│   └── dashboard.py          # Streamlit dashboard
└── models/                   # Saved ML models
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run ETL Pipeline
```bash
python src/etl.py
```

### 3. Train ML Models
```bash
python src/models.py
```

### 4. Launch Dashboard
```bash
streamlit run app/dashboard.py
```

---

## 📊 Database Schema

### PostgreSQL (Structured Data)
- `dim_genres`: Genre dimension table
- `dim_movies`: Movie metadata from TMDB
- `fact_reviews`: Individual review records
- `fact_daily_trends`: Aggregated daily trends
- `predictions`: ML prediction outputs

### MongoDB (Unstructured Data)
- `letterboxd_raw`: Raw Letterboxd reviews
- `metacritic_raw`: Raw Metacritic reviews
- `tmdb_movies_raw`: Raw TMDB movie data

---

## 🤖 Machine Learning Models

### Regression (Engagement Prediction)
- **Target**: Next-day engagement (likes + comments)
- **Features**: Lag values, moving averages, sentiment
- **Algorithm**: Random Forest Regressor

### Classification (Trend Direction)
- **Target**: RISING / DECLINING / STABLE
- **Features**: Same as regression
- **Algorithm**: Logistic Regression / Random Forest

---

## 📈 Evaluation Metrics

| Model | Metric | Description |
|-------|--------|-------------|
| Regression | MAE | Mean Absolute Error |
| Regression | R² | Coefficient of Determination |
| Classification | Accuracy | Correct predictions / Total |
| Classification | F1 Score | Harmonic mean of precision & recall |

---

## 🔗 Data Sources

1. **Letterboxd Reviews** - Social movie reviews with engagement metrics
2. **Metacritic Reviews** - Critic reviews with ratings
3. **TMDB 5000** - Movie metadata and genre information

---

## 📄 License

This project is for educational purposes (CS210 Final Project).
