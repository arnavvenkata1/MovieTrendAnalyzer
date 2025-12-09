-- ============================================================
-- CineSwipe Analytics Queries
-- CS210 Data Management Final Project
-- Use these queries to analyze movie and user data
-- ============================================================

-- ============================================================
-- MOVIE ANALYTICS
-- ============================================================

-- 1. Top 10 Highest Rated Movies (with minimum vote threshold)
SELECT 
    title, 
    vote_average, 
    vote_count,
    release_year, 
    genres
FROM dim_movies
WHERE vote_count > 100
ORDER BY vote_average DESC
LIMIT 10;

-- 2. Movies by Genre - Count and Average Rating
SELECT 
    UNNEST(genres) as genre,
    COUNT(*) as movie_count,
    ROUND(AVG(vote_average)::numeric, 2) as avg_rating,
    ROUND(AVG(popularity)::numeric, 2) as avg_popularity
FROM dim_movies
GROUP BY UNNEST(genres)
ORDER BY movie_count DESC;

-- 3. Movies by Decade
SELECT 
    (release_year / 10) * 10 as decade,
    COUNT(*) as movie_count,
    ROUND(AVG(vote_average)::numeric, 2) as avg_rating,
    ROUND(AVG(budget)::numeric, 0) as avg_budget
FROM dim_movies
WHERE release_year IS NOT NULL
GROUP BY (release_year / 10) * 10
ORDER BY decade DESC;

-- 4. Most Popular Movies (by TMDB popularity score)
SELECT 
    title, 
    popularity, 
    vote_average, 
    release_year,
    genres
FROM dim_movies
ORDER BY popularity DESC
LIMIT 10;

-- 5. Highest Grossing Movies
SELECT 
    title,
    budget,
    revenue,
    (revenue - budget) as profit,
    ROUND(((revenue - budget)::numeric / NULLIF(budget, 0) * 100), 2) as roi_percent
FROM dim_movies
WHERE budget > 0 AND revenue > 0
ORDER BY profit DESC
LIMIT 10;

-- 6. Movies by Language
SELECT 
    original_language,
    COUNT(*) as movie_count,
    ROUND(AVG(vote_average)::numeric, 2) as avg_rating
FROM dim_movies
GROUP BY original_language
ORDER BY movie_count DESC
LIMIT 10;

-- ============================================================
-- USER ENGAGEMENT ANALYTICS
-- ============================================================

-- 7. User Engagement Summary (using pre-built view)
SELECT * FROM vw_user_engagement
ORDER BY total_swipes DESC
LIMIT 20;

-- 8. Movie Approval Rates (using pre-built view)
SELECT * FROM vw_movie_popularity
WHERE total_swipes > 0
ORDER BY approval_rate DESC
LIMIT 20;

-- 9. Genre Preferences by User (using pre-built view)
SELECT * FROM vw_genre_preferences
ORDER BY user_id, likes DESC;

-- 10. Algorithm Performance Comparison (using pre-built view)
SELECT * FROM vw_algorithm_performance;

-- ============================================================
-- SWIPE ANALYTICS
-- ============================================================

-- 11. Daily Swipe Activity
SELECT 
    DATE(swipe_timestamp) as date,
    COUNT(*) as total_swipes,
    SUM(CASE WHEN swipe_direction = 'right' THEN 1 ELSE 0 END) as likes,
    SUM(CASE WHEN swipe_direction = 'left' THEN 1 ELSE 0 END) as passes,
    SUM(CASE WHEN swipe_direction = 'skip' THEN 1 ELSE 0 END) as skips,
    ROUND(
        SUM(CASE WHEN swipe_direction = 'right' THEN 1 ELSE 0 END)::numeric / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as like_rate_percent
FROM fact_swipes
GROUP BY DATE(swipe_timestamp)
ORDER BY date DESC;

-- 12. Swipes by Hour of Day (user behavior patterns)
SELECT 
    EXTRACT(HOUR FROM swipe_timestamp) as hour_of_day,
    COUNT(*) as total_swipes,
    ROUND(
        SUM(CASE WHEN swipe_direction = 'right' THEN 1 ELSE 0 END)::numeric / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as like_rate_percent
FROM fact_swipes
GROUP BY EXTRACT(HOUR FROM swipe_timestamp)
ORDER BY hour_of_day;

-- 13. User Retention Analysis
SELECT 
    COUNT(DISTINCT user_id) as total_users,
    COUNT(DISTINCT CASE WHEN total_swipes >= 5 THEN user_id END) as users_5plus_swipes,
    COUNT(DISTINCT CASE WHEN total_swipes >= 10 THEN user_id END) as users_10plus_swipes,
    COUNT(DISTINCT CASE WHEN total_swipes >= 20 THEN user_id END) as users_20plus_swipes,
    COUNT(DISTINCT CASE WHEN total_swipes >= 50 THEN user_id END) as power_users
FROM dim_users;

-- 14. Average Time Spent Before Swiping
SELECT 
    swipe_direction,
    COUNT(*) as count,
    ROUND(AVG(time_spent_ms)::numeric, 0) as avg_time_ms,
    ROUND(AVG(time_spent_ms)::numeric / 1000, 2) as avg_time_seconds
FROM fact_swipes
WHERE time_spent_ms IS NOT NULL
GROUP BY swipe_direction
ORDER BY avg_time_ms DESC;

-- ============================================================
-- RECOMMENDATION ANALYTICS
-- ============================================================

-- 15. Recommendation Success Rate by Algorithm
SELECT 
    algorithm_used,
    COUNT(*) as total_recs,
    SUM(CASE WHEN was_shown THEN 1 ELSE 0 END) as shown,
    SUM(CASE WHEN was_swiped_right THEN 1 ELSE 0 END) as liked,
    ROUND(AVG(score)::numeric, 3) as avg_confidence,
    ROUND(
        SUM(CASE WHEN was_swiped_right THEN 1 ELSE 0 END)::numeric / 
        NULLIF(SUM(CASE WHEN was_shown THEN 1 ELSE 0 END), 0) * 100, 2
    ) as hit_rate_percent
FROM fact_recommendations
GROUP BY algorithm_used
ORDER BY hit_rate_percent DESC NULLS LAST;

-- 16. Top Recommended Movies (most frequently recommended)
SELECT 
    m.title,
    m.genres,
    COUNT(r.rec_id) as times_recommended,
    SUM(CASE WHEN r.was_swiped_right THEN 1 ELSE 0 END) as times_liked,
    ROUND(AVG(r.score)::numeric, 3) as avg_score
FROM fact_recommendations r
JOIN dim_movies m ON r.movie_id = m.movie_id
GROUP BY m.movie_id, m.title, m.genres
ORDER BY times_recommended DESC
LIMIT 20;

-- ============================================================
-- USER PREFERENCE ANALYTICS
-- ============================================================

-- 17. Most Popular Preferred Genres (from onboarding)
SELECT 
    UNNEST(preferred_genres) as genre,
    COUNT(*) as user_count
FROM user_preferences
GROUP BY UNNEST(preferred_genres)
ORDER BY user_count DESC;

-- 18. Most Avoided Genres
SELECT 
    UNNEST(avoided_genres) as genre,
    COUNT(*) as user_count
FROM user_preferences
WHERE avoided_genres IS NOT NULL
GROUP BY UNNEST(avoided_genres)
ORDER BY user_count DESC;

-- 19. Mood Preferences Distribution
SELECT 
    mood_preference,
    COUNT(*) as user_count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM user_preferences) * 100, 2) as percentage
FROM user_preferences
WHERE mood_preference IS NOT NULL
GROUP BY mood_preference
ORDER BY user_count DESC;

-- 20. Decade Preferences Distribution
SELECT 
    preferred_decade,
    COUNT(*) as user_count
FROM user_preferences
WHERE preferred_decade IS NOT NULL
GROUP BY preferred_decade
ORDER BY user_count DESC;

