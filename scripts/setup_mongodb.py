#!/usr/bin/env python3
"""
MongoDB Setup Script for Student Dropout Prediction System

This script helps set up MongoDB connection and create necessary indexes.
Run this script after installing MongoDB dependencies.
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime

def install_dependencies():
    """Install required MongoDB dependencies"""
    print("Installing MongoDB dependencies...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo", "dnspython"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_connection(uri):
    """Test MongoDB connection"""
    print(f"Testing connection to: {uri}")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        return True, client
    except ConnectionFailure:
        print("❌ MongoDB connection failed - server not reachable")
        return False, None
    except ServerSelectionTimeoutError:
        print("❌ MongoDB connection timeout - check your connection string")
        return False, None
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False, None

def setup_database(client, db_name, collection_name):
    """Set up database and collection with indexes"""
    print(f"Setting up database: {db_name}")
    try:
        db = client[db_name]
        collection = db[collection_name]
        
        # Create indexes for better performance
        indexes = [
            ("dropout_probability", 1),
            ("timestamp", -1),
            ("student_id", 1),
            ("risk_level", 1)
        ]
        
        for field, direction in indexes:
            try:
                collection.create_index([(field, direction)])
                print(f"✅ Created index on {field}")
            except Exception as e:
                print(f"⚠️ Index on {field} may already exist: {e}")
        
        print(f"✅ Database setup completed!")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_sample_document(collection):
    """Create a sample document to test the schema"""
    print("Creating sample document...")
    try:
        sample_doc = {
            "student_id": "sample_student_001",
            "prediction_data": {
                "marital_status": 1,
                "course": 1,
                "age_at_enrollment": 20,
                "gender": 1
            },
            "prediction_result": {
                "prediction": "Dropout",
                "risk_level": "High",
                "confidence": 0.85,
                "probabilities": {
                    "Dropout": 0.85,
                    "Enrolled": 0.10,
                    "Graduate": 0.05
                }
            },
            "dropout_probability": 0.85,
            "risk_level": "High",
            "confidence": 0.85,
            "timestamp": datetime.now(),
            "created_at": datetime.now().isoformat()
        }
        
        result = collection.insert_one(sample_doc)
        print(f"✅ Sample document created with ID: {result.inserted_id}")
        
        # Clean up sample document
        collection.delete_one({"_id": result.inserted_id})
        print("✅ Sample document cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ Sample document creation failed: {e}")
        return False

def main():
    """Main setup function"""
    print("MongoDB Setup for Student Dropout Prediction System")
    print("=" * 60)
    
    # Get MongoDB URI
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    
    if len(sys.argv) > 1:
        mongodb_uri = sys.argv[1]
    
    print(f"Using MongoDB URI: {mongodb_uri}")
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return False
    
    # Test connection
    success, client = test_connection(mongodb_uri)
    if not success:
        print("\nTroubleshooting tips:")
        print("1. For local MongoDB: Start MongoDB service")
        print("2. For MongoDB Atlas: Check your connection string")
        print("3. For Docker: Run 'docker run -d -p 27017:27017 mongo:latest'")
        return False
    
    # Setup database
    db_name = "student_dropout_db"
    collection_name = "high_risk_students"
    
    if not setup_database(client, db_name, collection_name):
        print("❌ Setup failed at database setup")
        return False
    
    # Test with sample document
    db = client[db_name]
    collection = db[collection_name]
    
    if not create_sample_document(collection):
        print("❌ Setup failed at sample document test")
        return False
    
    print("\n🎉 MongoDB setup completed successfully!")
    print(f"Database: {db_name}")
    print(f"Collection: {collection_name}")
    print("You can now run the Streamlit application with MongoDB support.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
