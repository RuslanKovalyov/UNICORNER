# unicorner_cam_streamer/camera_streamer.py
import cv2

class CameraStreamer:
    def __init__(self, src=0):
        self.src = src
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.src)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera source {self.src}")

    def read(self):
        if not self.cap:
            raise RuntimeError("Stream not opened")
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame")
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
