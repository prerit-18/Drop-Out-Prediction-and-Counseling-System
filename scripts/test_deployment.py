#!/usr/bin/env python3
"""
Deployment Test Script for MongoDB Connection
Run this script to test MongoDB connection in your deployment environment
"""

import os
import sys
from pymongo import MongoClient

def test_mongodb_connection():
    """Test MongoDB connection using environment variables"""
    print("🔍 Testing MongoDB Connection for Deployment...")
    print("=" * 50)
    
    # Check environment variables
    mongodb_uri = os.getenv("MONGODB_URI")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL")
    
    print(f"MONGODB_URI: {'✅ Set' if mongodb_uri else '❌ Not set'}")
    print(f"GOOGLE_API_KEY: {'✅ Set' if google_api_key else '❌ Not set'}")
    print(f"GEMINI_MODEL: {'✅ Set' if gemini_model else '❌ Not set'}")
    print()
    
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not found!")
        print("Please set it in your deployment platform:")
        print('MONGODB_URI="mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"')
        return False
    
    # Test MongoDB connection
    try:
        print("🔌 Testing MongoDB connection...")
        client = MongoClient(mongodb_uri)
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client["student_dropout_db"]
        collection = db["high_risk_students"]
        
        # Try to insert a test document
        test_doc = {
            "test": True,
            "timestamp": "2025-09-27T01:00:00Z",
            "deployment_test": True
        }
        
        result = collection.insert_one(test_doc)
        print(f"✅ Database write test successful! Document ID: {result.inserted_id}")
        
        # Clean up test document
        collection.delete_one({"_id": result.inserted_id})
        print("✅ Database cleanup successful!")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check MongoDB Atlas Network Access settings")
        print("2. Verify username/password in connection string")
        print("3. Ensure deployment platform can reach MongoDB Atlas")
        print("4. Check if IP address is whitelisted in MongoDB Atlas")
        return False

def test_google_api():
    """Test Google API configuration"""
    print("\n🤖 Testing Google API Configuration...")
    print("=" * 50)
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY environment variable not found!")
        return False
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel(gemini_model)
        
        # Test with a simple prompt
        response = model.generate_content("Hello, this is a test.")
        print("✅ Google API connection successful!")
        print(f"✅ Model: {gemini_model}")
        return True
        
    except Exception as e:
        print(f"❌ Google API connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Deployment Configuration Test")
    print("=" * 50)
    
    mongodb_ok = test_mongodb_connection()
    google_ok = test_google_api()
    
    print("\n📊 Test Results:")
    print("=" * 50)
    print(f"MongoDB: {'✅ PASS' if mongodb_ok else '❌ FAIL'}")
    print(f"Google API: {'✅ PASS' if google_ok else '❌ FAIL'}")
    
    if mongodb_ok and google_ok:
        print("\n🎉 All tests passed! Your deployment should work correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        sys.exit(1)
