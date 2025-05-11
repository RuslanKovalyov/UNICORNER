import numpy as np
from typing import List, Tuple

class TrackedFace:
    """Represents a tracked object with a persistent track_id and bbox."""
    def __init__(self, track_id: int, bbox: Tuple[int,int,int,int]):
        self.track_id: int = track_id
        self.bbox: Tuple[int,int,int,int] = bbox  # (x, y, w, h)
        self.disappeared: int = 0

    def update(self, bbox: Tuple[int,int,int,int]):
        """Update bounding box and reset disappeared counter."""
        self.bbox = bbox
        self.disappeared = 0

class FaceTracker:
    """
    Simple IoU-based tracker.

    Parameters:
      max_disappeared  – how many consecutive frames a track may be missing
      iou_threshold    – minimum IoU to consider a detection matching a track
    """
    def __init__(self, max_disappeared: int = 10, iou_threshold: float = 0.5):
        self.max_disappeared = max_disappeared
        self.iou_threshold = iou_threshold
        self.next_track_id = 0
        self.tracks: dict[int, TrackedFace] = {}

    def update(self, detections: List[Tuple[int,int,int,int]]) -> List[TrackedFace]:
        """
        Update tracks with current frame detections.

        Args:
          detections: list of (x, y, w, h)

        Returns:
          List of active TrackedFace objects.
        """
        # No detections: increment disappeared & cull
        if not detections:
            to_remove = []
            for tid, track in self.tracks.items():
                track.disappeared += 1
                if track.disappeared > self.max_disappeared:
                    to_remove.append(tid)
            for tid in to_remove:
                del self.tracks[tid]
            return list(self.tracks.values())

        # Prepare boxes for IoU
        det_boxes = [self._to_xyxy(b) for b in detections]
        track_ids = list(self.tracks.keys())
        track_boxes = [self._to_xyxy(self.tracks[tid].bbox) for tid in track_ids]

        matched_tracks = set()
        matched_dets = set()

        # Greedy match each track to best detection
        for tid, tbox in zip(track_ids, track_boxes):
            best_iou = 0.0
            best_idx = None
            for i, dbox in enumerate(det_boxes):
                if i in matched_dets:
                    continue
                iou_val = self._iou(tbox, dbox)
                if iou_val > best_iou and iou_val >= self.iou_threshold:
                    best_iou = iou_val
                    best_idx = i
            if best_idx is not None:
                self.tracks[tid].update(detections[best_idx])
                matched_tracks.add(tid)
                matched_dets.add(best_idx)

        # Unmatched tracks → disappeared
        for tid in list(self.tracks):
            if tid not in matched_tracks:
                self.tracks[tid].disappeared += 1
                if self.tracks[tid].disappeared > self.max_disappeared:
                    del self.tracks[tid]

        # Unmatched detections → new tracks
        for i, bbox in enumerate(detections):
            if i not in matched_dets:
                self.tracks[self.next_track_id] = TrackedFace(self.next_track_id, bbox)
                self.next_track_id += 1

        return list(self.tracks.values())

    @staticmethod
    def _to_xyxy(bbox: Tuple[int,int,int,int]) -> Tuple[int,int,int,int]:
        x, y, w, h = bbox
        return (x, y, x + w, y + h)

    @staticmethod
    def _iou(boxA: Tuple[int,int,int,int], boxB: Tuple[int,int,int,int]) -> float:
        # Compute intersection
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        interArea = interW * interH

        # Areas
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        denom = areaA + areaB - interArea
        return interArea / denom if denom > 0 else 0.0
