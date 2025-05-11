"""
UNICORNER ─ camera_streamer.py
A reusable, thread-safe webcam / file / RTSP reader that

• captures in the background
• returns the latest JPEG bytes via .read()
• yields multipart MJPEG chunks via .frames()
• lets you change source / resolution / FPS on-the-fly

Pure OpenCV + std-lib (BSD-3).  Tested on macOS (M-series) & Linux.
"""

from __future__ import annotations
import cv2, threading, time
from typing import Generator, Optional


class CameraStreamer:
    # ─────────────────────── ctor ──────────────────────────────
    def __init__(
        self,
        src: int | str = 0,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        cap_fps: Optional[float] = None,
        stream_fps: Optional[float] = None,
        jpeg_q: int = 85,
    ):
        """
        Parameters
        ----------
        src         camera index / file path / stream URL
        width       requested capture width  (None ⇒ leave device default)
        height      requested capture height (None ⇒ leave device default)
        cap_fps     requested capture FPS    (None ⇒ leave device default)
        stream_fps  MJPEG generator FPS      (None ⇒ as fast as capture)
        jpeg_q      JPEG quality 0-100
        """
        self._lock = threading.RLock()
        self._cap = None                 # cv2.VideoCapture
        self._thr = None                 # reader thread
        self._running = False

        # user-requested settings
        self._src = src
        self._req_w, self._req_h = width, height
        self._req_cap_fps = cap_fps
        self._stream_fps = stream_fps
        self._jpeg_q = max(10, min(100, jpeg_q))
        self._jpeg_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_q]

        # data
        self._latest_jpeg: bytes | None = None

    # ─────────────────── public lifecycle ──────────────────────
    def open(self) -> None:
        """Open the source and start background capture."""
        with self._lock:
            if self._running:
                return
            self._open_locked()

    def _open_locked(self) -> None:
        self._cap = cv2.VideoCapture(self._src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {self._src}")

        # apply optional capture props
        if self._req_w:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._req_w)
        if self._req_h:
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._req_h)
        if self._req_cap_fps:
            self._cap.set(cv2.CAP_PROP_FPS, self._req_cap_fps)

        ok, frame = self._cap.read()
        if not ok or frame is None:
            self._cap.release()
            raise RuntimeError("Failed to grab first frame")

        ok, buf = cv2.imencode(".jpg", frame, self._jpeg_params)
        if not ok:
            self._cap.release()
            raise RuntimeError("JPEG encode failed")
        self._latest_jpeg = buf.tobytes()

        # spawn background reader
        self._running = True
        self._thr = threading.Thread(target=self._reader, daemon=True)
        self._thr.start()

        # log actual props
        act_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        act_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        act_f = self._cap.get(cv2.CAP_PROP_FPS) or 0
        if self._req_cap_fps and abs(act_f - self._req_cap_fps) > 1:
            print(f"[WARN] Camera ignored FPS={self._req_cap_fps}, using {act_f}")
        print(f"[INFO] Capture {act_w}×{act_h}@{act_f:.1f} from {self._src}")

    def release(self, timeout: float = 1.0) -> None:
        """Stop capture and free the camera."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._thr.join(timeout=timeout)
            self._cap.release()
            self._cap = None
            self._latest_jpeg = None
            self._thr = None

    # ───────────────────── reader thread ───────────────────────
    def _reader(self) -> None:
        last = time.time()
        while self._running:
            ok, frame = self._cap.read()
            if ok and frame is not None:
                ok2, buf = cv2.imencode(".jpg", frame, self._jpeg_params)
                if ok2:
                    with self._lock:
                        self._latest_jpeg = buf.tobytes()
            # enforce capture FPS if requested
            if self._req_cap_fps:
                elapsed = time.time() - last
                sleep = max(0, (1 / self._req_cap_fps) - elapsed)
                if sleep:
                    time.sleep(sleep)
                last = time.time()
            else:
                time.sleep(0)  # yield

    # ─────────────────── frame accessors ───────────────────────
    def read(self) -> bytes:
        """Return the latest JPEG frame bytes."""
        with self._lock:
            if self._latest_jpeg is None:
                raise RuntimeError("No frame available – camera not initialised?")
            return self._latest_jpeg

    def frames(self) -> Generator[bytes, None, None]:
        """Yield multipart MJPEG chunks for Flask `Response`."""
        boundary = b"--frame\r\n"
        header = b"Content-Type: image/jpeg\r\n\r\n"
        last_send = time.time()

        while True:
            if self._stream_fps:
                # throttling
                wait = max(0, (1 / self._stream_fps) - (time.time() - last_send))
                if wait:
                    time.sleep(wait)
                last_send = time.time()

            jpeg = self.read()
            yield boundary + header + jpeg + b"\r\n"

    # ─────────────────── dynamic setters ───────────────────────
    def set_capture_fps(self, fps: float):
        with self._lock:
            self._req_cap_fps = fps
            if self._cap:
                self._cap.set(cv2.CAP_PROP_FPS, fps)

    def set_stream_fps(self, fps: float):
        with self._lock:
            self._stream_fps = fps

    def set_resolution(self, width: int, height: int):
        with self._lock:
            self._req_w, self._req_h = width, height
            if self._cap:
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def set_source(self, src: int | str):
        """Switch to a new camera / file / URL without exiting app."""
        with self._lock:
            self.release()
            self._src = src
            self._open_locked()

    # ───────────────── context manager ─────────────────────────
    def __enter__(self): self.open(); return self
    def __exit__(self, *exc): self.release()
