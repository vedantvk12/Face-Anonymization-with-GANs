import copy
import numpy as np
from typing import List, Dict, Any, Optional, Tuple


def compute_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """Computes Intersection-over-Union between two bounding boxes [x1, y1, x2, y2]."""
    x1 = max(float(box1[0]), float(box2[0]))
    y1 = max(float(box1[1]), float(box2[1]))
    x2 = min(float(box1[2]), float(box2[2]))
    y2 = min(float(box1[3]), float(box2[3]))

    inter_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area1 = max(0.0, float(box1[2] - box1[0])) * max(0.0, float(box1[3] - box1[1]))
    area2 = max(0.0, float(box2[2] - box2[0])) * max(0.0, float(box2[3] - box2[1]))

    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return float(inter_area / union_area)


def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    if emb1 is None or emb2 is None:
        return -1.0
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 < 1e-6 or norm2 < 1e-6:
        return -1.0
    return float(np.dot(emb1, emb2) / (norm1 * norm2))


def clone_face(face: Any) -> Any:
    """Safely clones an InsightFace Face dictionary without triggering Python 3.13 pickle errors."""
    if face is None:
        return None
    try:
        from insightface.app.common import Face
        return Face(face)
    except Exception:
        return face.copy() if hasattr(face, "copy") else copy.copy(face)


class FaceTrack:
    """
    State container for a tracked person across video frames.
    Maintains temporal exponential moving average (EMA) smoothing for both bounding boxes
    and 5-point keypoints / 106-point landmarks to eliminate video jitter, wobbling,
    and flickering.
    """
    def __init__(self, track_id: int, face: Any, assigned_identity: str):
        self.track_id = track_id
        self.bbox = face.bbox.copy().astype(np.float32)
        self.assigned_identity = assigned_identity
        self.frames_lost = 0
        self.total_detected = 1
        self.last_face = clone_face(face)

        if hasattr(face, "kps") and face.kps is not None:
            self.kps = face.kps.copy().astype(np.float32)
        else:
            self.kps = None

        if hasattr(face, "landmark_2d_106") and face.landmark_2d_106 is not None:
            self.landmark_2d_106 = face.landmark_2d_106.copy().astype(np.float32)
        else:
            self.landmark_2d_106 = None

        if hasattr(face, "embedding") and face.embedding is not None:
            emb = face.embedding.astype(np.float32)
            self.embedding = emb / (np.linalg.norm(emb) + 1e-8)
        else:
            self.embedding = None

    def update(self, face: Any, smooth: bool = True):
        self.frames_lost = 0
        self.total_detected += 1
        self.last_face = clone_face(face)

        # Compute IoU to determine if motion is smooth or an abrupt jump
        iou = compute_iou(self.bbox, face.bbox)

        if smooth and iou >= 0.45:
            # High IoU: apply EMA smoothing to eliminate high-frequency jitter
            alpha = 0.75  # 75% new, 25% history
            self.bbox = alpha * face.bbox.astype(np.float32) + (1.0 - alpha) * self.bbox
            face.bbox = self.bbox.copy()

            if hasattr(face, "kps") and face.kps is not None and self.kps is not None:
                self.kps = alpha * face.kps.astype(np.float32) + (1.0 - alpha) * self.kps
                face.kps = self.kps.copy()
            elif hasattr(face, "kps") and face.kps is not None:
                self.kps = face.kps.copy().astype(np.float32)

            if hasattr(face, "landmark_2d_106") and face.landmark_2d_106 is not None and self.landmark_2d_106 is not None:
                self.landmark_2d_106 = alpha * face.landmark_2d_106.astype(np.float32) + (1.0 - alpha) * self.landmark_2d_106
                face.landmark_2d_106 = self.landmark_2d_106.copy()
            elif hasattr(face, "landmark_2d_106") and face.landmark_2d_106 is not None:
                self.landmark_2d_106 = face.landmark_2d_106.copy().astype(np.float32)
        else:
            # Low IoU or cut: adopt new coordinates immediately without lag
            self.bbox = face.bbox.copy().astype(np.float32)
            if hasattr(face, "kps") and face.kps is not None:
                self.kps = face.kps.copy().astype(np.float32)
            if hasattr(face, "landmark_2d_106") and face.landmark_2d_106 is not None:
                self.landmark_2d_106 = face.landmark_2d_106.copy().astype(np.float32)

        if hasattr(face, "embedding") and face.embedding is not None:
            emb = face.embedding.astype(np.float32)
            norm = np.linalg.norm(emb)
            if norm > 1e-6:
                emb = emb / norm
                if self.embedding is not None:
                    self.embedding = 0.85 * self.embedding + 0.15 * emb
                    self.embedding /= (np.linalg.norm(self.embedding) + 1e-8)
                else:
                    self.embedding = emb


class MultiFaceTracker:
    """
    Robust multi-face tracker maintaining identity consistency across video frames.
    Combines spatial IoU matching with ArcFace embedding re-identification to handle
    rapid movement, head poses, and temporary occlusions.
    Includes dead reckoning holdover to prevent un-anonymized face leaks on brief detector drops.
    """
    def __init__(
        self,
        iou_threshold: float = 0.30,
        similarity_threshold: float = 0.45,
        max_lost_frames: int = 30,
        max_holdover_frames: int = 2,
        unique_identities: bool = True
    ):
        self.iou_threshold = iou_threshold
        self.similarity_threshold = similarity_threshold
        self.max_lost_frames = max_lost_frames
        self.max_holdover_frames = max_holdover_frames
        self.unique_identities = unique_identities

        self.next_track_id = 0
        self.active_tracks: Dict[int, FaceTrack] = {}

    def update(
        self,
        detected_faces: List[Any],
        available_identities: List[str],
        default_identity: str = "random"
    ) -> List[Tuple[Any, str, int]]:
        """
        Updates tracks with detected faces in the current frame.
        Returns list of tuples: (face_object, assigned_synthetic_identity_name, track_id)
        """
        if not available_identities:
            available_identities = ["synthetic_01"]

        track_ids = list(self.active_tracks.keys())
        num_tracks = len(track_ids)
        num_faces = len(detected_faces)

        matched_tracks = set()
        matched_faces = set()
        results: List[Tuple[Any, str, int]] = []

        # 1. Spatial IoU matching
        if num_tracks > 0 and num_faces > 0:
            iou_matrix = np.zeros((num_tracks, num_faces), dtype=np.float32)
            for i, tid in enumerate(track_ids):
                for j, face in enumerate(detected_faces):
                    iou_matrix[i, j] = compute_iou(self.active_tracks[tid].bbox, face.bbox)

            # Greedy match highest IoU first
            while True:
                max_iou = np.max(iou_matrix) if iou_matrix.size > 0 else 0
                if max_iou < self.iou_threshold:
                    break
                i, j = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                tid = track_ids[i]
                if tid not in matched_tracks and j not in matched_faces:
                    matched_tracks.add(tid)
                    matched_faces.add(j)
                    track = self.active_tracks[tid]
                    track.update(detected_faces[j], smooth=True)
                    results.append((detected_faces[j], track.assigned_identity, track.track_id))
                iou_matrix[i, :] = -1.0
                iou_matrix[:, j] = -1.0

        # 2. Embedding Cosine Similarity Matching for unmatched faces (re-id across occlusion)
        unmatched_face_indices = [j for j in range(num_faces) if j not in matched_faces]
        unmatched_track_ids = [tid for tid in track_ids if tid not in matched_tracks]

        for j in unmatched_face_indices:
            face = detected_faces[j]
            best_sim = -1.0
            best_tid = None

            if hasattr(face, "embedding") and face.embedding is not None:
                face_emb = face.embedding.astype(np.float32)
                norm = np.linalg.norm(face_emb)
                if norm > 1e-6:
                    face_emb /= norm
                    for tid in unmatched_track_ids:
                        track = self.active_tracks[tid]
                        if track.embedding is not None:
                            sim = compute_cosine_similarity(face_emb, track.embedding)
                            if sim > best_sim and sim >= self.similarity_threshold:
                                best_sim = sim
                                best_tid = tid

            if best_tid is not None:
                matched_tracks.add(best_tid)
                matched_faces.add(j)
                unmatched_track_ids.remove(best_tid)
                track = self.active_tracks[best_tid]
                track.update(face, smooth=False)
                results.append((face, track.assigned_identity, track.track_id))

        # 3. Create new tracks for remaining unmatched faces
        for j in range(num_faces):
            if j not in matched_faces:
                face = detected_faces[j]
                tid = self.next_track_id
                self.next_track_id += 1

                # Identity assignment strategy
                if default_identity != "random" and default_identity in available_identities and not self.unique_identities:
                    assigned_id = default_identity
                elif self.unique_identities or default_identity == "random":
                    assigned_id = available_identities[tid % len(available_identities)]
                else:
                    assigned_id = default_identity if default_identity in available_identities else available_identities[0]

                new_track = FaceTrack(tid, face, assigned_id)
                self.active_tracks[tid] = new_track
                results.append((face, assigned_id, tid))

        # 4. Age and holdover for briefly lost tracks (occlusion safety)
        to_delete = []
        for tid, track in self.active_tracks.items():
            if tid not in matched_tracks and tid not in [r[2] for r in results]:
                track.frames_lost += 1

                # Occlusion holdover: if track was well-established, preserve anonymization for up to max_holdover_frames
                if track.total_detected >= 3 and track.frames_lost <= self.max_holdover_frames and track.last_face is not None:
                    holdover_face = clone_face(track.last_face)
                    holdover_face.bbox = track.bbox.copy()
                    if track.kps is not None:
                        holdover_face.kps = track.kps.copy()
                    if track.landmark_2d_106 is not None:
                        holdover_face.landmark_2d_106 = track.landmark_2d_106.copy()
                    results.append((holdover_face, track.assigned_identity, track.track_id))

                if track.frames_lost > self.max_lost_frames:
                    to_delete.append(tid)

        for tid in to_delete:
            del self.active_tracks[tid]

        return results
