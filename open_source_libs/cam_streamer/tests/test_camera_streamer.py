# tests/test_camera_streamer.py
import pytest
from unicorner_cam_streamer.camera_streamer import CameraStreamer
import cv2

def test_open_and_release(tmp_path):
    # We can test that opening a bad index raises, etc.
    cs = CameraStreamer(src=-1)  # almost certainly invalid
    with pytest.raises(RuntimeError):
        cs.open()

def test_read_frame(tmp_path, monkeypatch):
    # Monkey-patch cv2.VideoCapture to simulate success
    class FakeCap:
        def __init__(self, src):
            pass
        def isOpened(self): return True
        def read(self): return True, cv2.imread(str(tmp_path))  # None is fine
        def release(self): pass

    monkeypatch.setattr(cv2, "VideoCapture", FakeCap)

    cs = CameraStreamer(src=0)
    cs.open()
    frame = cs.read()
    assert frame is None or hasattr(frame, 'shape')
    cs.release()
