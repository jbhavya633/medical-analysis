# MIMIC-IV-Note Dataset Summary

## Dataset Overview
- **Name**: MIMIC-IV-Note
- **Modality**: Clinical text documentation
- **Primary Use**: Doctor notes, discharge summaries, clinical narratives, radiology reports, and longitudinal clinical NLP

## Key Characteristics
- **Size**: Large clinical note repository
- **Patients**: Overlap with MIMIC-IV patient population
- **Notes**: Hundreds of thousands of clinical documents
- **Document Types**:
  - Physician and nursing progress notes
  - Discharge summaries
  - Emergency department notes
  - Radiology reports
  - Echocardiogram reports
  - Electrocardiogram interpretations
  - Consultation reports
  - Procedure notes

## Access Information
- **Official Source**: [MIMIC-IV-Note](https://physionet.org/content/mimic-iv-note/?utm_source=chatgpt.com)
- **Access Type**: Credentialed PhysioNet access required
- **License**: PhysioNet Credentialed Health Data License 1.5.0
- **Citation**: To be cited as part of MIMIC-IV ecosystem; specific citation pending official release

## Linkage Capabilities
MIMIC-IV-Note links directly to:
- **MIMIC-IV**: Via subject_id and hadm_id
- **MIMIC-IV-ED**: For ED-specific notes
- **MIMIC-CXR**: For radiology reports linked to chest X-rays
- **MIMIC-IV-Echo**: For echocardiogram reports
- **MIMIC-IV-ECG**: For ECG interpretation reports

## Recommended Use in MedFusion AI
- **AI Medical-Record Assistant**: Core dataset for clinical NLP applications
- **Report Generation**: Automated discharge summary and report creation
- **Clinical Coding**: Automatic ICD code assignment from clinical text
- ** phenotyping**: Identifying patient cohorts using NLP criteria
- **Symptom Extraction**: Pulling symptoms and signs from unstructured text
- **Medication Reconciliation**: Extracting medication lists from notes
- **Question Answering**: Clinical information retrieval from patient records

## Suggested ML Tasks
- Clinical named entity recognition (diseases, medications, anatomy)
- Relation extraction (e.g., medication-dose, problem-treatment)
- Text classification (note type, urgency, sentiment)
- Sequence-to-sequence models for report generation
- Information extraction for structured data completion
- Transfer learning from biomedical language models (BioBERT, ClinicalBERT)
- Multimodal fusion with structured EHR data and imaging reports

## File Structure & Formats
- CSV file containing note metadata: subject_id, hadm_id, chartdate, charttime, category, description, etc.
- Separate directory containing the actual note text files (.txt)
- Timestamps enable alignment with clinical events in MIMIC-IV
- Category field indicates note type (e.g., 'Nursing', 'Physician ', 'Radiology')

## Important Notes
- Contains de-identified clinical text following HIPAA-safe harbor guidelines
- Enables study of clinical documentation practices and communication
- Radiology reports can be linked to MIMIC-CXR images for vision-language tasks
- Discharge summaries provide comprehensive episode summaries
- Longitudinal availability enables tracking of clinical narrative evolution
