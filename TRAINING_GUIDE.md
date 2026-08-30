
# Guide: Extracting Data from TCIA Manifest and Training a Model

This guide explains how to use the TCIA manifest files (TCGA-BLCA-August-30-2019-NBIA-manifest.tcia and CMB-PCA_v12_20260702.tcia) to download medical imaging data, extract features, and train a machine learning model.

## Overview

The TCGA-BLCA and CMB-PCA datasets contain medical imaging studies (likely DICOM format) that can be used for training predictive models. The manifest files provide a list of series identifiers that can be used to download the data from The Cancer Imaging Archive (TCIA).

## Prerequisites

To run the extraction and training process, you need:

1. **Python 3.7+** installed on your system
2. **Required Python packages**:
   - equests - for downloading data from TCIA
   - pydicom - for reading and processing DICOM files
   - 
umpy - for numerical operations
   - scikit-learn - for machine learning algorithms
   - joblib - for saving the trained model

Install packages using:
`ash
pip install requests pydicom numpy scikit-learn joblib
`

## Step-by-Step Process

### 1. Understanding the Manifest Format

TCIA manifest files contain:
- downloadServerUrl: The base URL for downloading data
- ListOfSeriesToDownload: A list of Series Instance UIDs (unique identifiers for imaging series)
- Other metadata like databasketId and manifestVersion

Example manifest content:
`
downloadServerUrl=https://public.cancerimagingarchive.net/nbia-download/servlet/DownloadServlet
includeAnnotation=true
noOfrRetry=4
databasketId=manifest-1567090213715.tcia
manifestVersion=3.0
ListOfSeriesToDownload=
1.3.6.1.4.1.14519.5.2.1.6354.4016.327461617226973472928798638276
1.3.6.1.4.1.14519.5.2.1.6354.4016.458992405132985983267405308283
...
`

### 2. Data Extraction Workflow

The process involves:
1. **Parsing the manifest** to extract Series Instance UIDs
2. **Downloading each series** from TCIA using the Series UID
3. **Converting DICOM series to 3D arrays** for processing
4. **Extracting radiomics features** from the 3D image data
5. **Training a machine learning model** using the extracted features
6. **Saving the model and features** for later use

### 3. Available Implementation

We have prepared a Python script that implements this workflow:
- Location: scripts/train_model_from_manifest.py
- Features extracted: mean, std, median, min, max, 10th/90th percentiles, histogram statistics, entropy
- Model: Logistic Regression (for demonstration; can be replaced with other algorithms)
- Includes proper error handling and progress reporting

### 4. How to Run the Script

#### Option 1: Using the TCGA-BLCA Manifest (default)
`ash
cd scripts
python train_model_from_manifest.py
`

#### Option 2: Using the CMB-PCA Manifest
1. Edit 	rain_model_from_manifest.py
2. Change the MANIFEST_PATH variable to:
   `python
   MANIFEST_PATH = r'C:\Users\ASUS\Desktop\CMB-PCA_v12_20260702.tcia'
   `
3. Run the script:
   `ash
   python train_model_from_manifest.py
   `

### 5. Expected Output

When running successfully, you should see:
1. Messages showing the number of series found in the manifest
2. Progress messages for each series being downloaded and processed
3. Image shape information for each loaded DICOM series
4. Final classification accuracy (using dummy labels for demonstration)
5. Confirmation that model and features have been saved to the data directory

### 6. Output Files

After successful execution, the data directory will contain:
- model.pkl: Trained machine learning model (joblib format)
- eatures.npy: NumPy array of extracted features for each series
- labels.npy: NumPy array of labels used for training

### 7. Important Notes

#### ⚠️ Dummy Labels Warning
The current script uses **dummy labels** for demonstration purposes (assigning labels based on whether the series index is even or odd). **In a real application, you must replace these with actual ground truth labels** (e.g., diagnosis, outcome, biomarker status) corresponding to each imaging series.

#### 📊 Feature Enhancement
The current feature extraction computes basic radiomics statistics. For improved model performance, consider adding:
- Texture features (GLCM, GLRLM, GLSZM, NGTDM)
- Shape and size features
- Wavelet-based features
- Deep learning features from pre-trained CNNs

#### 🔬 Model Selection
Logistic Regression is used as a simple baseline. Depending on your problem, you may want to try:
- Support Vector Machines (SVM)
- Random Forest
- Gradient Boosting (XGBoost, LightGBM)
- Neural Networks
- Ensemble methods

#### 💾 Data Management
DICOM files can be large (hundreds of MBs to GBs per series). Ensure you have sufficient disk space before downloading. The script creates subdirectories in the data folder for each downloaded series.

#### 🌐 Network Requirements
The script requires internet access to download data from TCIA servers. Download speed will depend on your connection.

### 8. Customization Options

#### Changing the Number of Series
To process more or fewer series, edit this line in the script:
`python
# Limit to first 5 for demo
series_uids = series_uids[:5]
`
Change 5 to your desired number, or remove the line to process all series.

#### Modifying Feature Extraction
Edit the extract_features() function to add or remove features:
`python
def extract_features(image_3d):
    # Your custom feature extraction code here
    pass
`

#### Changing the Model
Edit the model training section to use a different algorithm:
`python
# From:
clf = LogisticRegression(max_iter=1000)
# To example:
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier(n_estimators=100, random_state=42)
`

### 9. Troubleshooting

#### Common Issues
- **Package not found**: Ensure all required packages are installed (pip list to verify)
- **Download failures**: Check internet connection and TCIA server status
- **DICOM read errors**: Some series may have corrupted or non-standard DICOM files
- **Memory issues**: Very large series may require more RAM; consider processing smaller subsets

#### Getting Help
- TCIA API documentation: https://cancerimagingarchive.net/nbia-api/
- pydicom documentation: https://pydicom.github.io/pydicom/stable/
- scikit-learn documentation: https://scikit-learn.org/stable/

## Next Steps for Your Analysis

To adapt this for your specific research question:

1. **Obtain Ground Truth Labels**: Map each series UID in the manifest to its corresponding clinical outcome, diagnosis, or biomarker status.

2. **Replace Dummy Labels**: Modify the label assignment section:
   `python
   # Replace this dummy labeling:
   labels_list.append(idx % 2)
   
   # With actual label lookup:
   actual_label = get_label_for_series(uid)  # Implement this function
   labels_list.append(actual_label)
   `

3. **Validate Your Approach**: Use appropriate cross-validation and performance metrics for your problem type.

4. **Consider Data Augmentation**: For limited datasets, techniques like rotation, flipping, or intensity adjustments can help improve model generalization.

5. **Explore Advanced Techniques**: 
   - Transfer learning with deep learning models
   - Multi-modal analysis combining imaging with clinical/genomic data
   - Unsupervised learning for discovery of imaging phenotypes

## Files in This Repository

- scripts/train_model_from_manifest.py: Main implementation script
- scripts/README.md: Brief overview of the scripts
- TCGA-BLCA-August-30-2019-NBIA-manifest.tcia: TCGA Bladder Cancer manifest
- CMB-PCA_v12_20260702.tcia: CMB-PCA manifest
- TRAINING_GUIDE.md: This detailed guide

## Acknowledgments

Data provided by The Cancer Imaging Archive (TCIA). Funding for TCIA is provided by the National Cancer Institute (NCI) and the National Institutes of Health (NIH).

---

**Ready to begin?** Install the required Python packages and run the script from the scripts directory.

