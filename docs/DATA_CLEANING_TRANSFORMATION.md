# Data Cleaning and Transformation Module

**Created:** December 9, 2024  
**Purpose:** Key project requirement - Organized data preprocessing, cleaning, and transformation

---

## 📁 Module Structure

```
changing_data/
├── __init__.py              # Module exports
├── README.md                # Module documentation
├── data_cleaner.py          # Data cleaning operations
└── data_transformer.py      # Data transformation operations
```

---

## ✅ What Was Created

### 1. Data Cleaner Module (`data_cleaner.py`)
**Purpose:** Handle all data cleaning operations

**Key Functions:**
- `parse_json_column()` - Parse JSON strings (handles malformed JSON)
- `clean_text_column()` - Normalize and clean text data
- `clean_numeric_column()` - Validate and clean numeric data
- `clean_datetime_column()` - Convert and validate dates
- `handle_missing_values()` - Fill or drop missing values
- `remove_duplicates()` - Remove duplicate records
- `validate_movie_data()` - Validate data integrity

**Features:**
- ✅ Robust JSON parsing (handles errors gracefully)
- ✅ Missing value handling strategies
- ✅ Data validation and quality checks
- ✅ Removed 4 invalid records from dataset

### 2. Data Transformer Module (`data_transformer.py`)
**Purpose:** Transform cleaned data into analysis-ready format

**Key Functions:**
- `transform_movies()` - Complete transformation pipeline
- `prepare_for_postgres()` - Format for PostgreSQL
- `prepare_for_mongo()` - Format for MongoDB

**Transformations Applied:**

1. **JSON Parsing:**
   - Extracts genres from JSON arrays
   - Extracts keywords from JSON arrays

2. **Temporal Features:**
   - Extract release year from dates
   - Create decade categories

3. **Derived Features:**
   - Poster URLs
   - Profit calculations (revenue - budget)
   - ROI calculations (return on investment)
   - Genre/keyword counts

4. **Categorization:**
   - Rating categories (Excellent, Very Good, Good, etc.)
   - Budget categories (Blockbuster, Big Budget, Mid Budget, etc.)
   - Runtime categories (Epic, Long, Standard, etc.)

5. **Data Type Conversion:**
   - Numeric columns properly typed
   - Datetime columns converted
   - Text columns normalized

---

## 🔄 Updated Data Loader

The `src/data_loader.py` now uses the new modules:

**Before:**
- All cleaning/transformation code mixed in data loader

**After:**
- Clean separation of concerns
- Uses `DataCleaner` for cleaning
- Uses `DataTransformer` for transformation
- More maintainable and testable

**Pipeline:**
```
1. Load CSV files
2. Clean data (DataCleaner)
3. Transform data (DataTransformer)
4. Load to PostgreSQL
5. Load to MongoDB
```

---

## 📊 Results

### Data Quality Improvements:
- ✅ Removed 4 invalid records (missing titles/genres/overviews)
- ✅ Validated all remaining 4,799 movies
- ✅ Proper data types for all columns
- ✅ Handled missing values appropriately

### Features Created:
- ✅ 4,799 movies with complete data
- ✅ Genres extracted and parsed
- ✅ Keywords extracted and parsed
- ✅ Release years extracted
- ✅ Derived metrics calculated (profit, ROI)
- ✅ Categorical features created

---

## 🚀 Usage

### Direct Usage:
```python
from changing_data.data_cleaner import DataCleaner
from changing_data.data_transformer import DataTransformer
import pandas as pd

# Load raw data
df = pd.read_csv('data/raw/tmdb_5000_movies.csv')

# Clean
cleaner = DataCleaner()
df_clean = cleaner.handle_missing_values(df)
df_clean = cleaner.validate_movie_data(df_clean)

# Transform
transformer = DataTransformer()
df_transformed = transformer.transform_movies(df_clean)
```

### Through Data Loader:
```python
from src.data_loader import DataLoader

loader = DataLoader()
loader.run_full_load()  # Uses cleaning and transformation modules automatically
```

---

## ✅ Project Requirements Met

### Data Cleaning:
- [x] Handle missing values
- [x] Remove duplicates
- [x] Validate data integrity
- [x] Normalize data types
- [x] Clean text data
- [x] Handle malformed data (JSON)

### Data Transformation:
- [x] Parse complex structures (JSON)
- [x] Extract features from dates
- [x] Create derived columns
- [x] Categorize continuous variables
- [x] Calculate business metrics
- [x] Prepare for multiple databases

### Code Organization:
- [x] Separated concerns (cleaning vs transformation)
- [x] Reusable functions
- [x] Well-documented code
- [x] Error handling
- [x] Modular design

---

## 📈 Statistics

**Before Cleaning:**
- Total records: 4,803

**After Cleaning:**
- Valid records: 4,799
- Removed: 4 invalid records

**Transformations Applied:**
- JSON columns parsed: 2 (genres, keywords)
- Derived features created: 8+
- Categorical features: 3 (rating, budget, runtime)
- Date features: 2 (year, decade)

---

## 🔗 Integration

The `changing_data` module is fully integrated with:
- ✅ `src/data_loader.py` - Uses cleaner and transformer
- ✅ PostgreSQL loading - Properly formatted data
- ✅ MongoDB loading - NaT/NaN handled correctly
- ✅ ML models - Clean data for training

---

**Status:** ✅ Complete and tested  
**Files Created:** 4 (cleaner, transformer, __init__, README)  
**Files Modified:** 1 (data_loader.py)

---

**Next Steps:**
- Test with different data sources
- Add more transformation options
- Create unit tests for cleaning/transformation functions

