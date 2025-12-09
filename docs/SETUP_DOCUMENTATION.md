# Setup Documentation - Anish Shah

**Date:** December 9, 2024  
**Project:** CineSwipe - Movie Recommendation System  
**CS210 Data Management Final Project**

---

## 📋 Overview

This document details the complete setup process for the CineSwipe database infrastructure, including PostgreSQL and MongoDB installation, configuration, and data loading.

---

## ✅ Completed Setup Steps

### 1. Environment Setup
- **Operating System:** macOS (darwin 24.3.0)
- **Python Version:** 3.12.5
- **Shell:** zsh

### 2. PostgreSQL Setup

#### Installation
- **Version:** PostgreSQL 14.20 (Homebrew)
- **Installation Method:** Already installed via Homebrew
- **Status:** ✅ Running as a service

#### Database Creation
```bash
createdb cineswipe
```

#### Schema Deployment
```bash
psql -d cineswipe -f database/postgres_schema.sql
```

**Tables Created:**
- `dim_users` - User profiles
- `dim_movies` - Movie metadata (4,803 movies)
- `user_preferences` - User onboarding preferences
- `fact_swipes` - Swipe history tracking
- `fact_recommendations` - ML recommendation results
- `model_metrics` - Model performance metrics

**Views Created:**
- `vw_user_engagement` - User engagement statistics
- `vw_movie_popularity` - Movie approval rates
- `vw_genre_preferences` - User genre preferences
- `vw_algorithm_performance` - ML algorithm comparison

#### Configuration
Updated `config/settings.py`:
```python
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "cineswipe",
    "user": "anish",  # Mac username
    "password": ""     # Empty for local authentication
}
```

**Connection Status:** ✅ Verified and working

---

### 3. MongoDB Setup

#### Installation Process

**Step 1: Command Line Tools Update**
- **Issue Encountered:** MongoDB 7.0 requires Xcode Command Line Tools version 16.4+
- **Current Version:** 15.3.0.0.1.1708646388
- **Solution:** Updated Command Line Tools using:
  ```bash
  sudo rm -rf /Library/Developer/CommandLineTools
  sudo xcode-select --install
  ```
- **New Version:** 16.4.0.0.1.1747106510
- **Time Required:** ~15 minutes for download and installation

**Step 2: MongoDB Installation**
- **Version:** MongoDB Community Edition 7.0.26
- **Installation Method:** Homebrew
  ```bash
  brew tap mongodb/brew
  brew install mongodb-community@7.0
  brew link mongodb-community@7.0
  ```

**Step 3: Service Startup**
```bash
brew services start mongodb-community@7.0
```

**Status:** ✅ Running and auto-starting on login

#### Configuration
Default MongoDB configuration (local):
```python
MONGO_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "cineswipe_db"
}
MONGO_URI = "mongodb://localhost:27017"
```

**Connection Status:** ✅ Verified and working

---

### 4. Data Loading

#### Dataset Source
- **Source:** Kaggle TMDB Movie Metadata Dataset
- **Dataset:** `tmdb/tmdb-movie-metadata`
- **Files:**
  - `tmdb_5000_movies.csv` (5.4 MB)
  - `tmdb_5000_credits.csv` (38 MB)

#### Download Method
Created automated download script: `scripts/download_kaggle_data.py`
- Uses `kagglehub` library for automated dataset download
- Automatically copies CSV files to `data/raw/`
- Verifies file integrity

#### Data Loading Process

**PostgreSQL Loading:**
- ✅ Successfully loaded 4,803 movies
- Data transformation includes:
  - JSON parsing for genres, keywords
  - Release year extraction from dates
  - Poster URL generation
  - Data type conversions and null handling

**MongoDB Loading:**
- ✅ Successfully stored 4,803 raw records
- **Issue Encountered:** DateTime/NaT serialization error
- **Solution:** Added proper datetime handling in `data_loader.py`:
  ```python
  # Replace NaT and NaN values with None for MongoDB compatibility
  for col in df_copy.select_dtypes(include=['datetime64']).columns:
      df_copy[col] = df_copy[col].replace({pd.NaT: None})
  df_copy = df_copy.replace({np.nan: None, pd.NA: None})
  ```
- Fixed bug in `db_mongo.py`: Changed `if not self.db` to `if self.db is None` for proper MongoDB database object checking

**Loading Status:** ✅ Both databases populated successfully

---

## 🐛 Issues Encountered & Solutions

### Issue 1: MongoDB Installation Blocked by Outdated Command Line Tools
**Problem:** 
```
Error: Your Command Line Tools are too outdated.
Update them from Software Update in System Settings.
```

**Solution:**
1. Removed old Command Line Tools
2. Installed latest version (16.4) via GUI installer
3. Verified installation before proceeding with MongoDB

**Documentation:** Created `docs/MONGODB_SETUP_INSTRUCTIONS.md` for future reference

---

### Issue 2: MongoDB DateTime Serialization Error
**Problem:**
```
ValueError: NaTType does not support utcoffset
```

**Root Cause:** 
Pandas DataFrame datetime columns with NaT (Not a Time) values cannot be directly serialized to MongoDB.

**Solution:**
Modified `src/data_loader.py` to:
1. Replace all NaT values with None before conversion
2. Replace NaN values with None for MongoDB compatibility
3. Ensure all datetime objects are properly handled

---

### Issue 3: MongoDB Database Object Boolean Check
**Problem:**
```
NotImplementedError: Database objects do not implement truth value testing or bool().
```

**Root Cause:**
MongoDB database objects in pymongo don't support `if not self.db` syntax.

**Solution:**
Changed `if not self.db:` to `if self.db is None:` in `src/utils/db_mongo.py`

---

## 📊 Verification Results

### Database Verification

**PostgreSQL:**
```bash
psql -d cineswipe -c "SELECT COUNT(*) FROM dim_movies;"
# Result: 4803 movies
```

**MongoDB:**
```bash
mongosh cineswipe_db --eval "db.raw_kaggle_data.countDocuments()"
# Result: 4803 documents
```

### Test Suite Results

Ran `tests/test_database.py`:
- ✅ PostgreSQL Connection: **PASS**
- ✅ MongoDB Connection: **PASS**
- ✅ PostgreSQL Queries: **PASS**
- ✅ Database Views: **PASS**

---

## 📁 Files Created/Modified

### New Files Created:
1. `scripts/download_kaggle_data.py` - Automated Kaggle dataset download
2. `database/analytics_queries.sql` - 20+ analytics queries
3. `tests/test_database.py` - Database connection tests
4. `docs/SETUP_DOCUMENTATION.md` - This file
5. `docs/MONGODB_SETUP_INSTRUCTIONS.md` - MongoDB setup guide
6. `docs/README.md` - Documentation index

### Files Modified:
1. `config/settings.py` - Updated PostgreSQL credentials
2. `src/data_loader.py` - Added datetime handling for MongoDB
3. `src/utils/db_mongo.py` - Fixed database object boolean check
4. `requirements.txt` - Added `kagglehub` dependency

---

## ✅ Task Completion Status

- [x] **Task 1:** Verify Database Setup
- [x] **Task 2:** Create Analytics Queries
- [x] **Task 3:** Test Database Operations
- [x] **Task 4:** Document Your Setup (this document)
- [ ] **Task 5:** Commit and Push Work (pending)

---

## 🔧 Quick Reference Commands

```bash
# Start PostgreSQL
brew services start postgresql@14

# Start MongoDB
brew services start mongodb-community@7.0

# Connect to PostgreSQL
psql -d cineswipe

# Connect to MongoDB
mongosh cineswipe_db

# Run tests
python3 tests/test_database.py

# Run data loader
python3 src/data_loader.py

# Run analytics queries
psql -d cineswipe -f database/analytics_queries.sql
```

---

## 📝 Notes

- PostgreSQL uses peer authentication (no password required for local user)
- MongoDB runs as a local service on default port 27017
- All data loaded successfully with no errors
- All database utilities tested and working correctly
- Analytics queries verified and producing expected results

---

**Documentation Complete** ✅  
**Next Step:** Commit and push changes to repository

