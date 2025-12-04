-- ============================================================
-- Movie Trend Analyzer - PostgreSQL Schema
-- CS210 Data Management Final Project
-- Authors: Anish Shah & Arnav Venkata
-- ============================================================

-- Drop existing tables (for fresh setup)
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS fact_daily_trends CASCADE;
DROP TABLE IF EXISTS fact_reviews CASCADE;
DROP TABLE IF EXISTS dim_genres CASCADE;
DROP TABLE IF EXISTS dim_movies CASCADE;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- 1. Genres Dimension Table
CREATE TABLE dim_genres (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(50) UNIQUE NOT NULL,
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Movies Dimension Table
CREATE TABLE dim_movies (
    movie_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year INT,
    genre_id INT REFERENCES dim_genres(genre_id),
    tmdb_id INT,
    overview TEXT,
    popularity FLOAT,
    vote_average FLOAT,
    vote_count INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- FACT TABLES
-- ============================================================

-- 3. Reviews Fact Table (individual review data from Letterboxd/Metacritic)
CREATE TABLE fact_reviews (
    review_id SERIAL PRIMARY KEY,
    movie_id INT REFERENCES dim_movies(movie_id),
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('letterboxd', 'metacritic')),
    reviewer_name VARCHAR(100),
    review_date DATE,
    rating FLOAT,
    review_text TEXT,
    comment_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    sentiment_score FLOAT,  -- VADER compound score (-1 to 1)
    mongo_doc_id VARCHAR(100),  -- Reference to MongoDB raw document
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Daily Aggregated Trends (Fact Table)
CREATE TABLE fact_daily_trends (
    trend_id SERIAL PRIMARY KEY,
    record_date DATE NOT NULL,
    genre_id INT REFERENCES dim_genres(genre_id),
    platform VARCHAR(50) DEFAULT 'all',
    total_reviews INT DEFAULT 0,
    total_engagement INT DEFAULT 0,  -- Sum of likes + comments
    avg_sentiment_score FLOAT,
    avg_rating FLOAT,
    review_velocity FLOAT,  -- % change from previous day
    UNIQUE(record_date, genre_id, platform)
);

-- 5. ML Predictions Output Table
CREATE TABLE predictions (
    pred_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_date DATE NOT NULL,
    genre_id INT REFERENCES dim_genres(genre_id),
    predicted_engagement INT,
    actual_engagement INT,  -- For validation after the fact
    trend_direction VARCHAR(20) CHECK (trend_direction IN ('RISING', 'DECLINING', 'STABLE')),
    confidence_score FLOAT,
    model_version VARCHAR(50)
);

-- ============================================================
-- INDEXES FOR QUERY PERFORMANCE
-- ============================================================

CREATE INDEX idx_reviews_movie ON fact_reviews(movie_id);
CREATE INDEX idx_reviews_date ON fact_reviews(review_date);
CREATE INDEX idx_reviews_platform ON fact_reviews(platform);
CREATE INDEX idx_trends_date ON fact_daily_trends(record_date);
CREATE INDEX idx_trends_genre ON fact_daily_trends(genre_id);
CREATE INDEX idx_movies_genre ON dim_movies(genre_id);

-- ============================================================
-- SEED DATA: Initial Genre Categories
-- ============================================================

INSERT INTO dim_genres (genre_name, keywords) VALUES 
    ('Horror', ARRAY['horror', 'scary', 'terrifying', 'creepy', 'spooky', 'slasher']),
    ('Comedy', ARRAY['comedy', 'funny', 'hilarious', 'laugh', 'humor']),
    ('Romance', ARRAY['romance', 'love', 'romantic', 'relationship']),
    ('Sci-Fi', ARRAY['sci-fi', 'scifi', 'space', 'alien', 'future', 'science fiction']),
    ('Action', ARRAY['action', 'fight', 'explosion', 'chase', 'battle']),
    ('Drama', ARRAY['drama', 'emotional', 'intense', 'powerful']),
    ('Animation', ARRAY['animated', 'animation', 'cartoon', 'pixar']),
    ('Thriller', ARRAY['thriller', 'suspense', 'mystery', 'psychological']),
    ('Adventure', ARRAY['adventure', 'quest', 'journey', 'exploration']),
    ('Fantasy', ARRAY['fantasy', 'magic', 'mythical', 'supernatural'])
ON CONFLICT (genre_name) DO NOTHING;

-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- View: Genre Trend Summary
CREATE OR REPLACE VIEW vw_genre_trends AS
SELECT 
    g.genre_name,
    t.record_date,
    t.total_reviews,
    t.total_engagement,
    t.avg_sentiment_score,
    t.review_velocity
FROM fact_daily_trends t
JOIN dim_genres g ON t.genre_id = g.genre_id
ORDER BY t.record_date DESC, t.total_engagement DESC;

-- View: Top Reviewed Movies
CREATE OR REPLACE VIEW vw_top_movies AS
SELECT 
    m.title,
    g.genre_name,
    COUNT(r.review_id) as review_count,
    AVG(r.sentiment_score) as avg_sentiment,
    SUM(r.like_count) as total_likes
FROM dim_movies m
JOIN dim_genres g ON m.genre_id = g.genre_id
LEFT JOIN fact_reviews r ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title, g.genre_name
ORDER BY total_likes DESC;

