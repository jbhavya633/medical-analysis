#!/usr/bin/env python
"""Standalone chest X-ray segmentation server (port 5001). Prefer the FastAPI gateway in backend/main.py.

Run from the repo root: python -m backend.ml.inference.xray_segmentation_server
"""

import logging

from flask import Flask, jsonify, request

from backend.models import InvalidInputError, ModelUnavailableError
from backend.models.xray_model import XRayModel

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
MODEL = XRayModel()
MODEL.load()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': MODEL.status()})


@app.route('/segment', methods=['POST'])
def segment():
    file = request.files.get('image')
    if file is None:
        return jsonify({'error': 'No image provided'}), 400
    try:
        return jsonify(MODEL.predict_file(file.stream, file.filename))
    except ModelUnavailableError:
        return jsonify({'error': 'X-ray model is not loaded; this modality is unavailable'}), 503
    except InvalidInputError as exc:
        return jsonify({'error': str(exc)}), 422


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
