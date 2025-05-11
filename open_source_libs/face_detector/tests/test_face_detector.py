# tests/test_face_detector.py

import pytest
import cv2
import numpy as np
from unicorner_face_detector.face_detector import FaceDetector

def test_model_download(tmp_path, monkeypatch):
    # Point model_path to a temp file to force download
    dest = tmp_path/"yunet.onnx"
    fd = FaceDetector(model_path=dest, min_confidence=0.5)

    assert dest.exists()
    # monkeypatch sha256 to always “match”
    monkeypatch.setattr(FaceDetector, "_sha256", lambda self,p: FaceDetector.MODEL_SHA256)

def test_detect_no_faces(monkeypatch):
    fd = FaceDetector(min_confidence=0.5)
    blank = np.zeros((480,640,3), dtype=np.uint8)
    detections = fd.detect(blank)
    assert isinstance(detections, list)
    assert detections == []
