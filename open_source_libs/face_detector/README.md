# unicorner-face-detector

Simple wrapper around OpenCV’s YuNet face detector.

## Install

```bash
pip install unicorner-face-detector
```

# Usage

from unicorner_face_detector import FaceDetector
import cv2

fd = FaceDetector(min_confidence=0.8)
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
faces = fd.detect(frame)
for x,y,w,h,conf in faces:
    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
