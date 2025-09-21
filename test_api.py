import requests
import json

# Test data based on your dataset structure
test_student = {
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

def test_api():
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Flask API...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test features endpoint
    try:
        response = requests.get(f"{base_url}/features")
        print(f"✅ Features endpoint: {response.status_code}")
        features = response.json()
        print(f"   Available features: {len(features['features'])}")
    except Exception as e:
        print(f"❌ Features endpoint failed: {e}")
    
    # Test single prediction
    try:
        response = requests.post(f"{base_url}/predict", json=test_student)
        print(f"✅ Single prediction: {response.status_code}")
        result = response.json()
        print(f"   Prediction: {result.get('prediction', 'N/A')}")
        print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A'):.2f}")
    except Exception as e:
        print(f"❌ Single prediction failed: {e}")
    
    # Test batch prediction
    try:
        batch_data = {"students": [test_student, test_student]}
        response = requests.post(f"{base_url}/predict_batch", json=batch_data)
        print(f"✅ Batch prediction: {response.status_code}")
        result = response.json()
        print(f"   Processed: {result.get('total_processed', 0)}")
        print(f"   Successful: {result.get('successful', 0)}")
        print(f"   Failed: {result.get('failed', 0)}")
    except Exception as e:
        print(f"❌ Batch prediction failed: {e}")

if __name__ == "__main__":
    test_api()
