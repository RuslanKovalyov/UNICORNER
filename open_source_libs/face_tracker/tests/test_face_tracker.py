import pytest
from unicorner_face_tracker.face_tracker import FaceTracker, TrackedFace

def test_register_and_persist():
    tr = FaceTracker(max_disappeared=1, iou_threshold=0.1)
    tracks = tr.update([(0,0,10,10)])
    assert len(tracks) == 1
    assert isinstance(tracks[0], TrackedFace)
    first_id = tracks[0].track_id
    # same box next frame → same track_id
    tracks2 = tr.update([(0,0,10,10)])
    assert tracks2[0].track_id == first_id

def test_deregistration():
    tr = FaceTracker(max_disappeared=1, iou_threshold=0.1)
    tr.update([(0,0,10,10)])
    # no detections → disappears once
    tracks = tr.update([])
    assert tracks[0].disappeared == 1
    # disappears twice → removed
    tracks2 = tr.update([])
    assert len(tracks2) == 0

def test_multiple_faces():
    tr = FaceTracker(iou_threshold=0.1)
    dets = [(0,0,10,10), (100,100,20,20)]
    tracks = tr.update(dets)
    assert len(tracks) == 2
    # swap order but IoU matching persists IDs
    tracks2 = tr.update([dets[1], dets[0]])
    ids1 = {t.track_id for t in tracks}
    ids2 = {t.track_id for t in tracks2}
    assert ids1 == ids2
