"""
MongoDB Database Utilities
Handles all MongoDB connections and operations
"""

from pymongo import MongoClient
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import MONGO_URI, MONGO_CONFIG


class MongoDB:
    """MongoDB database handler"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[MONGO_CONFIG['database']]
            # Test connection
            self.client.server_info()
            print(f"✓ Connected to MongoDB: {MONGO_CONFIG['database']}")
            return True
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("MongoDB connection closed.")
    
    def get_collection(self, name):
        """Get a collection by name"""
        if self.db is None:
            self.connect()
        return self.db[name]
    
    # =========================================================
    # USER SESSION OPERATIONS
    # =========================================================
    
    def create_session(self, user_id, session_id, device_info=None):
        """Create a new user session"""
        collection = self.get_collection('user_sessions')
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "started_at": datetime.utcnow(),
            "ended_at": None,
            "device_info": device_info or {},
            "events": [],
            "summary": {
                "total_movies_viewed": 0,
                "total_swipes": 0,
                "right_swipes": 0,
                "left_swipes": 0,
                "skips": 0,
                "avg_view_time_ms": 0
            }
        }
        
        result = collection.insert_one(session)
        return str(result.inserted_id)
    
    def add_session_event(self, session_id, event_type, event_data):
        """Add an event to a session"""
        collection = self.get_collection('user_sessions')
        
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow(),
            **event_data
        }
        
        # Update session with new event
        collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"events": event},
                "$inc": self._get_summary_increments(event_type, event_data)
            }
        )
    
    def _get_summary_increments(self, event_type, event_data):
        """Get summary field increments based on event type"""
        increments = {}
        
        if event_type == "movie_view":
            increments["summary.total_movies_viewed"] = 1
        elif event_type == "swipe":
            increments["summary.total_swipes"] = 1
            direction = event_data.get("direction", "")
            if direction == "right":
                increments["summary.right_swipes"] = 1
            elif direction == "left":
                increments["summary.left_swipes"] = 1
            elif direction == "skip":
                increments["summary.skips"] = 1
        
        return increments
    
    def end_session(self, session_id):
        """Mark a session as ended"""
        collection = self.get_collection('user_sessions')
        collection.update_one(
            {"session_id": session_id},
            {"$set": {"ended_at": datetime.utcnow()}}
        )
    
    def get_session(self, session_id):
        """Get session by ID"""
        collection = self.get_collection('user_sessions')
        return collection.find_one({"session_id": session_id})
    
    def get_user_sessions(self, user_id, limit=10):
        """Get recent sessions for a user"""
        collection = self.get_collection('user_sessions')
        return list(collection.find(
            {"user_id": user_id}
        ).sort("started_at", -1).limit(limit))
    
    # =========================================================
    # RECOMMENDATION EXPLANATION OPERATIONS
    # =========================================================
    
    def save_recommendation_explanation(self, user_id, movie_id, algorithm, 
                                        score, explanation):
        """Save detailed recommendation explanation"""
        collection = self.get_collection('recommendation_explanations')
        
        doc = {
            "user_id": user_id,
            "movie_id": movie_id,
            "generated_at": datetime.utcnow(),
            "algorithm": algorithm,
            "confidence_score": score,
            "explanation": explanation,
            "user_feedback": {
                "was_helpful": None,
                "swiped_direction": None
            }
        }
        
        result = collection.insert_one(doc)
        return str(result.inserted_id)
    
    def get_recommendation_explanation(self, user_id, movie_id):
        """Get explanation for a specific recommendation"""
        collection = self.get_collection('recommendation_explanations')
        return collection.find_one({
            "user_id": user_id,
            "movie_id": movie_id
        })
    
    def update_recommendation_feedback(self, user_id, movie_id, swiped_direction):
        """Update recommendation with user feedback"""
        collection = self.get_collection('recommendation_explanations')
        collection.update_one(
            {"user_id": user_id, "movie_id": movie_id},
            {"$set": {
                "user_feedback.swiped_direction": swiped_direction,
                "user_feedback.updated_at": datetime.utcnow()
            }}
        )
    
    # =========================================================
    # MODEL VERSION OPERATIONS
    # =========================================================
    
    def save_model_version(self, model_name, version, training_config, 
                          training_data, performance_metrics, file_path):
        """Save model metadata"""
        collection = self.get_collection('model_versions')
        
        # Deactivate previous versions
        collection.update_many(
            {"model_name": model_name, "is_active": True},
            {"$set": {"is_active": False}}
        )
        
        doc = {
            "model_name": model_name,
            "version": version,
            "created_at": datetime.utcnow(),
            "training_config": training_config,
            "training_data": training_data,
            "performance_metrics": performance_metrics,
            "is_active": True,
            "file_path": file_path
        }
        
        result = collection.insert_one(doc)
        return str(result.inserted_id)
    
    def get_active_model(self, model_name):
        """Get currently active model version"""
        collection = self.get_collection('model_versions')
        return collection.find_one({
            "model_name": model_name,
            "is_active": True
        })
    
    def get_model_history(self, model_name, limit=10):
        """Get model version history"""
        collection = self.get_collection('model_versions')
        return list(collection.find(
            {"model_name": model_name}
        ).sort("created_at", -1).limit(limit))
    
    # =========================================================
    # RAW DATA OPERATIONS (Data Lake)
    # =========================================================
    
    def store_raw_kaggle_data(self, source, records):
        """Store raw Kaggle data before processing"""
        collection = self.get_collection('raw_kaggle_data')
        
        docs = [
            {
                "source": source,
                "imported_at": datetime.utcnow(),
                "raw_record": record,
                "processed": False,
                "processed_at": None,
                "postgres_movie_id": None
            }
            for record in records
        ]
        
        result = collection.insert_many(docs)
        return len(result.inserted_ids)
    
    def mark_raw_data_processed(self, source, postgres_ids_map):
        """Mark raw data as processed with PostgreSQL IDs"""
        collection = self.get_collection('raw_kaggle_data')
        
        for tmdb_id, postgres_id in postgres_ids_map.items():
            collection.update_one(
                {"source": source, "raw_record.id": tmdb_id},
                {"$set": {
                    "processed": True,
                    "processed_at": datetime.utcnow(),
                    "postgres_movie_id": postgres_id
                }}
            )
    
    # =========================================================
    # ANALYTICS
    # =========================================================
    
    def get_session_analytics(self, user_id=None, days=30):
        """Get session analytics"""
        collection = self.get_collection('user_sessions')
        
        pipeline = [
            {"$match": {"started_at": {"$gte": datetime.utcnow()}}},
            {"$group": {
                "_id": "$user_id" if user_id is None else None,
                "total_sessions": {"$sum": 1},
                "total_swipes": {"$sum": "$summary.total_swipes"},
                "total_right_swipes": {"$sum": "$summary.right_swipes"},
                "avg_session_swipes": {"$avg": "$summary.total_swipes"}
            }}
        ]
        
        if user_id:
            pipeline[0]["$match"]["user_id"] = user_id
        
        return list(collection.aggregate(pipeline))


# Singleton instance
mongo_db = MongoDB()

