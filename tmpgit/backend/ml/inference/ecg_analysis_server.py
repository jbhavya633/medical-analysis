#!/usr/bin/env python
"""
Stub server for ECG analysis.
Loads a trained 1D CNN model if available, else returns stub.
"""

import os
import io
import base64
from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

app = Flask(__name__)

# Global model and device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ecg_cnn_checkpoint.pth")
MODEL = None
LABEL_MAP = None  # will load from checkpoint or default
MAX_LENGTH = 5000  # must match training

def load_model():
    global MODEL, LABEL_MAP
    if MODEL is not None:
        return
    if not os.path.exists(MODEL_PATH):
        print(f"[Stub] Model checkpoint not found at {MODEL_PATH}. Using stub.")
        return
    try:
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
        # Extract label mapping if saved
        if 'label_map' in checkpoint:
            LABEL_MAP = checkpoint['label_map']
            inv_label_map = {v: k for k, v in LABEL_MAP.items()}
            num_classes = len(LABEL_MAP)
        else:
            # fallback: we cannot know number of classes; we'll use stub
            print("[Warning] Checkpoint missing label_map. Using stub.")
            MODEL = None
            return
        # Determine input channels from first layer conv weight shape
        # We'll need to instantiate model with correct architecture.
        # For simplicity, we assume the same architecture as training with 12 leads.
        # We'll infer input channels from the checkpoint's conv1 weight.
        conv1_weight = checkpoint['state_dict']['conv1.weight']
        in_channels = conv1_weight.shape[1]  # should be number of leads
        # Define model
        class ECGNet(nn.Module):
            def __init__(self, input_channels, num_classes, dropout_rate=0.5):
                super(ECGNet, self).__init__()
                self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=5, stride=1, padding=2)
                self.bn1 = nn.BatchNorm1d(64)
                self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)
                
                self.conv2 = nn.Conv1d(64, 128, kernel_size=5, stride=1, padding=2)
                self.bn2 = nn.BatchNorm1d(128)
                self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)
                
                self.conv3 = nn.Conv1d(128, 256, kernel_size=5, stride=1, padding=2)
                self.bn3 = nn.BatchNorm1d(256)
                self.pool3 = nn.MaxPool1d(kernel_size=2, stride=2)
                
                # Compute flattened size: after three poolings, length = MAX_LENGTH // 8
                # We'll need to know MAX_LENGTH; we'll assume same as used in training.
                # We'll compute dynamically by doing a forward pass with a dummy tensor? 
                # Instead, we can store the flattened size in checkpoint or compute from a dummy.
                # For simplicity, we'll assume MAX_LENGTH // 8 and 256 channels.
                self.fc1 = nn.Linear(256 * (MAX_LENGTH // 8), 128)
                self.bn4 = nn.BatchNorm1d(128)
                self.dropout = nn.Dropout(dropout_rate)
                self.fc2 = nn.Linear(128, num_classes)
                
                self.relu = nn.ReLU(inplace=True)
            
            def forward(self, x):
                x = self.relu(self.bn1(self.conv1(x)))
                x = self.pool1(x)
                
                x = self.relu(self.bn2(self.conv2(x)))
                x = self.pool2(x)
                
                x = self.relu(self.bn3(self.conv3(x)))
                x = self.pool3(x)
                
                x = x.view(x.size(0), -1)
                x = self.relu(self.bn4(self.fc1(x)))
                x = self.dropout(x)
                x = self.fc2(x)
                return x
        
        MODEL = ECGNet(input_channels=in_channels, num_classes=num_classes).to(DEVICE)
        MODEL.load_state_dict(checkpoint["state_dict"])
        MODEL.eval()
        print(f"[Info] Loaded ECG analysis model from {MODEL_PATH}")
        print(f"       Input channels: {in_channels}, Num classes: {num_classes}")
    except Exception as e:
        print(f"[Warning] Failed to load model: {e}. Using stub.")
        MODEL = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model_loaded': MODEL is not None})

@app.route('/analyze', methods=['POST'])
def analyze():
    # Expect a file upload with ECG data (CSV format)
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    load_model()  # ensure model is loaded if possible
    
    try:
        # Read the CSV file
        # We expect no header, each column is a lead, rows are time steps.
        # Alternatively, could have header; we'll try to detect.
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        # Try to read with pandas, no header
        try:
            df = pd.read_csv(stream, header=None)
        except:
            # Maybe there is a header; try again with header=0
            stream.seek(0)
            df = pd.read_csv(stream, header=0)
        
        # Convert to numpy array: shape (time_steps, leads) if columns are leads
        # We need (leads, time_steps)
        signal = df.values.astype(np.float32)  # (time, leads) if columns are leads
        # If shape[1] > shape[0] and shape[1] in typical lead counts, maybe leads are columns?
        # We'll assume columns are leads (common in CSV export). If not, we can transpose later.
        # For safety, we'll check if number of columns is plausible lead count (1,2,3,6,12,15)
        # If not, we might need to transpose.
        # We'll just assume columns are leads; if rows are leads, we'll transpose.
        # Determine orientation: if number of rows < number of columns and number of rows in [1,2,3,6,12,15], then rows are leads.
        rows, cols = signal.shape
        if rows in [1,2,3,6,12,15] and rows < cols:
            # likely rows are leads
            signal = signal.T  # now (leads, time)
        elif cols in [1,2,3,6,12,15] and cols < rows:
            # likely columns are leads
            pass
        else:
            # default: treat first dimension as time, second as leads? We'll assume columns are leads.
            # If unclear, we'll assume columns are leads.
            pass
        
        # Now signal shape should be (leads, time)
        # If not, we'll force to (leads, time) by making sure the smaller dimension is leads?
        # We'll just proceed and let the model fail if shape wrong.
        
        # Truncate or pad to MAX_LENGTH
        if signal.shape[1] > MAX_LENGTH:
            signal = signal[:, :MAX_LENGTH]
        elif signal.shape[1] < MAX_LENGTH:
            pad_width = MAX_LENGTH - signal.shape[1]
            signal = np.pad(signal, ((0, 0), (0, pad_width)), mode='constant')
        
        # Normalize per lead (zero mean, unit variance)
        signal = (signal - np.mean(signal, axis=1, keepdims=True)) / (np.std(signal, axis=1, keepdims=True) + 1e-8)
        
        # Convert to tensor
        input_tensor = torch.from_numpy(signal).unsqueeze(0).to(DEVICE)  # (1, leads, time)
        
        if MODEL is not None:
            with torch.no_grad():
                logits = MODEL(input_tensor)
                probs = torch.softmax(logits, dim=1)
                confidence, predicted_idx = torch.max(probs, 1)
                predicted_idx = predicted_idx.item()
                confidence = confidence.item()
                
                # Map index to label
                if LABEL_MAP is not None:
                    inv_label_map = {v: k for k, v in LABEL_MAP.items()}
                    predicted_label = inv_label_map[predicted_idx]
                else:
                    predicted_label = f"class_{predicted_idx}"
                
                # Optionally, compute some dummy measurements for compatibility with stub
                # We'll just return classification.
                results = {
                    'predicted_label': predicted_label,
                    'confidence': confidence,
                    'note': 'Model inference performed.' if MODEL is not None else 'Stub used.'
                }
                # Add some typical ECG measurements as placeholders (optional)
                results.update({
                    'heart_rate': 75,  # placeholder
                    'rhythm': predicted_label,
                    'intervals': {
                        'pr_interval': 160,
                        'qrs_duration': 90,
                        'qt_interval': 400,
                        'qtc': 420
                    },
                    'axis': {
                        'p_axis': 45,
                        'qrs_axis': 30,
                        't_axis': 50
                    },
                    'findings': [
                        f'Predicted rhythm: {predicted_label}.',
                        'Note: Measurements are placeholders.'
                    ]
                })
        else:
            # Stub: normal sinus rhythm
            results = {
                'predicted_label': 'normal',
                'confidence': 0.95,
                'heart_rate': 75,
                'rhythm': 'Normal Sinus Rhythm',
                'intervals': {
                    'pr_interval': 160,
                    'qrs_duration': 90,
                    'qt_interval': 400,
                    'qtc': 420
                },
                'axis': {
                    'p_axis': 45,
                    'qrs_axis': 30,
                    't_axis': 50
                },
                'findings': [
                    'Normal sinus rhythm.',
                    'No ST-segment elevation or depression.',
                    'No pathological Q waves.'
                ],
                'note': 'This is a stub response. Replace with actual model inference.'
            }
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on port 5002 for ECG analysis
    app.run(host='0.0.0.0', port=5002, debug=False)
