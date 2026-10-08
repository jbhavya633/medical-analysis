#!/usr/bin/env python
"""Standalone ECG analysis server (port 5002). Prefer the FastAPI gateway in backend/main.py.

Run from the repo root: python -m backend.ml.inference.ecg_analysis_server
"""

import logging

from flask import Flask, jsonify, request

from backend.models import InvalidInputError, ModelUnavailableError
from backend.models.ecg_model import ECGModel

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
MODEL = ECGModel()
MODEL.load()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': MODEL.status()})


@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    if file is None:
        return jsonify({'error': 'No file provided'}), 400
    try:
        return jsonify(MODEL.predict_file(file.stream, file.filename))
    except ModelUnavailableError:
        return jsonify({'error': 'ECG model is not loaded; this modality is unavailable'}), 503
    except InvalidInputError as exc:
        return jsonify({'error': str(exc)}), 422


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=False)
