"""
Database Connection Tests
Author: Anish Shah
Run with: python tests/test_database.py
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


def test_postgres_queries():
    """Test various PostgreSQL queries"""
    print("\nTesting PostgreSQL Queries...")
    
    if not postgres_db.connect():
        return False
    
    # Test 1: Get random movies
    print("  Testing get_random_movies()...")
    movies = postgres_db.get_random_movies(limit=3)
    print(f"  ✓ Got {len(movies)} random movies")
    
    # Test 2: Check if views exist
    print("  Testing views...")
    try:
        result = postgres_db.execute_query("SELECT COUNT(*) FROM vw_movie_popularity")
        print(f"  ✓ vw_movie_popularity view exists")
    except Exception as e:
        print(f"  ⚠ View test failed: {e}")
    
    postgres_db.disconnect()
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE CONNECTION TESTS")
    print("=" * 50)
    
    pg_ok = test_postgres_connection()
    mongo_ok = test_mongo_connection()
    
    if pg_ok:
        test_postgres_queries()
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"PostgreSQL: {'✅ PASS' if pg_ok else '❌ FAIL'}")
    print(f"MongoDB: {'✅ PASS' if mongo_ok else '❌ FAIL'}")

