# 🎓 AI-Based Student Dropout Prediction & Counseling System

A comprehensive system that combines Streamlit dashboards with Flask API for student dropout prediction and counseling management.

## 🚀 Features

### 📊 Streamlit Dashboards
- **Counselor Dashboard**: Student management, search, contact functionality, and analytics
- **Student Dashboard**: Personal information viewing for students
- **AI Predictions**: Machine learning-powered dropout risk prediction
- **About**: System documentation and field descriptions

### 🤖 Flask API
- **Single Prediction**: Predict individual student dropout risk
- **Batch Prediction**: Process multiple students from CSV files
- **Health Monitoring**: API status and model loading checks
- **RESTful Interface**: Easy integration with other systems

### 🗄️ MongoDB Integration
- **High-Risk Student Storage**: Automatically saves students with dropout probability >= 70%
- **Real-time Database Monitoring**: Connection status and student count tracking
- **Data Export**: Export high-risk student data for analysis
- **Historical Tracking**: Track prediction history and trends

## 📁 Project Structure

```
├── project.py                    # Main Streamlit application
├── app.py                       # Flask API server
├── create_model.py              # Model training script
├── test_api.py                  # API testing script
├── setup_mongodb.py             # MongoDB setup script
├── mongodb_config.py            # MongoDB configuration
├── requirements.txt             # Python dependencies
├── random_forest_model.pkl      # Trained ML model
├── sample_students.csv          # Sample data for testing
├── dataset.csv                  # Main dataset
├── counselling_table.xlsx       # Counseling data
├── API_DOCUMENTATION.md         # API documentation
└── README.md                    # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip or conda
- MongoDB (local or cloud)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup MongoDB
#### Option A: Local MongoDB
```bash
# Install MongoDB locally
# macOS: brew install mongodb-community
# Ubuntu: sudo apt-get install mongodb
# Windows: Download from MongoDB website

# Start MongoDB service
# macOS: brew services start mongodb-community
# Ubuntu: sudo systemctl start mongod
# Windows: Start MongoDB service from Services
```

#### Option B: MongoDB Atlas (Cloud)
1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a cluster
3. Get your connection string
4. Set environment variable:
```bash
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
```

#### Option C: Docker MongoDB
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. Setup MongoDB Database
```bash
python setup_mongodb.py
```

### 4. Start Flask API Server
```bash
python app.py
```
The API will be available at `http://localhost:5001`

### 5. Start Streamlit Application
```bash
streamlit run project.py
```
The web app will be available at `http://localhost:8501`

## 🎯 Usage

### Single Student Prediction
1. Navigate to "AI Predictions" in the sidebar
2. Select "Single Student Prediction" tab
3. Fill in the student information form
4. Click "🔮 Predict Dropout Risk"
5. View prediction results, risk level, and probabilities

### CSV Batch Prediction
1. Navigate to "AI Predictions" in the sidebar
2. Select "CSV Batch Prediction" tab
3. Upload a CSV file with student data
4. Click "🔮 Predict All Students"
5. Download results as CSV

### Counselor Dashboard
1. Navigate to "Counselor Dashboard"
2. View student metrics and analytics
3. Search for individual students
4. Use "Contact Student" for communication
5. Schedule meetings and interventions

### Student Dashboard
1. Navigate to "Student Dashboard"
2. Enter Student ID to view personal information
3. Check academic performance and financial status

## 📊 Model Performance

- **Training Accuracy**: 89.21%
- **Test Accuracy**: 77.40%
- **Model Type**: Random Forest Classifier
- **Features**: 31 student attributes
- **Classes**: Dropout, Enrolled, Graduate

## 🔧 API Endpoints

### Health Check
```
GET /health
```

### Single Prediction
```
POST /predict
Content-Type: application/json

{
  "marital_status": 1,
  "application_mode": 1,
  "course": 1,
  // ... all required features
}
```

### Batch Prediction
```
POST /predict_batch
Content-Type: application/json

{
  "students": [
    { "marital_status": 1, ... },
    { "marital_status": 2, ... }
  ]
}
```

## 📋 Required CSV Columns

For batch prediction, ensure your CSV file contains these columns:

- Marital status
- Application mode
- Course
- Daytime/evening attendance
- Previous qualification
- Nacionality
- Mother's qualification
- Father's qualification
- Mother's occupation
- Father's occupation
- Displaced
- Educational special needs
- Debtor
- Tuition fees up to date
- Gender
- Scholarship holder
- Age at enrollment
- International
- Curricular units 1st sem (credited)
- Curricular units 1st sem (enrolled)
- Curricular units 1st sem (evaluations)
- Curricular units 1st sem (approved)
- Curricular units 1st sem (grade)
- Curricular units 2nd sem (credited)
- Curricular units 2nd sem (enrolled)
- Curricular units 2nd sem (evaluations)
- Curricular units 2nd sem (approved)
- Curricular units 2nd sem (grade)
- Unemployment rate
- Inflation rate
- GDP

## 🎨 Features Overview

### AI Predictions Page
- **Single Student Form**: Interactive form with all required fields
- **CSV Upload**: Drag-and-drop file upload with validation
- **Batch Processing**: Process multiple students simultaneously
- **Results Download**: Export predictions as CSV
- **Analytics**: Visual analysis of prediction patterns

### Counselor Dashboard
- **Student Search**: Find students by ID
- **Contact Management**: Generate contact information
- **Meeting Scheduling**: Plan interventions
- **Analytics Charts**: Visualize student data patterns

### Student Dashboard
- **Personal Info**: View academic and personal details
- **Performance Tracking**: Monitor academic progress
- **Risk Assessment**: Understand current status

## 🔍 Risk Assessment

The system categorizes students into three risk levels:

- **Low Risk**: Dropout probability < 30%
- **Medium Risk**: Dropout probability 30-70%
- **High Risk**: Dropout probability > 70%

## 🚀 Quick Start

1. **Clone/Download** the project files
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Start API**: `python app.py` (in terminal 1)
4. **Start App**: `streamlit run project.py` (in terminal 2)
5. **Open browser**: Navigate to `http://localhost:8501`
6. **Test predictions**: Use the "AI Predictions" page

## 🧪 Testing

### Test API Connection
```bash
python test_api.py
```

### Test with Sample Data
Use the provided `sample_students.csv` file for testing batch predictions.

## 📈 Analytics Features

- **Prediction Distribution**: Pie chart of outcomes
- **Risk Level Analysis**: Bar chart of risk categories
- **Confidence Distribution**: Histogram of prediction confidence
- **Summary Statistics**: Key metrics and counts

## 🔧 Configuration

### API Settings
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 5001
- **Debug Mode**: Enabled
- **CORS**: Enabled for all origins

### Streamlit Settings
- **Page Title**: Student Dropout Prediction & Counseling System
- **Layout**: Wide
- **Theme**: Default

## 🛡️ Error Handling

The system includes comprehensive error handling for:
- API connection issues
- Missing CSV columns
- Invalid data formats
- Model prediction errors
- File upload problems

## 📞 Support

For issues or questions:
1. Check the API status indicator in the sidebar
2. Ensure Flask API is running (`python app.py`)
3. Verify CSV file format matches requirements
4. Check console logs for detailed error messages

## 🎯 Use Cases

- **Educational Institutions**: Monitor student success and intervene early
- **Counselors**: Identify at-risk students and plan interventions
- **Students**: Self-monitor academic progress and risk factors
- **Administrators**: Analyze patterns and improve retention strategies

## 🔮 Future Enhancements

- Real-time data integration
- Advanced analytics dashboard
- Email notifications for high-risk students
- Integration with student information systems
- Mobile app development
- Multi-language support

---

**Built with ❤️ using Streamlit, Flask, and Scikit-learn**
