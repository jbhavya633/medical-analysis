# Machine Learning Components

This directory contains code for training and inference of machine learning models for the MedFusion AI project.

## Directory Structure
- `inference/` - Stub servers for serving model predictions
- `train/`   - Scripts for training models (PyTorch)

## Files

### Inference Servers
- `xray_segmentation_server.py`: Flask server for chest X-ray segmentation (stub)
- `ecg_analysis_server.py`: Flask server for ECG analysis (stub)

### Training Scripts
- `xray_segmentation_train.py`: Training script for X-ray segmentation using U-Net (PyTorch)
- `ecg_analysis_train.py`: Training script for ECG analysis using 1D CNN (PyTorch)

## Dependencies
See `backend/requirements.txt` for basic Flask inference dependencies.
For training, additional packages are needed:
```
torch torchvision
```
Install with:
```bash
pip install torch torchvision
```

## Usage
1. **Train models** (requires actual dataset):
   - Prepare your dataset in the expected format.
   - Update the paths in the training scripts.
   - Run:
     ```bash
     python backend/ml/train/xray_segmentation_train.py
     python backend/ml/train/ecg_analysis_train.py
     ```
   - Trained model weights will be saved as checkpoints (specified in the scripts).

2. **Run inference servers**:
   - Install dependencies: `pip install -r backend/requirements.txt`
   - Start the X-ray segmentation server:
     ```bash
     python backend/ml/inference/xray_segmentation_server.py
     ```
   - Start the ECG analysis server:
     ```bash
     python backend/ml/inference/ecg_analysis_server.py
     ```
   - The servers will be available at:
     - X-ray: `http://localhost:5001`
     - ECG: `http://localhost:5002`

## Notes
- The inference servers currently return stub responses. Replace the stub logic with actual model loading and inference.
- The training scripts are complete implementations; you will need to set the correct data paths and possibly adjust hyperparameters.
- For X-ray segmentation, expect directories of images and corresponding masks (same filenames).
- For ECG analysis, expect ECG signal files (numpy .npy) and a label CSV with columns 'filename' and 'label'.
- Consider using GPU acceleration if available.
- For production, add authentication, error handling, and scalability measures.
