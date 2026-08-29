# Chest CT for Patients with Sepsis Dataset Summary

## Dataset Overview
- **Name**: Chest CT for Patients with Sepsis
- **Modality**: Computed Tomography (CT) scans of the chest with clinical sepsis data
- **Primary Use**: Studying pulmonary manifestations of sepsis, acute respiratory distress syndrome (ARDS), and sepsis-induced lung injury

## Key Characteristics
- **Size**: Moderate-sized clinical CT dataset
- **CT Scans**: Number varies by specific sepsis cohort (typically hundreds to low thousands)
- **Patients**: Patients with diagnosed sepsis or septic shock
- **Scan Specifications**:
  - Chest CT scans performed during sepsis hospitalization
  - Variable protocols: contrast-enhanced vs non-contrast, timing relative to sepsis onset
  - Slice thickness: typically 1-5 mm depending on clinical indication
  - Reconstruction: soft tissue and/or lung algorithms
  - Hounsfield Unit (HU) intensity values
- **Clinical Data**:
  - Sepsis diagnosis criteria (SOFA, qSOFA, or Sepsis-3)
  - Septic shock status (vasopressor requirement, lactate elevation)
  - Organ dysfunction scores (respiratory, cardiovascular, renal, hepatic, coagulation)
  - Laboratory markers (lactate, CRP, procalcitonin, cytokines)
  - Microbiology cultures and antibiotic administration
  - Ventilator settings and oxygenation indices (PaO2/FiO2)
  - Outcomes: mortality, ICU length of stay, ventilator-free days

## Access Information
- **Official Source**: [Chest CT for patients with sepsis](https://physionet.org/content/chestct-sepsis/?utm_source=chatgpt.com) (example link - actual may vary)
- **Access Type**: Credentialed PhysioNet access likely required
- **License**: PhysioNet Credentialed Health Data License 1.5.0 (if on PhysioNet)
- **Citation**: Varies by specific study; search PhysioNet for "sepsis chest CT"

## Linkage Capabilities
- **Strong clinical linkage** when hosted on PhysioNet (part of MIMIC or similar)
- **Can link to vital signs, labs, medications** if part of integrated EHR database
- **Shares imaging modality** with LIDC-IDRI and TCIA resources
- **Enables sepsis-specific imaging biomarker discovery**
- **Temporal imaging**: multiple scans per patient possible to track evolution

## Recommended Use in MedFusion AI
- **Sepsis Phenotyping**: Identifying sepsis subtypes based on lung involvement patterns
- **ARDS Detection**: Early identification of acute respiratory distress syndrome
- **Lung Injury Quantification**: Objective assessment of pulmonary edema, consolidation, atelectasis
- **Ventilator-Associated Lung Injury**: Monitoring iatrogenic complications from mechanical ventilation
- **Treatment Response Tracking**: Objective measures of lung improvement with therapy
- **Prognostic Modeling**: Predicting mortality and morbidity from early CT findings
- **Differential Diagnosis**: Distinguishing infectious vs non-infectious pulmonary infiltrates
- **Resource Utilization**: Predicting need for ICU admission, intubation, or ECMO

## Suggested ML Tasks
- Lung abnormality segmentation: quantifying edema, consolidation, ground glass opacity
- Severity scoring: automated calculation of lung injury scores (e.g., Murray score)
- Temporal change detection: quantifying improvement or deterioration between scans
- Outcome prediction: mortality, ICU LOS, ventilator duration from admission CT
- Subtype identification: clustering pneumonia patterns in sepsis (lobar, interstitial, etc.)
- Device detection: endotracheal tube, central line, tracheostomy verification
- Fluid balance assessment: correlating pleural effusions with fluid status
- Few-shot learning for rare sepsis phenotypes
- Multimodal fusion with lactate, cytokines, and ventilator parameters
- Uncertainty quantification: confidence estimates for automated sepsis lung injury scores

## File Structure & Formats
- Organized by patient_id or hadm_id directories
- Each study includes:
  - CT scan in DICOM format (series of .dcm files)
  - Associated clinical data in CSV or JSON format
  - Potential segmentation masks or structured reports
- Standard DICOM headers include acquisition timing relative to sepsis onset
- May include both arterial and venous phase contrast studies when performed
- Compatible with medical imaging software and deep learning frameworks
- Clinical data structured for easy integration with imaging features

## Important Notes
- **High clinical relevance** for understanding sepsis pathophysiology
- Enables study of lung-immune crosstalk in critical illness
- Temporal imaging available for subset allows studying evolution of lung injury
- Complementary to general chest CT resources (LIDC-IDRI) which focus on oncology
- Specific sepsis focus provides homogeneous population for targeted AI development
- Valuable for developing AI-assisted sepsis management in ICU settings
- Links well with vital signs and laboratory trends for comprehensive sepsis modeling
