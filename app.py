from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the Random Forest model
def load_model():
    try:
        model_path = 'random_forest_model.pkl'
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file {model_path} not found")
        
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None

# Load model at startup
model = load_model()

# Feature mapping based on your dataset
FEATURE_MAPPING = {
    'marital_status': 'Marital status',
    'application_mode': 'Application mode',
    'course': 'Course',
    'daytime_evening_attendance': 'Daytime/evening attendance',
    'previous_qualification': 'Previous qualification',
    'nationality': 'Nacionality',
    'mother_qualification': 'Mother\'s qualification',
    'father_qualification': 'Father\'s qualification',
    'mother_occupation': 'Mother\'s occupation',
    'father_occupation': 'Father\'s occupation',
    'displaced': 'Displaced',
    'educational_special_needs': 'Educational special needs',
    'debtor': 'Debtor',
    'tuition_fees_up_to_date': 'Tuition fees up to date',
    'gender': 'Gender',
    'scholarship_holder': 'Scholarship holder',
    'age_at_enrollment': 'Age at enrollment',
    'international': 'International',
    'curricular_units_1st_sem_credited': 'Curricular units 1st sem (credited)',
    'curricular_units_1st_sem_enrolled': 'Curricular units 1st sem (enrolled)',
    'curricular_units_1st_sem_evaluations': 'Curricular units 1st sem (evaluations)',
    'curricular_units_1st_sem_approved': 'Curricular units 1st sem (approved)',
    'curricular_units_1st_sem_grade': 'Curricular units 1st sem (grade)',
    'curricular_units_2nd_sem_credited': 'Curricular units 2nd sem (credited)',
    'curricular_units_2nd_sem_enrolled': 'Curricular units 2nd sem (enrolled)',
    'curricular_units_2nd_sem_evaluations': 'Curricular units 2nd sem (evaluations)',
    'curricular_units_2nd_sem_approved': 'Curricular units 2nd sem (approved)',
    'curricular_units_2nd_sem_grade': 'Curricular units 2nd sem (grade)',
    'unemployment_rate': 'Unemployment rate',
    'inflation_rate': 'Inflation rate',
    'gdp': 'GDP'
}

@app.route('/')
def home():
    return jsonify({
        "message": "Student Dropout Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "/predict": "POST - Predict student dropout risk",
            "/health": "GET - Health check",
            "/features": "GET - Get required features list"
        }
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None
    })

@app.route('/features')
def get_features():
    return jsonify({
        "features": list(FEATURE_MAPPING.keys()),
        "feature_descriptions": FEATURE_MAPPING
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if model is None:
            return jsonify({
                "error": "Model not loaded",
                "status": "error"
            }), 500

        # Get input data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No input data provided",
                "status": "error"
            }), 400

        # Validate required features
        missing_features = []
        for feature in FEATURE_MAPPING.keys():
            if feature not in data:
                missing_features.append(feature)

        if missing_features:
            return jsonify({
                "error": f"Missing required features: {missing_features}",
                "status": "error"
            }), 400

        # Convert input to DataFrame
        input_data = {}
        for feature, column_name in FEATURE_MAPPING.items():
            input_data[column_name] = [data[feature]]

        df = pd.DataFrame(input_data)

        # Make prediction
        prediction = model.predict(df)
        prediction_proba = model.predict_proba(df)

        # Get prediction probabilities
        classes = model.classes_
        probabilities = {}
        for i, class_name in enumerate(classes):
            probabilities[str(class_name)] = float(prediction_proba[0][i])

        # Determine risk level
        risk_level = "Low"
        prediction_str = str(prediction[0])
        if prediction_str == "Dropout":
            dropout_prob = probabilities.get("Dropout", 0)
            if dropout_prob > 0.7:
                risk_level = "High"
            elif dropout_prob > 0.4:
                risk_level = "Medium"
        else:
            dropout_prob = probabilities.get("Dropout", 0)
            if dropout_prob > 0.3:
                risk_level = "Medium"

        return jsonify({
            "prediction": prediction[0],
            "probabilities": probabilities,
            "risk_level": risk_level,
            "confidence": float(max(prediction_proba[0])),
            "status": "success"
        })

    except Exception as e:
        return jsonify({
            "error": f"Prediction failed: {str(e)}",
            "status": "error"
        }), 500

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    try:
        if model is None:
            return jsonify({
                "error": "Model not loaded",
                "status": "error"
            }), 500

        # Get input data
        data = request.get_json()
        
        if not data or 'students' not in data:
            return jsonify({
                "error": "No students data provided",
                "status": "error"
            }), 400

        students = data['students']
        if not isinstance(students, list):
            return jsonify({
                "error": "Students data must be a list",
                "status": "error"
            }), 400

        results = []
        for i, student_data in enumerate(students):
            try:
                # Validate required features
                missing_features = []
                for feature in FEATURE_MAPPING.keys():
                    if feature not in student_data:
                        missing_features.append(feature)

                if missing_features:
                    results.append({
                        "index": i,
                        "error": f"Missing required features: {missing_features}",
                        "status": "error"
                    })
                    continue

                # Convert input to DataFrame
                input_data = {}
                for feature, column_name in FEATURE_MAPPING.items():
                    input_data[column_name] = [student_data[feature]]

                df = pd.DataFrame(input_data)

                # Make prediction
                prediction = model.predict(df)
                prediction_proba = model.predict_proba(df)

                # Get prediction probabilities
                classes = model.classes_
                probabilities = {}
                for j, class_name in enumerate(classes):
                    probabilities[str(class_name)] = float(prediction_proba[0][j])

                # Determine risk level
                risk_level = "Low"
                prediction_str = str(prediction[0])
                if prediction_str == "Dropout":
                    dropout_prob = probabilities.get("Dropout", 0)
                    if dropout_prob > 0.7:
                        risk_level = "High"
                    elif dropout_prob > 0.4:
                        risk_level = "Medium"
                else:
                    dropout_prob = probabilities.get("Dropout", 0)
                    if dropout_prob > 0.3:
                        risk_level = "Medium"

                results.append({
                    "index": i,
                    "prediction": prediction[0],
                    "probabilities": probabilities,
                    "risk_level": risk_level,
                    "confidence": float(max(prediction_proba[0])),
                    "status": "success"
                })

            except Exception as e:
                results.append({
                    "index": i,
                    "error": f"Prediction failed: {str(e)}",
                    "status": "error"
                })

        return jsonify({
            "results": results,
            "total_processed": len(students),
            "successful": len([r for r in results if r.get("status") == "success"]),
            "failed": len([r for r in results if r.get("status") == "error"]),
            "status": "success"
        })

    except Exception as e:
        return jsonify({
            "error": f"Batch prediction failed: {str(e)}",
            "status": "error"
        }), 500

if __name__ == '__main__':
    if model is None:
        print("Warning: Model could not be loaded. Please check if random_forest_model.pkl exists.")
    
    print("Starting Flask API server...")
    print("API Documentation:")
    print("- GET / : API information")
    print("- GET /health : Health check")
    print("- GET /features : Get required features")
    print("- POST /predict : Single prediction")
    print("- POST /predict_batch : Batch prediction")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
