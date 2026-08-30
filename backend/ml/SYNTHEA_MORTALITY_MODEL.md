@
# Synthea Mortality Prediction Model

This directory contains code to train and use a mortality prediction model on Synthea sample EHR data.

## Files

### Training Script
- `synthea_mortality_train.py` - Trains an XGBoost model to predict patient mortality

### Inference Script  
- `synthea_mortality_inference.py` - Loads trained model and makes predictions on new data

## Usage

### 1. Prerequisites
Install required packages:
```bash
pip install scikit-learn xgboost joblib pandas numpy
```

### 2. Train the Model
```bash
python backend/ml/train/synthea_mortality_train.py
```

This will:
- Load all Synthea CSV files from `C:\Users\ASUS\Desktop\synthea_sample_data_csv_latest\`
- Engineer features including demographics, conditions, medications, encounters, observations, and procedures
- Train an XGBoost model to predict mortality (based on DEATHDATE)
- Save model artifacts to `backend/ml/models/`

### 3. Use the Model for Inference
After training, you can use the model to predict mortality risk:

```python
from backend.ml.inference.synthea_mortality_inference import predict_mortality
import pandas as pd

# Load your Synthea data (same format as training data)
patients = pd.read_csv("path/to/patients.csv")
encounters = pd.read_csv("path/to/encounters.csv")
conditions = pd.read_csv("path/to/conditions.csv")
observations = pd.read_csv("path/to/observations.csv")
medications = pd.read_csv("path/to/medications.csv")
procedures = pd.read_csv("path/to/procedures.csv")

# Get predictions
predictions = predict_mortality(patients, encounters, conditions, observations, medications, procedures)

# Results include:
# - Id: Patient ID
# - MORTALITY_PROBABILITY: Probability of death (0-1)
# - MORTALITY_PREDICTION: Binary prediction (0=alive, 1=deceased)
```

### 4. Model Artifacts
After training, the following files are saved in `backend/ml/models/`:
- `synthea_mortality_model.joblib` - Trained XGBoost model
- `synthea_mortality_scaler.joblib` - Feature scaler
- `synthea_mortality_encoders.joblib` - Label encoders for categorical variables
- `synthea_mortality_features.joblib` - List of feature names in correct order

## Features Engineered
The model uses features from all Synthea tables:
- **Demographics**: Age, gender, race, ethnicity, marital status
- **Conditions**: Condition counts, unique conditions, chronic condition indicators (diabetes, hypertension, etc.)
- **Medications**: Medication counts, unique medications, medication class indicators
- **Encounters**: Encounter counts, encounter types, recent encounters (last 6 months)
- **Observations**: Lab test counts, vital sign counts, latest values for key labs (HbA1c, cholesterol, creatinine, etc.) and vitals (BP, heart rate, etc.)
- **Procedures**: Procedure counts, unique procedures

## Expected Performance
On the Synthea sample data, you can expect:
- AUC-ROC: Typically 0.75-0.85 for mortality prediction
- Good calibration for risk stratification
- Feature importance showing which conditions, medications, and labs are most predictive

## Notes
- The model predicts whether a patient has a recorded death date (any time in their record)
- For time-specific predictions (e.g., 1-year mortality), you would need to define an index date and window
- This model serves as a strong baseline for more complex temporal models
- Feature engineering follows best practices for EHR mortality prediction

