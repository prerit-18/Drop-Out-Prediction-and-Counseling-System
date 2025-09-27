from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
import os
import uuid
try:
    import google.generativeai as genai
except Exception:
    genai = None
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Diagnostics for Gemini initialization
GEMINI_LAST_ERROR: str | None = None
GEMINI_TRIED_MODELS: list[str] = []

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

# In-memory chatbot sessions
CHAT_SESSIONS = {}
# Offline chatbot conversations store
OFFLINE_CONVERSATIONS = {}
SYSTEM_PROMPT = (
    "You are a helpful student counselor. Provide empathetic and practical advice for academic stress, family pressure, and dropout prevention."
)

def get_gemini_model():
    global GEMINI_TRIED_MODELS, GEMINI_LAST_ERROR
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key or genai is None:
        print("Gemini not configured: missing GOOGLE_API_KEY or google-generativeai package.")
        GEMINI_LAST_ERROR = "Missing GOOGLE_API_KEY or google-generativeai package"
        return None
    try:
        genai.configure(api_key=api_key)
        # Allow override via env
        preferred = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        candidates = [preferred, "gemini-1.5-flash", "gemini-1.5-flash-8b"]
        last_err = None
        GEMINI_TRIED_MODELS = []
        for name in candidates:
            if not name:
                continue
            try:
                print(f"Trying Gemini model: {name}")
                GEMINI_TRIED_MODELS.append(name)
                return genai.GenerativeModel(name)
            except Exception as e:
                last_err = e
                GEMINI_TRIED_MODELS.append(name)
                continue
        print(f"Failed to initialize Gemini model. Last error: {last_err}")
        GEMINI_LAST_ERROR = str(last_err) if last_err else None
        return None
    except Exception as e:
        print(f"Gemini configuration error: {e}")
        GEMINI_LAST_ERROR = str(e)
        return None

def _offline_get_or_create_session(session_id: str | None) -> str:
    if not session_id:
        session_id = str(uuid.uuid4())
    if session_id not in OFFLINE_CONVERSATIONS:
        OFFLINE_CONVERSATIONS[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return session_id

def rule_based_reply(user_message: str) -> str:
    m = (user_message or "").lower()
    if any(k in m for k in ("stress", "stressed", "anxious", "anxiety")):
        return (
            "I'm sorry you're feeling stressed. Try short study bursts (25–30 mins), take regular breaks, hydrate, and get good sleep. I can help make a simple schedule." )
    if any(k in m for k in ("exam", "exams", "test")):
        return (
            "Exams can be overwhelming. Break your syllabus into small chunks and review daily. Would you like a revision plan template?" )
    if any(k in m for k in ("family", "parents", "home")):
        return (
            "Family pressure is tough. If it’s safe, try a calm conversation about your goals. We can outline talking points together, or you can book a counselor session." )
    if any(k in m for k in ("career", "job", "future")):
        return (
            "Explore interests through small projects and short courses. Tell me a subject you enjoy and I can suggest a next step." )
    if any(k in m for k in ("suicide", "hurt myself", "kill myself", "die by")):
        return (
            "I'm really sorry you're feeling this way. I'm not a replacement for emergency help. If you are in immediate danger, please contact local emergency services or a crisis hotline now. I can share resources for your country if you’d like." )
    return "Thanks for sharing. Could you tell me a bit more so I can help better?"

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

@app.route('/ai_health')
def ai_health():
    api_key_present = bool(os.getenv("GOOGLE_API_KEY", ""))
    package_present = genai is not None
    # Try a lightweight init without generating content
    test_model = get_gemini_model()
    configured = test_model is not None
    return jsonify({
        "configured": configured,
        "api_key_present": api_key_present,
        "package_present": package_present,
        "tried_models": GEMINI_TRIED_MODELS,
        "last_error": GEMINI_LAST_ERROR
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

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        message = (data.get('message') or '').strip()
        if not session_id or not message:
            return jsonify({
                "error": "session_id and message are required",
                "status": "error"
            }), 400

        if session_id not in CHAT_SESSIONS:
            CHAT_SESSIONS[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        CHAT_SESSIONS[session_id].append({"role": "user", "content": message})

        model = get_gemini_model()
        if model is None:
            assistant_text = (
                "I'm currently unavailable because the AI service isn't configured. "
                "Please ask an admin to set GOOGLE_API_KEY (and optionally GEMINI_MODEL). "
                "Meanwhile, try deep breathing, break tasks into small steps, and reach out to your counselor if stress persists."
            )
        else:
            # Build prompt from history
            history = CHAT_SESSIONS[session_id]
            lines = []
            for turn in history:
                role = turn.get('role')
                content = turn.get('content', '')
                if role == 'system':
                    lines.append(f"System: {content}")
                elif role == 'user':
                    lines.append(f"User: {content}")
                else:
                    lines.append(f"Assistant: {content}")
            lines.append(f"User: {message}")
            prompt = "\n".join(lines)
            try:
                resp = model.generate_content(prompt)
                assistant_text = resp.text if hasattr(resp, 'text') else str(resp)
            except Exception:
                assistant_text = "I couldn't respond right now. Please try again in a moment."

        CHAT_SESSIONS[session_id].append({"role": "assistant", "content": assistant_text})
        return jsonify({
            "reply": assistant_text,
            "history": CHAT_SESSIONS[session_id][-20:],
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": f"Chat failed: {str(e)}",
            "status": "error"
        }), 500

@app.route('/chat_offline', methods=['POST'])
def chat_offline():
    try:
        data = request.get_json(force=True) or {}
        session_id = data.get('session_id')
        message = (data.get('message') or '').strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400

        session_id = _offline_get_or_create_session(session_id)
        history = OFFLINE_CONVERSATIONS[session_id]

        # Append user message
        history.append({"role": "user", "content": message})

        # Strictly offline response
        assistant_text = rule_based_reply(message)

        history.append({"role": "assistant", "content": assistant_text})
        return jsonify({
            "session_id": session_id,
            "reply": assistant_text,
            "history": history[-30:]
        })
    except Exception as e:
        return jsonify({"error": f"Chat offline failed: {str(e)}"}), 500

@app.route('/reset_offline_session', methods=['POST'])
def reset_offline_session():
    try:
        data = request.get_json(force=True) or {}
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id required"}), 400
        OFFLINE_CONVERSATIONS.pop(session_id, None)
        return jsonify({"status": "reset", "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=True, host='0.0.0.0', port=port)
