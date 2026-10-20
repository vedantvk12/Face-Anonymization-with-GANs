import cv2
import numpy as np
from typing import List, Any
from .models import get_models

def detect_faces(
    image: np.ndarray,
    max_dim: int = 1280,
    min_confidence: float = 0.50,
    min_face_size: int = 20
) -> List[Any]:
    """
    Detects faces in an image using InsightFace with strict quality validation:
    - Filters out low-confidence false positives (det_score < min_confidence).
    - Rejects tiny or degenerate bounding boxes (size < min_face_size).
    - Clamps bounding box coordinates safely to image borders.
    - Accurately scales bounding boxes and landmarks if image is downscaled for inference speed.
    - Sorts detections left-to-right (x1 coordinate) for deterministic identity assignment.
    """
    if image is None or image.size == 0:
        return []

    face_app, _, _, _ = get_models(blocking=True)
    if face_app is None:
        return []

    h, w = image.shape[:2]

    # If image is unusually large, downscale for detection speed while preserving aspect ratio
    if max_dim is not None and max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        target_w = int(w * scale)
        target_h = int(h * scale)
        resized = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_AREA)
        raw_faces = face_app.get(resized)

        # Scale bounding boxes and landmarks back up to original coordinates
        inv_scale = 1.0 / scale
        for face in raw_faces:
            face.bbox = face.bbox * inv_scale
            if hasattr(face, "kps") and face.kps is not None:
                face.kps = face.kps * inv_scale
            if hasattr(face, "landmark_3d_68") and face.landmark_3d_68 is not None:
                face.landmark_3d_68[:, :2] = face.landmark_3d_68[:, :2] * inv_scale
            if hasattr(face, "landmark_2d_106") and face.landmark_2d_106 is not None:
                face.landmark_2d_106 = face.landmark_2d_106 * inv_scale
    else:
        raw_faces = face_app.get(image)

    valid_faces = []
    for face in raw_faces:
        # Confidence check
        det_score = getattr(face, "det_score", 1.0)
        if det_score is not None and det_score < min_confidence:
            continue

        # Dimension check
        bbox = face.bbox
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        if bw < min_face_size or bh < min_face_size:
            continue

        # Clamp bounding box within frame
        face.bbox[0] = max(0.0, float(bbox[0]))
        face.bbox[1] = max(0.0, float(bbox[1]))
        face.bbox[2] = min(float(w), float(bbox[2]))
        face.bbox[3] = min(float(h), float(bbox[3]))

        # Validate landmarks are finite and not NaN
        if hasattr(face, "kps") and face.kps is not None:
            if not np.all(np.isfinite(face.kps)):
                continue

        valid_faces.append(face)

    # Sort left-to-right (x1 coordinate) for deterministic assignment across frames and components
    valid_faces.sort(key=lambda f: (f.bbox[0], f.bbox[1]))
    return valid_faces
