#!/usr/bin/env python
"""
Training script for chest X-ray segmentation.
This script trains a U-Net model for segmenting lung fields or other anatomical structures.
Replace the placeholder data loading with your actual dataset (e.g., Montgomery Set, JSRT, or custom masks from MIMIC-CXR).
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from torchvision.utils import save_image
from PIL import Image
import numpy as np
from tqdm import tqdm

# ----------------------------
# 1. Dataset Class
# ----------------------------
class XRaySegmentationDataset(Dataset):
    def __init__(self, image_dir, mask_dir, image_size=(256, 256), transform=None):
        """
        Args:
            image_dir (string): Directory with all X-ray images (PNG/JPG).
            mask_dir (string): Directory with all segmentation masks (PNG, same names).
            image_size (tuple): Target size for resizing.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.image_size = image_size
        self.transform = transform
        
        # List image files
        self.image_filenames = sorted([
            f for f in os.listdir(image_dir) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))
        ])
        # Optionally, verify that each image has a corresponding mask
        self.image_filenames = [
            f for f in self.image_filenames 
            if os.path.exists(os.path.join(mask_dir, f))
        ]
        if len(self.image_filenames) == 0:
            raise ValueError(f"No matching image-mask pairs found in {image_dir} and {mask_dir}")
    
    def __len__(self):
        return len(self.image_filenames)
    
    def __getitem__(self, idx):
        img_name = self.image_filenames[idx]
        img_path = os.path.join(self.image_dir, img_name)
        mask_path = os.path.join(self.mask_dir, img_name)
        
        # Load image and mask
        image = Image.open(img_path).convert("RGB")  # X-ray grayscale -> RGB for 3 channels
        mask = Image.open(mask_path).convert("L")    # grayscale mask
        
        # Resize
        image = image.resize(self.image_size, Image.BILINEAR)
        mask = mask.resize(self.image_size, Image.NEAREST)
        
        # Convert to tensor
        if self.transform:
            image = self.transform(image)
            mask = self.transform(mask)
        else:
            # Default: to tensor and normalize image to [0,1]
            image = transforms.ToTensor()(image)
            mask = transforms.ToTensor()(mask)  # mask values 0 or 1
        
        # Ensure mask is binary (0 or 1) - threshold if needed
        mask = (mask > 0.5).float()
        
        return image, mask

# ----------------------------
# 2. U-Net Model
# ----------------------------
class UNetBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(UNetBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
    
    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        return x

class UNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1, features=[64, 128, 256, 512]):
        super(UNet, self).__init__()
        self.ups = nn.ModuleList()
        self.downs = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Down part
        for feature in features:
            self.downs.append(UNetBlock(in_channels, feature))
            in_channels = feature
        
        # Up part
        for feature in reversed(features):
            self.ups.append(
                nn.ConvTranspose2d(
                    feature*2, feature, kernel_size=2, stride=2,
                )
            )
            self.ups.append(UNetBlock(feature*2, feature))
        
        self.bottleneck = UNetBlock(features[-1], features[-1]*2)
        self.final_conv = nn.Conv2d(features[0], out_channels, kernel_size=1)
    
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
                x = TF.resize(x, size=skip_connection.shape[2:])
            
            concat_skip = torch.cat((skip_connection, x), dim=1)
            x = self.ups[idx+1](concat_skip)
        
        return torch.sigmoid(self.final_conv(x))

# ----------------------------
# 3. Training & Validation Functions
# ----------------------------
def train_fn(train_loader, model, optimizer, loss_fn, scaler, device):
    model.train()
    loop = tqdm(train_loader, leave=True)
    total_loss = 0
    
    for batch_idx, (data, targets) in enumerate(loop):
        data = data.to(device=device)
        targets = targets.to(device=device)
        
        # Forward
        with torch.cuda.amp.autocast():
            predictions = model(data)
            loss = loss_fn(predictions, targets)
        
        # Backward
        optimizer.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        # Update tqdm
        loop.set_postfix(loss=loss.item())
        total_loss += loss.item()
    
    return total_loss / len(train_loader)

def val_fn(val_loader, model, loss_fn, device):
    model.eval()
    total_loss = 0
    
    with torch.no_grad():
        for data, targets in val_loader:
            data = data.to(device=device)
            targets = targets.to(device=device)
            
            predictions = model(data)
            loss = loss_fn(predictions, targets)
            total_loss += loss.item()
    
    return total_loss / len(val_loader)

# ----------------------------
# 4. Main Execution
# ----------------------------
if __name__ == '__main__':
    # Hyperparameters etc.
    LEARNING_RATE = 1e-4
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    BATCH_SIZE = 16
    NUM_EPOCHS = 30
    IMAGE_SIZE = (256, 256)
    NUM_WORKERS = 2
    PIN_MEMORY = True
    LOAD_MODEL = False
    TRAIN_IMG_DIR = "data/xray/train/images"
    TRAIN_MASK_DIR = "data/xray/train/masks"
    VAL_IMG_DIR = "data/xray/val/images"
    VAL_MASK_DIR = "data/xray/val/masks"
    MODEL_CHECKPOINT = "xray_unet_checkpoint.pth"
    
    print(f"Using device: {DEVICE}")
    
    # Model, loss, optimizer
    model = UNet(in_channels=3, out_channels=1).to(DEVICE)
    loss_fn = nn.BCEWithLogitsLoss()  # better for numerical stability
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scaler = torch.cuda.amp.GradScaler()
    
    # Data loaders
    train_transform = transforms.Compose([
        transforms.ToTensor(),
        # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # if using ImageNet stats
    ])
    
    val_transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    
    train_dataset = XRaySegmentationDataset(
        image_dir=TRAIN_IMG_DIR,
        mask_dir=TRAIN_MASK_DIR,
        image_size=IMAGE_SIZE,
        transform=train_transform,
    )
    
    val_dataset = XRaySegmentationDataset(
        image_dir=VAL_IMG_DIR,
        mask_dir=VAL_MASK_DIR,
        image_size=IMAGE_SIZE,
        transform=val_transform,
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=True,
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=False,
    )
    
    # Load model if desired
    if LOAD_MODEL:
        # utils.load_checkpoint(torch.load(MODEL_CHECKPOINT), model)
        pass
    
    # Training loop
    best_val_loss = float('inf')
    for epoch in range(NUM_EPOCHS):
        train_loss = train_fn(train_loader, model, optimizer, loss_fn, scaler, DEVICE)
        val_loss = val_fn(val_loader, model, loss_fn, DEVICE)
        
        print(f"Epoch {epoch+1}/{NUM_EPOCHS} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            checkpoint = {
                "state_dict": model.state_dict(),
                "optimizer": optimizer.state_dict(),
            }
            torch.save(checkpoint, MODEL_CHECKPOINT)
            print(f"Saved best model to {MODEL_CHECKPOINT}")
    
    print("Training finished!")
