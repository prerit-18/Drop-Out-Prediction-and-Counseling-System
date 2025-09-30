#!/usr/bin/env python3
"""
Debug script to check deployment configuration
Run this in your deployment environment to diagnose issues
"""

import os
import streamlit as st

st.set_page_config(page_title="Deployment Debug", layout="wide")

st.title("🔍 Deployment Configuration Debug")

st.header("Environment Variables")
st.write("Checking if required environment variables are set:")

# Check MongoDB
mongodb_uri = os.getenv("MONGODB_URI")
st.write(f"**MONGODB_URI**: {'✅ Set' if mongodb_uri else '❌ Not set'}")
if mongodb_uri:
    st.write(f"Value: `{mongodb_uri[:50]}...`")

# Check Google API
google_key = os.getenv("GOOGLE_API_KEY")
st.write(f"**GOOGLE_API_KEY**: {'✅ Set' if google_key else '❌ Not set'}")
if google_key:
    st.write(f"Value: `{google_key[:20]}...`")

gemini_model = os.getenv("GEMINI_MODEL")
st.write(f"**GEMINI_MODEL**: {'✅ Set' if gemini_model else '❌ Not set'}")
if gemini_model:
    st.write(f"Value: `{gemini_model}`")

st.header("Streamlit Secrets")
try:
    if hasattr(st, "secrets"):
        st.write("✅ Streamlit secrets available")
        
        # Check mongo secrets
        try:
            mongo_uri = st.secrets["mongo"]["uri"]
            st.write(f"**Mongo URI from secrets**: ✅ Set")
            st.write(f"Value: `{mongo_uri[:50]}...`")
        except:
            st.write("**Mongo URI from secrets**: ❌ Not found")
            
        # Check google secrets
        try:
            google_secret = st.secrets["google"]["api_key"]
            st.write(f"**Google API from secrets**: ✅ Set")
            st.write(f"Value: `{google_secret[:20]}...`")
        except:
            st.write("**Google API from secrets**: ❌ Not found")
            
except Exception as e:
    st.write(f"❌ Streamlit secrets error: {e}")

st.header("MongoDB Connection Test")
if mongodb_uri or (hasattr(st, "secrets") and "mongo" in st.secrets):
    try:
        from pymongo import MongoClient
        
        # Try to get connection string
        connection_uri = mongodb_uri
        if not connection_uri and hasattr(st, "secrets"):
            try:
                connection_uri = st.secrets["mongo"]["uri"]
            except:
                pass
        
        if connection_uri:
            st.write(f"Testing connection to: `{connection_uri[:50]}...`")
            client = MongoClient(connection_uri)
            client.admin.command('ping')
            st.write("✅ MongoDB connection successful!")
            
            # Test database access
            db = client["student_dropout_db"]
            collections = db.list_collection_names()
            st.write(f"✅ Database access successful! Collections: {collections}")
            
            client.close()
        else:
            st.write("❌ No MongoDB connection string found")
            
    except Exception as e:
        st.write(f"❌ MongoDB connection failed: {e}")
else:
    st.write("❌ No MongoDB configuration found")

st.header("Google API Test")
if google_key or (hasattr(st, "secrets") and "google" in st.secrets):
    try:
        import google.generativeai as genai
        
        # Try to get API key
        api_key = google_key
        if not api_key and hasattr(st, "secrets"):
            try:
                api_key = st.secrets["google"]["api_key"]
            except:
                pass
        
        if api_key:
            st.write(f"Testing Google API with key: `{api_key[:20]}...`")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content("Hello, this is a test.")
            st.write("✅ Google API connection successful!")
        else:
            st.write("❌ No Google API key found")
            
    except Exception as e:
        st.write(f"❌ Google API connection failed: {e}")
else:
    st.write("❌ No Google API configuration found")

st.header("Deployment Platform Info")
st.write(f"**Python Version**: {os.sys.version}")
st.write(f"**Working Directory**: {os.getcwd()}")
st.write(f"**Platform**: {os.name}")

# Check if we're in a deployment environment
deployment_indicators = [
    "STREAMLIT_CLOUD" in os.environ,
    "HEROKU_APP_NAME" in os.environ,
    "RAILWAY_PROJECT_ID" in os.environ,
    "VERCEL" in os.environ,
    "RENDER" in os.environ
]

if any(deployment_indicators):
    st.write("✅ Running in deployment environment")
    if "STREAMLIT_CLOUD" in os.environ:
        st.write("Platform: Streamlit Cloud")
    elif "HEROKU_APP_NAME" in os.environ:
        st.write(f"Platform: Heroku ({os.environ.get('HEROKU_APP_NAME')})")
    elif "RAILWAY_PROJECT_ID" in os.environ:
        st.write("Platform: Railway")
    elif "VERCEL" in os.environ:
        st.write("Platform: Vercel")
    elif "RENDER" in os.environ:
        st.write("Platform: Render")
else:
    st.write("ℹ️ Running locally (not in deployment)")

st.header("Next Steps")
st.write("""
Based on the results above:

1. **If environment variables are not set**: Configure them in your deployment platform
2. **If MongoDB connection fails**: Check MongoDB Atlas network access settings
3. **If Google API fails**: Verify API key is correct and has proper permissions
4. **If secrets are not found**: Update your secrets configuration

See `TROUBLESHOOTING.md` for detailed solutions.
""")
