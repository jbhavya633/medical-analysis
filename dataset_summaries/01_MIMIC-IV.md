# MIMIC-IV Dataset Summary

## Dataset Overview
- **Name**: MIMIC-IV (Medical Information Mart for Intensive Care, Version 4)
- **Modality**: Electronic Health Records (EHR), Laboratory data, Clinical documentation
- **Primary Use**: Clinical/EHR backbone for patient admissions, diagnoses, medications, procedures, ICU/hospital data

## Key Characteristics
- **Size**: Very large clinical database
- **Patients**: ~70,000+ unique patients (based on MIMIC-III scale; MIMIC-IV has similar or larger cohort)
- **Encounters**: Multiple hospital admissions per patient possible
- **Data Types**: 
  - Patient demographics
  - Admission and transfer information
  - Diagnosis codes (ICD-9/ICD-10)
  - Laboratory measurements
  - Medication prescriptions
  - Procedure codes
  - ICU stay details
  - Vital signs and charted events
  - Clinical notes (via linked MIMIC-IV-Note)

## Access Information
- **Official Source**: [MIMIC-IV official dataset](https://physionet.org/content/mimiciv/?utm_source=chatgpt.com)
- **Access Type**: Credentialed PhysioNet access required
- **License**: PhysioNet Credentialed Health Data License 1.5.0
- **Citation**: Johnson, A., Pollard, T., Shen, L., Lehman, L., Feng, M., Ghassemi, M., Moody, B., Szolovits, P., Celi, L. A., & Mark, R. G. (2020). MIMIC-IV, a freely accessible electronic health record dataset. Scientific data, 7(1), 1-13.

## Linkage Capabilities
MIMIC-IV is explicitly designed to link with:
- **MIMIC-IV-ED**: Emergency department data
- **MIMIC-IV-Note**: Clinical notes and discharge summaries  
- **MIMIC-CXR**: Chest X-ray images and reports
- **MIMIC-IV-ECG**: Electrocardiogram waveforms and measurements

## Recommended Use in MedFusion AI
- **Patient Backbone**: Core patient identifiers, demographics, and encounter tracking
- **Clinical History**: Longitudinal patient history through multiple admissions
- **Symptoms & Vitals**: Chief complaints, triage data, vital signs from ED and inpatient stays
- **Laboratory Results**: Comprehensive lab measurements (chemistry, hematology, microbiology)
- **Medications**: Inpatient and outpatient medication administrations
- **Procedures**: Surgical and medical procedures performed during encounters
- **ICU Data**: Detailed intensive care monitoring and interventions

## Suggested ML Tasks
- Patient risk stratification and mortality prediction
- Phenotyping and subgroup discovery
- Length of stay and readmission prediction
- Clinical trial matching and cohort selection
- Multimodal fusion with ECG, imaging, and notes data
- Temporal modeling of disease progression

## File Structure & Formats
- CSV files organized by subject ID directories
- Tables include: patients, admissions, icustays, chartevents, labevents, prescriptions, procedureevents, inputevents, outputevents, datetimeevents, microbiologyevents, transfusions, etc.
- Timestamps provided for all events enabling temporal analysis

## Important Notes
- Forms the foundational dataset for multimodal integration in MedFusion AI
- Explicit linkage keys (subject_id, hadm_id, stay_id) enable joining with other MIMIC-derived datasets
- Contains both structured data (codes, measurements) and unstructured data (via linked notes)
- Version 3.0 is currently available as of the recommendation date
