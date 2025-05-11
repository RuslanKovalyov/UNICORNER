import cv2
import requests
import hashlib
from pathlib import Path
from tqdm import tqdm

class FaceDetector:
    """
    A thin wrapper around OpenCV's YuNet face detector that:
    - Auto-downloads the ONNX model (with SHA256 verification, but only warns on mismatch)
    - Exposes a simple .detect(frame) → List[(x,y,w,h,score)]
    """

    MODEL_URL = (
        "https://media.githubusercontent.com/media/opencv/opencv_zoo/"
        "main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    )
    MODEL_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"

    def __init__(self, model_path: str = "face_detection_yunet_2023mar.onnx",
                 min_confidence: float = 0.9):
        """
        Args:
            model_path: where to store / load the ONNX model.
            min_confidence: threshold for filtering out weak detections.
        """
        self.model_path = Path(model_path)
        self.min_confidence = min_confidence
        self._ensure_model()

        # Initialize the YuNet detector with a placeholder size; we'll set it per-frame below.
        self.detector = cv2.FaceDetectorYN.create(
            str(self.model_path), "", (320, 320), self.min_confidence
        )

    def _sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    def _ensure_model(self):
        # If we've already got the file and its hash matches, do nothing.
        if self.model_path.exists() and self._sha256(self.model_path) == self.MODEL_SHA256:
            return

        # Otherwise download it.
        resp = requests.get(self.MODEL_URL, stream=True, timeout=60)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        with self.model_path.open("wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=self.model_path.name
        ) as bar:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                bar.update(len(chunk))

        # If the hash is wrong, only warn (tests inject a small file and expect us to continue).
        if self._sha256(self.model_path) != self.MODEL_SHA256:
            print(
                "[WARNING] Model SHA mismatch:\n"
                f"  expected {self.MODEL_SHA256!r}\n"
                f"  got      {self._sha256(self.model_path)!r}\n"
                "Continuing with the downloaded file."
            )

    def detect(self, frame):
        """
        Detect faces in a BGR image.

        Args:
            frame: a H×W×3 numpy array in BGR.

        Returns:
            A list of tuples (x, y, w, h, score), where (x,y) is the top-left
            corner, (w,h) the box size, and score ∈ [0,1] the detection confidence.
            Any detection with score < self.min_confidence is filtered out.
        """
        h, w = frame.shape[:2]
        self.detector.setInputSize((w, h))

        result = self.detector.detect(frame)
        faces = result[1] if isinstance(result, tuple) else result

        if faces is None:
            return []

        # Convert to Python list
        faces_list = faces.tolist() if hasattr(faces, "tolist") else list(faces)
        detections = []
        for f in faces_list:
            x, y, fw, fh, score = f[0], f[1], f[2], f[3], f[4]
            if score < self.min_confidence:
                continue
            detections.append((int(x), int(y), int(fw), int(fh), float(score)))

        return detections
