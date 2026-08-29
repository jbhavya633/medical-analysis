# Medical Dataset Summaries for MedFusion AI

This directory contains individual dataset summaries designed to be converted into PDF files for easy reference and distribution. Each summary provides comprehensive information about a specific medical dataset relevant to the MedFusion AI project.

## Contents

### Individual Dataset Summaries (01-19.md)
Each file contains detailed information about a specific medical dataset:

1. **01_MIMIC-IV.md** - Electronic Health Records backbone
2. **02_MIMIC-IV-ED.md** - Emergency department data
3. **03_MIMIC-IV-Note.md** - Clinical notes and documentation
4. **04_MIMIC-IV-ECG.md** - Electrocardiogram waveforms and measurements
5. **05_PTB-XL.md** - Large annotated ECG dataset
6. **06_MIMIC-IV-Echo.md** - Echocardiogram imaging and reports
7. **07_MIMIC-CXR.md** - Chest X-rays with radiology reports
8. **08_CheXpert.md** - Chest X-ray with pathology labels
9. **09_CheXpert-Plus.md** - Chest X-ray with reports and labels
10. **10_LIDC-IDRI.md** - Lung CT with nodule annotations
11. **11_Chest-CT-Sepsis.md** - Chest CT in sepsis patients
12. **12_TCIA.md** - Cancer imaging archive (CT, MRI, PET, etc.)
13. **13_BRSET.md** - Retinal photography with multilabel annotations
14. **14_ISIC.md** - Dermatological images with lesion annotations
15. **15_CDSL.md** - COVID-19 clinical data
16. **16_MIMIC-Ext-CXR-QBA.md** - Chest X-ray with 42M QA pairs
17. **17_AutoPET.md** - PET/CT for oncology lesion segmentation
18. **18_ADNI.md** - Alzheimer's neuroimaging with cognitive data
19. **19_EchoNet-Dynamic.md** - Echocardiogram videos with EF measurements

### Dataset Mapping (20_MedFusion-Dataset-Mapping.md)
This file shows how all the datasets integrate into the MedFusion AI platform architecture, illustrating:
- Clinical data backbone (MIMIC-IV family)
- Signals analysis (ECG, PET, etc.)
- Imaging analysis (X-ray, CT, MRI, Echo, etc.)
- Clinical text and reports
- Multimodal fusion hub
- Dataset-specific linkage highlights
- Recommended implementation strategy
- Fusion use case examples

## How to Create PDFs

To convert these markdown files to PDF, you can use several methods:

### Method 1: Using Pandoc (Recommended)
1. Install pandoc: https://pandoc.org/installing.html
2. Run for each file:
   `
   pandoc 01_MIMIC-IV.md -o 01_MIMIC-IV.pdf
   pandoc 02_MIMIC-IV-ED.md -o 02_MIMIC-IV-ED.pdf
   # ... repeat for all files
   `
3. Or batch convert:
   `
   for file in *.md; do
     pandoc "" -o ".pdf"
   done
   `

### Method 2: Using Typora
1. Install Typora: https://typora.io/
2. Open each .md file
3. Go to File ? Export ? PDF

### Method 3: Using MarkText or Other Markdown Editors
Many markdown editors have built-in PDF export functionality.

### Method 4: Using Online Converters
Various online markdown to PDF converters are available (search for "markdown to pdf online").

## PDF Naming Convention
The PDF files will follow the same numbering and naming as the source markdown files:
- 01_MIMIC-IV.pdf
- 02_MIMIC-IV-ED.pdf
- ...
- 20_MedFusion-Dataset-Mapping.pdf

## Usage Suggestions
- Print individual dataset summaries for quick reference
- Include in project documentation and onboarding materials
- Use as study materials for team members
- Reference during dataset selection and integration discussions
- Include in grant applications and project proposals
- Share with collaborators and stakeholders

## Important Notes
- These summaries are based on the information provided in the dataset requirements discussion
- For the most current and detailed information, always refer to the official dataset sources
- Some dataset specifics (like exact sizes, access procedures, and licensing) may change over time
- Verify access requirements and licenses before downloading or using any dataset
- The dataset mapping represents a proposed architecture and may need adjustment based on actual data availability and project evolution

## Contact
For questions about these summaries or the MedFusion AI project, please refer to the project documentation or contact the project team.
