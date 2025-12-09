# MongoDB Schema Documentation

## CineSwipe - NoSQL Database Design

MongoDB is used to store flexible, unstructured data that doesn't fit well in PostgreSQL's rigid schema.

---

## Database: `cineswipe_db`

---

### Collection: `user_sessions`

Tracks detailed user interaction events within a session.

```javascript
{
    "_id": ObjectId("..."),
    "session_id": "uuid-string",
    "user_id": 123,                          // References PostgreSQL dim_users
    "started_at": ISODate("2024-12-02T10:00:00Z"),
    "ended_at": ISODate("2024-12-02T10:15:00Z"),
    "device_info": {
        "type": "desktop",                   // desktop, mobile, tablet
        "browser": "Chrome",
        "os": "macOS",
        "screen_width": 1920,
        "screen_height": 1080
    },
    "events": [
        {
            "type": "page_view",
            "page": "swipe",
            "timestamp": ISODate("...")
        },
        {
            "type": "movie_view",
            "movie_id": 456,
            "duration_ms": 3500,
            "timestamp": ISODate("...")
        },
        {
            "type": "swipe",
            "movie_id": 456,
            "direction": "right",
            "timestamp": ISODate("...")
        }
    ],
    "summary": {
        "total_movies_viewed": 15,
        "total_swipes": 12,
        "right_swipes": 5,
        "left_swipes": 6,
        "skips": 1,
        "avg_view_time_ms": 2800
    }
}
```

---

### Collection: `recommendation_explanations`

Stores detailed explanations for why movies were recommended.

```javascript
{
    "_id": ObjectId("..."),
    "user_id": 123,
    "movie_id": 456,
    "generated_at": ISODate("..."),
    "algorithm": "hybrid",
    "confidence_score": 0.87,
    "explanation": {
        "primary_reason": "Similar to movies you've liked",
        "factors": [
            {
                "type": "genre_match",
                "description": "You enjoy Sci-Fi movies",
                "weight": 0.35,
                "matched_genres": ["Sci-Fi", "Action"]
            },
            {
                "type": "similar_users",
                "description": "Users like you enjoyed this",
                "weight": 0.30,
                "similar_user_count": 47
            },
            {
                "type": "director_match",
                "description": "From a director you've liked before",
                "weight": 0.20,
                "director": "Christopher Nolan"
            },
            {
                "type": "rating",
                "description": "Highly rated on TMDB",
                "weight": 0.15,
                "rating": 8.4
            }
        ],
        "similar_movies_liked": [
            {"movie_id": 100, "title": "Inception", "similarity": 0.92},
            {"movie_id": 101, "title": "Interstellar", "similarity": 0.88},
            {"movie_id": 102, "title": "The Matrix", "similarity": 0.85}
        ]
    },
    "user_feedback": {
        "was_helpful": null,                 // true/false after user rates
        "swiped_direction": null             // Updated after swipe
    }
}
```

---

### Collection: `model_versions`

Stores ML model metadata and training history.

```javascript
{
    "_id": ObjectId("..."),
    "model_name": "hybrid_recommender",
    "version": "2.1.0",
    "created_at": ISODate("..."),
    "training_config": {
        "algorithm": "matrix_factorization",
        "n_factors": 50,
        "learning_rate": 0.01,
        "regularization": 0.02,
        "epochs": 100
    },
    "training_data": {
        "total_users": 1500,
        "total_movies": 4803,
        "total_swipes": 45000,
        "train_test_split": 0.8
    },
    "performance_metrics": {
        "precision_at_10": 0.72,
        "recall_at_10": 0.45,
        "ndcg": 0.68,
        "hit_rate": 0.78,
        "coverage": 0.65
    },
    "is_active": true,                       // Currently deployed model
    "file_path": "models/saved/hybrid_v2.1.0.pkl"
}
```

---

### Collection: `ab_tests`

Tracks A/B test experiments for algorithm comparison.

```javascript
{
    "_id": ObjectId("..."),
    "test_name": "hybrid_vs_content_q4_2024",
    "status": "running",                     // draft, running, completed
    "started_at": ISODate("..."),
    "ended_at": null,
    "variants": [
        {
            "name": "control",
            "algorithm": "content_based",
            "traffic_percentage": 50,
            "users_assigned": 750
        },
        {
            "name": "treatment",
            "algorithm": "hybrid",
            "traffic_percentage": 50,
            "users_assigned": 750
        }
    ],
    "metrics": {
        "control": {
            "total_swipes": 12000,
            "right_swipes": 4200,
            "conversion_rate": 0.35
        },
        "treatment": {
            "total_swipes": 12500,
            "right_swipes": 5000,
            "conversion_rate": 0.40
        }
    },
    "statistical_significance": {
        "p_value": 0.023,
        "is_significant": true,
        "winner": "treatment"
    }
}
```

---

### Collection: `raw_kaggle_data`

Stores original Kaggle data before transformation (data lake pattern).

```javascript
{
    "_id": ObjectId("..."),
    "source": "tmdb_5000_movies",
    "imported_at": ISODate("..."),
    "raw_record": {
        // Original CSV row as JSON
        "budget": 237000000,
        "genres": "[{\"id\": 28, \"name\": \"Action\"}, ...]",
        "title": "Avatar",
        // ... all original fields
    },
    "processed": true,
    "processed_at": ISODate("..."),
    "postgres_movie_id": 1                   // Foreign key after ETL
}
```

---

## Indexes

```javascript
// user_sessions
db.user_sessions.createIndex({ "user_id": 1 })
db.user_sessions.createIndex({ "session_id": 1 }, { unique: true })
db.user_sessions.createIndex({ "started_at": -1 })

// recommendation_explanations
db.recommendation_explanations.createIndex({ "user_id": 1, "movie_id": 1 })
db.recommendation_explanations.createIndex({ "algorithm": 1 })

// model_versions
db.model_versions.createIndex({ "model_name": 1, "version": 1 }, { unique: true })
db.model_versions.createIndex({ "is_active": 1 })

// ab_tests
db.ab_tests.createIndex({ "test_name": 1 }, { unique: true })
db.ab_tests.createIndex({ "status": 1 })
```

---

## Why MongoDB for These Collections?

| Collection | Reason for NoSQL |
|------------|------------------|
| `user_sessions` | Nested event arrays, flexible schema per session |
| `recommendation_explanations` | Complex nested explanation objects |
| `model_versions` | Training configs vary by algorithm |
| `ab_tests` | Flexible variant structures |
| `raw_kaggle_data` | Data lake - preserve original format |

