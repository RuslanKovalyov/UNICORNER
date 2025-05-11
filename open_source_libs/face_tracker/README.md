# unicorner-face-tracker

A lightweight Python library for tracking face bounding boxes across frames using IoU, assigning persistent track IDs.

## Features

- Pure-Python, zero-dependency apart from **NumPy**.
- Simple IoU-based greedy matching.
- Configurable disappearance frames and IoU threshold.
- PyPI-ready, MIT-licensed, suitable for commercial use.

## Installation

```bash
pip install unicorner-face-tracker
```

# Usage

from unicorner_face_tracker.face_tracker import FaceTracker, TrackedFace

# Create a tracker
tracker = FaceTracker(max_disappeared=5, iou_threshold=0.3)

# Each frame, supply detections as list of (x, y, w, h) tuples:
detections = [(10,20,50,50), (200,100,60,60)]
tracks = tracker.update(detections)

for t in tracks:
    print(t.track_id, t.bbox, t.disappeared)

