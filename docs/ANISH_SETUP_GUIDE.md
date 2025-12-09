# 📋 ANISH'S COMPLETE SETUP & TASK GUIDE

## CineSwipe - Movie Recommendation System
**CS210 Data Management Final Project**

---

## 🎯 PROJECT OVERVIEW

We're building **CineSwipe** - a Tinder-style movie recommendation app where users:
1. Complete an onboarding questionnaire (favorite genres, mood, etc.)
2. Swipe left/right on movie cards
3. Get personalized AI recommendations based on their swipes

**Your Role:** Database & Backend (PostgreSQL + MongoDB setup, data loading, SQL queries)  
**Arnav's Role:** ML Models & Frontend (Streamlit app, recommendation algorithms)

---

## 🏗️ WHAT'S ALREADY BUILT

| Component | Status | Your Involvement |
|-----------|--------|------------------|
| Project Structure | ✅ Done | Just review |
| PostgreSQL Schema | ✅ Written | **You deploy it** |
| MongoDB Schema | ✅ Documented | **You deploy it** |
| Database Utilities | ✅ Done | You may modify |
| Data Loader Script | ✅ Done | **You run it** |
| ML Models | ✅ Done | Arnav handles |
| Streamlit App | ✅ Done | Arnav handles |

---

## 📁 PROJECT STRUCTURE

```
MovieTrendAnalyzer/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
│
├── config/
│   └── settings.py              # ⭐ Database connection settings (UPDATE THIS)
│
├── database/
│   ├── postgres_schema.sql      # ⭐ PostgreSQL tables (YOU RUN THIS)
│   └── mongo_schema.md          # MongoDB collection documentation
│
├── src/
│   ├── data_loader.py           # ⭐ Loads Kaggle CSVs into databases (YOU RUN THIS)
│   ├── utils/
│   │   ├── db_postgres.py       # PostgreSQL operations
│   │   └── db_mongo.py          # MongoDB operations
│   └── models/                  # ML recommendation models (Arnav's domain)
│
├── app/
│   └── main.py                  # Streamlit frontend (Arnav's domain)
│
└── data/
    ├── raw/                     # ⭐ PUT KAGGLE CSVs HERE
    └── processed/               # Transformed data output
```

---

## 🚀 STEP-BY-STEP SETUP INSTRUCTIONS

### Step 1: Clone the Repository

```bash
git clone https://github.com/arnavvenkata1/MovieTrendAnalyzer.git
cd MovieTrendAnalyzer
```

### Step 2: Switch to Your Branch

```bash
git checkout dg
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download Kaggle Datasets

**Option A - Automated (Recommended):**
```bash
python3 scripts/download_kaggle_data.py
```

**Option B - Manual:**
1. Go to: https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata
2. Download the dataset (you'll get a zip file)
3. Extract and copy these files to `data/raw/`:
   - `tmdb_5000_movies.csv`
   - `tmdb_5000_credits.csv`

### Step 5: Install PostgreSQL

**Mac (using Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Verify it's running:**
```bash
psql --version
```

### Step 6: Create the Database

```bash
createdb cineswipe
```

### Step 7: Run the PostgreSQL Schema

```bash
psql -d cineswipe -f database/postgres_schema.sql
```

**Verify tables were created:**
```bash
psql -d cineswipe -c "\dt"
```

You should see:
```
              List of relations
 Schema |        Name         | Type  
--------+---------------------+-------
 public | dim_movies          | table
 public | dim_users           | table
 public | fact_recommendations| table
 public | fact_swipes         | table
 public | model_metrics       | table
 public | user_preferences    | table
```

### Step 8: Install MongoDB

**Option A - Local MongoDB (Mac):**
See detailed instructions in: `docs/MONGODB_SETUP_INSTRUCTIONS.md`

Quick version:
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

**Option B - MongoDB Atlas (Cloud - Easier):**
1. Go to: https://www.mongodb.com/atlas
2. Create free account
3. Create a free cluster
4. Get your connection string
5. Update `config/settings.py` with your connection string

### Step 9: Update Database Credentials

Edit `config/settings.py`:

```python
# PostgreSQL Configuration
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "cineswipe",
    "user": "YOUR_MAC_USERNAME",  # Usually your Mac username
    "password": ""                 # Usually empty for local
}

# MongoDB Configuration (if using Atlas)
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

### Step 10: Load Data into Databases

```bash
python src/data_loader.py
```

You should see output like:
```
============================================================
CINESWIPE - DATA LOADER
============================================================

[1] Loading CSV files...
  ✓ Loaded 4803 movies from tmdb_5000_movies.csv

[2] Transforming movie data...
  ✓ Transformed 4803 movies

[3] Loading data into PostgreSQL...
  ✓ Connected to PostgreSQL: cineswipe
  ✓ Loaded 4803 movies into PostgreSQL

[4] Loading raw data into MongoDB...
  ✓ Connected to MongoDB: cineswipe_db
  ✓ Stored 4803 raw records in MongoDB

============================================================
DATA LOADING COMPLETE
============================================================
```

---

## 📝 YOUR TASKS (What You Need to Create/Do)

**✅ ALL TASKS COMPLETED! See `docs/SETUP_DOCUMENTATION.md` for details.**

### Task 1: Verify Database Setup ✅ COMPLETED
After running the steps above, verify everything works:

```bash
# Check PostgreSQL has data
psql -d cineswipe -c "SELECT COUNT(*) FROM dim_movies;"
# Should return: 4803

# Check a sample movie
psql -d cineswipe -c "SELECT title, genres, vote_average FROM dim_movies LIMIT 5;"
```

### Task 2: Create Analytics Queries 📊 ✅ COMPLETED

Created file: `database/analytics_queries.sql`

Write these SQL queries:

```sql
-- ============================================================
-- CineSwipe Analytics Queries
-- Author: Anish Shah
-- ============================================================

-- 1. Top 10 Highest Rated Movies
SELECT title, vote_average, release_year, genres
FROM dim_movies
WHERE vote_count > 100
ORDER BY vote_average DESC
LIMIT 10;

-- 2. Movies by Genre Count
SELECT 
    UNNEST(genres) as genre,
    COUNT(*) as movie_count,
    ROUND(AVG(vote_average)::numeric, 2) as avg_rating
FROM dim_movies
GROUP BY UNNEST(genres)
ORDER BY movie_count DESC;

-- 3. Movies by Decade
SELECT 
    (release_year / 10) * 10 as decade,
    COUNT(*) as movie_count,
    ROUND(AVG(vote_average)::numeric, 2) as avg_rating
FROM dim_movies
WHERE release_year IS NOT NULL
GROUP BY (release_year / 10) * 10
ORDER BY decade DESC;

-- 4. Most Popular Movies (by popularity score)
SELECT title, popularity, vote_average, release_year
FROM dim_movies
ORDER BY popularity DESC
LIMIT 10;

-- 5. User Engagement Summary (after users start swiping)
SELECT * FROM vw_user_engagement;

-- 6. Movie Approval Rates (after swipes exist)
SELECT * FROM vw_movie_popularity
WHERE total_swipes > 0
LIMIT 20;

-- 7. Genre Preferences by User
SELECT * FROM vw_genre_preferences
ORDER BY user_id, likes DESC;

-- 8. Algorithm Performance Comparison
SELECT * FROM vw_algorithm_performance;

-- 9. Daily Swipe Activity
SELECT 
    DATE(swipe_timestamp) as date,
    COUNT(*) as total_swipes,
    SUM(CASE WHEN swipe_direction = 'right' THEN 1 ELSE 0 END) as likes,
    SUM(CASE WHEN swipe_direction = 'left' THEN 1 ELSE 0 END) as passes
FROM fact_swipes
GROUP BY DATE(swipe_timestamp)
ORDER BY date DESC;

-- 10. User Retention (users who swiped more than once)
SELECT 
    COUNT(DISTINCT user_id) as total_users,
    COUNT(DISTINCT CASE WHEN total_swipes > 10 THEN user_id END) as engaged_users,
    COUNT(DISTINCT CASE WHEN total_swipes > 50 THEN user_id END) as power_users
FROM dim_users;
```

### Task 3: Test Database Operations 🧪 ✅ COMPLETED

Created test script: `tests/test_database.py` (all tests passing)

```python
"""
Database Connection Tests
Author: Anish Shah
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.db_postgres import db as postgres_db
from src.utils.db_mongo import mongo_db

def test_postgres_connection():
    """Test PostgreSQL connection and queries"""
    print("Testing PostgreSQL...")
    
    if postgres_db.connect():
        # Test query
        movies = postgres_db.execute_query(
            "SELECT title, vote_average FROM dim_movies LIMIT 5"
        )
        print(f"✓ Found {len(movies)} movies")
        for m in movies:
            print(f"  - {m['title']}: {m['vote_average']}")
        
        # Test movie count
        count = postgres_db.get_total_movies()
        print(f"✓ Total movies in database: {count}")
        
        postgres_db.disconnect()
        return True
    return False

def test_mongo_connection():
    """Test MongoDB connection"""
    print("\nTesting MongoDB...")
    
    if mongo_db.connect():
        # Test collection access
        collection = mongo_db.get_collection('raw_kaggle_data')
        count = collection.count_documents({})
        print(f"✓ Found {count} raw records in MongoDB")
        
        mongo_db.disconnect()
        return True
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE CONNECTION TESTS")
    print("=" * 50)
    
    pg_ok = test_postgres_connection()
    mongo_ok = test_mongo_connection()
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"PostgreSQL: {'✅ PASS' if pg_ok else '❌ FAIL'}")
    print(f"MongoDB: {'✅ PASS' if mongo_ok else '❌ FAIL'}")
```

Run it:
```bash
python tests/test_database.py
```

### Task 4: Document Your Setup 📄 ✅ COMPLETED

Created comprehensive documentation: `docs/SETUP_DOCUMENTATION.md`

Includes:
- ✅ PostgreSQL setup process
- ✅ MongoDB setup process
- ✅ All issues encountered and solutions
- ✅ Verification results
- ✅ Quick reference commands

### Task 5: Commit and Push Your Work 🚀

```bash
git add .
git commit -m "Database setup: PostgreSQL + MongoDB with analytics queries"
git push origin dg
```

---

## 🗄️ DATABASE SCHEMA REFERENCE

### PostgreSQL Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `dim_users` | User profiles | user_id, username, total_swipes |
| `dim_movies` | Movie data (4,803 films) | movie_id, title, genres, vote_average |
| `user_preferences` | Onboarding answers | preferred_genres, mood_preference |
| `fact_swipes` | Swipe history | user_id, movie_id, swipe_direction |
| `fact_recommendations` | ML recommendations | user_id, movie_id, score, algorithm |
| `model_metrics` | Model performance | precision, recall, hit_rate |

### Pre-built Views

| View | What It Shows |
|------|---------------|
| `vw_user_engagement` | User stats (swipes, like rate) |
| `vw_movie_popularity` | Movie approval rates |
| `vw_genre_preferences` | Which genres each user likes |
| `vw_algorithm_performance` | Which ML model performs best |

---

## ❓ TROUBLESHOOTING

### PostgreSQL won't start
```bash
brew services restart postgresql@15
```

### "database cineswipe does not exist"
```bash
createdb cineswipe
```

### "permission denied"
```bash
# Check your Mac username
whoami

# Use that in psql
psql -U your_username -d cineswipe
```

### MongoDB connection failed
- Make sure MongoDB is running: `brew services list`
- Or use MongoDB Atlas (cloud) instead

### Python import errors
```bash
pip install -r requirements.txt
```

---

## 📞 CONTACT

If you're stuck, message Arnav. We can debug together!

**GitHub Repo:** https://github.com/arnavvenkata1/MovieTrendAnalyzer

---

## 🔧 Quick Reference Commands

```bash
# Start PostgreSQL
brew services start postgresql@15

# Start MongoDB  
brew services start mongodb-community

# Connect to database
psql -d cineswipe

# Run data loader
python src/data_loader.py

# Run the app (after setup)
streamlit run app/main.py

# Push your changes
git add . && git commit -m "Your message" && git push origin dg
```

---

**Good luck! 🚀**

