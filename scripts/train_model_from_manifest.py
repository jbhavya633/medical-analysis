import requests
import zipfile
import io
import os
import numpy as np
import pydicom
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import hashlib

import argparse

# Configuration: override with env vars or --manifest / --output-dir
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.getenv('TCIA_MANIFEST_PATH', os.path.join(REPO_ROOT, 'data', 'manifests', 'TCGA-BLCA-August-30-2019-NBIA-manifest.tcia'))
OUTPUT_DIR = os.getenv('TCIA_OUTPUT_DIR', os.path.join(REPO_ROOT, 'data', 'tcia'))

def parse_manifest(manifest_path):
    """Parse TCIA manifest to get series UIDs."""
    with open(manifest_path, 'r') as f:
        lines = f.readlines()
    # Skip header lines until we find 'ListOfSeriesToDownload='
    series_uids = []
    capturing = False
    for line in lines:
        line = line.strip()
        if line.startswith('ListOfSeriesToDownload='):
            capturing = True
            continue
        if capturing and line:
            # Each line is a series UID
            series_uids.append(line)
    return series_uids

def download_series(series_uid, output_dir):
    """Download a series from TCIA given its series UID."""
    # The manifest includes a downloadServerUrl; we need to extract it from the manifest.
    # For simplicity, we hardcode the URL from the manifest we saw earlier.
    # In practice, we should parse the manifest for downloadServerUrl.
    base_url = 'https://public.cancerimagingarchive.net/nbia-download/servlet/DownloadServlet'
    # Parameters: SeriesInstanceUID, includeAnnotation=true
    params = {
        'SeriesInstanceUID': series_uid,
        'includeAnnotation': 'true'
    }
    print(f'Downloading series {series_uid}...')
    try:
        resp = requests.get(base_url, params=params, stream=True, timeout=30)
        resp.raise_for_status()
        # The response is a ZIP file containing DICOM files
        zip_data = io.BytesIO(resp.content)
        with zipfile.ZipFile(zip_data) as zf:
            # Extract to a subdirectory named after the series UID (or hash)
            extract_dir = os.path.join(output_dir, hashlib.md5(series_uid.encode()).hexdigest())
            zf.extractall(extract_dir)
        return extract_dir
    except Exception as e:
        print(f'Failed to download series {series_uid}: {e}')
        return None

def load_dicom_series(dicom_dir):
    """Load all DICOM files in a directory and stack into a 3D array."""
    dicom_files = []
    for root, dirs, files in os.walk(dicom_dir):
        for file in files:
            if file.lower().endswith('.dcm') or '.' not in file:  # DICOM may have no extension
                dicom_files.append(os.path.join(root, file))
    if not dicom_files:
        raise ValueError('No DICOM files found in directory')
    # Read and sort by InstanceNumber or ImagePositionPatient
    datasets = []
    for f in dicom_files:
        try:
            ds = pydicom.dcmread(f, force=True)
            datasets.append(ds)
        except Exception as e:
            print(f'Warning: Could not read {f}: {e}')
    if not datasets:
        raise ValueError('No valid DICOM datasets')
    # Sort by InstanceNumber if present, else by filename
    try:
        datasets.sort(key=lambda x: int(x.InstanceNumber) if hasattr(x, 'InstanceNumber') else 0)
    except:
        datasets.sort(key=lambda x: x.filename)
    # Stack pixel arrays
    arrays = []
    for ds in datasets:
        arr = ds.pixel_array
        # Ensure 2D
        if arr.ndim != 2:
            # If it's already 3D (unlikely for single slice), take first slice?
            arr = arr.squeeze()
        arrays.append(arr.astype(np.float32))
    # Stack along third dimension
    stack = np.stack(arrays, axis=-1)
    return stack

def extract_features(image_3d):
    """Extract simple radiomics features from a 3D image."""
    # Flatten the image
    flat = image_3d.flatten()
    # Basic statistics
    features = {}
    features['mean'] = np.mean(flat)
    features['std'] = np.std(flat)
    features['median'] = np.median(flat)
    features['min'] = np.min(flat)
    features['max'] = np.max(flat)
    features['percentile_10'] = np.percentile(flat, 10)
    features['percentile_90'] = np.percentile(flat, 90)
    # Histogram features
    hist, bins = np.histogram(flat, bins=50, density=True)
    features['hist_mean'] = np.mean(hist)
    features['hist_std'] = np.std(hist)
    # Entropy
    p = hist + 1e-10  # avoid zeros
    features['entropy'] = -np.sum(p * np.log2(p))
    # Return as numpy array
    return np.array(list(features.values()))

def main():
    global MANIFEST_PATH, OUTPUT_DIR
    parser = argparse.ArgumentParser(description='Download a TCIA manifest and train a demo model.')
    parser.add_argument('--manifest', default=MANIFEST_PATH, help='Path to the .tcia manifest file')
    parser.add_argument('--output-dir', default=OUTPUT_DIR, help='Directory for downloads and artifacts')
    args = parser.parse_args()
    MANIFEST_PATH, OUTPUT_DIR = args.manifest, args.output_dir
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Parse manifest
    series_uids = parse_manifest(MANIFEST_PATH)
    print(f'Found {len(series_uids)} series in manifest.')
    # Limit to first 5 for demo
    series_uids = series_uids[:5]
    
    features_list = []
    labels_list = []  # dummy labels: even index -> 0, odd index -> 1
    
    for idx, uid in enumerate(series_uids):
        print(f'Processing series {idx+1}/{len(series_uids)}: {uid}')
        # Download series
        dicom_dir = download_series(uid, OUTPUT_DIR)
        if dicom_dir is None:
            continue
        try:
            # Load DICOM series
            image_3d = load_dicom_series(dicom_dir)
            print(f'  Loaded image shape: {image_3d.shape}')
            # Extract features
            feats = extract_features(image_3d)
            features_list.append(feats)
            # Dummy label: based on index parity
            labels_list.append(idx % 2)
        except Exception as e:
            print(f'  Error processing series {uid}: {e}')
            continue
    
    if len(features_list) == 0:
        print('No features extracted. Exiting.')
        return
    
    X = np.array(features_list)
    y = np.array(labels_list)
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train logistic regression
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    
    # Predict
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f'Classification accuracy (dummy labels): {acc:.2f}')
    
    # Save model and features
    import joblib
    joblib.dump(clf, os.path.join(OUTPUT_DIR, 'model.pkl'))
    np.save(os.path.join(OUTPUT_DIR, 'features.npy'), X)
    np.save(os.path.join(OUTPUT_DIR, 'labels.npy'), y)
    print('Model and features saved to', OUTPUT_DIR)

if __name__ == '__main__':
    main()
