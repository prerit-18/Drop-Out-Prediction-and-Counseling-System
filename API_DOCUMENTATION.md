# Student Dropout Prediction API Documentation

## 🚀 Overview

This Flask API provides machine learning-based predictions for student dropout risk using a trained Random Forest model. The API can predict individual student outcomes or process batch predictions for multiple students.

## 📊 Model Performance

- **Training Accuracy**: 89.21%
- **Test Accuracy**: 77.40%
- **Model Type**: Random Forest Classifier
- **Classes**: Dropout, Enrolled, Graduate

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Required packages (see requirements.txt)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install Flask Flask-CORS pandas numpy scikit-learn
```

### Running the API
```bash
python app.py
```

The API will start on `http://localhost:5001`

## 📡 API Endpoints

### 1. Health Check
**GET** `/health`

Returns the API health status and model loading status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### 2. Get Features
**GET** `/features`

Returns the list of required features and their descriptions.

**Response:**
```json
{
  "features": ["marital_status", "application_mode", ...],
  "feature_descriptions": {
    "marital_status": "Marital status",
    "application_mode": "Application mode",
    ...
  }
}
```

### 3. Single Prediction
**POST** `/predict`

Predicts dropout risk for a single student.

**Request Body:**
```json
{
  "marital_status": 1,
  "application_mode": 1,
  "course": 1,
  "daytime_evening_attendance": 1,
  "previous_qualification": 1,
  "nationality": 1,
  "mother_qualification": 1,
  "father_qualification": 1,
  "mother_occupation": 1,
  "father_occupation": 1,
  "displaced": 0,
  "educational_special_needs": 0,
  "debtor": 0,
  "tuition_fees_up_to_date": 1,
  "gender": 1,
  "scholarship_holder": 0,
  "age_at_enrollment": 20,
  "international": 0,
  "curricular_units_1st_sem_credited": 0,
  "curricular_units_1st_sem_enrolled": 0,
  "curricular_units_1st_sem_evaluations": 0,
  "curricular_units_1st_sem_approved": 0,
  "curricular_units_1st_sem_grade": 0,
  "curricular_units_2nd_sem_credited": 0,
  "curricular_units_2nd_sem_enrolled": 0,
  "curricular_units_2nd_sem_evaluations": 0,
  "curricular_units_2nd_sem_approved": 0,
  "curricular_units_2nd_sem_grade": 0,
  "unemployment_rate": 10.8,
  "inflation_rate": 1.4,
  "gdp": 1.74
}
```

**Response:**
```json
{
  "prediction": "Dropout",
  "probabilities": {
    "Dropout": 0.40,
    "Enrolled": 0.35,
    "Graduate": 0.25
  },
  "risk_level": "Low",
  "confidence": 0.40,
  "status": "success"
}
```

### 4. Batch Prediction
**POST** `/predict_batch`

Predicts dropout risk for multiple students.

**Request Body:**
```json
{
  "students": [
    {
      "marital_status": 1,
      "application_mode": 1,
      // ... all required features
    },
    {
      "marital_status": 2,
      "application_mode": 1,
      // ... all required features
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "index": 0,
      "prediction": "Dropout",
      "probabilities": {...},
      "risk_level": "Low",
      "confidence": 0.40,
      "status": "success"
    }
  ],
  "total_processed": 2,
  "successful": 2,
  "failed": 0,
  "status": "success"
}
```

## 📋 Feature Descriptions

| Feature | Description | Type | Values |
|---------|-------------|------|--------|
| marital_status | Marital status | Integer | 1-6 |
| application_mode | Application method | Integer | 1-18 |
| course | Course taken | Integer | 1-17 |
| daytime_evening_attendance | Attendance time | Integer | 0-1 |
| previous_qualification | Previous education | Integer | 1-17 |
| nationality | Student nationality | Integer | 1-21 |
| mother_qualification | Mother's education | Integer | 1-34 |
| father_qualification | Father's education | Integer | 1-34 |
| mother_occupation | Mother's occupation | Integer | 1-46 |
| father_occupation | Father's occupation | Integer | 1-46 |
| displaced | Displaced person | Integer | 0-1 |
| educational_special_needs | Special needs | Integer | 0-1 |
| debtor | Debt status | Integer | 0-1 |
| tuition_fees_up_to_date | Fee payment status | Integer | 0-1 |
| gender | Student gender | Integer | 0-1 |
| scholarship_holder | Scholarship status | Integer | 0-1 |
| age_at_enrollment | Age at enrollment | Integer | 17-70 |
| international | International student | Integer | 0-1 |
| curricular_units_1st_sem_* | First semester units | Integer | 0+ |
| curricular_units_2nd_sem_* | Second semester units | Integer | 0+ |
| unemployment_rate | Unemployment rate % | Float | 0-30 |
| inflation_rate | Inflation rate % | Float | -2-5 |
| gdp | GDP | Float | 0-5 |

## 🎯 Risk Levels

- **Low Risk**: Dropout probability < 30%
- **Medium Risk**: Dropout probability 30-70%
- **High Risk**: Dropout probability > 70%

## 🔍 Example Usage

### Python Example
```python
import requests

# Single prediction
url = "http://localhost:5001/predict"
data = {
    "marital_status": 1,
    "application_mode": 1,
    "course": 1,
    # ... all required features
}

response = requests.post(url, json=data)
result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Risk Level: {result['risk_level']}")
```

### cURL Example
```bash
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "marital_status": 1,
    "application_mode": 1,
    "course": 1,
    "daytime_evening_attendance": 1,
    "previous_qualification": 1,
    "nationality": 1,
    "mother_qualification": 1,
    "father_qualification": 1,
    "mother_occupation": 1,
    "father_occupation": 1,
    "displaced": 0,
    "educational_special_needs": 0,
    "debtor": 0,
    "tuition_fees_up_to_date": 1,
    "gender": 1,
    "scholarship_holder": 0,
    "age_at_enrollment": 20,
    "international": 0,
    "curricular_units_1st_sem_credited": 0,
    "curricular_units_1st_sem_enrolled": 0,
    "curricular_units_1st_sem_evaluations": 0,
    "curricular_units_1st_sem_approved": 0,
    "curricular_units_1st_sem_grade": 0,
    "curricular_units_2nd_sem_credited": 0,
    "curricular_units_2nd_sem_enrolled": 0,
    "curricular_units_2nd_sem_evaluations": 0,
    "curricular_units_2nd_sem_approved": 0,
    "curricular_units_2nd_sem_grade": 0,
    "unemployment_rate": 10.8,
    "inflation_rate": 1.4,
    "gdp": 1.74
  }'
```

## 🧪 Testing

Run the test script to verify API functionality:
```bash
python test_api.py
```

## 📁 File Structure

```
├── app.py                    # Main Flask API
├── create_model.py          # Model training script
├── test_api.py              # API testing script
├── requirements.txt         # Python dependencies
├── random_forest_model.pkl  # Trained model
├── label_encoders.pkl       # Label encoders
├── feature_names.pkl        # Feature names
└── API_DOCUMENTATION.md     # This documentation
```

## ⚠️ Error Handling

The API returns appropriate HTTP status codes:
- **200**: Success
- **400**: Bad Request (missing features, invalid data)
- **500**: Internal Server Error (model issues, prediction errors)

Error responses include:
```json
{
  "error": "Error description",
  "status": "error"
}
```

## 🔧 Configuration

- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 5001
- **Debug Mode**: Enabled
- **CORS**: Enabled for all origins

## 📈 Model Performance Insights

The model shows strong performance with the following key insights:
- **Most Important Features**: Curricular units performance (approved, grade, evaluations)
- **Academic Performance**: Strong predictor of student success
- **Financial Factors**: Tuition payment status significantly impacts predictions
- **Demographics**: Age and course selection also influence outcomes

## 🚀 Production Deployment

For production deployment, consider:
1. Using a production WSGI server (Gunicorn, uWSGI)
2. Setting up proper logging
3. Implementing rate limiting
4. Adding authentication/authorization
5. Using environment variables for configuration
6. Setting up monitoring and health checks
