# Machine Learning Components

This directory contains code for training and inference of machine learning models for the MedFusion AI project.

## Directory Structure
- `inference/` - Stub servers for serving model predictions
- `train/`   - Scripts for training models (PyTorch)

## Files

### Inference Servers
- `xray_segmentation_server.py`: Flask server for chest X-ray segmentation (stub)
- `ecg_analysis_server.py`: Flask server for ECG analysis (stub)
- `echonet_dynamic_server.py`: Flask server for EchoNet-Dynamic LVEF regression (stub)

### Training Scripts
- `xray_segmentation_train.py`: Training script for X-ray segmentation using U-Net (PyTorch)
- `ecg_analysis_train.py`: Training script for ECG analysis using 1D CNN (PyTorch)
- `synthea_mortality_train.py`: Mortality prediction using Synthea data (scikit-learn/XGBoost)
- `echonet_dynamic_train.py`: Training script for EchoNet-Dynamic LVEF regression using R(2+1)D (PyTorch)

## Dependencies
See `backend/requirements.txt` for Flask inference dependencies.
For training, additional packages are needed:
```
torch torchvision tqdm opencv-python scikit-learn xgboost joblib pydicom
```
Install with:
```bash
pip install -r backend/requirements.txt
```

## Usage
1. **Train models** (requires actual dataset):
   - Prepare your dataset in the expected format.
   - Update the paths in the training scripts.
   - Run:
     ```bash
     python backend/ml/train/xray_segmentation_train.py
     python backend/ml/train/ecg_analysis_train.py
     python backend/ml/train/echonet_dynamic_train.py
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
   - Start the EchoNet-Dynamic LVEF server:
     ```bash
     python backend/ml/inference/echonet_dynamic_server.py
     ```
   - The servers will be available at:
     - X-ray: `http://localhost:5001`
     - ECG: `http://localhost:5002`
     - Echo: `http://localhost:5003`

## EchoNet-Dynamic Dataset
The `echonet_dynamic_train.py` script automatically clones the EchoNet-Dynamic repository from GitHub:
```
https://github.com/echonet/dynamic.git
```
You will need to download the dataset (videos and FileList.csv) and place them in:
```
data/echonet/Videos/
data/echonet/FileList.csv
```
Download from: https://echonet.github.io/dynamic/

## Notes
- The inference servers currently return stub responses if model checkpoints are not found. Replace the stub logic with actual model loading and inference.
- The training scripts are complete implementations; you will need to set the correct data paths and possibly adjust hyperparameters.
- For X-ray segmentation, expect directories of images and corresponding masks (same filenames).
- For ECG analysis, expect ECG signal files (numpy .npy) and a label CSV with columns 'filename' and 'label'.
- For EchoNet-Dynamic, expect video files (.mp4, .avi) and a FileList.csv with columns 'FileName', 'Split', 'EF'.
- Consider using GPU acceleration if available.
- For production, add authentication, error handling, and scalability measures.
