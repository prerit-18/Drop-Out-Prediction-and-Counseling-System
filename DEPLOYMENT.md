# Deployment Configuration Guide

## MongoDB Atlas Configuration for Deployment

### For Streamlit Cloud Deployment

1. **Set Environment Variables in Streamlit Cloud:**
   - Go to your Streamlit Cloud dashboard
   - Navigate to your app settings
   - Add these environment variables:
     ```
     MONGODB_URI=mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1
     GOOGLE_API_KEY=AIzaSyCwdTJtuHhD49OeKrsNZVz0OSKGlbRCLi8
     GEMINI_MODEL=gemini-2.5-flash
     ```

2. **Update API_BASE_URL for Production:**
   - Change `API_BASE_URL = "http://localhost:5001"` to your deployed Flask API URL
   - Or deploy Flask API alongside Streamlit

### For Other Deployment Platforms

#### Heroku
```bash
heroku config:set MONGODB_URI="mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
heroku config:set GOOGLE_API_KEY="AIzaSyCwdTJtuHhD49OeKrsNZVz0OSKGlbRCLi8"
heroku config:set GEMINI_MODEL="gemini-2.5-flash"
```

#### Railway
Add to `railway.toml` or environment variables:
```
MONGODB_URI=mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1
GOOGLE_API_KEY=AIzaSyCwdTJtuHhD49OeKrsNZVz0OSKGlbRCLi8
GEMINI_MODEL=gemini-2.5-flash
```

#### Docker
Create `.env` file:
```
MONGODB_URI=mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1
GOOGLE_API_KEY=AIzaSyCwdTJtuHhD49OeKrsNZVz0OSKGlbRCLi8
GEMINI_MODEL=gemini-2.5-flash
```

### MongoDB Atlas Network Access

1. **Whitelist IP Addresses:**
   - Go to MongoDB Atlas → Network Access
   - Add `0.0.0.0/0` for all IPs (less secure but works for testing)
   - Or add specific deployment platform IP ranges

2. **Database User Permissions:**
   - Ensure `preritmehta77_db_user` has read/write access
   - Check user roles in MongoDB Atlas → Database Access

### Troubleshooting Deployment Issues

1. **Connection Timeout:**
   - Check network access settings in MongoDB Atlas
   - Verify connection string format
   - Ensure deployment platform can reach MongoDB Atlas

2. **Authentication Failed:**
   - Verify username/password in connection string
   - Check user permissions in MongoDB Atlas
   - Ensure user has proper database access

3. **Environment Variables Not Loading:**
   - Verify environment variables are set correctly
   - Check deployment platform documentation
   - Use `os.getenv()` to debug variable loading

### Testing Deployment

Test MongoDB connection in deployed environment:
```python
import os
from pymongo import MongoClient

# Test connection
uri = os.getenv("MONGODB_URI")
if uri:
    try:
        client = MongoClient(uri)
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
else:
    print("❌ MONGODB_URI environment variable not set")
```
