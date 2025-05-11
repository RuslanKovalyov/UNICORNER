import pytest, cv2, numpy as np
from unicorner_cam_streamer.camera_streamer import CameraStreamer


# ───────── helpers ─────────────────────────────────────────────
class _DummyCap:
    """Fake cv2.VideoCapture for unit-tests (returns a black frame)."""
    def __init__(self, src): self.src = src
    def isOpened(self):      return True
    def read(self):          return True, np.zeros((5, 5, 3), np.uint8)
    def set(self, *args):    pass
    def release(self):       pass


# ───────── tests ───────────────────────────────────────────────
def test_open_invalid():
    cs = CameraStreamer(src=-99)
    with pytest.raises(RuntimeError):
        cs.open()


def test_read_success(monkeypatch):
    monkeypatch.setattr(cv2, "VideoCapture", _DummyCap)
    cs = CameraStreamer(src=0, width=100, height=100, cap_fps=30)
    cs.open()
    jpeg = cs.read()
    assert jpeg.startswith(b"\xff\xd8")  # JPEG SOI
    cs.release()


def test_frames_generator(monkeypatch):
    monkeypatch.setattr(cv2, "VideoCapture", _DummyCap)
    cs = CameraStreamer(src=0, cap_fps=1, stream_fps=10)
    cs.open()
    gen = cs.frames()
    chunk = next(gen)
    assert b"--frame" in chunk and b"Content-Type" in chunk
    cs.release()


def test_dynamic_setters(monkeypatch):
    monkeypatch.setattr(cv2, "VideoCapture", _DummyCap)
    cs = CameraStreamer(src=0)
    cs.open()
    cs.set_resolution(320, 240)
    cs.set_capture_fps(15)
    cs.set_stream_fps(5)
    cs.set_source(1)  # switch to “another” fake cam
    assert cs.read().startswith(b"\xff\xd8")
    cs.release()
