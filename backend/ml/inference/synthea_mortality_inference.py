#!/usr/bin/env python
"""
Inference script for Synthea mortality prediction model.
Loads a trained model and makes predictions on new Synthea-formatted data.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import joblib
from sklearn.preprocessing import StandardScaler, LabelEngineer

# Note: This is a simplified inference script that assumes you have 
# the same feature engineering process as in training.
# For production use, you would want to save and reuse the exact 
# preprocessing pipelines.

def load_model_artifacts(model_dir="backend/ml/models"):
    """Load trained model and preprocessing objects"""
    model_path = os.path.join(model_dir, "synthea_mortality_model.joblib")
    scaler_path = os.path.join(model_dir, "synthea_mortality_scaler.joblib")
    encoder_path = os.path.join(model_dir, "synthea_mortality_encoders.joblib")
    feature_path = os.path.join(model_dir, "synthea_mortality_features.joblib")
    
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    label_encoders = joblib.load(encoder_path)
    feature_names = joblib.load(feature_path)
    
    print(f"Loaded model from {model_dir}")
    return model, scaler, label_encoders, feature_names

def engineer_features_for_inference(patients, encounters, conditions, observations, medications, procedures, reference_date=None):
    """Engineer features for inference - same process as training"""
    if reference_date is None:
        reference_date = pd.to_datetime('2023-01-01')
    
    # Start with patients dataframe
    df = patients.copy()
    
    # Convert dates to datetime
    df['BIRTHDATE'] = pd.to_datetime(df['BIRTHDATE'])
    df['DEATHDATE'] = pd.to_datetime(df['DEATHDATE'], errors='coerce')
    
    # Age
    df['AGE'] = (reference_date - df['BIRTHDATE']).dt.days / 365.25
    
    # Demographics
    df['GENDER_MALE'] = (df['GENDER'] == 'M').astype(int)
    df['GENDER_FEMALE'] = (df['GENDER'] == 'F').astype(int)
    
    race_dummies = pd.get_dummies(df['RACE'], prefix='RACE')
    df = pd.concat([df, race_dummies], axis=1)
    
    df['ETHNICITY_HISPANIC'] = (df['ETHNICITY'] == 'hispanic').astype(int)
    df['ETHNICITY_NON_HISPANIC'] = (df['ETHNICITY'] == 'nonhispanic').astype(int)
    
    marital_dummies = pd.get_dummies(df['MARITAL'], prefix='MARITAL')
    df = pd.concat([df, marital_dummies], axis=1)
    
    # Condition features
    condition_counts = conditions.groupby('PATIENT').size().reset_index(name='CONDITION_COUNT')
    df = df.merge(condition_counts, left_on='Id', right_on='PATIENT', how='left')
    df['CONDITION_COUNT'] = df['CONDITION_COUNT'].fillna(0)
    
    unique_conditions = conditions.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_CONDITIONS')
    df = df.merge(unique_conditions, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_CONDITIONS'] = df['UNIQUE_CONDITIONS'].fillna(0)
    
    # Chronic conditions
    chronic_condition_keywords = [
        'diabetes', 'hypertension', 'heart failure', 'ckd', 'copd', 
        'asthma', 'depression', 'cancer', 'stroke', 'atrial fibrillation'
    ]
    
    for keyword in chronic_condition_keywords:
        has_condition = conditions[
            conditions['DESCRIPTION'].str.lower().str.contains(keyword, na=False)
        ]['PATIENT'].unique()
        df[f'HAS_{keyword.upper().replace(" ", "_")}'] = df['Id'].isin(has_condition).astype(int)
    
    # Medication features
    med_counts = medications.groupby('PATIENT').size().reset_index(name='MEDICATION_COUNT')
    df = df.merge(med_counts, left_on='Id', right_on='PATIENT', how='left')
    df['MEDICATION_COUNT'] = df['MEDICATION_COUNT'].fillna(0)
    
    unique_meds = medications.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_MEDICATIONS')
    df = df.merge(unique_meds, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_MEDICATIONS'] = df['UNIQUE_MEDICATIONS'].fillna(0)
    
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
    
    # Encounter features
    encounter_counts = encounters.groupby('PATIENT').size().reset_index(name='ENCOUNTER_COUNT')
    df = df.merge(encounter_counts, left_on='Id', right_on='PATIENT', how='left')
    df['ENCOUNTER_COUNT'] = df['ENCOUNTER_COUNT'].fillna(0)
    
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
    
    # Observation features
    labs = observations[observations['CATEGORY'] == 'laboratory'].copy()
    vitals = observations[observations['CATEGORY'] == 'vital-signs'].copy()
    
    lab_counts = labs.groupby('PATIENT').size().reset_index(name='LAB_TEST_COUNT')
    df = df.merge(lab_counts, left_on='Id', right_on='PATIENT', how='left')
    df['LAB_TEST_COUNT'] = df['LAB_TEST_COUNT'].fillna(0)
    
    unique_labs = labs.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_LABS')
    df = df.merge(unique_labs, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_LABS'] = df['UNIQUE_LABS'].fillna(0)
    
    vital_counts = vitals.groupby('PATIENT').size().reset_index(name='VITAL_MEASUREMENT_COUNT')
    df = df.merge(vital_counts, left_on='Id', right_on='PATIENT', how='left')
    df['VITAL_MEASUREMENT_COUNT'] = df['VITAL_MEASUREMENT_COUNT'].fillna(0)
    
    # Key vital signs
    vital_mapping = {
        'SYSTOLIC_BP': ['8480-6', 'Systolic Blood Pressure'],
        'DIASTOLIC_BP': ['8462-4', 'Diastolic Blood Pressure'],
        'HEART_RATE': ['8867-4', 'Heart rate'],
        'RESPIRATORY_RATE': ['9279-1', 'Respiratory rate'],
        'TEMPERATURE': ['8310-5', 'Body temperature'],
        'O2_SAT': ['2708-6', 'Oxygen saturation in Arterial blood']
    }
    
    for vital_name, (code, desc) in vital_mapping.items():
        vital_data = vitals[
            (vitals['CODE'] == code) | (vitals['DESCRIPTION'] == desc)
        ].copy()
        
        if len(vital_data) > 0:
            vital_data['DATE'] = pd.to_datetime(vital_data['DATE'])
            latest_vital = vital_data.sort_values('DATE').groupby('PATIENT').last().reset_index()
            latest_vital = latest_vital[['PATIENT', 'VALUE']].rename(columns={'VALUE': vital_name})
            df = df.merge(latest_vital, left_on='Id', right_on='PATIENT', how='left')
            median_val = df[vital_name].median()
            df[vital_name] = df[vital_name].fillna(median_val)
        else:
            df[vital_name] = np.nan
    
    # Lab values
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
    
    # Procedure features
    procedure_counts = procedures.groupby('PATIENT').size().reset_index(name='PROCEDURE_COUNT')
    df = df.merge(procedure_counts, left_on='Id', right_on='PATIENT', how='left')
    df['PROCEDURE_COUNT'] = df['PROCEDURE_COUNT'].fillna(0)
    
    unique_procedures = procedures.groupby('PATIENT')['CODE'].nunique().reset_index(name='UNIQUE_PROCEDURES')
    df = df.merge(unique_procedures, left_on='Id', right_on='PATIENT', how='left')
    df['UNIQUE_PROCEDURES'] = df['UNIQUE_PROCEDURES'].fillna(0)
    
    return df

def prepare_features(df, feature_names, label_encoders):
    """Prepare features for prediction using saved encoders"""
    # Define columns to exclude (same as in training)
    exclude_cols = [
        'Id', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT', 
        'PREFIX', 'FIRST', 'MIDDLE', 'LAST', 'SUFFIX', 'MAIDEN',
        'BIRTHPLACE', 'ADDRESS', 'CITY', 'STATE', 'COUNTY', 'FIPS', 
        'ZIP', 'LAT', 'LON', 'HEALTHCARE_EXPENSES', 'HEALTHCARE_COVERAGE', 'INCOME',
        'DEATH'  # target (may not be present in inference data)
    ]
    
    # Select feature columns
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Ensure we have all expected features
    missing_features = set(feature_names) - set(feature_cols)
    extra_features = set(feature_cols) - set(feature_names)
    
    if missing_features:
        print(f"Warning: Missing features: {missing_features}")
        # Add missing features with default values (0 for numeric, 'Unknown' for categorical)
        for feat in missing_features:
            df[feat] = 0  # Default to 0
    
    if extra_features:
        print(f"Warning: Extra features will be ignored: {list(extra_features)[:10]}...")
    
    # Select and order features as expected by model
    X = df[feature_names].copy()
    
    # Handle missing values
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    categorical_cols = X.select_dtypes(exclude=[np.number]).columns
    
    for col in numeric_cols:
        X[col] = X[col].fillna(X[col].median())
    
    for col in categorical_cols:
        if col in label_encoders:
            le = label_encoders[col]
            # Handle unseen labels
            X[col] = X[col].astype(str)
            known_classes = set(le.classes_)
            X[col] = X[col].apply(lambda x: x if x in known_classes else le.classes_[0])
            X[col] = le.transform(X[col])
        else:
            # If no encoder, treat as numeric if possible, else fill with 0
            try:
                X[col] = pd.to_numeric(X[col], errors='coerce')
                X[col] = X[col].fillna(X[col].median())
            except:
                X[col] = 0
    
    return X

def predict_mortality(patients_df, encounters_df, conditions_df, observations_df, 
                     medications_df, procedures_df, model_dir="backend/ml/models"):
    """Main function to predict mortality risk"""
    print("Loading model artifacts...")
    model, scaler, label_encoders, feature_names = load_model_artifacts(model_dir)
    
    print("Engineering features...")
    df = engineer_features_for_inference(
        patients_df, encounters_df, conditions_df, 
        observations_df, medications_df, procedures_df
    )
    
    print("Preparing features...")
    X = prepare_features(df, feature_names, label_encoders)
    
    print("Scaling features...")
    X_scaled = scaler.transform(X)
    
    print("Making predictions...")
    mortality_prob = model.predict_proba(X_scaled)[:, 1]
    mortality_pred = model.predict(X_scaled)
    
    # Add predictions to patient dataframe
    df_result = df[['Id']].copy()
    df_result['MORTALITY_PROBABILITY'] = mortality_prob
    df_result['MORTALITY_PREDICTION'] = mortality_pred
    
    return df_result

# ----------------------------
# 4. Example Usage
# ----------------------------
if __name__ == '__main__':
    print("Synthea Mortality Prediction Inference Script")
    print("=" * 50)
    print("This script demonstrates how to use the trained mortality model.")
    print("To use it:")
    print("1. Train the model first using synthea_mortality_train.py")
    print("2. Ensure the model artifacts are in backend/ml/models/")
    print("3. Call predict_mortality() with your Synthea dataframes")
    print("")
    print("Example usage:")
    print("  predictions = predict_mortality(patients, encounters, conditions,")
    print("                                   observations, medications, procedures)")
    print("  print(predictions[['Id', 'MORTALITY_PROBABILITY', 'MORTALITY_PREDICTION']].head())")
