# unicorner_cam_streamer/camera_streamer.py

import cv2

class CameraStreamer:
    """
    Simple camera‐reader class.

    Usage:
        streamer = CameraStreamer(src=0)
        streamer.open()
        frame = streamer.read()
        # … use `frame` (a BGR NumPy array) …
        streamer.release()
    """

    def __init__(self, src=0):
        """
        :param src: index of the camera (0,1,…) or a file/URL string
        """
        self.src = src
        self.cap = None

    def open(self):
        """Open the video source."""
        self.cap = cv2.VideoCapture(self.src)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {self.src}")

    def read(self):
        """
        Read a single frame.

        :return: frame as a BGR NumPy array
        :raises RuntimeError: if the stream isn't open or frame read fails
        """
        if self.cap is None:
            raise RuntimeError("Stream not opened. Call .open() first.")
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Failed to read frame from source.")
        return frame

    def release(self):
        """Release the video source."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
