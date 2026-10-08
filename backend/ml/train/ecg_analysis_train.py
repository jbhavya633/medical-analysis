#!/usr/bin/env python
"""
Training script for ECG analysis.
This script trains a 1D CNN model for ECG classification (e.g., rhythm detection).
Replace the placeholder data loading with your actual dataset (e.g., PTB-XL, MIT-BIH, or MIMIC-IV-ECG).
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from tqdm import tqdm

# ----------------------------
# 1. Dataset Class
# ----------------------------
class ECGDataset(Dataset):
    def __init__(self, data_dir, label_csv, max_length=5000, transform=None):
        """
        Args:
            data_dir (string): Directory with ECG signal files (.npy).
            label_csv (string): Path to CSV file with columns: 'filename', 'label' (or multiple labels).
            max_length (int): Fixed length to truncate/pad signals.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.data_dir = data_dir
        self.labels_df = pd.read_csv(label_csv)
        self.max_length = max_length
        self.transform = transform
        
        # Ensure filename column exists
        if 'filename' not in self.labels_df.columns:
            raise ValueError("Label CSV must contain a 'filename' column")
        if 'label' not in self.labels_df.columns:
            raise ValueError("Label CSV must contain a 'label' column")
        
        # Map string labels to integers if needed
        self.label_values = self.labels_df['label'].unique()
        self.label_to_int = {label: i for i, label in enumerate(self.label_values)}
        self.labels_df['label_int'] = self.labels_df['label'].map(self.label_to_int)
        self.num_classes = len(self.label_to_int)
    
    def __len__(self):
        return len(self.labels_df)
    
    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        
        row = self.labels_df.iloc[idx]
        file_name = row['filename']
        label_int = row['label_int']
        
        # Load ECG signal
        file_path = os.path.join(self.data_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ECG file not found: {file_path}")
        
        # Assuming .npy format; adjust if needed
        signal = np.load(file_path)  # shape: (leads, time) or (time, leads) or (time,)
        
        # Ensure shape is (leads, time)
        if signal.ndim == 1:
            # Single lead, reshape to (1, time)
            signal = signal.reshape(1, -1)
        elif signal.ndim == 2:
            # Could be (leads, time) or (time, leads)
            # Heuristic: if second dimension is common lead count (e.g., 12), assume (time, leads)
            if signal.shape[1] in [12, 15, 18]:  # typical lead counts
                signal = signal.T  # convert to (leads, time)
            # else assume first dim is leads
        else:
            raise ValueError(f"Unexpected signal shape: {signal.shape}")
        
        # Truncate or pad to max_length
        if signal.shape[1] > self.max_length:
            signal = signal[:, :self.max_length]
        elif signal.shape[1] < self.max_length:
            pad_width = self.max_length - signal.shape[1]
            signal = np.pad(signal, ((0, 0), (0, pad_width)), mode='constant')
        
        # Normalize per lead (zero mean, unit variance)
        signal = (signal - np.mean(signal, axis=1, keepdims=True)) / (np.std(signal, axis=1, keepdims=True) + 1e-8)
        
        # Convert to tensor
        signal = torch.from_numpy(signal).float()
        
        if self.transform:
            signal = self.transform(signal)
        
        label = torch.tensor(label_int, dtype=torch.long)
        
        return signal, label

# ----------------------------
# 2. 1D CNN Model
# ----------------------------
class ECGNet(nn.Module):
    def __init__(self, input_channels=12, num_classes=5, dropout_rate=0.5):
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
        
        # Compute flattened size: after three poolings, length = max_length // 8
        self.fc1 = nn.Linear(256 * (5000 // 8), 128)  # placeholder max_length; will adjust later
        self.bn4 = nn.BatchNorm1d(128)
        self.dropout = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(128, num_classes)
        
        self.relu = nn.ReLU(inplace=True)
    
    def forward(self, x):
        # x shape: (batch, leads, seq_len)
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

# ----------------------------
# 3. Training & Validation Functions
# ----------------------------
def train_fn(train_loader, model, optimizer, loss_fn, device):
    model.train()
    loop = tqdm(train_loader, leave=True)
    total_loss = 0
    correct = 0
    total = 0
    
    for batch_idx, (data, targets) in enumerate(loop):
        data = data.to(device=device)
        targets = targets.to(device=device)
        
        # Forward
        scores = model(data)
        loss = loss_fn(scores, targets)
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Metrics
        _, predictions = scores.max(1)
        correct += (predictions == targets).sum().item()
        total += targets.size(0)
        total_loss += loss.item()
        
        loop.set_postfix(loss=loss.item(), acc=100.*correct/total)
    
    return total_loss / len(train_loader), correct / total

def val_fn(val_loader, model, loss_fn, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for data, targets in val_loader:
            data = data.to(device=device)
            targets = targets.to(device=device)
            
            scores = model(data)
            loss = loss_fn(scores, targets)
            
            _, predictions = scores.max(1)
            correct += (predictions == targets).sum().item()
            total += targets.size(0)
            total_loss += loss.item()
    
    return total_loss / len(val_loader), correct / total

# ----------------------------
# 4. Main Execution
# ----------------------------
if __name__ == '__main__':
    # Hyperparameters etc.
    LEARNING_RATE = 1e-3
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    BATCH_SIZE = 64
    NUM_EPOCHS = 25
    MAX_LENGTH = 5000  # adjust based on your ECG sampling rate and duration (e.g., 5000 samples @ 500Hz = 10 sec)
    NUM_WORKERS = 2
    PIN_MEMORY = True
    TRAIN_DATA_DIR = "data/ecg/train/signals"
    TRAIN_LABEL_CSV = "data/ecg/train_labels.csv"
    VAL_DATA_DIR = "data/ecg/val/signals"
    VAL_LABEL_CSV = "data/ecg/val_labels.csv"
    MODEL_CHECKPOINT = "ecg_cnn_checkpoint.pth"
    
    print(f"Using device: {DEVICE}")
    
    # Model, loss, optimizer
    # We need to know input channels (number of leads) and num classes from data
    # For now, we assume 12 leads; will adjust after peeking at dataset
    # Let's create a temporary dataset to infer shape and classes
    temp_dataset = ECGDataset(
        data_dir=TRAIN_DATA_DIR,
        label_csv=TRAIN_LABEL_CSV,
        max_length=MAX_LENGTH,
    )
    num_leads = temp_dataset[0][0].shape[0]  # leads from first sample
    num_classes = temp_dataset.num_classes
    print(f"Detected {num_leads} leads, {num_classes} classes")
    
    model = ECGNet(input_channels=num_leads, num_classes=num_classes).to(DEVICE)
    # Adjust fc1 input size based on actual MAX_LENGTH
    model.fc1 = nn.Linear(256 * (MAX_LENGTH // 8), 128).to(DEVICE)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Data loaders
    train_dataset = ECGDataset(
        data_dir=TRAIN_DATA_DIR,
        label_csv=TRAIN_LABEL_CSV,
        max_length=MAX_LENGTH,
    )
    
    val_dataset = ECGDataset(
        data_dir=VAL_DATA_DIR,
        label_csv=VAL_LABEL_CSV,
        max_length=MAX_LENGTH,
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
    
    # Training loop
    best_val_acc = 0.0
    for epoch in range(NUM_EPOCHS):
        train_loss, train_acc = train_fn(train_loader, model, optimizer, loss_fn, DEVICE)
        val_loss, val_acc = val_fn(val_loader, model, loss_fn, DEVICE)
        
        print(f"Epoch {epoch+1}/{NUM_EPOCHS} - "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint = {
                "state_dict": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch,
                "val_acc": val_acc,
                "label_map": temp_dataset.label_to_int,  # save mapping
                "max_length": MAX_LENGTH,
                "num_leads": num_leads,
                "num_classes": num_classes
            }
            torch.save(checkpoint, MODEL_CHECKPOINT)
            print(f"Saved best model to {MODEL_CHECKPOINT}")
    
    print(f"Training finished! Best validation accuracy: {best_val_acc:.4f}")
