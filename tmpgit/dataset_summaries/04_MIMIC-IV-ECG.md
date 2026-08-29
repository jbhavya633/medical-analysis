# MIMIC-IV-ECG Dataset Summary

## Dataset Overview
- **Name**: MIMIC-IV-ECG
- **Modality**: Electrocardiogram (ECG) waveforms and measurements
- **Primary Use**: Diagnostic electrocardiograms for cardiac rhythm analysis, ischemia detection, and cardiovascular risk stratification

## Key Characteristics
- **Size**: Approximately 90.4 GB uncompressed
- **ECGs**: ~800,000 diagnostic ECGs
- **Patients**: ~160,000 unique patients
- **ECG Specifications**:
  - 12-lead standard electrocardiograms
  - 10-second duration per recording
  - 500 Hz sampling rate
  - Digital signal format
- **Overlap**: Patients overlap with MIMIC-IV cohort enabling multimodal studies

## Access Information
- **Official Source**: [MIMIC-IV-ECG](https://physionet.org/content/mimic-iv-ecg/?utm_source=chatgpt.com)
- **Access Type**: Credentialed PhysioNet access required
- **License**: PhysioNet Credentialed Health Data License 1.5.0
- **Citation**: Gago-Silva, V., et al. (2021). MIMIC-IV-ECG: Diagnostic Electrocardiogram Matched Subset. PhysioNet. https://doi.org/10.13026/0p8f-6q65

## Linkage Capabilities
MIMIC-IV-ECG links directly to:
- **MIMIC-IV**: Via subject_id for comprehensive clinical context
- **MIMIC-IV-ED**: For ECGs obtained in emergency department
- **MIMIC-IV-Note**: For ECG interpretation reports and clinical context
- Enables ECG-EHR fusion studies

## Recommended Use in MedFusion AI
- **ECG Analysis Component**: Automated ECG interpretation and arrhythmia detection
- **Cardiovascular Risk Prediction**: Long-term risk stratification from ECG features
- **Ischemia and Infarction Detection**: Acute coronary syndrome identification
- ** ventricular hypertrophy and electrolyte abnormality screening
- **Drug Effect Monitoring**: QT interval and other drug-induced changes
- **Baseline Cardiac Status**: Pre-procedure cardiac assessment

## Suggested ML Tasks
- Arrhythmia classification (AFib, ventricular tachycardia, heart block, etc.)
- Myocardial infarction detection (STEMI/NSTEMI identification)
- Interval measurement automation (PR, QRS, QT, QTc)
- Axis and hypertrophy detection (left/right ventricular hypertrophy)
- Electrolyte abnormality screening (hyperkalemia, hypokalemia signs)
- ECG-to-clinical outcome prediction (mortality, readmission)
- Multimodal fusion with labs (troponin, BNP) and symptoms (chest pain)
- Few-shot learning for rare ECG patterns
- Unsupervised representation learning for ECG embeddings

## File Structure & Formats
- Organized by subject_id directories
- Each ECG stored as:
  - Header file (.hea) with metadata (sampling rate, baseline, etc.)
  - Signal file (.dat) in binary format (16-bit integer samples)
- Waveform database format (WFDB) compatible with PhysioNet toolkits
- Metadata includes: age, sex, acquisition time, technician notes

## Important Notes
- One of the largest publicly available ECG datasets with rich clinical linkage
- Enables study of ECG changes across hospitalizations and longitudinally
- High sampling rate preserves fine waveform details for advanced analysis
- Includes both diagnostic and monitoring ECGs (though primarily diagnostic)
- Complementary to PTB-XL which has more detailed cardiologist annotations
