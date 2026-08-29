# MIMIC-IV-Echo Dataset Summary

## Dataset Overview
- **Name**: MIMIC-IV-Echo
- **Modality**: Echocardiogram (ultrasound) imaging and reports
- **Primary Use**: Cardiac structure and function assessment, valve analysis, congenital heart disease screening

## Key Characteristics
- **Size**: Very large imaging dataset
- **Echocardiograms**: Over 200,000 studies
- **DICOM Files**: More than 500,000 echocardiogram DICOM files
- **Patients**: Overlap with MIMIC-IV cohort (~90,000+ unique patients based on preliminary data)
- **Study Types**:
  - Transthoracic echocardiography (TTE)
  - Transesophageal echocardiography (TEE)
  - Stress echocardiography
  - Contrast-enhanced echocardiography
  - Pediatric and fetal echocardiography (subset)
- **Imaging Modalities**:
  - 2D grayscale and color Doppler
  - M-mode
  - Spectral and tissue Doppler
  - 3D/4D echocardiography (where available)
  - Strain and strain rate imaging

## Access Information
- **Official Source**: [MIMIC-IV-Echo](https://physionet.org/content/mimic-iv-echo/?utm_source=chatgpt.com)
- **Access Type**: Credentialed PhysioNet access required
- **License**: PhysioNet Credentialed Health Data License 1.5.0
- **Citation**: To be cited as part of MIMIC-IV ecosystem; specific citation pending official release

## Linkage Capabilities
MIMIC-IV-Echo links directly to:
- **MIMIC-IV**: Via subject_id for comprehensive clinical context
- **MIMIC-IV-ED**: For echocardiograms performed in emergency department
- **MIMIC-IV-Note**: For echocardiogram interpretation reports
- **MIMIC-IV-ECG**: For correlation between ECG and echocardiographic findings
- Enables comprehensive cardiac multimodal studies

## Recommended Use in MedFusion AI
- **Echocardiography Analysis Component**: Automated cardiac chamber quantification, valve assessment, and function analysis
- **Cardiac Phenotyping**: Identification of cardiomyopathy, valvular heart disease, congenital abnormalities
- ** ventricular Function Analysis**: Ejection fraction, wall motion analysis, diastolic function assessment
- **Valve Disease Classification**: Stenosis, regurgitation, prolapse detection
- **Cardiac Mass and Vegetation Detection**: Tumor, thrombus, endocarditis identification
- **Pediatric Cardiac Applications**: Congenital heart disease screening (where applicable)

## Suggested ML Tasks
- Cardiac chamber segmentation and quantification (LV, RV, LA, RA volumes and dimensions)
- Ejection fraction estimation from 2D and 4D volumes
- Valve area calculation and stenosis severity grading
- Regurgitation quantification (jet area, vena contracta, PISA method)
- Wall motion scoring and abnormality detection
- Diastolic function grading (E/e', deceleration time, pulmonary vein flow)
- Automatic measurements: LV mass, atrial volume, aortic root diameter
- Pathology detection: cardiomyopathy, valvular heart disease, pericardial effusion
- Report generation: structured echo report creation from images and measurements
- Few-shot learning for rare cardiac pathologies
- Multimodal fusion with ECG (rhythm correlation) and labs (BNP, troponin)

## File Structure & Formats
- Organized by subject_id/study_id directories
- Each study contains:
  - DICOM files (.dcm) with echocardiographic images and loops
  - Structured reports (where available) in XML or text format
  - Potential metadata files with acquisition parameters
- DICOM standard ensures compatibility with medical imaging software
- May include both raw cine loops and single-frame images
- Header information contains: patient demographics, acquisition date, technician, indications

## Important Notes
- **Largest publicly available echocardiogram dataset** with linkage to rich EHR data
- Enables study of echocardiographic changes across hospitalizations and longitudinally
- DICOM format supports advanced post-processing and AI analysis pipelines
- Overlap with MIMIC-IV enables outcome-linked studies (mortality, readmission, HF hospitalization)
- Complementary to ECG data: ECG provides electrical activity, Echo provides mechanical function
- Valuable for developing AI-assisted echocardiography in resource-limited settings
