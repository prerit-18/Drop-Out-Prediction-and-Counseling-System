"""
MongoDB Configuration for Student Dropout Prediction System

This file contains configuration settings for MongoDB connection.
You can customize these settings based on your MongoDB setup.

For MongoDB Atlas (Cloud):
1. Get your connection string from MongoDB Atlas
2. Set the MONGODB_URI environment variable
3. Example: export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"

For Local MongoDB:
1. Install MongoDB locally
2. Start MongoDB service
3. Use default connection string: mongodb://localhost:27017/

For Docker MongoDB:
1. Run: docker run -d -p 27017:27017 --name mongodb mongo:latest
2. Use connection string: mongodb://localhost:27017/
"""

import os

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "student_dropout_db"
COLLECTION_NAME = "high_risk_students"

# Database Schema
HIGH_RISK_STUDENT_SCHEMA = {
    "student_id": "string",  # Unique identifier for the student
    "prediction_data": "object",  # Original student data used for prediction
    "prediction_result": "object",  # Full prediction result from AI model
    "dropout_probability": "float",  # Dropout probability (0.0 to 1.0)
    "risk_level": "string",  # Risk level: Low, Medium, High
    "confidence": "float",  # Model confidence (0.0 to 1.0)
    "timestamp": "datetime",  # When the prediction was made
    "created_at": "string"  # ISO format timestamp
}

# Indexes for better performance
RECOMMENDED_INDEXES = [
    {"dropout_probability": 1},  # For filtering high-risk students
    {"timestamp": -1},  # For sorting by most recent
    {"student_id": 1},  # For unique student lookups
    {"risk_level": 1}  # For filtering by risk level
]

def get_connection_string():
    """Get the MongoDB connection string"""
    return MONGODB_URI

def get_database_name():
    """Get the database name"""
    return DATABASE_NAME

def get_collection_name():
    """Get the collection name"""
    return COLLECTION_NAME

def validate_connection_string(uri):
    """Validate MongoDB connection string format"""
    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        return False, "Connection string must start with 'mongodb://' or 'mongodb+srv://'"
    
    if "mongodb+srv://" in uri and "@" not in uri:
        return False, "Atlas connection string must include username and password"
    
    return True, "Valid connection string"

# Example usage and setup instructions
if __name__ == "__main__":
    print("MongoDB Configuration for Student Dropout Prediction System")
    print("=" * 60)
    print(f"Connection String: {MONGODB_URI}")
    print(f"Database Name: {DATABASE_NAME}")
    print(f"Collection Name: {COLLECTION_NAME}")
    print("\nSetup Instructions:")
    print("1. Install MongoDB: pip install pymongo dnspython")
    print("2. Set environment variable: export MONGODB_URI='your_connection_string'")
    print("3. Or modify MONGODB_URI in this file directly")
    print("\nFor MongoDB Atlas (Cloud):")
    print("- Get connection string from MongoDB Atlas dashboard")
    print("- Format: mongodb+srv://username:password@cluster.mongodb.net/")
    print("\nFor Local MongoDB:")
    print("- Install MongoDB locally")
    print("- Start MongoDB service")
    print("- Use: mongodb://localhost:27017/")
