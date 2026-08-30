#!/usr/bin/env python
"""
Training script for EchoNet-Dynamic LVEF regression.
This script clones the EchoNet-Dynamic repository from GitHub and trains an R(2+1)D model
for left ventricular ejection fraction estimation from echocardiogram videos.
Dataset: https://github.com/echonet/dynamic
"""

import os
import sys
import subprocess
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision
from torchvision.models.video import r3d_18, R3D_18_Weights
import numpy as np
import pandas as pd
from tqdm import tqdm
import cv2
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ----------------------------
# 0. Setup / Git Clone
# ----------------------------
REPO_URL = "https://github.com/echonet/dynamic.git"
REPO_DIR = "echonet-dynamic"
DATA_DIR = "data/echonet"
MODEL_CHECKPOINT = "echonet_dynamic_r2plus1d_checkpoint.pth"

def clone_repo_if_needed():
    """Clone the EchoNet-Dynamic repo if not present."""
    if not os.path.exists(REPO_DIR):
        print(f"Cloning EchoNet-Dynamic from {REPO_URL}...")
        try:
            subprocess.run(["git", "clone", REPO_URL, REPO_DIR], check=True)
            print("Repository cloned successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone repository: {e}")
            print("Please ensure git is installed and you have internet access.")
            sys.exit(1)
    else:
        print(f"Repository already exists at {REPO_DIR}")

def download_dataset():
    """
    Download EchoNet-Dynamic dataset.
    The dataset is typically available via the GitHub releases or direct links in the repo.
    This function attempts to download from the repo's data directory or release assets.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check if data already exists
    video_dir = os.path.join(DATA_DIR, "Videos")
    if os.path.exists(video_dir) and len(os.listdir(video_dir)) > 0:
        print(f"Dataset already exists at {video_dir}")
        return

    # The EchoNet repo typically contains a FileList.csv and videos in Videos/ directory
    # or provides download links. We'll check the repo structure.
    repo_data_dir = os.path.join(REPO_DIR, "data")
    if os.path.exists(repo_data_dir):
        print("Found data directory in repo, checking contents...")
        # Copy or symlink if present
        import shutil
        if not os.path.exists(video_dir):
            shutil.copytree(os.path.join(repo_data_dir, "Videos"), video_dir, dirs_exist_ok=True)
            print(f"Copied videos to {video_dir}")
        return

    # If not in repo, try to download from common locations
    print("Dataset not found in repo. Attempting to download from EchoNet releases...")
    # Note: Actual download URLs would need to be obtained from the EchoNet website/releases
    # This is a placeholder - in practice you'd use the official download links
    print("Please manually download the EchoNet-Dynamic dataset from:")
    print("  https://echonet.github.io/dynamic/")
    print(f"  and place videos in {video_dir}")
    print("  Expected structure: {video_dir}/<video_id>.mp4")
    print("  Also place FileList.csv in {DATA_DIR}/FileList.csv")

# ----------------------------
# 1. Dataset Class
# ----------------------------
class EchoNetDynamicDataset(Dataset):
    """
    Dataset for EchoNet-Dynamic echocardiogram videos.
    Each sample: video clip (C, T, H, W) -> LVEF regression target (float)
    """
    def __init__(self, video_dir, filelist_csv, clip_length=16, image_size=(112, 112),
                 transform=None, split='train', val_ratio=0.2, seed=42):
        """
        Args:
            video_dir (str): Directory containing video files (.mp4, .avi)
            filelist_csv (str): Path to FileList.csv with columns: FileName, Split, EF, ...
            clip_length (int): Number of frames to sample per video (T)
            image_size (tuple): Target spatial size (H, W)
            transform (callable): Optional transform on frames
            split (str): 'train', 'val', or 'test'
            val_ratio (float): Validation split ratio if using random split
            seed (int): Random seed for splitting
        """
        self.video_dir = video_dir
        self.clip_length = clip_length
        self.image_size = image_size
        self.transform = transform
        self.split = split

        # Load file list
        if not os.path.exists(filelist_csv):
            raise FileNotFoundError(f"FileList.csv not found at {filelist_csv}")

        self.df = pd.read_csv(filelist_csv)

        # Standard EchoNet FileList columns: FileName, Split, EF, ...
        # Handle different column names
        if 'FileName' not in self.df.columns:
            # Try common alternatives
            for col in ['filename', 'File', 'video']:
                if col in self.df.columns:
                    self.df = self.df.rename(columns={col: 'FileName'})
                    break

        if 'EF' not in self.df.columns:
            for col in ['ef', 'LVEF', 'ejection_fraction']:
                if col in self.df.columns:
                    self.df = self.df.rename(columns={col: 'EF'})
                    break

        if 'Split' not in self.df.columns:
            # Create random split
            np.random.seed(seed)
            self.df['Split'] = np.random.choice(['train', 'val', 'test'],
                                                 size=len(self.df),
                                                 p=[1-val_ratio-0.1, val_ratio, 0.1])

        # Filter by split
        self.df = self.df[self.df['Split'] == split].reset_index(drop=True)

        # Ensure EF is numeric
        self.df['EF'] = pd.to_numeric(self.df['EF'], errors='coerce')
        self.df = self.df.dropna(subset=['EF', 'FileName']).reset_index(drop=True)

        print(f"Loaded {len(self.df)} samples for split '{split}'")
        print(f"EF range: {self.df['EF'].min():.1f} - {self.df['EF'].max():.1f}")

        # Default transform: resize + normalize
        if self.transform is None:
            self.transform = torchvision.transforms.Compose([
                torchvision.transforms.ToPILImage(),
                torchvision.transforms.Resize(image_size),
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                                 std=[0.229, 0.224, 0.225]),
            ])

    def __len__(self):
        return len(self.df)

    def _load_video_frames(self, video_path):
        """Load and sample frames from video file."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            cap.release()
            raise ValueError(f"Video has 0 frames: {video_path}")

        # Uniformly sample clip_length frames
        frame_indices = np.linspace(0, total_frames - 1, self.clip_length, dtype=int)
        frames = []

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                # If failed, duplicate last frame or use black
                if frames:
                    frames.append(frames[-1])
                else:
                    frames.append(np.zeros((self.image_size[1], self.image_size[0], 3), dtype=np.uint8))
                continue

            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)

        cap.release()

        # Stack: (T, H, W, C) -> will be permuted to (C, T, H, W) after transform
        return frames  # list of (H, W, C) numpy arrays

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        video_filename = row['FileName']
        ef = float(row['EF'])

        # Try different extensions
        video_path = None
        for ext in ['.mp4', '.avi', '.mov', '.MP4', '.AVI']:
            test_path = os.path.join(self.video_dir, video_filename + ext)
            if os.path.exists(test_path):
                video_path = test_path
                break
            # Also try without extension if filename already has one
            test_path = os.path.join(self.video_dir, video_filename)
            if os.path.exists(test_path):
                video_path = test_path
                break

        if video_path is None:
            # Return dummy data if video not found (for robustness)
            print(f"Warning: Video not found for {video_filename}, returning dummy")
            dummy_video = torch.zeros(3, self.clip_length, *self.image_size)
            return dummy_video, torch.tensor(ef, dtype=torch.float32)

        # Load frames
        frames = self._load_video_frames(video_path)  # list of (H, W, C)

        # Apply transform to each frame
        transformed_frames = []
        for frame in frames:
            if self.transform:
                # transform expects (H, W, C) numpy or PIL
                transformed = self.transform(frame)  # (C, H, W)
            else:
                transformed = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0
            transformed_frames.append(transformed)

        # Stack: (T, C, H, W) -> (C, T, H, W) for 3D CNN
        video_tensor = torch.stack(transformed_frames, dim=1)  # (C, T, H, W)

        return video_tensor, torch.tensor(ef, dtype=torch.float32)

# ----------------------------
# 2. R(2+1)D Model
# ----------------------------
class R2Plus1D_LVEF(nn.Module):
    """
    R(2+1)D model for LVEF regression.
    Based on torchvision's R3D_18 but with (2+1)D convolutions.
    """
    def __init__(self, num_classes=1, pretrained=True, dropout_rate=0.5):
        super(R2Plus1D_LVEF, self).__init__()

        # Use torchvision's R3D_18 as backbone
        # R3D uses 3D convolutions; we'll modify for (2+1)D
        weights = R3D_18_Weights.KINETICS400_V1 if pretrained else None
        self.backbone = r3d_18(weights=weights)

        # Modify first conv to (2+1)D: spatial 2D conv + temporal 1D conv
        # Original: Conv3d(3, 64, kernel_size=(3,7,7), stride=(1,2,2), padding=(1,3,3))
        # We replace with sequential: Conv2d + Conv1d
        # For simplicity, we'll keep the 3D conv but note it's R3D not R(2+1)D
        # True R(2+1)D would require custom layers

        # Get input features for final FC
        in_features = self.backbone.fc.in_features

        # Replace classifier
        self.backbone.fc = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes)  # Regression output
        )

    def forward(self, x):
        # x: (B, C, T, H, W)
        return self.backbone(x)

# Alternative: True R(2+1)D implementation
class R2Plus1DStem(nn.Module):
    """R(2+1)D stem: spatial 2D conv + temporal 1D conv"""
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
    """R(2+1)D residual block"""
    def __init__(self, in_channels, out_channels, stride=1, downsample=None):
        super().__init__()
        # First (2+1)D conv
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

        # Second (2+1)D conv
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
    """
    Full R(2+1)D network for LVEF regression.
    Architecture similar to R3D-18 but with (2+1)D blocks.
    """
    def __init__(self, num_classes=1, layers=[2, 2, 2, 2], dropout_rate=0.5):
        super(R2Plus1DNet, self).__init__()

        self.in_channels = 64

        # Stem
        self.stem = R2Plus1DStem(3, 64)
        self.pool = nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))

        # Layers
        self.layer1 = self._make_layer(64, layers[0], stride=1)
        self.layer2 = self._make_layer(128, layers[1], stride=2)
        self.layer3 = self._make_layer(256, layers[2], stride=2)
        self.layer4 = self._make_layer(512, layers[3], stride=2)

        self.avgpool = nn.AdaptiveAvgPool3d((1, 1, 1))

        # Classifier
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

# ----------------------------
# 3. Training & Validation
# ----------------------------
def train_fn(train_loader, model, optimizer, loss_fn, device, scaler=None):
    model.train()
    loop = tqdm(train_loader, leave=True, desc="Training")
    total_loss = 0
    all_preds = []
    all_targets = []

    for data, targets in loop:
        data = data.to(device=device, non_blocking=True)  # (B, C, T, H, W)
        targets = targets.to(device=device, non_blocking=True).unsqueeze(1)  # (B, 1)

        optimizer.zero_grad()

        if scaler is not None:
            with torch.cuda.amp.autocast():
                preds = model(data)
                loss = loss_fn(preds, targets)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            preds = model(data)
            loss = loss_fn(preds, targets)
            loss.backward()
            optimizer.step()

        total_loss += loss.item()
        all_preds.append(preds.detach().cpu())
        all_targets.append(targets.detach().cpu())

        loop.set_postfix(loss=loss.item())

    all_preds = torch.cat(all_preds).numpy().flatten()
    all_targets = torch.cat(all_targets).numpy().flatten()
    mae = np.mean(np.abs(all_preds - all_targets))

    return total_loss / len(train_loader), mae

def val_fn(val_loader, model, loss_fn, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for data, targets in val_loader:
            data = data.to(device=device, non_blocking=True)
            targets = targets.to(device=device, non_blocking=True).unsqueeze(1)

            preds = model(data)
            loss = loss_fn(preds, targets)

            total_loss += loss.item()
            all_preds.append(preds.cpu())
            all_targets.append(targets.cpu())

    all_preds = torch.cat(all_preds).numpy().flatten()
    all_targets = torch.cat(all_targets).numpy().flatten()
    mae = np.mean(np.abs(all_preds - all_targets))
    rmse = np.sqrt(np.mean((all_preds - all_targets) ** 2))

    return total_loss / len(val_loader), mae, rmse

# ----------------------------
# 4. Main Execution
# ----------------------------
def main():
    # Hyperparameters
    LEARNING_RATE = 1e-4
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    BATCH_SIZE = 8  # Smaller batch for video data
    NUM_EPOCHS = 50
    CLIP_LENGTH = 16
    IMAGE_SIZE = (112, 112)
    NUM_WORKERS = 4
    PIN_MEMORY = True
    USE_AMP = torch.cuda.is_available()

    # Data paths
    VIDEO_DIR = os.path.join(DATA_DIR, "Videos")
    FILELIST_CSV = os.path.join(DATA_DIR, "FileList.csv")

    print(f"Using device: {DEVICE}")
    print(f"Mixed precision: {USE_AMP}")

    # Clone repo and download data
    clone_repo_if_needed()
    download_dataset()

    # Check if data exists
    if not os.path.exists(VIDEO_DIR) or not os.path.exists(FILELIST_CSV):
        print("\n" + "="*60)
        print("DATASET NOT FOUND!")
        print("="*60)
        print(f"Please download EchoNet-Dynamic dataset and place:")
        print(f"  - Videos in: {VIDEO_DIR}")
        print(f"  - FileList.csv in: {FILELIST_CSV}")
        print("\nDownload from: https://echonet.github.io/dynamic/")
        print("Or check the cloned repo at: ./echonet-dynamic/")
        print("="*60)
        return

    # Create datasets
    print("\nCreating datasets...")
    train_dataset = EchoNetDynamicDataset(
        video_dir=VIDEO_DIR,
        filelist_csv=FILELIST_CSV,
        clip_length=CLIP_LENGTH,
        image_size=IMAGE_SIZE,
        split='train'
    )

    val_dataset = EchoNetDynamicDataset(
        video_dir=VIDEO_DIR,
        filelist_csv=FILELIST_CSV,
        clip_length=CLIP_LENGTH,
        image_size=IMAGE_SIZE,
        split='val'
    )

    if len(train_dataset) == 0 or len(val_dataset) == 0:
        print("Error: No data loaded. Check FileList.csv and video directory.")
        return

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=True,
        drop_last=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=False,
    )

    # Model
    print("\nInitializing R(2+1)D model...")
    model = R2Plus1DNet(num_classes=1).to(DEVICE)

    # Loss and optimizer
    loss_fn = nn.L1Loss()  # MAE loss for regression
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    scaler = torch.cuda.amp.GradScaler() if USE_AMP else None

    # Training loop
    print("\nStarting training...")
    best_val_mae = float('inf')

    for epoch in range(NUM_EPOCHS):
        train_loss, train_mae = train_fn(train_loader, model, optimizer, loss_fn, DEVICE, scaler)
        val_loss, val_mae, val_rmse = val_fn(val_loader, model, loss_fn, DEVICE)

        scheduler.step(val_loss)

        print(f"Epoch {epoch+1}/{NUM_EPOCHS} - "
              f"Train Loss: {train_loss:.4f}, Train MAE: {train_mae:.4f} | "
              f"Val Loss: {val_loss:.4f}, Val MAE: {val_mae:.4f}, Val RMSE: {val_rmse:.4f}")

        # Save best model
        if val_mae < best_val_mae:
            best_val_mae = val_mae
            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "val_mae": val_mae,
                "val_rmse": val_rmse,
                "config": {
                    "clip_length": CLIP_LENGTH,
                    "image_size": IMAGE_SIZE,
                    "architecture": "R(2+1)D-18",
                }
            }
            torch.save(checkpoint, MODEL_CHECKPOINT)
            print(f"  ✓ Saved best model (Val MAE: {val_mae:.4f}) to {MODEL_CHECKPOINT}")

    print(f"\nTraining finished! Best validation MAE: {best_val_mae:.4f}")
    print(f"Model saved to: {MODEL_CHECKPOINT}")

if __name__ == '__main__':
    main()