#!/usr/bin/env python
"""
Stub server for chest X-ray segmentation.
Loads a trained U-Net model if available, else returns stub.
"""

import os
import io
import base64
from flask import Flask, request, jsonify
from PIL import Image
import numpy as np
import torch
import torchvision.transforms as transforms

app = Flask(__name__)

# Global model and device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "xray_unet_checkpoint.pth")
MODEL = None
TRANSFORM = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    # Note: training did not use normalization; if you used normalization, add it here.
])

def load_model():
    global MODEL
    if MODEL is not None:
        return
    if not os.path.exists(MODEL_PATH):
        print(f"[Stub] Model checkpoint not found at {MODEL_PATH}. Using stub.")
        return
    try:
        # Define model architecture (must match training)
        class UNetBlock(torch.nn.Module):
            def __init__(self, in_channels, out_channels):
                super(UNetBlock, self).__init__()
                self.conv1 = torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
                self.bn1 = torch.nn.BatchNorm2d(out_channels)
                self.conv2 = torch.nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
                self.bn2 = torch.nn.BatchNorm2d(out_channels)
                self.relu = torch.nn.ReLU(inplace=True)
            
            def forward(self, x):
                x = self.relu(self.bn1(self.conv1(x)))
                x = self.relu(self.bn2(self.conv2(x)))
                return x

        class UNet(torch.nn.Module):
            def __init__(self, in_channels=3, out_channels=1, features=[64, 128, 256, 512]):
                super(UNet, self).__init__()
                self.ups = torch.nn.ModuleList()
                self.downs = torch.nn.ModuleList()
                self.pool = torch.nn.MaxPool2d(kernel_size=2, stride=2)
                
                for feature in features:
                    self.downs.append(UNetBlock(in_channels, feature))
                    in_channels = feature
                
                for feature in reversed(features):
                    self.ups.append(
                        torch.nn.ConvTranspose2d(
                            feature*2, feature, kernel_size=2, stride=2,
                        )
                    )
                    self.ups.append(UNetBlock(feature*2, feature))
                
                self.bottleneck = UNetBlock(features[-1], features[-1]*2)
                self.final_conv = torch.nn.Conv2d(features[0], out_channels, kernel_size=1)
            
            def forward(self, x):
                skip_connections = []
                for down in self.downs:
                    x = down(x)
                    skip_connections.append(x)
                    x = self.pool(x)
                
                x = self.bottleneck(x)
                skip_connections = skip_connections[::-1]
                
                for idx in range(0, len(self.ups), 2):
                    x = self.ups[idx](x)
                    skip_connection = skip_connections[idx//2]
                    
                    if x.shape != skip_connection.shape:
                        x = torch.nn.functional.interpolate(x, size=skip_connection.shape[2:], mode='bilinear', align_corners=False)
                    
                    concat_skip = torch.cat((skip_connection, x), dim=1)
                    x = self.ups[idx+1](concat_skip)
                
                return torch.sigmoid(self.final_conv(x))
        
        MODEL = UNet(in_channels=3, out_channels=1).to(DEVICE)
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
        MODEL.load_state_dict(checkpoint["state_dict"])
        MODEL.eval()
        print(f"[Info] Loaded X-ray segmentation model from {MODEL_PATH}")
    except Exception as e:
        print(f"[Warning] Failed to load model: {e}. Using stub.")
        MODEL = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model_loaded': MODEL is not None})

@app.route('/segment', methods=['POST'])
def segment():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    load_model()  # ensure model is loaded if possible
    
    try:
        # Read image
        img = Image.open(file.stream)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        original_size = img.size  # (width, height)
        
        if MODEL is not None:
            # Preprocess
            input_tensor = TRANSFORM(img).unsqueeze(0).to(DEVICE)  # (1, 3, H, W)
            with torch.no_grad():
                output = MODEL(input_tensor)  # (1, 1, H, W)
                # Convert to binary mask (threshold 0.5)
                mask = (output > 0.5).float()
            # Remove batch and channel dimensions
            mask_np = mask.squeeze(0).squeeze(0).cpu().numpy()  # (H, W)
            # Convert to uint8 (0 or 255)
            mask_img = Image.fromarray((mask_np * 255).astype(np.uint8))
        else:
            # Stub: blank mask
            width, height = original_size
            mask_img = Image.new('L', (width, height), 0)
        
        # Encode mask as base64 PNG
        buffered = io.BytesIO()
        mask_img.save(buffered, format="PNG")
        mask_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return jsonify({
            'segmentation_mask': mask_base64,
            'mask_format': 'PNG base64',
            'original_size': list(original_size),
            'note': 'This is a stub response.' if MODEL is None else 'Model inference performed.'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on port 5001 for X-ray segmentation
    app.run(host='0.0.0.0', port=5001, debug=False)
