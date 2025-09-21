import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# Load the dataset
print("Loading dataset...")
df = pd.read_csv('dataset.csv')

# Prepare features and target
print("Preparing features...")

# Select features (excluding target and application order)
feature_columns = [
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

# Prepare the data
X = df[feature_columns].copy()
y = df['Target'].copy()

# Handle missing values
X = X.fillna(X.median())

# Encode categorical variables
le_dict = {}
for col in X.columns:
    if X[col].dtype == 'object':
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        le_dict[col] = le

# Split the data
print("Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train Random Forest model
print("Training Random Forest model...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2
)

rf_model.fit(X_train, y_train)

# Evaluate the model
train_score = rf_model.score(X_train, y_train)
test_score = rf_model.score(X_test, y_test)

print(f"Training accuracy: {train_score:.4f}")
print(f"Test accuracy: {test_score:.4f}")

# Save the model
print("Saving model...")
with open('random_forest_model.pkl', 'wb') as f:
    pickle.dump(rf_model, f)

# Save the label encoders
with open('label_encoders.pkl', 'wb') as f:
    pickle.dump(le_dict, f)

# Save feature names
with open('feature_names.pkl', 'wb') as f:
    pickle.dump(feature_columns, f)

print("Model saved successfully!")
print(f"Model type: {type(rf_model)}")
print(f"Classes: {rf_model.classes_}")
print(f"Feature importance (top 10):")
feature_importance = list(zip(feature_columns, rf_model.feature_importances_))
feature_importance.sort(key=lambda x: x[1], reverse=True)
for i, (feature, importance) in enumerate(feature_importance[:10]):
    print(f"  {i+1}. {feature}: {importance:.4f}")
