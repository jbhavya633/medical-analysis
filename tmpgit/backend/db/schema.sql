-- Supabase PostgreSQL schema for MedFusion AI project
-- Created based on MIMIC-IV and other medical datasets
-- Tables for patients, admissions, ICU stays, ED stays, chartevents, labevents, prescriptions, etc.

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS prescription CASCADE;
DROP TABLE IF EXISTS outputevent CASCADE;
DROP TABLE IF EXISTS inputevent CASCADE;
DROP TABLE IF EXISTS procedureevent CASCADE;
DROP TABLE IF EXISTS datetimeevent CASCADE;
DROP TABLE IF EXISTS microbiologyevent CASCADE;
DROP TABLE IF EXISTS transfusion CASCADE;
DROP TABLE IF EXISTS chartevent CASCADE;
DROP TABLE IF EXISTS labevent CASCADE;
DROP TABLE IF EXISTS icustay CASCADE;
DROP TABLE IF EXISTS edstay CASCADE;
DROP TABLE IF EXISTS admission CASCADE;
DROP TABLE IF EXISTS patient CASCADE;
DROP TABLE IF EXISTS noteevent CASCADE;
DROP TABLE IF EXISTS ecg_waveform CASCADE;
DROP TABLE IF EXISTS ecg_measurement CASCADE;
DROP TABLE IF EXISTS cxr_study CASCADE;
DROP TABLE IF EXISTS cxr_report CASCADE;
DROP TABLE IF EXISTS echo_study CASCADE;
DROP TABLE IF EXISTS echo_report CASCADE;
DROP TABLE IF EXISTS imaging_study CASCADE;
DROP TABLE IF EXISTS imaging_report CASCADE;
DROP TABLE IF EXISTS specimen CASCADE;
DROP TABLE IF EXISTS drug CASCADE;
DROP TABLE IF EXISTS caregiver CASCADE;
DROP TABLE IF EXISTS location CASCADE;

-- Patient demographics
CREATE TABLE patient (
    subject_id INTEGER PRIMARY KEY,
    gender VARCHAR(5) NOT NULL,
    anchor_age INTEGER,
    anchor_year INTEGER,
    anchor_year_group VARCHAR(20),
    dod TIMESTAMP, -- date of death
    -- Additional demographics can be added as needed
    ethnicity VARCHAR(50),
    marital_status VARCHAR(20),
    insurance VARCHAR(50),
    language VARCHAR(10),
    religion VARCHAR(50)
);

-- Hospital admissions
CREATE TABLE admission (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER PRIMARY KEY,
    admittime TIMESTAMP NOT NULL,
    dischtime TIMESTAMP,
    deathtime TIMESTAMP,
    admission_type VARCHAR(20),
    admission_location VARCHAR(50),
    discharge_location VARCHAR(50),
    ethnicity VARCHAR(50), -- redundant with patient but kept for MIMIC-IV compatibility
    diagnosis VARCHAR(255), -- primary diagnosis description (could be a code, but we keep simple)
    -- Additional fields
    marital_status VARCHAR(20),
    insurance VARCHAR(50),
    language VARCHAR(10),
    religion VARCHAR(50),
    edregtime TIMESTAMP, -- ED registration time
    edouttime TIMESTAMP  -- ED exit time
);

-- ICU stays
CREATE TABLE icustay (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    stay_id INTEGER PRIMARY KEY,
    intime TIMESTAMP NOT NULL,
    outtime TIMESTAMP,
    los NUMERIC, -- length of stay in days
    first_careunit VARCHAR(50),
    last_careunit VARCHAR(50)
);

-- Emergency Department stays
CREATE TABLE edstay (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    stay_id INTEGER PRIMARY KEY,
    intime TIMESTAMP NOT NULL,
    outtime TIMESTAMP,
    los NUMERIC
);

-- Charted events (vitals, settings, etc.)
CREATE TABLE chartevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    stay_id INTEGER REFERENCES icustay(stay_id),
    charttime TIMESTAMP NOT NULL,
    storetime TIMESTAMP,
    itemid INTEGER NOT NULL,
    value VARCHAR(255),
    valuenum NUMERIC,
    valueuom VARCHAR(20),
    warning INTEGER,
    error INTEGER,
    -- We'll not create a foreign key to d_items for simplicity
    PRIMARY KEY (subject_id, hadm_id, charttime, itemid)
);

-- Laboratory events
CREATE TABLE labevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    specimen_id INTEGER,
    itemid INTEGER NOT NULL,
    charttime TIMESTAMP NOT NULL,
    value VARCHAR(255),
    valuenum NUMERIC,
    valueuom VARCHAR(20),
    flag VARCHAR(10),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, specimen_id, charttime, itemid)
);

-- Prescriptions
CREATE TABLE prescription (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    pharmacy_id INTEGER,
    starttime TIMESTAMP NOT NULL,
    stoptime TIMESTAMP,
    drug_type VARCHAR(50), -- e.g., 'Antibiotic', 'Vasopressor'
    drug VARCHAR(100) NOT NULL, -- drug name as text
    gsndrugname VARCHAR(100), -- generic name
    form_val_disp NUMERIC,
    form_unit_disp VARCHAR(20),
    form_val_ord NUMERIC,
    form_unit_ord VARCHAR(20),
    route VARCHAR(20), -- e.g., 'IV', 'PO'
    -- Additional fields
    PRIMARY KEY (subject_id, hadm_id, pharmacy_id, starttime)
);

-- Input events (medications, fluids given)
CREATE TABLE inputevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    stay_id INTEGER REFERENCES icustay(stay_id),
    starttime TIMESTAMP NOT NULL,
    endtime TIMESTAMP,
    itemid INTEGER NOT NULL,
    amount NUMERIC,
    amountuom VARCHAR(20),
    rate NUMERIC,
    rateuom VARCHAR(20),
    orderid NUMERIC,
    linkorderid NUMERIC,
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, starttime, itemid)
);

-- Output events (urine output, etc.)
CREATE TABLE outputevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    stay_id INTEGER REFERENCES icustay(stay_id),
    charttime TIMESTAMP NOT NULL,
    itemid INTEGER NOT NULL,
    value NUMERIC,
    valueuom VARCHAR(20),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, charttime, itemid)
);

-- Procedure events
CREATE TABLE procedureevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    stay_id INTEGER REFERENCES icustay(stay_id),
    starttime TIMESTAMP NOT NULL,
    endtime TIMESTAMP,
    itemid INTEGER NOT NULL,
    value NUMERIC,
    valueuom VARCHAR(20),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, starttime, itemid)
);

-- Datetime events
CREATE TABLE datetimeevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    stay_id INTEGER REFERENCES icustay(stay_id),
    starttime TIMESTAMP NOT NULL,
    endtime TIMESTAMP,
    itemid INTEGER NOT NULL,
    value TIMESTAMP,
    valueuom VARCHAR(20),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, starttime, itemid)
);

-- Microbiology events
CREATE TABLE microbiologyevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    spec_itemid INTEGER,
    spec_type_desc VARCHAR(100),
    spec NUMERIC,
    seq_num INTEGER,
    chartdate DATE,
    charttime TIMESTAMP,
    org_itemid INTEGER,
    org_name VARCHAR(100),
    isol_num INTEGER,
    antibiot_itemid INTEGER,
    antibiot_name VARCHAR(100),
    dilution_comparison VARCHAR(20),
    dilution_value NUMERIC,
    interpreted_antibiot VARCHAR(10),
    sensitivity VARCHAR(10),
    resistance VARCHAR(10),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, spec_itemid, spec_type_desc, spec, seq_num, chartdate, charttime, org_itemid, isol_num, antibiot_itemid)
);

-- Transfusions
CREATE TABLE transfusion (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    starttime TIMESTAMP NOT NULL,
    endtime TIMESTAMP,
    itemid INTEGER NOT NULL,
    amount NUMERIC,
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, starttime, itemid)
);

-- Drug reference table (optional, for standardization)
CREATE TABLE drug (
    drug_id SERIAL PRIMARY KEY,
    gsndrugname VARCHAR(100) UNIQUE,
    atc_code VARCHAR(10),
    -- Additional properties
);

-- Caregiver / Provider
CREATE TABLE caregiver (
    caregiver_id SERIAL PRIMARY KEY,
    caregiver_name VARCHAR(100) NOT NULL
);

-- Location (hospital wards, etc.)
CREATE TABLE location (
    location_id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50) -- e.g., 'ICU', 'ED', 'Floor'
);

-- Note events (clinical notes, discharge summaries, radiology reports, etc.)
CREATE TABLE noteevent (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    chartdate DATE,
    charttime TIMESTAMP,
    storetime TIMESTAMP,
    category VARCHAR(50), -- e.g., 'Nursing', 'Physician ', 'Radiology', 'Echo', 'ECG'
    description VARCHAR(200),
    cgid INTEGER REFERENCES caregiver(caregiver_id),
    iserror CHAR(1), -- '0' or '1'
    text TEXT NOT NULL,
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, charttime)
);

-- ECG waveform metadata (links to actual waveform files stored elsewhere)
CREATE TABLE ecg_waveform (
    subject_id INTEGER REFERENCES patient(subject_id),
    study_id INTEGER PRIMARY KEY,
    storetime TIMESTAMP,
    acqtime TIMESTAMP, -- acquisition time
    ecg_time TIMESTAMP, -- time of ECG
    -- File information
    filename VARCHAR(255),
    filepath VARCHAR(255),
    -- Signal metadata
    sampling_frequency INTEGER,
    num_leads INTEGER,
    signal_length INTEGER, -- number of samples
    -- Quality indicators
    qrs_count INTEGER,
    avg_heart_rate NUMERIC,
    -- We can add more as needed
);

-- ECG measurements (derived from waveform or provided)
CREATE TABLE ecg_measurement (
    subject_id INTEGER REFERENCES patient(subject_id),
    study_id INTEGER REFERENCES ecg_waveform(study_id),
    itemid INTEGER NOT NULL, -- e.g., heart rate, PR interval, QRS duration, QT, etc.
    value NUMERIC,
    valueuom VARCHAR(20),
    -- Primary key
    PRIMARY KEY (subject_id, study_id, itemid)
);

-- Chest X-ray study metadata
CREATE TABLE cxr_study (
    subject_id INTEGER REFERENCES patient(subject_id),
    study_id INTEGER PRIMARY KEY,
    dicom_id VARCHAR(50),
    storetime TIMESTAMP,
    acqtime TIMESTAMP,
    -- Study description
    modality VARCHAR(10) DEFAULT 'CXR',
    bodypart VARCHAR(20),
    -- View position
    view_position VARCHAR(10),
    -- File information
    filename VARCHAR(255),
    filepath VARCHAR(255),
    -- Optional: foreign key to admission or icustay if applicable
    hadm_id INTEGER REFERENCES admission(hadm_id)
);

-- Chest X-ray reports
CREATE TABLE cxr_report (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    charttime TIMESTAMP,
    storetime TIMESTAMP,
    report_text TEXT,
    impression TEXT,
    findings TEXT,
    -- Link to study
    study_id INTEGER REFERENCES cxr_study(study_id),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, charttime)
);

-- Echocardiogram study metadata
CREATE TABLE echo_study (
    subject_id INTEGER REFERENCES patient(subject_id),
    study_id INTEGER PRIMARY KEY,
    dicom_id VARCHAR(50),
    storetime TIMESTAMP,
    acqtime TIMESTAMP,
    modality VARCHAR(10) DEFAULT 'Echo',
    bodypart VARCHAR(20) DEFAULT 'Heart',
    -- File information
    filename VARCHAR(255),
    filepath VARCHAR(255),
    -- Link to admission
    hadm_id INTEGER REFERENCES admission(hadm_id)
);

-- Echocardiogram reports
CREATE TABLE echo_report (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    charttime TIMESTAMP,
    storetime TIMESTAMP,
    report_text TEXT,
    impression TEXT,
    findings TEXT,
    -- Measurements (we can have a separate table for echo measurements, but for simplicity we put key measurements here)
    lv_ef NUMERIC, -- left ventricular ejection fraction
    lv_lvdiastolic NUMERIC,
    -- etc.
    -- Link to study
    study_id INTEGER REFERENCES echo_study(study_id),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, charttime)
);

-- General imaging study for other modalities (CT, MRI, PET, etc.)
CREATE TABLE imaging_study (
    subject_id INTEGER REFERENCES patient(subject_id),
    study_id INTEGER PRIMARY KEY,
    dicom_id VARCHAR(50),
    storetime TIMESTAMP,
    acqtime TIMESTAMP,
    modality VARCHAR(20), -- e.g., 'CT', 'MRI', 'PT', 'PET', 'US'
    bodypart VARCHAR(50),
    -- File information
    filename VARCHAR(255),
    filepath VARCHAR(255),
    -- Link to admission
    hadm_id INTEGER REFERENCES admission(hadm_id)
);

-- General imaging reports
CREATE TABLE imaging_report (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    charttime TIMESTAMP,
    storetime TIMESTAMP,
    report_text TEXT,
    impression TEXT,
    findings TEXT,
    -- Link to study
    study_id INTEGER REFERENCES imaging_study(study_id),
    -- Primary key
    PRIMARY KEY (subject_id, hadm_id, charttime)
);

-- Specimen table (for lab, microbiology, etc.)
CREATE TABLE specimen (
    subject_id INTEGER REFERENCES patient(subject_id),
    hadm_id INTEGER REFERENCES admission(hadm_id),
    specimen_id INTEGER PRIMARY KEY,
    spec_type_desc VARCHAR(100),
    spec_derived VARCHAR(100),
    -- Child specimen if applicable
    child_present CHAR(1),
    -- Add more as needed
);

-- Insert some sample data for testing (optional)
-- We'll skip sample data for now.

-- Add comments to tables and columns for clarity
COMMENT ON TABLE patient IS 'Patient demographics';
COMMENT ON TABLE admission IS 'Hospital admissions';
COMMENT ON TABLE icustay IS 'ICU stays';
COMMENT ON TABLE edstay IS 'Emergency department stays';
COMMENT ON TABLE chartevent IS 'Charted data (vitals, settings, etc.)';
COMMENT ON TABLE labevent IS 'Laboratory results';
COMMENT ON TABLE prescription IS 'Medication prescriptions';
COMMENT ON TABLE inputevent IS 'Input events (medications, fluids)';
COMMENT ON TABLE outputevent IS 'Output events (urine output, etc.)';
COMMENT ON TABLE procedureevent IS 'Procedure events';
COMMENT ON TABLE datetimeevent IS 'Datetime events';
COMMENT ON TABLE microbiologyevent IS 'Microbiology cultures';
COMMENT ON TABLE transfusion IS 'Blood product transfusions';
COMMENT ON TABLE drug IS 'Drug reference';
COMMENT ON TABLE caregiver IS 'Caregivers / providers';
COMMENT ON TABLE location IS 'Hospital locations';
COMMENT ON TABLE noteevent IS 'Clinical notes and reports';
COMMENT ON TABLE ecg_waveform IS 'ECG waveform metadata';
COMMENT ON TABLE ecg_measurement IS 'ECG measurements';
COMMENT ON TABLE cxr_study IS 'Chest X-ray study metadata';
COMMENT ON TABLE cxr_report IS 'Chest X-ray reports';
COMMENT ON TABLE echo_study IS 'Echocardiogram study metadata';
COMMENT ON TABLE echo_report IS 'Echocardiogram reports';
COMMENT ON TABLE imaging_study IS 'General imaging study (CT, MRI, PET, etc.)';
COMMENT ON TABLE imaging_report IS 'General imaging reports';
COMMENT ON TABLE specimen IS 'Specimens for lab and microbiology';

-- End of schema

