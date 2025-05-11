# tests/test_camera_streamer.py
import pytest
import cv2
import numpy as np
from unicorner_cam_streamer.camera_streamer import CameraStreamer


def test_open_and_release():
    # Opening an invalid source should raise
    cs = CameraStreamer(src=-1)
    with pytest.raises(RuntimeError):
        cs.open()


def test_read_success(monkeypatch):
    # Simulate VideoCapture that returns a valid frame
    dummy_frame = np.zeros((10, 10, 3), dtype=np.uint8)

    class FakeCap:
        def __init__(self, src):
            pass
        def isOpened(self):
            return True
        def read(self):
            return True, dummy_frame
        def release(self):
            pass

    monkeypatch.setattr(cv2, 'VideoCapture', FakeCap)
    cs = CameraStreamer(src=0)
    cs.open()
    frame = cs.read()
    assert isinstance(frame, np.ndarray)
    assert frame.shape == dummy_frame.shape
    cs.release()


def test_read_failure(monkeypatch):
    # Simulate VideoCapture that fails to read
    class FakeCap:
        def __init__(self, src):
            pass
        def isOpened(self):
            return True
        def read(self):
            return False, None
        def release(self):
            pass

    monkeypatch.setattr(cv2, 'VideoCapture', FakeCap)
    cs = CameraStreamer(src=0)
    cs.open()
    with pytest.raises(RuntimeError):
        cs.read()
    cs.release()