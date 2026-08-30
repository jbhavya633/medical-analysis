
# Scripts for Training Model from TCIA Manifest

This directory contains a Python script that demonstrates how to use a TCIA manifest file to download DICOM series, extract radiomics features, and train a simple classifier.

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - requests
  - pydicom
  - numpy
  - scikit-learn
  - joblib

You can install them using pip:

`ash
pip install requests pydicom numpy scikit-learn joblib
`

## Usage

1. Place your TCIA manifest file (e.g., TCGA-BLCA-August-30-2019-NBIA-manifest.tcia or CMB-PCA_v12_20260702.tcia) on your Desktop (or update the MANIFEST_PATH variable in the script).

2. Run the script:

`ash
python train_model_from_manifest.py
`

The script will:
- Parse the manifest to get a list of series UIDs.
- Download the first 5 series (for demonstration) from TCIA.
- Load the DICOM series into 3D arrays.
- Extract basic radiomics features (mean, std, median, min, max, percentiles, histogram, entropy).
- Train a logistic regression classifier using dummy labels (based on series index parity) for demonstration.
- Save the trained model and extracted features to the data directory.

## Notes

- The script uses dummy labels for demonstration purposes. In a real scenario, you would need to replace the dummy labels with actual ground truth labels (e.g., diagnosis, outcome) corresponding to each series.
- Downloading DICOM data may consume significant disk space and bandwidth. The script limits to 5 series to keep the demo lightweight.
- Ensure you have internet access to download from the TCIA servers.

## Output

- data/model.pkl: Trained logistic regression model.
- data/features.npy: Extracted features for each series.
- data/labels.npy: Labels used for training (dummy labels).

## Disclaimer

This script is for educational purposes only. Always ensure you have the right to use the data and comply with TCIA usage policies.

