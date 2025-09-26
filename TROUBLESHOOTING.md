# 🚨 Deployment Troubleshooting Guide

## Common Deployment Issues & Solutions

### Issue 1: MongoDB Connection Fails in Deployment

**Symptoms:**
- App works locally but fails in deployment
- Error: "MongoDB connection failed: 127.0.0.1:27017"
- Error: "No MongoDB connection string found"

**Solutions:**

#### For Streamlit Cloud:
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Select your app
3. Click "Settings" → "Secrets"
4. Add these secrets:
```toml
[mongo]
uri = "mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"

[google]
api_key = "AIzaSyCwdTJtuHhD49OeKrsNZVz0OSKGlbRCLi8"
model = "gemini-2.5-flash"
```

#### For Heroku:
```bash
heroku config:set MONGODB_URI="mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
heroku config:set GOOGLE_API_KEY="AIzaSyCwdTJtuHhD49OeKrsNZVz0OSKGlbRCLi8"
heroku config:set GEMINI_MODEL="gemini-2.5-flash"
```

#### For Railway:
1. Go to Railway dashboard
2. Select your project
3. Go to "Variables" tab
4. Add:
```
MONGODB_URI=mongodb+srv://preritmehta77_db_user:mIP0oKJsTMEeIm5p@cluster1.iuexd8p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1
GOOGLE_API_KEY=AIzaSyCwdTJtuHhD49OeKrsNZVz0OSKGlbRCLi8
GEMINI_MODEL=gemini-2.5-flash
```

### Issue 2: API_BASE_URL Points to Localhost

**Problem:** Your deployed Streamlit app tries to connect to `http://localhost:5001` which doesn't exist in deployment.

**Solution:** Update the API_BASE_URL in project.py for production:

```python
# For production deployment, change this line:
API_BASE_URL = "http://localhost:5001"

# To your deployed Flask API URL, for example:
API_BASE_URL = "https://your-flask-api.herokuapp.com"
# or
API_BASE_URL = "https://your-flask-api.railway.app"
```

### Issue 3: MongoDB Atlas Network Access

**Problem:** MongoDB Atlas blocks connections from deployment platforms.

**Solution:**
1. Go to MongoDB Atlas → Network Access
2. Click "Add IP Address"
3. Add `0.0.0.0/0` (allows all IPs - less secure but works for testing)
4. Or add specific IP ranges for your deployment platform

### Issue 4: Environment Variables Not Loading

**Debug Steps:**
1. Add this debug code to your project.py:
```python
# Add this at the top of your project.py for debugging
import os
st.write("Environment Variables Debug:")
st.write(f"MONGODB_URI: {'✅ Set' if os.getenv('MONGODB_URI') else '❌ Not set'}")
st.write(f"GOOGLE_API_KEY: {'✅ Set' if os.getenv('GOOGLE_API_KEY') else '❌ Not set'}")
```

2. Deploy and check if variables are showing as "Set"

### Issue 5: Flask API Not Deployed

**Problem:** Only Streamlit is deployed, but Flask API is still running locally.

**Solutions:**

#### Option A: Deploy Flask API Separately
1. Deploy Flask API to Heroku/Railway/etc.
2. Update API_BASE_URL to point to deployed Flask API

#### Option B: Use Offline Mode
The app has offline chat functionality that doesn't require Flask API.

### Issue 6: Dependencies Missing

**Problem:** Deployment platform doesn't have required packages.

**Solution:** Ensure `requirements.txt` includes:
```
Flask>=2.0.0
Flask-CORS>=3.0.0
pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.0.0
pymongo>=4.0.0
dnspython>=2.0.0
streamlit>=1.24.0
plotly>=5.17.0
requests>=2.31.0
google-generativeai>=0.7.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
```

## 🔍 Quick Debug Checklist

- [ ] Environment variables set in deployment platform
- [ ] MongoDB Atlas allows connections from deployment IP
- [ ] API_BASE_URL points to correct deployed Flask API (if using Flask)
- [ ] All dependencies in requirements.txt
- [ ] Database user has proper permissions
- [ ] Connection string format is correct

## 🚀 Recommended Deployment Strategy

### For Streamlit Cloud (Easiest):
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Set secrets in Streamlit Cloud dashboard
4. Deploy

### For Full Stack (Streamlit + Flask):
1. Deploy Flask API to Heroku/Railway
2. Deploy Streamlit to Streamlit Cloud
3. Update API_BASE_URL in Streamlit app
4. Set environment variables in both deployments

## 📞 Need Help?

If you're still having issues, please share:
1. Which deployment platform you're using
2. The exact error message
3. Whether you've set environment variables
4. Your deployment URL (if public)
