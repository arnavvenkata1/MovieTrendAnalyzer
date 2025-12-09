-- ============================================================
-- CineSwipe - PostgreSQL Database Schema
-- Movie Recommendation System with Swipe Interface
-- CS210 Data Management Final Project
-- Authors: Anish Shah & Arnav Venkata
-- ============================================================

-- Drop existing tables (for fresh setup)
DROP TABLE IF EXISTS model_metrics CASCADE;
DROP TABLE IF EXISTS fact_recommendations CASCADE;
DROP TABLE IF EXISTS fact_swipes CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS dim_movies CASCADE;
DROP TABLE IF EXISTS dim_users CASCADE;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- 1. Users Dimension Table
CREATE TABLE dim_users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    age_group VARCHAR(20),                    -- '18-24', '25-34', '35-44', '45+'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_swipes INT DEFAULT 0,
    total_right_swipes INT DEFAULT 0
);

-- 2. User Preferences Table (from onboarding)
CREATE TABLE user_preferences (
    pref_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES dim_users(user_id) ON DELETE CASCADE,
    preferred_genres TEXT[],                  -- ARRAY['Action', 'Sci-Fi', 'Comedy']
    avoided_genres TEXT[],                    -- ARRAY['Horror', 'War']
    preferred_decade VARCHAR(10),             -- '2020s', '2010s', '2000s', '1990s', 'classic'
    mood_preference VARCHAR(50),              -- 'feel-good', 'thrilling', 'thought-provoking', 'romantic'
    min_rating FLOAT DEFAULT 6.0,             -- Minimum TMDB rating to show
    language_pref VARCHAR(10) DEFAULT 'en',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- 3. Movies Dimension Table (populated from TMDB Kaggle dataset)
CREATE TABLE dim_movies (
    movie_id SERIAL PRIMARY KEY,
    tmdb_id INT UNIQUE,
    title VARCHAR(255) NOT NULL,
    genres TEXT[],                            -- ARRAY['Action', 'Adventure', 'Sci-Fi']
    overview TEXT,
    release_year INT,
    release_date DATE,
    popularity FLOAT,
    vote_average FLOAT,
    vote_count INT,
    budget BIGINT,
    revenue BIGINT,
    runtime INT,                              -- minutes
    original_language VARCHAR(10),
    poster_url VARCHAR(500),
    backdrop_url VARCHAR(500),
    keywords TEXT[],                          -- Extracted from TMDB keywords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- FACT TABLES
-- ============================================================

-- 4. Swipe History (Core engagement data)
CREATE TABLE fact_swipes (
    swipe_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES dim_users(user_id) ON DELETE CASCADE,
    movie_id INT REFERENCES dim_movies(movie_id) ON DELETE CASCADE,
    swipe_direction VARCHAR(10) NOT NULL CHECK (swipe_direction IN ('left', 'right', 'skip', 'superlike')),
    swipe_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_spent_ms INT,                        -- How long user viewed before swiping
    session_id VARCHAR(50),                   -- Group swipes by session
    recommendation_source VARCHAR(50),        -- 'content', 'collaborative', 'hybrid', 'popular', 'random'
    UNIQUE(user_id, movie_id)                 -- One swipe per user per movie
);

-- 5. Recommendations Log (Track what we recommended)
CREATE TABLE fact_recommendations (
    rec_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES dim_users(user_id) ON DELETE CASCADE,
    movie_id INT REFERENCES dim_movies(movie_id) ON DELETE CASCADE,
    score FLOAT NOT NULL,                     -- ML confidence score (0-1)
    rank_position INT,                        -- Position in recommendation list
    algorithm_used VARCHAR(50) NOT NULL,      -- 'content_based', 'collaborative', 'hybrid'
    was_shown BOOLEAN DEFAULT FALSE,          -- Did user see this recommendation?
    was_swiped_right BOOLEAN DEFAULT NULL,    -- Did user like it? NULL = not yet seen
    explanation_text TEXT,                    -- "Because you liked Inception..."
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Model Performance Metrics (Track ML model quality)
CREATE TABLE model_metrics (
    metric_id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,          -- 'content_based', 'collaborative', 'hybrid'
    model_version VARCHAR(20),
    precision_at_k FLOAT,                     -- Precision@10
    recall_at_k FLOAT,                        -- Recall@10
    ndcg_score FLOAT,                         -- Normalized Discounted Cumulative Gain
    hit_rate FLOAT,                           -- % of recommendations swiped right
    coverage FLOAT,                           -- % of movies that got recommended
    diversity_score FLOAT,                    -- Genre diversity in recommendations
    total_users_evaluated INT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES FOR QUERY PERFORMANCE
-- ============================================================

-- User lookups
CREATE INDEX idx_users_username ON dim_users(username);
CREATE INDEX idx_users_created ON dim_users(created_at);

-- Movie lookups
CREATE INDEX idx_movies_tmdb ON dim_movies(tmdb_id);
CREATE INDEX idx_movies_title ON dim_movies(title);
CREATE INDEX idx_movies_year ON dim_movies(release_year);
CREATE INDEX idx_movies_rating ON dim_movies(vote_average);
CREATE INDEX idx_movies_popularity ON dim_movies(popularity);

-- Swipe analytics
CREATE INDEX idx_swipes_user ON fact_swipes(user_id);
CREATE INDEX idx_swipes_movie ON fact_swipes(movie_id);
CREATE INDEX idx_swipes_direction ON fact_swipes(swipe_direction);
CREATE INDEX idx_swipes_timestamp ON fact_swipes(swipe_timestamp);
CREATE INDEX idx_swipes_session ON fact_swipes(session_id);

-- Recommendations
CREATE INDEX idx_recs_user ON fact_recommendations(user_id);
CREATE INDEX idx_recs_algorithm ON fact_recommendations(algorithm_used);

-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- View: User engagement summary
CREATE OR REPLACE VIEW vw_user_engagement AS
SELECT 
    u.user_id,
    u.username,
    u.total_swipes,
    u.total_right_swipes,
    CASE WHEN u.total_swipes > 0 
         THEN ROUND(u.total_right_swipes::DECIMAL / u.total_swipes * 100, 2)
         ELSE 0 
    END as like_rate_pct,
    COUNT(DISTINCT s.session_id) as total_sessions,
    MAX(s.swipe_timestamp) as last_swipe
FROM dim_users u
LEFT JOIN fact_swipes s ON u.user_id = s.user_id
GROUP BY u.user_id, u.username, u.total_swipes, u.total_right_swipes;

-- View: Movie popularity by swipes
CREATE OR REPLACE VIEW vw_movie_popularity AS
SELECT 
    m.movie_id,
    m.title,
    m.genres,
    m.vote_average as tmdb_rating,
    COUNT(s.swipe_id) as total_swipes,
    SUM(CASE WHEN s.swipe_direction = 'right' THEN 1 ELSE 0 END) as right_swipes,
    SUM(CASE WHEN s.swipe_direction = 'left' THEN 1 ELSE 0 END) as left_swipes,
    CASE WHEN COUNT(s.swipe_id) > 0
         THEN ROUND(SUM(CASE WHEN s.swipe_direction = 'right' THEN 1 ELSE 0 END)::DECIMAL / COUNT(s.swipe_id) * 100, 2)
         ELSE 0
    END as approval_rate
FROM dim_movies m
LEFT JOIN fact_swipes s ON m.movie_id = s.movie_id
GROUP BY m.movie_id, m.title, m.genres, m.vote_average
ORDER BY right_swipes DESC;

-- View: Algorithm performance comparison
CREATE OR REPLACE VIEW vw_algorithm_performance AS
SELECT 
    algorithm_used,
    COUNT(*) as total_recommendations,
    SUM(CASE WHEN was_shown THEN 1 ELSE 0 END) as shown_count,
    SUM(CASE WHEN was_swiped_right THEN 1 ELSE 0 END) as liked_count,
    ROUND(AVG(score)::DECIMAL, 3) as avg_confidence,
    CASE WHEN SUM(CASE WHEN was_shown THEN 1 ELSE 0 END) > 0
         THEN ROUND(SUM(CASE WHEN was_swiped_right THEN 1 ELSE 0 END)::DECIMAL / 
                    SUM(CASE WHEN was_shown THEN 1 ELSE 0 END) * 100, 2)
         ELSE 0
    END as hit_rate_pct
FROM fact_recommendations
GROUP BY algorithm_used
ORDER BY hit_rate_pct DESC;

-- View: Genre preferences by user
CREATE OR REPLACE VIEW vw_genre_preferences AS
SELECT 
    s.user_id,
    u.username,
    UNNEST(m.genres) as genre,
    COUNT(*) as swipe_count,
    SUM(CASE WHEN s.swipe_direction = 'right' THEN 1 ELSE 0 END) as likes,
    ROUND(AVG(CASE WHEN s.swipe_direction = 'right' THEN 1.0 ELSE 0.0 END) * 100, 2) as like_rate
FROM fact_swipes s
JOIN dim_movies m ON s.movie_id = m.movie_id
JOIN dim_users u ON s.user_id = u.user_id
GROUP BY s.user_id, u.username, UNNEST(m.genres)
ORDER BY s.user_id, likes DESC;

-- ============================================================
-- SAMPLE QUERIES FOR ANALYTICS
-- ============================================================

-- Query 1: Top 10 most liked movies
-- SELECT * FROM vw_movie_popularity WHERE total_swipes >= 5 ORDER BY approval_rate DESC LIMIT 10;

-- Query 2: User with highest engagement
-- SELECT * FROM vw_user_engagement ORDER BY total_swipes DESC LIMIT 10;

-- Query 3: Best performing algorithm
-- SELECT * FROM vw_algorithm_performance;

-- Query 4: Genre performance
-- SELECT genre, SUM(likes) as total_likes, AVG(like_rate) as avg_like_rate
-- FROM vw_genre_preferences GROUP BY genre ORDER BY total_likes DESC;

