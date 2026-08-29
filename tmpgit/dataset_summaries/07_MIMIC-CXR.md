# MIMIC-CXR Dataset Summary

## Dataset Overview
- **Name**: MIMIC-CXR (Medical Information Mart for Intensive Care Chest X-ray)
- **Modality**: Chest radiographs (X-ray) with associated radiology reports
- **Primary Use**: Chest X-ray interpretation, disease detection, and multimodal vision-language learning

## Key Characteristics
- **Size**: Large imaging dataset
- **Chest X-rays**: 377,000+ frontal and lateral chest radiographs
- **Patients**: Overlap with MIMIC-IV cohort (~200,000+ unique patients)
- **Studies**: ~220,000+ chest X-ray studies (one study may have multiple views)
- **Image Specifications**:
  - Digital chest radiographs (primarily posterior-anterior and lateral views)
  - Variable resolution (typically 2048x2048 or similar)
  - DICOM format
  - Grayscale intensity values
- **Reports**: Associated radiology findings and impression sections

## Access Information
- **Official Source**: [MIMIC-CXR](https://physionet.org/content/mimic-cxr/?utm_source=chatgpt.com)
- **Access Type**: Credentialed PhysioNet access required
- **License**: PhysioNet Credentialed Health Data License 1.5.0
- **Citation**: Johnson, A. W., et al. (2019). MIMIC-CXR-JPG, a large publicly available database of labeled chest radiographs. arXiv preprint arXiv:1901.07042.

## Linkage Capabilities
MIMIC-CXR links directly to:
- **MIMIC-IV**: Via subject_id and hadm_id for comprehensive clinical context
- **MIMIC-IV-ED**: For chest X-rays obtained in emergency department
- **MIMIC-IV-Note**: For radiology reports and clinical documentation
- **MIMIC-IV-ECG**: For correlation between cardiac findings on ECG and CXR
- Enables comprehensive cardiopulmonary multimodal studies

## Recommended Use in MedFusion AI
- **Chest X-ray Analysis Component**: Automated abnormality detection and report generation
- **Disease Screening**: Pneumonia, heart failure, pneumothorax, nodules, fibrosis detection
- **Cardiac Silhouette Analysis**: Cardiomegaly, pulmonary edema, aortic calcification
- **Tube and Line Placement**: Endotracheal tube, central line, PICC position verification
- **Change Detection**: Comparison of prior and current studies for interval change
- **Report Generation**: Automated radiology report creation from images
- **Visual Question Answering**: Answering clinical questions about chest X-rays

## Suggested ML Tasks
- Classification of common CXR findings (atelectasis, cardiomegaly, effusion, infiltrate, nodule, pneumothorax, fracture)
- Multi-label detection of thoracic pathologies
- Segmentation of lungs, heart, clavicles, and diaphragm
- Registration and change detection between serial studies
- Report generation from images (image-to-text translation)
- Visual question answering (VQA) on chest radiographs
- Few-shot learning for rare radiographic findings
- Domain adaptation from natural images to medical radiographs
- Multimodal fusion with clinical data (symptoms, labs, ECG) for improved diagnosis
- Temporal analysis of disease progression using serial imaging

## File Structure & Formats
- Organized by subject_id/study_id directories
- Each study contains:
  - DICOM files (.dicom) for each view (PA, lateral, etc.)
  - Optional JPG previews for quick viewing
  - Associated reports in text format (when available)
- Metadata CSV files: patient demographics, study date/time, view position, etc.
- Master listing linking images to reports and clinical encounters
- Compatible with DICOM software, Python libraries (pydicom), and deep learning frameworks
- Pixel values typically stored as 16-bit integers with rescale slope/intercept

## Important Notes
- **Strong linkage to MIMIC-IV** enables rich clinical context for imaging studies
- Includes both frontal and lateral views when available
- Reports provide ground truth for supervised learning (with appropriate NLP processing)
- Temporally resolved: enables studying changes over time
- Large scale supports training of deep learning models from scratch
- Complementary to CheXpert and CheXpert Plus which have different annotation styles
- Forms foundation for cardiopulmonary assessment in MedFusion AI
