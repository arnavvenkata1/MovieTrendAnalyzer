# Data Cleaning and Transformation Module

This folder contains all data cleaning and transformation operations - a **key requirement** of the CS210 Data Management project.

---

## 📋 Overview

The `changing_data` module handles the ETL (Extract, Transform, Load) pipeline for converting raw Kaggle data into analysis-ready format.

---

## 📁 Module Structure

### `data_cleaner.py`
**Purpose:** Data cleaning operations

**Functions:**
- `parse_json_column()` - Parse JSON strings to extract values
- `clean_text_column()` - Clean and normalize text data
- `clean_numeric_column()` - Clean and validate numeric data
- `clean_datetime_column()` - Convert and validate datetime data
- `handle_missing_values()` - Handle missing data
- `remove_duplicates()` - Remove duplicate records
- `validate_movie_data()` - Validate data integrity

### `data_transformer.py`
**Purpose:** Data transformation operations

**Functions:**
- `transform_movies()` - Main transformation pipeline
- `prepare_for_postgres()` - Format for PostgreSQL insertion
- `prepare_for_mongo()` - Format for MongoDB insertion

**Transformations Applied:**
1. **JSON Parsing:** Extract genres, keywords from JSON strings
2. **Date Extraction:** Extract release year, decade from dates
3. **Feature Engineering:** 
   - Poster URLs
   - Profit calculations
   - ROI calculations
   - Genre/keyword counts
4. **Categorization:**
   - Rating categories
   - Budget categories
   - Runtime categories
5. **Data Type Conversion:** Ensure proper types for database

---

## 🔄 Transformation Pipeline

```
Raw CSV Data
    ↓
[Data Cleaner]
  - Parse JSON
  - Handle missing values
  - Remove duplicates
  - Validate data
    ↓
[Data Transformer]
  - Extract features
  - Create derived columns
  - Categorize data
  - Prepare for databases
    ↓
Clean Transformed Data
    ↓
PostgreSQL / MongoDB
```

---

## 🚀 Usage

### In Data Loader:
```python
from changing_data.data_cleaner import DataCleaner
from changing_data.data_transformer import DataTransformer

# Load raw data
df = pd.read_csv('data/raw/tmdb_5000_movies.csv')

# Clean
cleaner = DataCleaner()
df_clean = cleaner.handle_missing_values(df)
df_clean = cleaner.validate_movie_data(df_clean)

# Transform
transformer = DataTransformer()
df_transformed = transformer.transform_movies(df_clean)

# Prepare for database
df_pg = transformer.prepare_for_postgres(df_transformed)
df_mongo = transformer.prepare_for_mongo(df_transformed)
```

---

## 📊 Data Quality Improvements

### Cleaning Operations:
- ✅ Removed invalid records (missing titles, genres)
- ✅ Handled missing values appropriately
- ✅ Removed duplicate entries
- ✅ Validated data integrity

### Transformations Applied:
- ✅ Parsed JSON columns (genres, keywords)
- ✅ Extracted temporal features (year, decade)
- ✅ Created derived metrics (profit, ROI)
- ✅ Added categorical features
- ✅ Normalized data types

---

## 🔍 Key Features

### 1. Robust JSON Parsing
- Handles malformed JSON
- Gracefully handles errors
- Extracts nested values

### 2. Missing Data Handling
- Text columns: Fill with empty strings
- Numeric columns: Fill with appropriate defaults
- Datetime columns: Convert to datetime or None

### 3. Data Validation
- Removes invalid records
- Validates required fields
- Ensures data quality

### 4. Feature Engineering
- Creates business-relevant features
- Categorizes continuous variables
- Calculates derived metrics

---

## 📝 Project Requirements Met

✅ **Data Cleaning:**
- Handle missing values
- Remove duplicates
- Validate data integrity
- Normalize data types

✅ **Data Transformation:**
- Parse complex data structures (JSON)
- Extract features from dates
- Create derived columns
- Prepare for multiple databases

✅ **Code Organization:**
- Separated concerns (cleaning vs transformation)
- Reusable functions
- Well-documented
- Error handling

---

**Author:** Anish Shah  
**Date:** December 9, 2024  
**Project:** CS210 Data Management Final Project

