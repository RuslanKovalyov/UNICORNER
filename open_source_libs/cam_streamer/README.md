# unicorner-cam-streamer

Simple camera‐capture module.

## Installation

```bash
pip install unicorner-cam-streamer
```
# Usage

from unicorner_cam_streamer import CameraStreamer

cs = CameraStreamer(0)
cs.open()
frame = cs.read()
# ... process frame ...
cs.release()

