#!/usr/bin/env python
"""
Mortality prediction model training using Synthea sample data (small subset).
This script creates features from Synthea CSV files and trains a model 
to predict patient mortality (based on DEATHDATE in patients.csv).
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import xgboost as xgb
import joblib

print("=== Script started (small subset) ===", flush=True)

# ----------------------------
# 1. Data Loading
# ----------------------------
def load_synthea_data(data_dir):
    """Load all Synthea CSV files"""
    print("Loading Synthea data...", flush=True)
    
    # Core tables
    patients = pd.read_csv(os.path.join(data_dir, "patients.csv"))
    encounters = pd.read_csv(os.path.join(data_dir, "encounters.csv"))
    conditions = pd.read_csv(os.path.join(data_dir, "conditions.csv"))
    observations = pd.read_csv(os.path.join(data_dir, "observations.csv"))
    medications = pd.read_csv(os.path.join(data_dir, "medications.csv"))
    procedures = pd.read_csv(os.path.join(data_dir, "procedures.csv"))
    
    print(f"Loaded: {len(patients)} patients, {len(encounters)} encounters, "
          f"{len(conditions)} conditions, {len(observations)} observations, "
          f"{len(medications)} medications, {len(procedures)} procedures", flush=True)
    
    return patients, encounters, conditions, observations, medications, procedures

# ----------------------------
# 2. Feature Engineering
# ----------------------------
def engineer_features(patients, encounters, conditions, observations, medications, procedures):
    """Engineer features for mortality prediction"""
    print("Engineering features...", flush=True)
    
    # Start with patients dataframe
    df = patients.copy()
    
    # Convert dates to datetime
    df['BIRTHDATE'] = pd.to_datetime(df['BIRTHDATE'])
    df['DEATHDATE'] = pd.to_datetime(df['DEATHDATE'], errors='coerce')
    
    # Target: has death record (anytime)
    df['DEATH'] = df['DEATHDATE'].notna().astype(int)
    
    # Age at reference date (use max date in data or current date)
    # For simplicity, use 2023-01-01 as reference (adjust based on your data)
    reference_date = pd.to_datetime('2023-01-01')
    df['AGE'] = (reference_date - df['BIRTHDATE']).dt.days / 365.25
    
    # Basic demographics
    df['GENDER_MALE'] = (df['GENDER'] == 'M').astype(int)
    df['GENDER_FEMALE'] = (df['GENDER'] == 'F').astype(int)
    
    # Race encoding (simplified)
    race_dummies = pd.get_dummies(df['RACE'], prefix='RACE')
    df = pd.concat([df, race_dummies], axis=1)
    
    # Ethnicity encoding
    df['ETHNICITY_HISPANIC'] = (df['ETHNICITY'] == 'hispanic').astype(int)
    df['ETHNICITY_NON_HISPANIC'] = (df['ETHNICITY'] == 'nonhispanic').astype(int)
    
    # Marital status encoding
    marital_dummies = pd.get_dummies(df['MARITAL'], prefix='MARITAL')
    df = pd.concat([df, marital_dummies], axis=1)
    
    # ----------------------------
    # Condition features (comorbidity burden)
    # ----------------------------
    # Count of conditions per patient
    condition_counts = conditions.groupby('PATIENT').size().reset_index(name='CONDITION_COUNT')
    df = df.merge(condition_counts, left_on='Id', right_on='PATIENT', how='left')
    df['CONDITION_COUNT'] = df['CONDITION_COUNT'].fillna(0)
    
    # Unique condition types
    unique_conditions = conditions.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_CONDITIONS')
    df = df.merge(unique_conditions, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_CONDITIONS'] = df['UNIQUE_CONDITIONS'].fillna(0)
    
    # Chronic condition indicators (examples)
    chronic_condition_keywords = [
        'diabetes', 'hypertension', 'heart failure', 'ckd', 'copd', 
        'asthma', 'depression', 'cancer', 'stroke', 'atrial fibrillation'
    ]
    
    for keyword in chronic_condition_keywords:
        # Check if any condition description contains keyword (case insensitive)
        has_condition = conditions[
            conditions['DESCRIPTION'].str.lower().str.contains(keyword, na=False)
        ]['PATIENT'].unique()
        df[f'HAS_{keyword.upper().replace(" ", "_")}'] = df['Id'].isin(has_condition).astype(int)
    
    # ----------------------------
    # Medication features
    # ----------------------------
    # Count of medications per patient
    med_counts = medications.groupby('PATIENT').size().reset_index(name='MEDICATION_COUNT')
    df = df.merge(med_counts, left_on='Id', right_on='PATIENT', how='left')
    df['MEDICATION_COUNT'] = df['MEDICATION_COUNT'].fillna(0)
    
    # Unique medications
    unique_meds = medications.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_MEDICATIONS')
    df = df.merge(unique_meds, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_MEDICATIONS'] = df['UNIQUE_MEDICATIONS'].fillna(0)
    
    # Medication classes (simplified - look at first part of description or code)
    # For now, just count psych meds, antibiotics, etc. based on keywords in description
    med_keywords = {
        'PSYCH_MEDS': ['antidepressant', 'antipsychotic', 'anxiolytic', 'mood stabilizer'],
        'ANTIBIOTICS': ['antibiotic', 'penicillin', 'cephalosporin'],
        'ANTICOAGULANTS': ['warfarin', 'heparin', 'apixaban', 'rivaroxaban'],
        'INSULIN': ['insulin'],
        'OPIOIDS': ['opioid', 'morphine', 'oxycodone', 'hydrocodone', 'fentanyl']
    }
    
    for class_name, keywords in med_keywords.items():
        has_med = medications[
            medications['DESCRIPTION'].str.lower().str.contains('|'.join(keywords), na=False)
        ]['PATIENT'].unique()
        df[f'HAS_{class_name}'] = df['Id'].isin(has_med).astype(int)
    
    # ----------------------------
    # Encounter features (healthcare utilization)
    # ----------------------------
    # Encounter count
    encounter_counts = encounters.groupby('PATIENT').size().reset_index(name='ENCOUNTER_COUNT')
    df = df.merge(encounter_counts, left_on='Id', right_on='PATIENT', how='left')
    df['ENCOUNTER_COUNT'] = df['ENCOUNTER_COUNT'].fillna(0)
    
    # Encounter types
    encounter_types = encounters['ENCOUNTERCLASS'].unique()
    for etype in encounter_types:
        if pd.notna(etype):
            has_encounter = encounters[
                encounters['ENCOUNTERCLASS'] == etype
            ]['PATIENT'].unique()
            df[f'ENCOUNTER_{etype.upper()}'] = df['Id'].isin(has_encounter).astype(int)
    
    # Recent encounters (last 6 months)
    six_months_ago = reference_date - timedelta(days=180)
    encounters['START_DATE'] = pd.to_datetime(encounters['START'])
    recent_encounters = encounters[encounters['START_DATE'] >= six_months_ago]
    recent_encounter_counts = recent_encounters.groupby('PATIENT').size().reset_index(name='RECENT_ENCOUNTER_COUNT')
    df = df.merge(recent_encounter_counts, left_on='Id', right_on='PATIENT', how='left')
    df['RECENT_ENCOUNTER_COUNT'] = df['RECENT_ENCOUNTER_COUNT'].fillna(0)
    
    # ----------------------------
    # Observation features (labs and vitals)
    # ----------------------------
    # Separate labs and vitals
    labs = observations[observations['CATEGORY'] == 'laboratory'].copy()
    vitals = observations[observations['CATEGORY'] == 'vital-signs'].copy()
    
    # Lab features: count of tests, abnormal flags (if available)
    lab_counts = labs.groupby('PATIENT').size().reset_index(name='LAB_TEST_COUNT')
    df = df.merge(lab_counts, left_on='Id', right_on='PATIENT', how='left')
    df['LAB_TEST_COUNT'] = df['LAB_TEST_COUNT'].fillna(0)
    
    # Unique lab tests
    unique_labs = labs.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_LABS')
    df = df.merge(unique_labs, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_LABS'] = df['UNIQUE_LABS'].fillna(0)
    
    # Vital signs features: count, and try to get latest values for key vitals
    vital_counts = vitals.groupby('PATIENT').size().reset_index(name='VITAL_MEASUREMENT_COUNT')
    df = df.merge(vital_counts, left_on='Id', right_on='PATIENT', how='left')
    df['VITAL_MEASUREMENT_COUNT'] = df['VITAL_MEASUREMENT_COUNT'].fillna(0)
    
    # Key vital signs to extract (systolic BP, diastolic BP, heart rate, temperature, resp rate, o2 sat)
    vital_mapping = {
        'SYSTOLIC_BP': ['8480-6', 'Systolic Blood Pressure'],
        'DIASTOLIC_BP': ['8462-4', 'Diastolic Blood Pressure'],
        'HEART_RATE': ['8867-4', 'Heart rate'],
        'RESPIRATORY_RATE': ['9279-1', 'Respiratory rate'],
        'TEMPERATURE': ['8310-5', 'Body temperature'],
        'O2_SAT': ['2708-6', 'Oxygen saturation in Arterial blood']
    }
    
    for vital_name, (code, desc) in vital_mapping.items():
        # Try to get latest value for this vital
        vital_data = vitals[
            (vitals['CODE'] == code) | (vitals['DESCRIPTION'] == desc)
        ].copy()
        
        if len(vital_data) > 0:
            vital_data['DATE'] = pd.to_datetime(vital_data['DATE'])
            # Get most recent measurement per patient
            latest_vital = vital_data.sort_values('DATE').groupby('PATIENT').last().reset_index()
            latest_vital = latest_vital[['PATIENT', 'VALUE']].rename(columns={'VALUE': vital_name})
            df = df.merge(latest_vital, left_on='Id', right_on='PATIENT', how='left')
            # Fill missing with median or mean
            median_val = df[vital_name].median()
            df[vital_name] = df[vital_name].fillna(median_val)
        else:
            df[vital_name] = np.nan
    
    # Lab values for common tests
    lab_mapping = {
        'HEMOGLOBIN_A1C': ['4548-4', 'Hemoglobin A1c/Hemoglobin.total in Blood'],
        'CHOLESTEROL': ['2093-3', 'Cholesterol in Blood'],
        'HDL': ['2085-9', 'HDL Cholesterol'],
        'LDL': ['2089-1', 'LDL Cholesterol'],
        'TRIGLYCERIDES': ['2571-8', 'Triglycerides'],
        'CREATININE': ['2160-0', 'Creatinine'],
        'BUN': ['3094-0', 'Urea nitrogen'],
        'GLUCOSE': ['2345-7', 'Glucose'],
        'WBC': ['26464-8', 'Leukocytes [#/volume] in Blood'],
        'HEMOGLOBIN': ['718-7', 'Hemoglobin']
    }
    
    for lab_name, (code, desc) in lab_mapping.items():
        lab_data = labs[
            (labs['CODE'] == code) | (labs['DESCRIPTION'] == desc)
        ].copy()
        
        if len(lab_data) > 0:
            lab_data['DATE'] = pd.to_datetime(lab_data['DATE'])
            latest_lab = lab_data.sort_values('DATE').groupby('PATIENT').last().reset_index()
            latest_lab = latest_lab[['PATIENT', 'VALUE']].rename(columns={'VALUE': lab_name})
            df = df.merge(latest_lab, left_on='Id', right_on='PATIENT', how='left')
            median_val = df[lab_name].median()
            df[lab_name] = df[lab_name].fillna(median_val)
        else:
            df[lab_name] = np.nan
    
    # ----------------------------
    # Procedure features
    # ----------------------------
    procedure_counts = procedures.groupby('PATIENT').size().reset_index(name='PROCEDURE_COUNT')
    df = df.merge(procedure_counts, left_on='Id', right_on='PATIENT', how='left')
    df['PROCEDURE_COUNT'] = df['PROCEDURE_COUNT'].fillna(0)
    
    unique_procedures = procedures.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_PROCEDURES')
    df = df.merge(unique_procedures, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_PROCEDURES'] = df['UNIQUE_PROCEDURES'].fillna(0)
    
    # ----------------------------
    # Final feature preparation
    # ----------------------------
    # Select feature columns (exclude IDs, dates, target, and other non-features)
    exclude_cols = [
        'Id', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT', 
        'PREFIX', 'FIRST', 'MIDDLE', 'LAST', 'SUFFIX', 'MAIDEN',
        'BIRTHPLACE', 'ADDRESS', 'CITY', 'STATE', 'COUNTY', 'FIPS', 
        'ZIP', 'LAT', 'LON', 'HEALTHCARE_EXPENSES', 'HEALTHCARE_COVERAGE', 'INCOME',
        'DEATH'  # target
    ]
    
    # Also exclude any columns that are all NaN or have too many missing values
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Handle missing values: for numeric columns, fill with median; for categorical, fill with mode
    df_features = df[feature_cols].copy()
    
    # Identify numeric vs categorical columns
    numeric_cols = df_features.select_dtypes(include=[np.number]).columns
    categorical_cols = df_features.select_dtypes(exclude=[np.number]).columns
    
    # Fill numeric missing with median
    for col in numeric_cols:
        df_features[col] = df_features[col].fillna(df_features[col].median())
    
    # Fill categorical missing with mode (or 'Unknown')
    for col in categorical_cols:
        mode_val = df_features[col].mode()
        if len(mode_val) > 0:
            df_features[col] = df_features[col].fillna(mode_val[0])
        else:
            df_features[col] = df_features[col].fillna('Unknown')
    
    # Convert categorical to numeric if needed (label encoding)
    label_encoders = {}
    for col in categorical_cols:
        if df_features[col].dtype == 'object':
            le = LabelEncoder()
            df_features[col] = le.fit_transform(df_features[col].astype(str))
            label_encoders[col] = le
    
    print(f"Engineered {df_features.shape[1]} features for {df_features.shape[0]} patients", flush=True)
    print(f"Positive class (deaths): {df['DEATH'].sum()} ({df['DEATH'].mean()*100:.1f}%)", flush=True)
    
    return df_features, df['DEATH'], label_encoders

# ----------------------------
# 3. Model Training
# ----------------------------
def train_model(X, y):
    """Train and evaluate mortality prediction model"""
    print("Splitting data...", flush=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("Scaling features...", flush=True)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Training XGBoost model...", flush=True)
    # XGBoost parameters for binary classification
    xgb_params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42
    }
    
    model = xgb.XGBClassifier(**xgb_params)
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        early_stopping_rounds=10,
        verbose=False
    )
    
    print("Evaluating model...", flush=True)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    y_pred = model.predict(X_test_scaled)
    
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"AUC-ROC: {auc:.4f}", flush=True)
    
    print("\nClassification Report:", flush=True)
    print(classification_report(y_test, y_pred))
    
    print("\nConfusion Matrix:", flush=True)
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 20 Features:", flush=True)
    print(feature_importance.head(20))
    
    return model, scaler, feature_importance, auc

# ----------------------------
# 4. Main Execution
# ----------------------------
if __name__ == '__main__':
    try:
        # Set data directory (small subset) using environment variable TEMP
        temp_dir = os.environ.get('TEMP')
        if temp_dir is None:
            # fallback to TMP
            temp_dir = os.environ.get('TMP')
        data_dir = os.path.join(temp_dir, 'synthea_sample_data_csv_latest_small')
        
        # Check if directory exists
        if not os.path.exists(data_dir):
            print(f"Error: Data directory not found: {data_dir}", flush=True)
            print("Please create the small subset directory first.", flush=True)
            exit(1)
        
        print(f"Data directory: {data_dir}", flush=True)
        
        # Load data
        print("Loading data...", flush=True)
        patients, encounters, conditions, observations, medications, procedures = load_synthea_data(data_dir)
        
        # Engineer features
        print("Feature engineering...", flush=True)
        X, y, label_encoders = engineer_features(patients, encounters, conditions, observations, medications, procedures)
        
        # Train model
        print("Training model...", flush=True)
        model, scaler, feature_importance, auc = train_model(X, y)
        
        # Save model and preprocessing objects
        model_dir = "backend/ml/models"
        print(f"Creating model directory: {model_dir}", flush=True)
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, "synthea_mortality_model.joblib")
        scaler_path = os.path.join(model_dir, "synthea_mortality_scaler.joblib")
        encoder_path = os.path.join(model_dir, "synthea_mortality_encoders.joblib")
        feature_path = os.path.join(model_dir, "synthea_mortality_features.joblib")
        
        print(f"Saving model to {model_path}", flush=True)
        joblib.dump(model, model_path)
        print(f"Saving scaler to {scaler_path}", flush=True)
        joblib.dump(scaler, scaler_path)
        print(f"Saving encoders to {encoder_path}", flush=True)
        joblib.dump(label_encoders, encoder_path)
        print(f"Saving feature names to {feature_path}", flush=True)
        joblib.dump(list(X.columns), feature_path)
        
        print(f"\nModel saved to: {model_path}", flush=True)
        print(f"Scaler saved to: {scaler_path}", flush=True)
        print(f"Encoders saved to: {encoder_path}", flush=True)
        print(f"Feature names saved to: {feature_path}", flush=True)
        print(f"Final AUC-ROC: {auc:.4f}", flush=True)
        
        print("\nTraining complete! To use this model for inference:", flush=True)
        print("1. Load the model and scaler from the saved files", flush=True)
        print("2. Engineer features from new patient data using the same process", flush=True)
        print("3. Scale features using the saved scaler", flush=True)
        print("4. Predict mortality probability using model.predict_proba()", flush=True)
        
        print("=== Script finished ===", flush=True)
        
    except Exception as e:
        print(f"Error during execution: {e}", flush=True)
        import traceback
        traceback.print_exc()
        exit(1)
