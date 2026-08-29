# AutoPET Dataset Summary

## Dataset Overview
- **Name**: AutoPET
- **Modality**: Positron Emission Tomography (PET) and Computed Tomography (CT) hybrid imaging
- **Primary Use**: Automated lesion segmentation in whole-body PET/CT, particularly for oncology

## Key Characteristics
- **Size**: Large multimodal imaging dataset
- **Patients**: Number varies by challenge iteration (typically hundreds to thousands)
- **Studies**: Whole-body PET/CT scans
- **Tracer**: Primarily FDG (fluorodeoxyglucose) for glucose metabolism imaging
- **Imaging Specifications**:
  - PET: metabolic activity imaging (Standardized Uptake Values - SUV)
  - CT: anatomical localization (low-dose diagnostic or attenuation correction)
  - Fusion: co-registered PET and CT images
  - Whole-body coverage: from skull base to mid-thigh (or entire body depending on protocol)
  - Variable voxel size depending on reconstruction parameters
  - Time-stamped acquisition (uptake time post-injection recorded)
- **Annotations**:
  - Tumor lesion segmentations (primary challenge focus)
  - Lesion markings by nuclear medicine physicians and radiologists
  - Standardized uptake value (SUV) measurements
  - Lymph node involvement assessment
  - Skeletal metastasis detection
  - Treatment response evaluation (PERCIST criteria)

## Access Information
- **Official Source**: [AutoPET Grand Challenge](https://autopet.grand-challenge.org/Dataset/?utm_source=chatgpt.com)
- **Access Type**: Open access via registration (Grand Challenge platform)
- **License**: Typically Creative Commons Attribution-ShareAlike or similar (check challenge terms)
- **Citation**: To be cited according to the specific AutoPET challenge year (e.g., AutoPET 2021, AutoPET 2022)

## Linkage Capabilities
- **Rich quantitative imaging data** (SUV values, lesion volumes)
- **Can link to outcomes** if provided in challenge metadata (survival, treatment response)
- **Shares imaging modality** with TCIA and general PET/CT resources
- **Standardized formats** enable multi-institutional studies
- **DICOM standard** ensures compatibility with nuclear medicine and radiotherapy systems

## Recommended Use in MedFusion AI
- **PET/CT Analysis Component**: Automated tumor detection, segmentation, and treatment response assessment
- **Oncology Imaging**: Lesion detection in lymphoma, lung cancer, colorectal cancer, melanoma, etc.
- **Therapy Monitoring**: Tracking metabolic response to chemotherapy, immunotherapy, targeted therapy
- **Recurrence Detection**: Early identification of metastatic disease or local recurrence
- **Radiation Therapy Planning**: Defining gross tumor volume (GTV) and clinical target volume (CTV)
- **Prognostic Modeling**: Predicting survival and progression-free survival from baseline PET/CT
- **Biomarker Discovery**: Linking imaging features to genomic markers (if genomic data available)
- **Multimodal Fusion**: Combining PET metabolic data with CT anatomy and clinical labs

## Suggested ML Tasks
- Lesion segmentation: whole-body tumor delineation in PET/CT
- False positive reduction: distinguishing true tumors from physiological uptake (brown fat, muscle, gut)
- Lesion detection and counting: automated metastasis detection
- Treatment response assessment: PERCIST or EORTC criteria automation
- SUV quantification: automated measurement of maximum and mean SUV in lesions
- Lymph node assessment: cervical, axillary, mediastinal, pelvic chain evaluation
- Skeletal metastasis detection: identifying bone lesions from PET uptake
- Radiation dose prediction: estimating tumor dose from imaging features
- Few-shot learning for rare cancer types
- Domain adaptation: transferring models between tracers (FDG, PSMA, choline, etc.)
- Uncertainty quantification: confidence estimates for automated lesion segmentations

## File Structure & Formats
- Organized by patient_id directories
- Each patient study includes:
  - PET series in DICOM format (.dcm files)
  - CT series in DICOM format (.dcm files)
  - Metadata: patient demographics, injection time, uptake time, tracer dose
  - Annotation files: lesion segmentations (when provided) in DICOM RTSTRUCT or contour format
  - Potential: SUV maps, parametric images, or derived quantitative maps
- Standard DICOM headers include: scanner model, reconstruction algorithm, slice thickness, etc.
- Compatible with: 3D Slicer, ITK-SimpleITK, PYMEDICAL, TensorFlow, PyTorch
- Preprocessed versions often available: numpy arrays, NRRD format, etc.
- Segmentation tasks typically use Dice coefficient, Hausdorff distance, etc. for evaluation

## Important Notes
- **Grand Challenge format** ensures high-quality annotations and standardized evaluation
- Focuses on the technically challenging task of whole-body lesion segmentation
- Longitudinal data available in some iterations (enabling response tracking)
- Complementary to general TCIA resources with specific oncology imaging focus
- Forms foundation for oncology AI applications in MedFusion AI
- Valuable for developing AI-assisted nuclear medicine and radiotherapy workflows
- Addresses a critical need in oncology: automated tumor burden quantification
