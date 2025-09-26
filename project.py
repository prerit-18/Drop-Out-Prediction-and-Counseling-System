import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import io
from pymongo import MongoClient
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="Student Dropout Prediction & Counseling System",
    page_icon="🎓",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    try:
        counselling_data = pd.read_excel("counselling_table.xlsx", engine="openpyxl")
        student_data = pd.read_csv("dataset.csv")
        
        # Create unique Student ID using row index (0-based)
        student_data['Student_ID'] = range(1, len(student_data) + 1)
        counselling_data['Student_ID'] = range(1, len(counselling_data) + 1)
        
        # Set Student_ID as index for both datasets
        student_data.set_index('Student_ID', inplace=True)
        counselling_data.set_index('Student_ID', inplace=True)
        
        return counselling_data, student_data
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None, None

counselling_data, student_data = load_data()

if counselling_data is None or student_data is None:
    st.stop()

# API Configuration
API_BASE_URL = "http://localhost:5001"

# MongoDB Configuration (secrets > env > localhost)
try:
    _secret_uri = None
    if hasattr(st, "secrets"):
        _secret_uri = st.secrets.get("MONGODB_URI")
except Exception:
    _secret_uri = None
MONGODB_URI = (
    _secret_uri
    or os.getenv("MONGODB_URI")
    or "mongodb://127.0.0.1:27017/"
)
DATABASE_NAME = "student_dropout_db"
COLLECTION_NAME = "high_risk_students"
MOOD_COLLECTION_NAME = "student_moods"

# MongoDB Connection Functions
@st.cache_resource(ttl=10)
def get_mongodb_connection():
    """Get MongoDB connection with retries and localhost fallback."""
    import time

    candidate_uris = []
    # Prefer explicit env override first
    if MONGODB_URI:
        candidate_uris.append(MONGODB_URI)
    # Fallbacks to avoid IPv6/hosts issues
    if "mongodb://127.0.0.1:27017/" not in candidate_uris:
        candidate_uris.append("mongodb://127.0.0.1:27017/")
    if "mongodb://localhost:27017/" not in candidate_uris:
        candidate_uris.append("mongodb://localhost:27017/")

    last_error = None
    for uri in candidate_uris:
        for attempt in range(1, 6):
            try:
                client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=3000,
                    connectTimeoutMS=3000,
                    socketTimeoutMS=3000,
                )
                client.admin.command('ping')
                return client
            except Exception as e:
                last_error = e
                time.sleep(0.6)

    st.error(f"❌ MongoDB connection failed: {str(last_error)}")
    return None

def save_student_to_database(student_data, prediction_result):
    """Save student data to MongoDB"""
    try:
        client = get_mongodb_connection()
        if client is None:
            return False, "MongoDB connection failed"
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Prepare document for MongoDB
        document = {
            "student_id": student_data.get("student_id", "unknown"),
            "prediction_data": student_data,
            "prediction_result": prediction_result,
            "dropout_probability": prediction_result.get("probabilities", {}).get("Dropout", 0),
            "risk_level": prediction_result.get("risk_level", "Unknown"),
            "confidence": prediction_result.get("confidence", 0),
            "timestamp": datetime.now(),
            "created_at": datetime.now().isoformat()
        }
        
        # Insert document
        result = collection.insert_one(document)
        
        if result.inserted_id:
            return True, f"Student saved successfully with ID: {result.inserted_id}"
        else:
            return False, "Failed to save student data"
            
    except Exception as e:
        return False, f"Error saving to MongoDB: {str(e)}"

def save_mood_entry(student_id, mood, stress_level, sleep_hours, notes=None):
    """Save a student's mood entry to MongoDB"""
    try:
        client = get_mongodb_connection()
        if client is None:
            return False, "MongoDB connection failed"

        db = client[DATABASE_NAME]
        collection = db[MOOD_COLLECTION_NAME]

        entry = {
            "student_id": student_id,
            "mood": mood,  # e.g., Very Happy, Happy, Neutral, Sad, Very Sad
            "stress_level": stress_level,  # 0-10
            "sleep_hours": sleep_hours,  # numeric
            "notes": notes or "",
            "timestamp": datetime.now(),
            "created_at": datetime.now().isoformat()
        }

        result = collection.insert_one(entry)
        if result.inserted_id:
            return True, f"Mood saved with ID: {result.inserted_id}"
        return False, "Failed to save mood entry"
    except Exception as e:
        return False, f"Error saving mood entry: {str(e)}"

def get_recent_mood_entries(student_id=None, limit=30):
    """Fetch recent mood entries, optionally filtered by student_id"""
    try:
        client = get_mongodb_connection()
        if client is None:
            return []

        db = client[DATABASE_NAME]
        collection = db[MOOD_COLLECTION_NAME]

        query = {"student_id": student_id} if student_id else {}
        entries = list(collection.find(query).sort("timestamp", -1).limit(limit))
        return entries
    except Exception:
        return []

def get_students_count():
    """Get count of students in database"""
    try:
        client = get_mongodb_connection()
        if client is None:
            return 0
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        count = collection.count_documents({})
        return count
        
    except Exception as e:
        st.error(f"❌ Error getting high-risk students count: {str(e)}")
        return 0

def get_recent_students(limit=10):
    """Get recent students from database"""
    try:
        client = get_mongodb_connection()
        if client is None:
            return []
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get all recent students
        students = list(collection.find(
            {}
        ).sort("timestamp", -1).limit(limit))
        
        return students
        
    except Exception as e:
        st.error(f"❌ Error getting recent high-risk students: {str(e)}")
        return []

def search_student_by_id(student_id):
    """Search for a student by ID in MongoDB"""
    try:
        client = get_mongodb_connection()
        if client is None:
            return None, "MongoDB connection failed"
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Search for student by student_id
        student = collection.find_one({"student_id": student_id})
        
        if student:
            return student, "Student found"
        else:
            return None, "Student not found"
            
    except Exception as e:
        return None, f"Error searching student: {str(e)}"

# API Connection Functions
@st.cache_data
def check_api_health():
    """Check if the Flask API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200, response.json()
    except:
        return False, None

def get_api_features():
    """Get required features from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/features", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def predict_single_student(student_data_dict):
    """Predict single student using API"""
    try:
        response = requests.post(f"{API_BASE_URL}/predict", 
                               json=student_data_dict, 
                               timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}", "status": "error"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}", "status": "error"}

def predict_batch_students(students_list):
    """Predict multiple students using API"""
    try:
        response = requests.post(f"{API_BASE_URL}/predict_batch", 
                               json={"students": students_list}, 
                               timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}", "status": "error"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}", "status": "error"}

def convert_student_to_api_format(student_row):
    """Convert student data to API format"""
    api_mapping = {
        'Marital status': 'marital_status',
        'Application mode': 'application_mode',
        'Course': 'course',
        'Daytime/evening attendance': 'daytime_evening_attendance',
        'Previous qualification': 'previous_qualification',
        'Nacionality': 'nationality',
        'Mother\'s qualification': 'mother_qualification',
        'Father\'s qualification': 'father_qualification',
        'Mother\'s occupation': 'mother_occupation',
        'Father\'s occupation': 'father_occupation',
        'Displaced': 'displaced',
        'Educational special needs': 'educational_special_needs',
        'Debtor': 'debtor',
        'Tuition fees up to date': 'tuition_fees_up_to_date',
        'Gender': 'gender',
        'Scholarship holder': 'scholarship_holder',
        'Age at enrollment': 'age_at_enrollment',
        'International': 'international',
        'Curricular units 1st sem (credited)': 'curricular_units_1st_sem_credited',
        'Curricular units 1st sem (enrolled)': 'curricular_units_1st_sem_enrolled',
        'Curricular units 1st sem (evaluations)': 'curricular_units_1st_sem_evaluations',
        'Curricular units 1st sem (approved)': 'curricular_units_1st_sem_approved',
        'Curricular units 1st sem (grade)': 'curricular_units_1st_sem_grade',
        'Curricular units 2nd sem (credited)': 'curricular_units_2nd_sem_credited',
        'Curricular units 2nd sem (enrolled)': 'curricular_units_2nd_sem_enrolled',
        'Curricular units 2nd sem (evaluations)': 'curricular_units_2nd_sem_evaluations',
        'Curricular units 2nd sem (approved)': 'curricular_units_2nd_sem_approved',
        'Curricular units 2nd sem (grade)': 'curricular_units_2nd_sem_grade',
        'Unemployment rate': 'unemployment_rate',
        'Inflation rate': 'inflation_rate',
        'GDP': 'gdp'
    }
    
    api_data = {}
    for col_name, api_name in api_mapping.items():
        if col_name in student_row:
            api_data[api_name] = student_row[col_name]
    
    return api_data

# Check API status
api_connected, api_info = check_api_health()

# Check MongoDB status
mongodb_client = get_mongodb_connection()
mongodb_connected = mongodb_client is not None

# Sidebar navigation
st.sidebar.title("🎓 Team Data Dynamos")


# Simplified top-level navigation
main_section = st.sidebar.selectbox("Choose Section", ["Counselor Section", "Student Section", "About"])

# Map to internal pages
if main_section == "Counselor Section":
    page = st.sidebar.radio("Counselor Pages", ["Counselor Dashboard", "Student Database", "AI Predictions"])
elif main_section == "Student Section":
    # Student sub-menu
    student_page = st.sidebar.radio("Student Pages", ["Mood Tracker", "Gemini Chatbot", "Offline Chatbot"])
    page = (
        "Student Mood Tracker" if student_page == "Mood Tracker" else
        "Student Chatbot" if student_page == "Gemini Chatbot" else
        "Offline Chatbot"
    )
else:
    page = "About"

# API Status Indicator
if api_connected:
    st.sidebar.success("🤖 AI API Connected")
    if api_info and api_info.get('model_loaded'):
        st.sidebar.success("✅ Model Loaded")
else:
    st.sidebar.error("❌ AI API Disconnected")
    st.sidebar.info("💡 Start Flask API: `python app.py`")

# MongoDB Status Indicator
if mongodb_connected:
    st.sidebar.success("🗄️ MongoDB Connected")
    students_count = get_students_count()
    st.sidebar.info(f"📊 Students in Database: {students_count}")
else:
    st.sidebar.error("❌ MongoDB Disconnected")
    st.sidebar.info("💡 Check MongoDB connection")

if page == "Counselor Dashboard":
    st.title("🎓 Counselor Dashboard")
    
    # Initialize session state for contact and meeting popups
    if 'show_contact' not in st.session_state:
        st.session_state.show_contact = False
    if 'show_meeting' not in st.session_state:
        st.session_state.show_meeting = False
    if 'student_found' not in st.session_state:
        st.session_state.student_found = False
    if 'student_info' not in st.session_state:
        st.session_state.student_info = None

    if not mongodb_connected:
        st.error("❌ MongoDB is not connected. Cannot access students database.")
        st.info("💡 Please check your MongoDB connection and try again.")
        st.stop()
    
    # Get students from MongoDB
    all_students = get_recent_students(100)
    
    if not all_students:
        st.info("ℹ️ No students found in the database.")
        st.write("Students will be automatically saved here when predictions are made.")
        st.stop()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", len(all_students))
    
    with col2:
        avg_dropout_prob = sum([s.get('dropout_probability', 0) for s in all_students]) / len(all_students)
        st.metric("Average Dropout Probability", f"{avg_dropout_prob:.1%}")
    
    with col3:
        high_risk_count = len([s for s in all_students if s.get('risk_level') == 'High'])
        st.metric("High Risk Students", high_risk_count)
    
    with col4:
        recent_count = len([s for s in all_students if s.get('created_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
        st.metric("Added Today", recent_count)
    
    st.divider()

    # Filters
    st.write("### Filters")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        risk_levels = ["All"] + list(set([s.get('risk_level', 'Unknown') for s in all_students]))
        selected_risk = st.selectbox("Filter by Risk Level", risk_levels)
    
    with col_filter2:
        predictions = ["All"] + list(set([s.get('prediction_result', {}).get('prediction', 'Unknown') for s in all_students]))
        selected_prediction = st.selectbox("Filter by Prediction", predictions)
    
    with col_filter3:
        min_probability = st.slider("Minimum Dropout Probability", 0.0, 1.0, 0.0, 0.01)
    
    # Apply filters
    filtered_students = all_students.copy()
    
    if selected_risk != "All":
        filtered_students = [s for s in filtered_students if s.get('risk_level') == selected_risk]
    
    if selected_prediction != "All":
        filtered_students = [s for s in filtered_students if s.get('prediction_result', {}).get('prediction') == selected_prediction]
    
    filtered_students = [s for s in filtered_students if s.get('dropout_probability', 0) >= min_probability]
    
    # Display filtered results
    st.write(f"### Students ({len(filtered_students)} found)")
    
    if filtered_students:
        # Prepare data for display
        display_data = []
        for student in filtered_students:
            prediction_data = student.get('prediction_data', {})
            display_data.append({
                'Student ID': student.get('student_id', 'N/A'),
                'Dropout Probability': f"{student.get('dropout_probability', 0):.2%}",
                'Risk Level': student.get('risk_level', 'N/A'),
                'Confidence': f"{student.get('confidence', 0):.2%}",
                'Prediction': student.get('prediction_result', {}).get('prediction', 'N/A'),
                'Course': prediction_data.get('course', 'N/A'),
                'Age': prediction_data.get('age_at_enrollment', 'N/A'),
                'Gender': 'Male' if prediction_data.get('gender') == 1 else 'Female' if prediction_data.get('gender') == 0 else 'N/A',
                'Created At': student.get('created_at', 'N/A')[:19] if student.get('created_at') else 'N/A'
            })
        
        if display_data:
            display_df = pd.DataFrame(display_data)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No students match the current filters.")
    else:
        st.info("No students found matching the current filters.")
    
    # Search functionality
    st.write("### Search Student")
    search_id = st.text_input("Enter Student ID")

    # Persist previously found student across reruns
    found_student = st.session_state.get('student_info', None)
    search_id_display = st.session_state.get('search_id', None)

    if st.button("Search Student") and search_id:
        found_student = None
        for student in all_students:
            if student.get('student_id') == search_id:
                found_student = student
                break
        
        if found_student:
            # Persist selection
            st.session_state.student_info = found_student
            st.session_state.student_found = True
            st.session_state.search_id = search_id
            search_id_display = search_id
            st.success(f"Student {search_id} found!")
            
            # Display detailed student information
            prediction_data = found_student.get('prediction_data', {})
            prediction_result = found_student.get('prediction_result', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Personal Information**")
                st.markdown(f"**Student ID:** {found_student.get('student_id', 'N/A')}")
                st.markdown(f"**Course:** {prediction_data.get('course', 'N/A')}")
                st.markdown(f"**Gender:** {'Male' if prediction_data.get('gender') == 1 else 'Female' if prediction_data.get('gender') == 0 else 'N/A'}")
                st.markdown(f"**Age at Enrollment:** {prediction_data.get('age_at_enrollment', 'N/A')}")
                st.markdown(f"**Marital Status:** {prediction_data.get('marital_status', 'N/A')}")
                st.markdown(f"**Nationality:** {prediction_data.get('nationality', 'N/A')}")
                st.markdown(f"**International:** {'Yes' if prediction_data.get('international') == 1 else 'No' if prediction_data.get('international') == 0 else 'N/A'}")
                st.markdown(f"**Scholarship Holder:** {'Yes' if prediction_data.get('scholarship_holder') == 1 else 'No' if prediction_data.get('scholarship_holder') == 0 else 'N/A'}")
            
            with col2:
                st.write("**Prediction Results**")
                st.markdown(f"**Dropout Probability:** {found_student.get('dropout_probability', 0):.2%}")
                st.markdown(f"**Risk Level:** {found_student.get('risk_level', 'N/A')}")
                st.markdown(f"**Confidence:** {found_student.get('confidence', 0):.2%}")
                st.markdown(f"**Prediction:** {prediction_result.get('prediction', 'N/A')}")
                st.markdown(f"**Created At:** {found_student.get('created_at', 'N/A')}")
                
                # Show probabilities
                probabilities = prediction_result.get('probabilities', {})
                if probabilities:
                    st.write("**Detailed Probabilities:**")
                    for outcome, prob in probabilities.items():
                        st.markdown(f"**{outcome}:** {prob:.2%}")
            
            # Risk assessment
            st.write("### Risk Assessment")
            dropout_prob = found_student.get('dropout_probability', 0)
            if dropout_prob >= 0.9:
                st.error("🚨 **CRITICAL RISK**: This student has an extremely high probability of dropping out. Immediate intervention required!")
            elif dropout_prob >= 0.8:
                st.error("🚨 **VERY HIGH RISK**: This student has a very high probability of dropping out. Urgent intervention needed!")
            elif dropout_prob >= 0.7:
                st.warning("⚠️ **HIGH RISK**: This student has a high probability of dropping out. Intervention recommended.")
            
            # Contact and action buttons
            st.write("### Actions")
            col_contact, col_meeting, col_export = st.columns(3)
            
            with col_contact:
                if st.button("📞 Contact Student", key="contact_btn"):
                    st.session_state.show_contact = True
                    st.session_state.student_found = True
                    st.session_state.student_info = found_student
                    st.rerun()
            
            with col_meeting:
                if st.button("📅 Schedule Meeting", key="meeting_btn"):
                    st.session_state.show_meeting = True
                    st.session_state.student_found = True
                    st.session_state.student_info = found_student
                    st.rerun()
            
            with col_export:
                if st.button("📥 Export Student Data", key="export_btn"):
                    # Create export data
                    export_data = {
                        'student_id': found_student.get('student_id'),
                        'dropout_probability': found_student.get('dropout_probability'),
                        'risk_level': found_student.get('risk_level'),
                        'confidence': found_student.get('confidence'),
                        'prediction': prediction_result.get('prediction'),
                        'created_at': found_student.get('created_at'),
                        **prediction_data
                    }
                    
                    export_df = pd.DataFrame([export_data])
                    csv = export_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Student Data",
                        data=csv,
                        file_name=f"high_risk_student_{(search_id_display or search_id or found_student.get('student_id','unknown'))}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            # Contact popup
            if st.session_state.get('show_contact', False):
                with st.container():
                    import random
                    st.markdown(f"""
                    <div style=\"background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0; border: 2px solid #1f77b4;\">
                        <h3 style=\"color: #1f77b4; margin-top: 0;\">📞 Contact Information</h3>
                        <p style=\"color: #000000; margin: 5px 0;\"><strong>Student Email:</strong> {(search_id_display or search_id or found_student.get('student_id','unknown'))}@university.edu</p>
                        <p style=\"color: #000000; margin: 5px 0;\"><strong>Student Phone:</strong> +1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}</p>
                        <p style=\"color: #000000; margin: 5px 0;\"><strong>Mother's Phone:</strong> +1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}</p>
                        <p style=\"color: #000000; margin: 5px 0;\"><strong>Father's Phone:</strong> +1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}</p>
                        <div style=\"margin-top: 15px;\">
                            <button style=\"background-color: #1f77b4; color: white; padding: 8px 16px; border: none; border-radius: 5px; margin-right: 10px;\">📧 Send Email</button>
                            <button style=\"background-color: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 5px; margin-right: 10px;\">📞 Call Now</button>
                            <button style=\"background-color: #ffc107; color: black; padding: 8px 16px; border: none; border-radius: 5px;\">📅 Schedule</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("❌ Close Contact Window", key="close_contact"):
                        st.session_state.show_contact = False

            # Meeting scheduling popup
            if st.session_state.get('show_meeting', False):
                with st.container():
                    st.markdown(f"""
                    <div style=\"background-color: #e8f5e8; padding: 20px; border-radius: 10px; margin: 10px 0; border: 2px solid #28a745;\">
                        <h3 style=\"color: #28a745; margin-top: 0;\">📅 Schedule Meeting</h3>
                        <p style=\"color: #000000; margin: 5px 0;\"><strong>Student:</strong> {(search_id_display or search_id or found_student.get('student_id','unknown'))}</p>
                        <p style=\"color: #000000; margin: 5px 0;\"><strong>Risk Level:</strong> {found_student.get('risk_level', 'N/A')}</p>
                        <p style=\"color: #000000; margin: 5px 0;\"><strong>Dropout Probability:</strong> {found_student.get('dropout_probability', 0):.1%}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Meeting form
                    with st.form("meeting_form"):
                        meeting_date = st.date_input("Select Meeting Date")
                        meeting_time = st.time_input("Select Meeting Time")
                        meeting_type = st.selectbox("Meeting Type", ["Academic Counseling", "Financial Aid Discussion", "General Support", "Emergency Intervention"])
                        notes = st.text_area("Meeting Notes", placeholder="Add any notes or agenda items...")
                        
                        submitted = st.form_submit_button("📅 Schedule Meeting")
                        
                        if submitted:
                            st.success(f"✅ Meeting scheduled for {meeting_date} at {meeting_time}!")
                            st.info(f"Meeting Type: {meeting_type}")
                            if notes:
                                st.info(f"Notes: {notes}")
                            st.session_state.show_meeting = False
                    
                    if st.button("❌ Cancel", key="cancel_meeting"):
                        st.session_state.show_meeting = False
        else:
            st.error(f"Student {search_id} not found in database!")
    
    # Analytics
    st.write("### Students Analytics")
    
    if all_students:
        # Risk Level Distribution
        risk_counts = {}
        for student in all_students:
            risk = student.get('risk_level', 'Unknown')
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        if risk_counts:
            fig_risk = px.pie(values=list(risk_counts.values()), names=list(risk_counts.keys()), 
                            title="Risk Level Distribution")
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Dropout Probability Distribution
        dropout_probs = [s.get('dropout_probability', 0) for s in all_students]
        fig_prob = px.histogram(x=dropout_probs, nbins=20, 
                               title="Dropout Probability Distribution",
                               labels={'x': 'Dropout Probability', 'count': 'Number of Students'})
        st.plotly_chart(fig_prob, use_container_width=True)
        
        # Course-wise Students
        course_counts = {}
        for student in all_students:
            course = student.get('prediction_data', {}).get('course', 'Unknown')
            course_counts[course] = course_counts.get(course, 0) + 1
        
        if course_counts:
            # Get top 10 courses
            top_courses = dict(sorted(course_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            fig_course = px.bar(x=list(top_courses.keys()), y=list(top_courses.values()),
                               title="Students by Course (Top 10)",
                               labels={'x': 'Course', 'y': 'Number of Students'})
            st.plotly_chart(fig_course, use_container_width=True)
        
        # Age Distribution of Students
        ages = []
        for student in all_students:
            age = student.get('prediction_data', {}).get('age_at_enrollment')
            if age is not None:
                ages.append(age)
        
        if ages:
            fig_age = px.histogram(x=ages, nbins=15, 
                                  title="Age Distribution of Students",
                                  labels={'x': 'Age at Enrollment', 'count': 'Number of Students'})
            st.plotly_chart(fig_age, use_container_width=True)
        
        # Time-based Analysis (if we have enough data)
        if len(all_students) > 5:
            # Group by creation date
            daily_counts = {}
            for student in all_students:
                created_at = student.get('created_at', '')
                if created_at:
                    date = created_at[:10]  # Get YYYY-MM-DD
                    daily_counts[date] = daily_counts.get(date, 0) + 1
            
            if daily_counts:
                dates = sorted(daily_counts.keys())
                counts = [daily_counts[date] for date in dates]
                fig_time = px.line(x=dates, y=counts, 
                                  title="Students Added Over Time",
                                  labels={'x': 'Date', 'y': 'Number of Students Added'})
                st.plotly_chart(fig_time, use_container_width=True)
        
        # Export all students
        st.write("### Export Data")
        if st.button("📥 Export All Students"):
            export_data = []
            for student in all_students:
                export_data.append({
                    'student_id': student.get('student_id', 'N/A'),
                    'dropout_probability': student.get('dropout_probability', 0),
                    'risk_level': student.get('risk_level', 'N/A'),
                    'confidence': student.get('confidence', 0),
                    'prediction': student.get('prediction_result', {}).get('prediction', 'N/A'),
                    'created_at': student.get('created_at', 'N/A'),
                    'course': student.get('prediction_data', {}).get('course', 'N/A'),
                    'age_at_enrollment': student.get('prediction_data', {}).get('age_at_enrollment', 'N/A'),
                    'gender': student.get('prediction_data', {}).get('gender', 'N/A'),
                    'marital_status': student.get('prediction_data', {}).get('marital_status', 'N/A'),
                    'nationality': student.get('prediction_data', {}).get('nationality', 'N/A')
                })
            
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download All Students CSV",
                data=csv,
                file_name=f"all_students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

elif page == "Student Database":
    st.title("👨‍🎓 Student Database")
    
    if not mongodb_connected:
        st.error("❌ MongoDB is not connected. Cannot access student database.")
        st.info("💡 Please check your MongoDB connection and try again.")
        st.stop()
    
    # Search functionality
    st.write("### Search Your Information")
    search_id = st.text_input("Enter Your Student ID")
    
    if st.button("Search My Information") and search_id:
        student, message = search_student_by_id(search_id)
        
        if student:
            st.success(f"✅ Welcome, Student {search_id}!")
            
            # Display comprehensive student information
            st.write("### Your Academic Profile")
            
            prediction_data = student.get("prediction_data", {})
            prediction_result = student.get("prediction_result", {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Personal Details:**")
                st.write(f"- **Student ID:** {student.get('student_id', 'N/A')}")
                st.write(f"- **Course:** {prediction_data.get('course', 'N/A')}")
                st.write(f"- **Gender:** {'Male' if prediction_data.get('gender') == 1 else 'Female' if prediction_data.get('gender') == 0 else 'N/A'}")
                st.write(f"- **Age at Enrollment:** {prediction_data.get('age_at_enrollment', 'N/A')}")
                st.write(f"- **Marital Status:** {prediction_data.get('marital_status', 'N/A')}")
                st.write(f"- **Nationality:** {prediction_data.get('nationality', 'N/A')}")
            
            with col2:
                st.write("**Academic Information:**")
                st.write(f"- **Prediction:** {prediction_result.get('prediction', 'N/A')}")
                st.write(f"- **Risk Level:** {student.get('risk_level', 'N/A')}")
                st.write(f"- **Dropout Probability:** {student.get('dropout_probability', 0):.1%}")
                st.write(f"- **Confidence:** {student.get('confidence', 0):.1%}")
                st.write(f"- **Application Mode:** {prediction_data.get('application_mode', 'N/A')}")
                st.write(f"- **Previous Qualification:** {prediction_data.get('previous_qualification', 'N/A')}")
            
            with col3:
                st.write("**Family Background:**")
                st.write(f"- **Mother's Qualification:** {prediction_data.get('mother_qualification', 'N/A')}")
                st.write(f"- **Father's Qualification:** {prediction_data.get('father_qualification', 'N/A')}")
                st.write(f"- **Mother's Occupation:** {prediction_data.get('mother_occupation', 'N/A')}")
                st.write(f"- **Father's Occupation:** {prediction_data.get('father_occupation', 'N/A')}")
                st.write(f"- **Scholarship Holder:** {'Yes' if prediction_data.get('scholarship_holder') == 1 else 'No' if prediction_data.get('scholarship_holder') == 0 else 'N/A'}")
                st.write(f"- **International:** {'Yes' if prediction_data.get('international') == 1 else 'No' if prediction_data.get('international') == 0 else 'N/A'}")
            
            # Academic Performance
            st.write("### Academic Performance")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Semester 1 Performance:**")
                st.write(f"- **Units Credited:** {prediction_data.get('curricular_units_1st_sem_credited', 'N/A')}")
                st.write(f"- **Units Enrolled:** {prediction_data.get('curricular_units_1st_sem_enrolled', 'N/A')}")
                st.write(f"- **Units Evaluated:** {prediction_data.get('curricular_units_1st_sem_evaluations', 'N/A')}")
                st.write(f"- **Units Approved:** {prediction_data.get('curricular_units_1st_sem_approved', 'N/A')}")
                st.write(f"- **Average Grade:** {prediction_data.get('curricular_units_1st_sem_grade', 'N/A')}")
            
            with col2:
                st.write("**Semester 2 Performance:**")
                st.write(f"- **Units Credited:** {prediction_data.get('curricular_units_2nd_sem_credited', 'N/A')}")
                st.write(f"- **Units Enrolled:** {prediction_data.get('curricular_units_2nd_sem_enrolled', 'N/A')}")
                st.write(f"- **Units Evaluated:** {prediction_data.get('curricular_units_2nd_sem_evaluations', 'N/A')}")
                st.write(f"- **Units Approved:** {prediction_data.get('curricular_units_2nd_sem_approved', 'N/A')}")
                st.write(f"- **Average Grade:** {prediction_data.get('curricular_units_2nd_sem_grade', 'N/A')}")
            
            # Financial Status
            st.write("### Financial Status")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"- **Debtor:** {'Yes' if prediction_data.get('debtor') == 1 else 'No' if prediction_data.get('debtor') == 0 else 'N/A'}")
                st.write(f"- **Tuition Fees Up to Date:** {'Yes' if prediction_data.get('tuition_fees_up_to_date') == 1 else 'No' if prediction_data.get('tuition_fees_up_to_date') == 0 else 'N/A'}")
            
            with col2:
                st.write(f"- **Displaced:** {'Yes' if prediction_data.get('displaced') == 1 else 'No' if prediction_data.get('displaced') == 0 else 'N/A'}")
                st.write(f"- **Educational Special Needs:** {'Yes' if prediction_data.get('educational_special_needs') == 1 else 'No' if prediction_data.get('educational_special_needs') == 0 else 'N/A'}")
            
            # Risk Assessment
            st.write("### Risk Assessment")
            risk_level = student.get("risk_level", "Unknown")
            dropout_prob = student.get("dropout_probability", 0)
            
            if risk_level == "High":
                st.error(f"🚨 **High Risk**: Dropout probability is {dropout_prob:.1%}. Immediate intervention recommended.")
            elif risk_level == "Medium":
                st.warning(f"⚠️ **Medium Risk**: Dropout probability is {dropout_prob:.1%}. Consider monitoring and support.")
            else:
                st.success(f"✅ **Low Risk**: Dropout probability is {dropout_prob:.1%}. You are likely to continue successfully.")
            
            # Recommendations
            st.write("### Recommendations")
            if risk_level == "High":
                st.info("📚 Consider meeting with academic counselor to discuss challenges and support options")
            if prediction_data.get("debtor") == 1 or prediction_data.get("tuition_fees_up_to_date") == 0:
                st.info("💳 Contact financial aid office to discuss payment options and available assistance")
            if prediction_data.get("educational_special_needs") == 1:
                st.info("🎓 Reach out to disability services for additional academic support")
            
            # Prediction Details
            st.write("### Prediction Details")
            if prediction_result.get("probabilities"):
                prob_df = pd.DataFrame([
                    {"Outcome": "Dropout", "Probability": f"{prediction_result['probabilities'].get('Dropout', 0):.1%}"},
                    {"Outcome": "Enrolled", "Probability": f"{prediction_result['probabilities'].get('Enrolled', 0):.1%}"},
                    {"Outcome": "Graduate", "Probability": f"{prediction_result['probabilities'].get('Graduate', 0):.1%}"}
                ])
                st.dataframe(prob_df, use_container_width=True)
            
            # Timestamp
            st.write(f"**Prediction Date:** {student.get('created_at', 'N/A')}")
            
        else:
            st.error(f"❌ {message}")
            st.info("💡 Make sure you have the correct Student ID. Students are added to the database when predictions are made.")

elif page == "About":
    st.title("📚 About the System")

    st.write("""
    ## Student Dropout Prediction & Counseling System

    This comprehensive system provides both counselor and student dashboards for managing academic success and dropout prevention.
    """)

    st.write("### System Features")

    col1, col2 = st.columns(2)

    with col1:
        st.write("""
        **🎓 Counselor Dashboard:**
        - View all students needing counseling
        - Search students by unique Student ID
        - Filter by counseling type and student status
        - Analytics and visualizations
        - Risk assessment tools
        """)

    with col2:
        st.write("""
        **👨‍🎓 Student Dashboard:**
        - Personal academic information
        - Academic performance tracking
        - Risk factor analysis
        - Counseling recommendations
        - Progress visualization
        """)

    st.write("### Dataset Information")
    st.write(f"""
    - **Total Students:** {len(student_data):,}
    - **Unique Student IDs:** 1 to {len(student_data)}
    - **Data Fields:** 35 different attributes per student
    """)

    st.write("### Future Updates")
    st.write(f"""
    - Real Counsellors
    - Chatbot
    - Achievement Badges
    - Different Counsellors Can be provided( Academic, Financial, Personal, Time Management)
    """)
    
    st.write("### Field Descriptions")
    st.write("Below is a comprehensive guide to all the fields in the dataset and their possible values:")
    
    # Display field descriptions table
    st.markdown("""
    | S/N | Field | Description | Categories Explained |
    | --- | --- | --- | --- |
    | 1 | Marital status | The marital status of the student. | 1—Single 2—Married 3—Widower 4—Divorced 5—Facto union 6—Legally separated |
    | 2 | Application mode | Method of application used by student | 1—1st phase—general contingent 2—Ordinance No. 612/93 3—1st phase—special contingent (Azores Island) 4—Holders of other higher courses 5—Ordinance No. 854-B/99 6—International student (bachelor) 7—1st phase—special contingent (Madeira Island) 8—2nd phase—general contingent 9—3rd phase—general contingent 10—Ordinance No. 533-A/99, item b2) (Different Plan) 11—Ordinance No. 533-A/99, item b3 (Other Institution) 12—Over 23 years old 13—Transfer 14—Change in course 15—Technological specialization diploma holders 16—Change in institution/course 17—Short cycle diploma holders 18—Change in institution/course (International) |
    | 3 | Application order | The order in which the student applied | |
    | 4 | Course | The course taken by the student | 1—Biofuel Production Technologies 2—Animation and Multimedia Design 3—Social Service (evening attendance) 4—Agronomy 5—Communication Design 6—Veterinary Nursing 7—Informatics Engineering 8—Equiniculture 9—Management 10—Social Service 11—Tourism 12—Nursing 13—Oral Hygiene 14—Advertising and Marketing Management 15—Journalism and Communication 16—Basic Education 17—Management (evening attendance) |
    | 5 | Daytime/evening attendance | Whether the student attends classes during the day or in the evening | 1—daytime 0—evening |
    | 6 | Previous qualification | The qualification obtained by the student before enrolling in higher education | 1—Secondary education 2—Higher education—bachelor's degree 3—Higher education—degree 4—Higher education—master's degree 5—Higher education—doctorate 6—Frequency of higher education 7—12th year of schooling—not completed 8—11th year of schooling—not completed 9—Other—11th year of schooling 10—10th year of schooling 11—10th year of schooling—not completed 12—Basic education 3rd cycle (9th/10th/11th year) or equivalent 13—Basic education 2nd cycle (6th/7th/8th year) or equivalent 14—Technological specialization course 15—Higher education—degree (1st cycle) 16—Professional higher technical course 17—Higher education—master's degree (2nd cycle) |
    | 7 | Nationality | The nationality of the student | 1—Portuguese 2—German 3—Spanish 4—Italian 5—Dutch 6—English 7—Lithuanian 8—Angolan 9—Cape Verdean 10—Guinean 11—Mozambican 12—Santomean 13—Turkish 14—Brazilian 15—Romanian 16—Moldova (Republic of) 17—Mexican 18—Ukrainian 19—Russian 20—Cuban 21—Colombian |
    | 8 | Mother's qualification / Father's qualification | The qualification of the student's mother and father | 1—Secondary Education—12th Year of Schooling or Equivalent 2—Higher Education—bachelor's degree 3—Higher Education—degree 4—Higher Education—master's degree 5—Higher Education—doctorate 6—Frequency of Higher Education 7—12th Year of Schooling—not completed 8—11th Year of Schooling—not completed 9—7th Year (Old) 10—Other—11th Year of Schooling 11—2nd year complementary high school course 12—10th Year of Schooling 13—General commerce course 14—Basic Education 3rd Cycle (9th/10th/11th Year) or Equivalent 15—Complementary High School Course 16—Technical-professional course 17—Complementary High School Course—not concluded 18—7th year of schooling 19—2nd cycle of the general high school course 20—9th Year of Schooling—not completed 21—8th year of schooling 22—General Course of Administration and Commerce 23—Supplementary Accounting and Administration 24—Unknown 25—Cannot read or write 26—Can read without having a 4th year of schooling 27—Basic education 1st cycle (4th/5th year) or equivalent 28—Basic Education 2nd Cycle (6th/7th/8th Year) or equivalent 29—Technological specialization course 30—Higher education—degree (1st cycle) 31—Specialized higher studies course 32—Professional higher technical course 33—Higher Education—master's degree (2nd cycle) 34—Higher Education—doctorate (3rd cycle) |
    | 9 | Mother's occupation / Father's occupation | The occupation of the student's Mother and Father | 1—Student 2—Representatives of the Legislative Power and Executive Bodies, Directors, Directors and Executive Managers 3—Specialists in Intellectual and Scientific Activities 4—Intermediate Level Technicians and Professions 5—Administrative staff 6—Personal Services, Security and Safety Workers, and Sellers 7—Farmers and Skilled Workers in Agriculture, Fisheries,and Forestry 8—Skilled Workers in Industry, Construction, and Craftsmen 9—Installation and Machine Operators and Assembly Workers 10—Unskilled Workers 11—Armed Forces Professions 12—Other Situation 13—(blank) 14—Armed Forces Officers 15—Armed Forces Sergeants 16—Other Armed Forces personnel 17—Directors of administrative and commercial services 18—Hotel, catering, trade, and other services directors 19—Specialists in the physical sciences, mathematics, engineering,and related techniques 20—Health professionals 21—Teachers 22—Specialists in finance, accounting, administrative organization,and public and commercial relations 23—Intermediate level science and engineering techniciansand professions 24—Technicians and professionals of intermediate level of health 25—Intermediate level technicians from legal, social, sports, cultural,and similar services 26—Information and communication technology technicians 27—Office workers, secretaries in general, and data processing operators 28—Data, accounting, statistical, financial services, and registry-related operators 29—Other administrative support staff 30—Personal service workers 31—Sellers 32—Personal care workers and the like 33—Protection and security services personnel 34—Market-oriented farmers and skilled agricultural and animal production workers 35—Farmers, livestock keepers, fishermen, hunters and gatherers,and subsistence 36—Skilled construction workers and the like, except electricians 37—Skilled workers in metallurgy, metalworking, and similar 38—Skilled workers in electricity and electronics 39—Workers in food processing, woodworking, and clothing and other industries and crafts 40—Fixed plant and machine operators 41—Assembly workers 42—Vehicle drivers and mobile equipment operators 43—Unskilled workers in agriculture, animal production, and fisheries and forestry 44—Unskilled workers in extractive industry, construction,manufacturing, and transport 45—Meal preparation assistants 46—Street vendors (except food) and street service providers |
    | 10 | Displaced | Whether the student is a displaced person | 1—yes 0—no |
    | 11 | Educational special needs | Whether the student has any special educational needs | 1—yes 0—no |
    | 12 | Debtor | Whether the student is a debtor or not | 1—yes 0—no |
    | 13 | Tuition fees up to date | Whether the student's tuition fees are up to date | 1—yes 0—no |
    | 14 | Gender | The gender of the student | 1—male 0—female |
    | 15 | Scholarship holder | Whether the student is a scholarship holder | 1—yes 0—no |
    | 16 | Age at enrollment | The age of the student at the time of enrollment | |
    | 17 | International | Whether the student is an international student | 1—yes 0—no |
    | 18 | Curricular units 1st & 2nd sem (credited) | The number of curricular units credited by the student in the first and second semester | |
    | 19 | Curricular units 1st & 2nd sem (enrolled) | The number of curricular units enrolled by the student in the first and second semester | |
    | 20 | Curricular units 1st & 2nd sem (evaluations) | The number of curricular units evaluated by the student in the first and second semester | |
    | 21 | Curricular units 1st & 2nd sem (approved) | The number of curricular units approved by the student in the first and second semester | |
    | 22 | Curricular units 1st & 2nd sem (grade) | The number of curricular units graded by the student in the first and second semester | |
    | 23 | Unemployment rate | The Unemployment rate % | |
    | 24 | Inflation rate | The Inflation rate % | |
    | 25 | GDP | GDP per capita (USD) | |
    | 26 | Target | Status of the student | Graduate Dropout Enrolled |
    """)

elif page == "AI Predictions":
    st.title("🤖 Let's Predict")
    
    if not api_connected:
        st.error("❌ AI API is not connected. Please start the Flask API server.")
        st.info("💡 Run `python app.py` in your terminal to start the API server.")
        st.stop()
    
    # Tabs for different prediction modes
    tab1, tab2, tab3 = st.tabs(["📊 Single Student Prediction", "📁 CSV Batch Prediction", "📈 Prediction Analytics"])
    
    with tab1:
        st.write("### Single Student Prediction")
        st.write("Predict dropout risk for an individual student using the AI model.")
        
        # Get API features
        api_features = get_api_features()
        if not api_features:
            st.error("❌ Could not retrieve API features.")
            st.stop()
        
        # Create form for single student prediction
        with st.form("single_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Personal Information**")
                marital_status = st.selectbox("Marital Status", [1, 2, 3, 4, 5, 6], index=0)
                application_mode = st.selectbox("Application Mode", list(range(1, 19)), index=0)
                course = st.selectbox("Course", list(range(1, 18)), index=0)
                daytime_evening = st.selectbox("Daytime/Evening Attendance", [0, 1], index=0)
                previous_qualification = st.selectbox("Previous Qualification", list(range(1, 18)), index=0)
                nationality = st.selectbox("Nationality", list(range(1, 22)), index=0)
                age_at_enrollment = st.number_input("Age at Enrollment", min_value=17, max_value=70, value=20)
                gender = st.selectbox("Gender", [0, 1], index=0)
                international = st.selectbox("International Student", [0, 1], index=0)
            
            with col2:
                st.write("**Family Information**")
                mother_qualification = st.selectbox("Mother's Qualification", list(range(1, 35)), index=0)
                father_qualification = st.selectbox("Father's Qualification", list(range(1, 35)), index=0)
                mother_occupation = st.selectbox("Mother's Occupation", list(range(1, 47)), index=0)
                father_occupation = st.selectbox("Father's Occupation", list(range(1, 47)), index=0)
                
                st.write("**Academic & Financial**")
                displaced = st.selectbox("Displaced", [0, 1], index=0)
                educational_special_needs = st.selectbox("Educational Special Needs", [0, 1], index=0)
                debtor = st.selectbox("Debtor", [0, 1], index=0)
                tuition_fees_up_to_date = st.selectbox("Tuition Fees Up to Date", [0, 1], index=0)
                scholarship_holder = st.selectbox("Scholarship Holder", [0, 1], index=0)
            
            st.write("**Academic Performance**")
            col3, col4 = st.columns(2)
            
            with col3:
                st.write("**1st Semester**")
                curricular_1st_credited = st.number_input("1st Sem - Credited", min_value=0, value=0)
                curricular_1st_enrolled = st.number_input("1st Sem - Enrolled", min_value=0, value=0)
                curricular_1st_evaluations = st.number_input("1st Sem - Evaluations", min_value=0, value=0)
                curricular_1st_approved = st.number_input("1st Sem - Approved", min_value=0, value=0)
                curricular_1st_grade = st.number_input("1st Sem - Grade", min_value=0, value=0)
            
            with col4:
                st.write("**2nd Semester**")
                curricular_2nd_credited = st.number_input("2nd Sem - Credited", min_value=0, value=0)
                curricular_2nd_enrolled = st.number_input("2nd Sem - Enrolled", min_value=0, value=0)
                curricular_2nd_evaluations = st.number_input("2nd Sem - Evaluations", min_value=0, value=0)
                curricular_2nd_approved = st.number_input("2nd Sem - Approved", min_value=0, value=0)
                curricular_2nd_grade = st.number_input("2nd Sem - Grade", min_value=0, value=0)
            
            st.write("**Economic Factors**")
            col5, col6, col7 = st.columns(3)
            with col5:
                unemployment_rate = st.number_input("Unemployment Rate (%)", min_value=0.0, max_value=30.0, value=10.8)
            with col6:
                inflation_rate = st.number_input("Inflation Rate (%)", min_value=-2.0, max_value=5.0, value=1.4)
            with col7:
                gdp = st.number_input("GDP", min_value=0.0, max_value=5.0, value=1.74)
            
            # Submit button
            submitted = st.form_submit_button("🔮 Predict Dropout Risk", type="primary")
            
            if submitted:
                # Prepare data for API
                student_data = {
                    "marital_status": marital_status,
                    "application_mode": application_mode,
                    "course": course,
                    "daytime_evening_attendance": daytime_evening,
                    "previous_qualification": previous_qualification,
                    "nationality": nationality,
                    "mother_qualification": mother_qualification,
                    "father_qualification": father_qualification,
                    "mother_occupation": mother_occupation,
                    "father_occupation": father_occupation,
                    "displaced": displaced,
                    "educational_special_needs": educational_special_needs,
                    "debtor": debtor,
                    "tuition_fees_up_to_date": tuition_fees_up_to_date,
                    "gender": gender,
                    "scholarship_holder": scholarship_holder,
                    "age_at_enrollment": age_at_enrollment,
                    "international": international,
                    "curricular_units_1st_sem_credited": curricular_1st_credited,
                    "curricular_units_1st_sem_enrolled": curricular_1st_enrolled,
                    "curricular_units_1st_sem_evaluations": curricular_1st_evaluations,
                    "curricular_units_1st_sem_approved": curricular_1st_approved,
                    "curricular_units_1st_sem_grade": curricular_1st_grade,
                    "curricular_units_2nd_sem_credited": curricular_2nd_credited,
                    "curricular_units_2nd_sem_enrolled": curricular_2nd_enrolled,
                    "curricular_units_2nd_sem_evaluations": curricular_2nd_evaluations,
                    "curricular_units_2nd_sem_approved": curricular_2nd_approved,
                    "curricular_units_2nd_sem_grade": curricular_2nd_grade,
                    "unemployment_rate": unemployment_rate,
                    "inflation_rate": inflation_rate,
                    "gdp": gdp
                }
                
                # Make prediction
                with st.spinner("🤖 Making prediction..."):
                    result = predict_single_student(student_data)
                
                if result.get("status") == "success":
                    prediction = result["prediction"]
                    risk_level = result["risk_level"]
                    confidence = result["confidence"]
                    probabilities = result["probabilities"]
                    dropout_probability = probabilities.get("Dropout", 0)
                    
                    # Display results
                    st.success("✅ Prediction completed!")
                    
                    # Prediction result
                    col_pred1, col_pred2, col_pred3 = st.columns(3)
                    with col_pred1:
                        st.metric("Prediction", prediction)
                    with col_pred2:
                        st.metric("Risk Level", risk_level)
                    with col_pred3:
                        st.metric("Confidence", f"{confidence:.2%}")
                    
                    # Probabilities
                    st.write("**Prediction Probabilities:**")
                    prob_df = pd.DataFrame(list(probabilities.items()), columns=['Outcome', 'Probability'])
                    prob_df['Probability'] = prob_df['Probability'].apply(lambda x: f"{x:.2%}")
                    st.dataframe(prob_df, use_container_width=True)
                    
                    # Save to MongoDB (all students)
                    if mongodb_connected:
                        with st.spinner("💾 Saving student to database..."):
                            # Add student_id to the data
                            student_data_with_id = student_data.copy()
                            student_data_with_id["student_id"] = f"student_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            
                            save_success, save_message = save_student_to_database(student_data_with_id, result)
                            if save_success:
                                st.success(f"💾 {save_message}")
                            else:
                                st.warning(f"⚠️ {save_message}")
                    elif not mongodb_connected:
                        st.warning("⚠️ MongoDB not connected. Data not saved.")
                    
                    # Risk assessment
                    if risk_level == "High":
                        st.error("🚨 **High Risk**: This student has a high probability of dropping out. Immediate intervention recommended.")
                    elif risk_level == "Medium":
                        st.warning("⚠️ **Medium Risk**: This student may be at risk. Consider monitoring and support.")
                    else:
                        st.success("✅ **Low Risk**: This student is likely to continue successfully.")
                        
                else:
                    st.error(f"❌ Prediction failed: {result.get('error', 'Unknown error')}")
    
    with tab2:
        st.write("### CSV Batch Prediction")
        st.write("Upload a CSV file with student data to get batch predictions.")
        
        # File upload
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                # Read CSV
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ File uploaded successfully! Found {len(df)} students.")
                
                # Show preview
                st.write("**Data Preview:**")
                st.dataframe(df.head(), use_container_width=True)
                
                # Check if required columns exist
                required_columns = [
                    'Marital status', 'Application mode', 'Course', 'Daytime/evening attendance',
                    'Previous qualification', 'Nacionality', 'Mother\'s qualification',
                    'Father\'s qualification', 'Mother\'s occupation', 'Father\'s occupation',
                    'Displaced', 'Educational special needs', 'Debtor', 'Tuition fees up to date',
                    'Gender', 'Scholarship holder', 'Age at enrollment', 'International',
                    'Curricular units 1st sem (credited)', 'Curricular units 1st sem (enrolled)',
                    'Curricular units 1st sem (evaluations)', 'Curricular units 1st sem (approved)',
                    'Curricular units 1st sem (grade)', 'Curricular units 2nd sem (credited)',
                    'Curricular units 2nd sem (enrolled)', 'Curricular units 2nd sem (evaluations)',
                    'Curricular units 2nd sem (approved)', 'Curricular units 2nd sem (grade)',
                    'Unemployment rate', 'Inflation rate', 'GDP'
                ]
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {missing_columns}")
                    st.info("💡 Please ensure your CSV file contains all required columns.")
                else:
                    # Convert to API format
                    students_list = []
                    for _, row in df.iterrows():
                        api_data = convert_student_to_api_format(row)
                        students_list.append(api_data)
                    
                    # Make batch prediction
                    if st.button("🔮 Predict All Students", type="primary"):
                        with st.spinner(f"🤖 Processing {len(students_list)} students..."):
                            result = predict_batch_students(students_list)
                        
                        if result.get("status") == "success":
                            st.success(f"✅ Batch prediction completed!")
                            st.info(f"Processed: {result['total_processed']} | Successful: {result['successful']} | Failed: {result['failed']}")
                            
                            # Create results dataframe and save high-risk students to MongoDB
                            results_data = []
                            students_saved = 0
                            
                            for res in result['results']:
                                if res.get('status') == 'success':
                                    dropout_prob = res['probabilities'].get('Dropout', 0)
                                    
                                    results_data.append({
                                        'Student_Index': res['index'],
                                        'Prediction': res['prediction'],
                                        'Risk_Level': res['risk_level'],
                                        'Confidence': f"{res['confidence']:.2%}",
                                        'Dropout_Probability': f"{dropout_prob:.2%}",
                                        'Enrolled_Probability': f"{res['probabilities'].get('Enrolled', 0):.2%}",
                                        'Graduate_Probability': f"{res['probabilities'].get('Graduate', 0):.2%}"
                                    })
                                    
                                    # Save all students to MongoDB
                                    if mongodb_connected:
                                        try:
                                            # Get original student data
                                            original_student_data = students_list[res['index']]
                                            original_student_data["student_id"] = f"batch_student_{res['index']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                            
                                            save_success, save_message = save_student_to_database(original_student_data, res)
                                            if save_success:
                                                students_saved += 1
                                        except Exception as e:
                                            st.warning(f"⚠️ Failed to save student {res['index']}: {str(e)}")
                            
                            if results_data:
                                results_df = pd.DataFrame(results_data)
                                st.session_state.prediction_results = results_df
                                st.write("**Prediction Results:**")
                                st.dataframe(results_df, use_container_width=True)
                                
                                # Show MongoDB save status
                                if students_saved > 0:
                                    st.success(f"💾 Saved {students_saved} students to MongoDB")
                                elif mongodb_connected:
                                    st.info("ℹ️ No students were saved to MongoDB")
                                else:
                                    st.warning("⚠️ MongoDB not connected - students not saved")
                                
                                # Download results
                                csv = results_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Results as CSV",
                                    data=csv,
                                    file_name="prediction_results.csv",
                                    mime="text/csv"
                                )
                                
                                # Summary statistics
                                st.write("**Summary Statistics:**")
                                col_sum1, col_sum2, col_sum3 = st.columns(3)
                                with col_sum1:
                                    dropout_count = len(results_df[results_df['Prediction'] == 'Dropout'])
                                    st.metric("Dropout Predictions", dropout_count)
                                with col_sum2:
                                    high_risk_count = len(results_df[results_df['Risk_Level'] == 'High'])
                                    st.metric("High Risk Students", high_risk_count)
                                with col_sum3:
                                    avg_confidence = results_df['Confidence'].str.rstrip('%').astype(float).mean()
                                    st.metric("Average Confidence", f"{avg_confidence:.1f}%")
                        else:
                            st.error(f"❌ Batch prediction failed: {result.get('error', 'Unknown error')}")
                            
            except Exception as e:
                st.error(f"❌ Error reading CSV file: {str(e)}")
    
    with tab3:
        st.write("### Prediction Analytics")
        st.write("Analyze prediction patterns and model performance.")
        
        if 'prediction_results' in st.session_state:
            results_df = st.session_state.prediction_results
            
            # Prediction distribution
            st.write("**Prediction Distribution:**")
            pred_counts = results_df['Prediction'].value_counts()
            fig_pred = px.pie(values=pred_counts.values, names=pred_counts.index, 
                            title="Prediction Distribution")
            st.plotly_chart(fig_pred, use_container_width=True)
            
            # Risk level distribution
            st.write("**Risk Level Distribution:**")
            risk_counts = results_df['Risk_Level'].value_counts()
            fig_risk = px.bar(x=risk_counts.index, y=risk_counts.values,
                            title="Risk Level Distribution",
                            labels={'x': 'Risk Level', 'y': 'Number of Students'})
            st.plotly_chart(fig_risk, use_container_width=True)
            
            # Confidence distribution
            st.write("**Confidence Distribution:**")
            results_df['Confidence_Numeric'] = results_df['Confidence'].str.rstrip('%').astype(float)
            fig_conf = px.histogram(results_df, x='Confidence_Numeric', 
                                  title="Confidence Score Distribution",
                                  labels={'Confidence_Numeric': 'Confidence (%)', 'count': 'Number of Students'})
            st.plotly_chart(fig_conf, use_container_width=True)
        else:
            st.info("💡 Upload and process a CSV file to see analytics here.")

elif page == "Student Mood Tracker":
    st.title("🧠 Student Mood Tracker")
    
    if not mongodb_connected:
        st.error("❌ MongoDB is not connected. Cannot save or fetch moods.")
        st.stop()
    
    # Session-based simple login
    if 'logged_in_student_id' not in st.session_state:
        st.session_state.logged_in_student_id = None
    
    if st.session_state.logged_in_student_id is None:
        st.write("Please login with your Student ID to access the mood tracker.")
        with st.form("mood_login_form"):
            login_student_id = st.text_input("Student ID", key="mood_login_student_id")
            login_submitted = st.form_submit_button("🔐 Login", type="primary")
        if login_submitted:
            if login_student_id.strip():
                st.session_state.logged_in_student_id = login_student_id.strip()
                st.success(f"Logged in as {st.session_state.logged_in_student_id}")
                st.rerun()
            else:
                st.warning("Please enter a valid Student ID.")
        st.stop()

    # Logged in
    st.info(f"Logged in as: {st.session_state.logged_in_student_id}")
    if st.button("🔓 Logout"):
        st.session_state.logged_in_student_id = None
        st.rerun()

    st.write("Track your daily mood and wellbeing. This helps counselors support you better.")
    
    # Mood submission form
    with st.form("mood_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.text_input("Your Student ID", value=st.session_state.logged_in_student_id, key="mood_student_id", disabled=True)
            mood = st.select_slider(
                "How are you feeling today?",
                options=["Very Sad", "Sad", "Neutral", "Happy", "Very Happy"],
                value="Neutral"
            )
            stress_level = st.slider("Stress Level (0=none, 10=extreme)", 0, 10, 5)
        with col_b:
            sleep_hours = st.number_input("Sleep Last Night (hours)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
            notes = st.text_area("Notes (optional)", placeholder="Anything you'd like to share...")
        submitted = st.form_submit_button("💾 Submit Mood", type="primary")
    
    if submitted:
        student_id = st.session_state.logged_in_student_id
        with st.spinner("Saving your mood..."):
            ok, msg = save_mood_entry(student_id, mood, stress_level, sleep_hours, notes)
        if ok:
            st.success(msg)
        else:
            st.error(msg)
    
    st.divider()
    st.write("### Recent Mood History")
    
    # Always restrict to the logged-in student
    entries = get_recent_mood_entries(st.session_state.logged_in_student_id, limit=100)
    
    if not entries:
        st.info("No mood entries found yet.")
        st.stop()
    
    # Convert to DataFrame for display and charts
    mood_df = pd.DataFrame([
        {
            "Student ID": e.get("student_id"),
            "Mood": e.get("mood"),
            "Stress": e.get("stress_level"),
            "Sleep (h)": e.get("sleep_hours"),
            "Notes": e.get("notes", ""),
            "Time": e.get("created_at", "")
        }
        for e in entries
    ])
    
    st.dataframe(mood_df, use_container_width=True)
    
    # # Simple charts
    # st.write("### Mood Analytics")
    # col_c1, col_c2 = st.columns(2)
    # with col_c1:
    #     try:
    #         mood_counts = mood_df["Mood"].value_counts().reset_index()
    #         mood_counts.columns = ["Mood", "Count"]
    #         fig_mood = px.bar(mood_counts, x="Mood", y="Count", title="Mood Frequency")
    #         st.plotly_chart(fig_mood, use_container_width=True)
    #     except Exception:
    #         pass
    # with col_c2:
    #     try:
    #         fig_sleep = px.histogram(mood_df, x="Sleep (h)", nbins=20, title="Sleep Hours Distribution")
    #         st.plotly_chart(fig_sleep, use_container_width=True)
    #     except Exception:
    #         pass

elif page == "Student Chatbot":
    st.title("💬 Student Chatbot")
    st.write("Share your concerns and get supportive, practical guidance.")

    # Ensure a session ID for backend chat context
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = f"student_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if 'chat_history_ui' not in st.session_state:
        st.session_state.chat_history_ui = []

    # Render chat history
    for role, content in st.session_state.chat_history_ui:
        st.chat_message("user" if role == 'user' else "assistant").markdown(content)

    user_msg = st.chat_input("Type your message...")

    if user_msg:
        st.session_state.chat_history_ui.append(('user', user_msg))
        st.chat_message("user").markdown(user_msg)
        # Send to backend
        try:
            resp = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "session_id": st.session_state.chat_session_id,
                    "message": user_msg
                },
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get('reply', '...')
            else:
                reply = f"Backend error: {resp.status_code}"
        except Exception as e:
            reply = f"Connection error: {str(e)}"

        st.session_state.chat_history_ui.append(('assistant', reply))
        st.chat_message("assistant").markdown(reply)

elif page == "Offline Chatbot":
    st.title("💬 Offline Chatbot")
    st.write("This chatbot works without internet or API keys using built-in guidance.")

    if 'offline_session_id' not in st.session_state:
        st.session_state.offline_session_id = f"offline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if 'offline_history_ui' not in st.session_state:
        st.session_state.offline_history_ui = []

    for role, content in st.session_state.offline_history_ui:
        st.chat_message("user" if role == 'user' else "assistant").markdown(content)

    user_msg = st.chat_input("Type your message...")

    if user_msg:
        st.session_state.offline_history_ui.append(('user', user_msg))
        st.chat_message("user").markdown(user_msg)
        try:
            resp = requests.post(
                f"{API_BASE_URL}/chat_offline",
                json={
                    "session_id": st.session_state.offline_session_id,
                    "message": user_msg
                },
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get('reply', '...')
                st.session_state.offline_session_id = data.get('session_id', st.session_state.offline_session_id)
            else:
                reply = f"Backend error: {resp.status_code}"
        except Exception as e:
            reply = f"Connection error: {str(e)}"

        st.session_state.offline_history_ui.append(('assistant', reply))
        st.chat_message("assistant").markdown(reply)
