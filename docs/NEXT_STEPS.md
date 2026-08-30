# MedFusion AI: Next Steps for Model Training

This document provides concrete, actionable steps to train models for the MedFusion AI project using the datasets and code created in this repository.

## Prerequisites

Before beginning, ensure you have:
1. **Credentialed access** to PhysioNet datasets (MIMIC-IV, MIMIC-IV-ECG, MIMIC-CXR, etc.)
2. **Storage space** for large datasets (MIMIC-IV-ECG alone is ~90.4 GB uncompressed)
3. **Computing resources**: GPU recommended for training (especially for imaging models)
4. **Basic Linux/Unix command line familiarity**

## Step 1: Set Up the Environment

### 1.1 Clone Repository (if not already done)
`ash
# Assuming you have the files from this session
# If starting fresh, clone or copy the medfusion-ai directory
`

### 1.2 Install Python Dependencies
`ash
# Base dependencies for inference servers
pip install -r backend/requirements.txt

# Additional dependencies for training
pip install torch torchvision tqdm pandas scikit-learn

# Optional but recommended for medical imaging
pip install pydicom nibabel SimpleITK monai

# For NLP tasks
pip install transformers torchtext
`

### 1.3 Verify Installation
`ash
python -c "import torch; print('PyTorch version:', torch.__version__)"
python -c "import torchvision; print('Torchvision version:', torchvision.__version__)"
`

## Step 2: Obtain and Prepare Datasets

### 2.1 Download Core MIMIC Datasets (Recommended Starting Point)
You'll need credentialed access to PhysioNet. Create an account at https://physionet.org/ and complete the required training.

#### MIMIC-IV (EHR Backbone)
`ash
# Using wget with PhysioNet credentials (replace USERNAME and PASSWORD)
wget -r -N -c -np --user USERNAME --password PASSWORD \
  https://physionet.org/files/mimiciv/3.1/
`

#### MIMIC-IV-ECG
`ash
wget -r -N -c -np --user USERNAME --password PASSWORD \
  https://physionet.org/files/mimic-iv-ecg/1.0/
`

#### MIMIC-CXR
`ash
wget -r -N -c -np --user USERNAME --password PASSWORD \
  https://physionet.org/files/mimic-cxr/2.0.0/
`

#### MIMIC-IV-Note
`ash
wget -r -N -c -np --user USERNAME --password PASSWORD \
  https://physionet.org/files/mimic-iv-note/2.2.0/
`

### 2.2 Download Supplementary Datasets
#### PTB-XL (Open Access - No Credentials Needed)
`ash
wget -r -N -c -np https://physionet.org/files/ptb-xl/1.0.3/
`

#### CheXpert (Requires Agreement - Visit URL)
`ash
# Visit https://aimi.stanford.edu/datasets/chexpert-chest-x-rays
# Complete the data use agreement, then download
`

#### LIDC-IDRI (Open Access via TCIA)
`ash
# Use NCIA Data Retrieval Tool or download from:
# https://www.cancerimagingarchive.net/collection/lidc-idri/
`

### 2.3 Organize Dataset Structure
Create a directory structure like:
`
medfusion-data/
+- mimiciv/
¦  +- patients/
¦  +- hospitals/
¦  +- ... (MIMIC-IV extracted files)
+- mimic-iv-ecg/
¦  +- p10000000/
¦  +- ... (ECG files by subject_id)
+- mimic-cxr/
¦  +- files/
¦  +- ... (CXR files)
+- ptb-xl/
¦  +- ... (PTB-XL files)
+- chexpert/
¦  +- ... (CheXpert files)
+- lidc-idri/
   +- ... (LIDC-IDRI files)
`

### 2.4 Preprocess Datasets (Dataset-Specific)
Refer to docs/TRAINING_STRATEGY.md for detailed preprocessing guidelines per modality.

#### Example: ECG Preprocessing Script Concept
`python
# This would be in your preprocessing pipeline
import numpy as np
import wfdb  # Install with: pip install wfdb

def preprocess_ecg_signal(record_path, sampling_rate=500, duration=10):
    """Load and preprocess ECG signal"""
    # Load record
    record = wfdb.rdrecord(record_path)
    signal = record.p_signal  # Shape: (samples, leads)
    
    # Resample if needed
    if record.fs != sampling_rate:
        # Implement resampling (use scipy.signal.resample or similar)
        pass
    
    # Trim or pad to fixed duration
    target_samples = sampling_rate * duration
    if signal.shape[0] > target_samples:
        signal = signal[:target_samples, :]
    elif signal.shape[0] < target_samples:
        padding = np.zeros((target_samples - signal.shape[0], signal.shape[1]))
        signal = np.vstack([signal, padding])
    
    # Normalize per lead (zero mean, unit variance)
    signal = (signal - np.mean(signal, axis=0, keepdims=True)) / (np.std(signal, axis=0, keepdims=True) + 1e-8)
    
    return signal
`

## Step 3: Train Unimodal Foundation Models

### 3.1 Train ECG Analysis Model
`ash
# Edit the paths in backend/ml/train/ecg_analysis_train.py:
# Set TRAIN_DATA_DIR, TRAIN_LABEL_CSV, VAL_DATA_DIR, VAL_LABEL_CSV
# to point to your preprocessed ECG data

# Run training
python backend/ml/train/ecg_analysis_train.py
`

**Expected Output**: 
- Training progress bars showing loss and accuracy
- Best model saved as ecg_cnn_checkpoint.pth (or similar)
- Final validation accuracy reported

### 3.2 Train Chest X-ray Segmentation Model
`ash
# Edit the paths in backend/ml/train/xray_segmentation_train.py:
# Set TRAIN_IMG_DIR, TRAIN_MASK_DIR, VAL_IMG_DIR, VAL_MASK_DIR
# to point to your X-ray images and segmentation masks

# Run training
python backend/ml/train/xray_segmentation_train.py
`

**Expected Output**:
- Training progress showing loss values
- Best model saved as xray_unet_checkpoint.pth
- Validation loss reported

### 3.3 Train Other Models (Follow Similar Pattern)
- Echo: Use ecg_analysis_train.py as template but adapt for echo data
- Text: Create similar training script for MIMIC-IV-Note using Hugging Face Transformers
- Time Series: Develop specialized scripts for MIMIC-IV lab/vital signs data

## Step 4: Update Inference Servers to Use Trained Models

### 4.1 Update X-ray Segmentation Server
In ackend/ml/inference/xray_segmentation_server.py:
- The script already looks for xray_unet_checkpoint.pth in the project root
- After training, ensure the checkpoint is in the expected location
- Or update MODEL_PATH variable to point to your checkpoint

### 4.2 Update ECG Analysis Server
In ackend/ml/inference/ecg_analysis_server.py:
- The script looks for ecg_cnn_checkpoint.pth in the project root
- Ensure your trained ECG checkpoint is available at this location
- Or update MODEL_PATH and related loading logic

### 4.3 Test Inference Servers
`ash
# Start X-ray segmentation server (in one terminal)
python backend/ml/inference/xray_segmentation_server.py

# Start ECG analysis server (in another terminal)
python backend/ml/inference/ecg_analysis_server.py

# Test with curl or Postman:
# X-ray: curl -X POST -F "image=@test_xray.jpg" http://localhost:5001/segment
# ECG: curl -X POST -F "file=@test_ecg.csv" http://localhost:5002/analyze
`

## Step 5: Implement Multimodal Fusion (Advanced)

After establishing strong unimodal performance, implement fusion strategies:

### 5.1 Cardiopulmonary Fusion (ECG + CXR + Labs)
1. Train unimodal encoders for each modality
2. Create fusion model that combines features
3. Train on joint outcomes (e.g., heart failure prediction, mortality)

### 5.2 Report Generation and Visual Question Answering
1. Use MIMIC-Ext-CXR-QBA (42M QA pairs) for VQA pretraining
2. Fine-tune on MIMIC-CXR + MIMIC-IV-Note for clinical VQA
3. Implement image-to-text translation for report generation

## Step 6: Validation and Deployment

### 6.1 Internal Validation
- Use validation sets during training to prevent overfitting
- Perform patient-stratified cross-validation
- Check calibration (reliability diagrams, Brier score)

### 6.2 External Validation
- Test on held-out patients from same dataset
- Validate on supplementary datasets (e.g., test ECG model trained on MIMIC-IV-ECG on PTB-XL)
- Geographic/temporal validation if multiple sites/time periods available

### 6.3 Clinical Validation Planning
- Design prospective studies comparing AI-assisted vs standard care
- Plan reader studies with clinicians
- Define clinically meaningful endpoints

### 6.4 Deployment Preparation
- Containerize with Docker for reproducible deployment
- Implement API gateway for multiple inference servers
- Add authentication, rate limiting, and monitoring
- Plan for model retraining schedules and drift detection

## Troubleshooting Common Issues

### Issue: "Out of Memory" during training
**Solutions**:
- Reduce batch size
- Use gradient accumulation
- Enable mixed precision training (	orch.cuda.amp)
- Use model parallelism for very large models
- Train on smaller image patches or downsampled volumes

### Issue: NaN losses or exploding gradients
**Solutions**:
- Check for data preprocessing errors (inf/nan values)
- Reduce learning rate
- Add gradient clipping
- Verify label encoding is correct

### Issue: Poor validation performance despite good training
**Solutions**:
- Check for data leakage (patient appearing in both train and validation)
- Verify preprocessing is identical between train/val
- Increase regularization (dropout, weight decay)
- Collect more training data or use data augmentation

## Estimated Time and Resource Requirements

| Modality | Dataset Size | Training Time (Single GPU) | Recommended Hardware |
|----------|--------------|----------------------------|----------------------|
| ECG (1D CNN) | ~10 GB processed | 2-24 hours | 1x GPU (8GB+ VRAM) |
| CXR Segmentation | ~50 GB processed | 6-48 hours | 1x GPU (12GB+ VRAM) |
| Echo Segmentation | ~100 GB+ processed | 12-72 hours | 1-2x GPU (24GB+ VRAM) |
| Clinical NLP | ~5-10 GB processed | 1-12 hours | 1x CPU or GPU |
| Time Series (Labs/Vitals) | ~5-15 GB processed | 1-24 hours | 1x CPU or GPU |

## Monitoring Training Progress
- Use TensorBoard: 	ensorboard --logdir=runs/
- Weights & Biases: wandb login then wandb init in training script
- Simple logging: training scripts already include tqdm progress bars

## Safety and Ethics Considerations
1. **Bias Checking**: Regularly evaluate model performance across demographic groups
2. **Explainability**: Use techniques like Grad-CAM for imaging, attention weights for text
3. **Failure Modes**: Identify and document conditions where model performs poorly
4. **Human Oversight**: Design for clinician-in-the-loop, especially for high-risk decisions
5. **Data Privacy**: Ensure all data handling complies with HIPAA/GDPR and DUA requirements

## Getting Help and Resources
- PhysioNet Tutorials: https://physionet.org/content/tutorials/
- MIMIC Code Repository: https://github.com/MIT-LCP/mimic-code
- Medical Imaging Tutorials: MONAI tutorials (https://monai.io/)
- NLP for Clinical Text: Hugging Face Course (https://huggingface.co/learn/nlp-course/chapter1/6)

## Final Verification Checklist
Before considering a model "ready for deployment":
- [ ] Training and validation loss converged appropriately
- [ ] Validation metrics meet clinical requirements (sensitivity/specificity targets)
- [ ] Model tested on external dataset(s) showing generalization
- [ ] Bias analysis performed across key demographics (age, sex, ethnicity if available)
- [ ] Explainability methods validated (e.g., radiologists agree with attention maps)
- [ ] Inference server tested with real sample data
- [ ] Deployment package (Dockerfile, requirements, etc.) created and tested
- [ ] Monitoring and alerting plan established
- [ ] Documentation completed (model card, data sheet, usage instructions)

---

**Remember**: The key to success with medical AI is not just technical accuracy, but clinical validity and utility. Always collaborate with domain experts (clinicians, radiologists, cardiologists) throughout the development process to ensure your models address real clinical needs and integrate smoothly into workflows.

Good luck with your MedFusion AI training journey!
