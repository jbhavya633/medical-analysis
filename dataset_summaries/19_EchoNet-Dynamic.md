# EchoNet-Dynamic Dataset Summary

## Dataset Overview
- **Name**: EchoNet-Dynamic
- **Modality**: Echocardiogram (ultrasound) video clips with ejection fraction measurements
- **Primary Use**: Automated cardiac function assessment from echocardiogram videos, particularly left ventricular ejection fraction estimation

## Key Characteristics
- **Size**: Large video-based echocardiography dataset
- **Video Clips**: Approximately 10,000+ echocardiogram videos
- **Patients**: Several thousand unique patients
- **Video Specifications**:
  - Echocardiogram loops acquired during clinical studies
  - Primarily apical views (4-chamber, 2-chamber, long-axis)
  - Variable frame rates (typically 50-60 fps)
  - Variable duration (typically 3-6 seconds per clip)
  - Grayscale intensity values
  - Standardized depth and sector settings where available
- **Annotations**:
  - Left ventricular ejection fraction (LVEF) as primary outcome
  - End-diastolic and end-systolic frame identifiers
  - Left ventricular cavity tracing (endocardial border) in some versions
  - Patient demographics: age, sex, height, weight
  - Indications for echocardiography
  - Image quality assessments
- **Image Characteristics**:
  - Standard grayscale ultrasound format
  - May include contrast-enhanced studies (subset)
  - Both pediatric and adult studies (depending on version)
  - Various probe types (pediatric vs adult phased array)

## Access Information
- **Official Source**: [EchoNet-Dynamic](https://echonet.github.io/dynamic) (primary site - verify current URL)
- **Access Type**: Open access (typically via GitHub or similar platform)
- **License**: Typically MIT or similar permissive license (verify specific terms)
- **Citation**: To be cited according to the official EchoNet-Dynamic publication

## Linkage Capabilities
- **Limited clinical linkage** beyond basic demographics and echo indications
- **Rich phenotypic data** available for cardiac function studies
- **Shares imaging modality** with MIMIC-IV-Echo (different format: videos vs DICOM volumes)
- **Standardized view acquisition** enables comparison across studies
- **Quantitative measurements** (LVEF) provide supervised learning targets

## Recommended Use in MedFusion AI
- **Echocardiography Video Analysis**: Automated ejection fraction estimation from echo clips
- **Cardiac Function Screening**: Rapid assessment of systolic function in point-of-care settings
- **Telemedicine Applications**: Enabling remote cardiac function evaluation
- **Quality Control**: Automated detection of suboptimal image quality
- **Pediatric Cardiology**: Where applicable (children and congenital heart disease)
- **Stress Echocardiography**: Where stress-induced clips are available
- **Comparison to MIMIC-IV-Echo**: Complementary resource with different data format (clips vs volumes)

## Suggested ML Tasks
- Ejection fraction regression: estimating LVF from echocardiogram videos
- Frame identification: detecting end-diastolic and end-systolic frames
- Segmentation: left ventricular cavity tracing for volumetry
- Quality assessment: determining diagnostic adequacy of echo clips
- View classification: identifying apical 4-chamber, 2-chamber, long-axis views
- Motion analysis: quantifying regional wall motion abnormalities
- Temporal analysis: tracking cardiac function changes over time (if longitudinal)
- Few-shot learning for rare cardiac conditions
- Domain adaptation: transferring models between probe types and settings
- Unsupervised learning: discovering novel cardiac motion phenotypes
- Multimodal fusion: combining video features with patient demographics and clinical data

## File Structure & Formats
- Organized by patient_id or video_id directories
- Each video clip includes:
  - Echocardiogram video in standard format (.mp4, .avi, or .mov)
  - Metadata file (.csv or .json) with patient details and measurements
  - Annotation file(s): tracing coordinates, frame identifiers, quality scores
- Standardized naming conventions for easy tracking
- May include multiple views per patient (when available)
- Compatible with: OpenCV, scikit-video, TensorFlow, PyTorch video libraries
- Metadata typically in CSV format for easy integration
- Annotations may follow medical imaging or cardiology data standards
- Frame rates and timing information critical for accurate analysis

## Important Notes
- **Video-based complement to volume-based echocardiography datasets** like MIMIC-IV-Echo
- Enables study of cardiac motion dynamics rather than just static measurements
- Larger sample size than many clinical echocardiography video datasets
- Focuses on the clinically critical ejection fraction measurement
- Valuable for developing point-of-care ultrasound AI applications
- Forms foundation for cardiology AI components in MedFusion AI
- Note: Specific details (exact size, annotations, access) should be verified from the official EchoNet-Dynamic release
