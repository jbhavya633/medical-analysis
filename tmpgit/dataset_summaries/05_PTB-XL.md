# PTB-XL Dataset Summary

## Dataset Overview
- **Name**: PTB-XL
- **Modality**: Electrocardiogram (ECG) waveforms with detailed annotations
- **Primary Use**: Large-scale ECG benchmark for arrhythmia detection, myocardial infarction classification, and cardiovascular disease screening

## Key Characteristics
- **Size**: Approximately 1.8 GB uncompressed
- **ECGs**: 21,801 12-lead ECGs
- **Patients**: 18,869 unique patients
- **ECG Specifications**:
  - 12-lead standard electrocardiograms
  - 10-second duration per recording
  - 500 Hz sampling rate (same as MIMIC-IV-ECG)
- **Annotations**:
  - Cardiologist-validated labels
  - 71 ECG statements (diagnostic categories)
  - Hierarchical classification system (diagnostic, subdiagnostic, superdiagnostic, format)
  - Stratified folds for cross-validation

## Access Information
- **Official Source**: [PTB-XL](https://physionet.org/content/ptb-xl/1.0.3/?utm_source=chatgpt.com)
- **Access Type**: Open access (PhysioNet)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Citation**: Wagner, P., et al. (2020). PTB-XL, a large publicly available electrocardiogram dataset. Scientific Data, 7(1), 1-15. https://doi.org/10.1038/s41597-020-0495-6

## Linkage Capabilities
- **Limited direct patient linkage** to MIMIC-IV (different cohort)
- **Can be used for pre-training** ECG models before fine-tuning on MIMIC-IV-ECG
- **Shares similar technical specifications** (500Hz, 12-lead, 10-sec) enabling model transfer
- **Contains rich annotations** useful for developing and validating ECG analysis algorithms

## Recommended Use in MedFusion AI
- **Pre-training Resource**: Large annotated dataset for initial ECG model training
- **Benchmarking**: Standardized evaluation of ECG analysis algorithms
- **Data Augmentation**: Supplemental ECG data for rare condition classes
- **Transfer Learning**: Domain adaptation from PTB-XL to MIMIC-IV-ECG
- **Algorithm Development**: Testing and validation of new ECG analysis techniques

## Suggested ML Tasks
- Multi-label classification of 71 ECG statements
- Hierarchical classification (diagnostic ? subdiagnostic ? superdiagnostic)
- Rare condition detection using focal loss or sampling strategies
- ECG age and sex prediction from waveforms
- Mortality risk prediction (when linked to outcome data in other cohorts)
- Quality control: lead noise detection and signal quality assessment
- Few-shot learning for underrepresented ECG patterns
- Unsupervised pretraining followed by supervised fine-tuning

## File Structure & Formats
- Organized by patient_id directories
- Each ECG record includes:
  - Raw signal data in .dat format (16-bit integer, 500Hz)
  - Header file (.hea) with metadata and annotation references
  - Annotation file (.atr) containing cardiologist labels
- CSV file providing metadata: age, sex, height, weight, nursing home status, etc.
- Master spreadsheet (ptbxl_database.csv) linking records to annotations and metadata
- Compatible with WFDB software and Python libraries (wfdb, ecgdetectors)

## Important Notes
- **Gold standard for ECG benchmarking** with expert cardiologist annotations
- Larger than previous PTB diagnostic database (PTB DB: 549 records)
- Includes both healthy controls and pathological cases
- Temporally resolved annotations available for some records
- Excellent complement to MIMIC-IV-ECG which has larger scale but less detailed per-ECG annotations
- Open access enables unrestricted use for research and commercial applications
