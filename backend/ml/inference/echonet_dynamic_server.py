#!/usr/bin/env python
"""
Stub server for EchoNet-Dynamic LVEF regression.
Loads a trained R(2+1)D model if available, else returns stub.
"""

import os
import io
import base64
import tempfile
from flask import Flask, request, jsonify
import numpy as np
import torch
import torch.nn as nn
import cv2

app = Flask(__name__)

# Global model and device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "echonet_dynamic_r2plus1d_checkpoint.pth")
MODEL = None
MODEL_CONFIG = None

def load_model():
    global MODEL, MODEL_CONFIG
    if MODEL is not None:
        return
    if not os.path.exists(MODEL_PATH):
        print(f"[Stub] Model checkpoint not found at {MODEL_PATH}. Using stub.")
        return
    try:
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)

        # Extract config
        if 'config' in checkpoint:
            MODEL_CONFIG = checkpoint['config']
            clip_length = MODEL_CONFIG.get('clip_length', 16)
            image_size = MODEL_CONFIG.get('image_size', (112, 112))
        else:
            clip_length = 16
            image_size = (112, 112)

        # Define R(2+1)D model architecture (must match training)
        class R2Plus1DStem(nn.Module):
            def __init__(self, in_channels=3, out_channels=64):
                super().__init__()
                self.spatial_conv = nn.Conv3d(in_channels, out_channels,
                                               kernel_size=(1, 7, 7),
                                               stride=(1, 2, 2),
                                               padding=(0, 3, 3),
                                               bias=False)
                self.spatial_bn = nn.BatchNorm3d(out_channels)
                self.temporal_conv = nn.Conv3d(out_channels, out_channels,
                                                kernel_size=(3, 1, 1),
                                                stride=(1, 1, 1),
                                                padding=(1, 0, 0),
                                                bias=False)
                self.temporal_bn = nn.BatchNorm3d(out_channels)
                self.relu = nn.ReLU(inplace=True)

            def forward(self, x):
                x = self.relu(self.spatial_bn(self.spatial_conv(x)))
                x = self.relu(self.temporal_bn(self.temporal_conv(x)))
                return x

        class R2Plus1DBlock(nn.Module):
            def __init__(self, in_channels, out_channels, stride=1, downsample=None):
                super().__init__()
                self.conv1_spatial = nn.Conv3d(in_channels, out_channels,
                                                kernel_size=(1, 3, 3),
                                                stride=(1, stride, stride),
                                                padding=(0, 1, 1),
                                                bias=False)
                self.bn1 = nn.BatchNorm3d(out_channels)
                self.conv1_temporal = nn.Conv3d(out_channels, out_channels,
                                                 kernel_size=(3, 1, 1),
                                                 stride=(1, 1, 1),
                                                 padding=(1, 0, 0),
                                                 bias=False)
                self.bn1_t = nn.BatchNorm3d(out_channels)

                self.conv2_spatial = nn.Conv3d(out_channels, out_channels,
                                                kernel_size=(1, 3, 3),
                                                stride=(1, 1, 1),
                                                padding=(0, 1, 1),
                                                bias=False)
                self.bn2 = nn.BatchNorm3d(out_channels)
                self.conv2_temporal = nn.Conv3d(out_channels, out_channels,
                                                 kernel_size=(3, 1, 1),
                                                 stride=(1, 1, 1),
                                                 padding=(1, 0, 0),
                                                 bias=False)
                self.bn2_t = nn.BatchNorm3d(out_channels)

                self.relu = nn.ReLU(inplace=True)
                self.downsample = downsample
                self.stride = stride

            def forward(self, x):
                identity = x

                out = self.relu(self.bn1(self.conv1_spatial(x)))
                out = self.relu(self.bn1_t(self.conv1_temporal(out)))

                out = self.relu(self.bn2(self.conv2_spatial(out)))
                out = self.bn2_t(self.conv2_temporal(out))

                if self.downsample is not None:
                    identity = self.downsample(x)

                out += identity
                out = self.relu(out)
                return out

        class R2Plus1DNet(nn.Module):
            def __init__(self, num_classes=1, layers=[2, 2, 2, 2], dropout_rate=0.5):
                super(R2Plus1DNet, self).__init__()

                self.in_channels = 64

                self.stem = R2Plus1DStem(3, 64)
                self.pool = nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))

                self.layer1 = self._make_layer(64, layers[0], stride=1)
                self.layer2 = self._make_layer(128, layers[1], stride=2)
                self.layer3 = self._make_layer(256, layers[2], stride=2)
                self.layer4 = self._make_layer(512, layers[3], stride=2)

                self.avgpool = nn.AdaptiveAvgPool3d((1, 1, 1))

                self.classifier = nn.Sequential(
                    nn.Dropout(dropout_rate),
                    nn.Linear(512, 512),
                    nn.ReLU(inplace=True),
                    nn.Dropout(dropout_rate),
                    nn.Linear(512, 128),
                    nn.ReLU(inplace=True),
                    nn.Linear(128, num_classes)
                )

            def _make_layer(self, out_channels, blocks, stride):
                downsample = None
                if stride != 1 or self.in_channels != out_channels:
                    downsample = nn.Sequential(
                        nn.Conv3d(self.in_channels, out_channels, kernel_size=1,
                                  stride=(1, stride, stride), bias=False),
                        nn.BatchNorm3d(out_channels),
                    )

                layers = []
                layers.append(R2Plus1DBlock(self.in_channels, out_channels, stride, downsample))
                self.in_channels = out_channels
                for _ in range(1, blocks):
                    layers.append(R2Plus1DBlock(out_channels, out_channels))

                return nn.Sequential(*layers)

            def forward(self, x):
                x = self.stem(x)
                x = self.pool(x)

                x = self.layer1(x)
                x = self.layer2(x)
                x = self.layer3(x)
                x = self.layer4(x)

                x = self.avgpool(x)
                x = torch.flatten(x, 1)
                x = self.classifier(x)

                return x

        MODEL = R2Plus1DNet(num_classes=1).to(DEVICE)
        MODEL.load_state_dict(checkpoint["model_state_dict"])
        MODEL.eval()
        print(f"[Info] Loaded EchoNet-Dynamic model from {MODEL_PATH}")
        print(f"       Config: clip_length={clip_length}, image_size={image_size}")
        print(f"       Best Val MAE: {checkpoint.get('val_mae', 'N/A'):.4f}")

    except Exception as e:
        print(f"[Warning] Failed to load model: {e}. Using stub.")
        MODEL = None

def preprocess_video(video_path, clip_length=16, image_size=(112, 112)):
    """Load and preprocess video for model input."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        cap.release()
        raise ValueError(f"Video has 0 frames: {video_path}")

    # Uniformly sample frames
    frame_indices = np.linspace(0, total_frames - 1, clip_length, dtype=int)
    frames = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            if frames:
                frames.append(frames[-1])
            else:
                frames.append(np.zeros((image_size[1], image_size[0], 3), dtype=np.uint8))
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, image_size)
        frames.append(frame)

    cap.release()

    # Convert to tensor: (T, H, W, C) -> (C, T, H, W)
    frames = np.array(frames)  # (T, H, W, C)
    frames = frames.transpose(3, 0, 1, 2)  # (C, T, H, W)
    frames = frames.astype(np.float32) / 255.0

    # Normalize with ImageNet stats
    mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1, 1)
    std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1, 1)
    frames = (frames - mean) / std

    # Add batch dimension: (1, C, T, H, W)
    frames = np.expand_dims(frames, axis=0)

    return torch.from_numpy(frames).float()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': MODEL is not None,
        'model_type': 'EchoNet-Dynamic LVEF Regression',
        'architecture': 'R(2+1)D-18'
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze echocardiogram video for LVEF.
    Expects a video file upload (mp4, avi, mov).
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    load_model()

    # Save uploaded file temporarily
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in ['.mp4', '.avi', '.mov', '.mkv']:
        suffix = '.mp4'

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        video_path = tmp.name

    try:
        # Determine config
        if MODEL_CONFIG:
            clip_length = MODEL_CONFIG.get('clip_length', 16)
            image_size = tuple(MODEL_CONFIG.get('image_size', (112, 112)))
        else:
            clip_length = 16
            image_size = (112, 112)

        if MODEL is not None:
            # Preprocess
            input_tensor = preprocess_video(video_path, clip_length, image_size).to(DEVICE)

            with torch.no_grad():
                lvef_pred = MODEL(input_tensor)
                lvef = float(lvef_pred.item())

            results = {
                'lvef': round(lvef, 1),
                'confidence': 'high' if 20 <= lvef <= 70 else 'moderate',
                'note': 'Model inference performed.',
                'model': 'EchoNet-Dynamic R(2+1)D',
                'architecture': 'R(2+1)D-18',
                'input_frames': clip_length,
                'input_size': f"{image_size[0]}x{image_size[1]}"
            }
        else:
            # Stub: return simulated LVEF
            import random
            lvef = random.uniform(30, 65)
            results = {
                'lvef': round(lvef, 1),
                'confidence': 'simulated',
                'note': 'This is a stub response. Replace with actual model inference.',
                'model': 'EchoNet-Dynamic (stub)',
            }

        # Add clinical interpretation
        if results['lvef'] >= 55:
            results['interpretation'] = 'Normal systolic function'
            results['severity'] = 'normal'
        elif results['lvef'] >= 40:
            results['interpretation'] = 'Mildly reduced systolic function (HFmrEF)'
            results['severity'] = 'mild'
        elif results['lvef'] >= 30:
            results['interpretation'] = 'Moderately reduced systolic function (HFrEF)'
            results['severity'] = 'moderate'
        else:
            results['interpretation'] = 'Severely reduced systolic function (HFrEF)'
            results['severity'] = 'severe'

        results['recommendations'] = []
        if results['lvef'] < 40:
            results['recommendations'].append('Consider GDMT initiation per guidelines')
            results['recommendations'].append('Cardiology referral recommended')
        if results['lvef'] < 30:
            results['recommendations'].append('Consider ICD/CRT evaluation per guidelines')

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up temp file
        try:
            os.unlink(video_path)
        except:
            pass

if __name__ == '__main__':
    # Run on port 5003 for EchoNet Dynamic
    app.run(host='0.0.0.0', port=5003, debug=False)