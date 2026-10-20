import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from .models import get_models
from .detection import detect_faces

def get_face_embedding(image: np.ndarray, face_app) -> Optional[np.ndarray]:
    """Extracts and L2-normalizes the ArcFace embedding for the largest detected face."""
    if image is None or image.size == 0:
        return None
    faces = face_app.get(image)
    if not faces:
        return None

    # Pick largest detected face
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    if not hasattr(face, "embedding") or face.embedding is None:
        return None

    embedding = face.embedding.astype(np.float32)
    norm = np.linalg.norm(embedding)
    if norm < 1e-6:
        return None
    return embedding / norm


def cosine_similarity(a: Optional[np.ndarray], b: Optional[np.ndarray]) -> Optional[float]:
    """Computes cosine similarity between two normalized vectors."""
    if a is None or b is None:
        return None
    sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
    # Clip to [-1.0, 1.0]
    return max(-1.0, min(1.0, sim))


def compute_non_face_difference(original: np.ndarray, output: np.ndarray, mask: np.ndarray) -> float:
    """Computes mean absolute pixel difference on non-face pixels."""
    diff = np.abs(original.astype(np.float32) - output.astype(np.float32))
    valid_pixels = (mask == 1)
    if not np.any(valid_pixels):
        return 0.0
    return float(diff[valid_pixels].mean())


def compute_scene_preservation(original: np.ndarray, processed: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
    """
    Computes non-face pixel difference and scene preservation score [0-100].
    Returns (non_face_diff, scene_preservation_score).
    """
    if original is None or processed is None:
        return None, None

    if processed.shape != original.shape:
        processed = cv2.resize(processed, (original.shape[1], original.shape[0]))

    faces = detect_faces(original)
    mask = np.ones(original.shape[:2], dtype=np.uint8)

    if faces:
        h, w = original.shape[:2]
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            pad_x = int((x2 - x1) * 0.20)
            pad_y = int((y2 - y1) * 0.20)
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(w, x2 + pad_x)
            y2 = min(h, y2 + pad_y)
            mask[y1:y2, x1:x2] = 0
    else:
        # Fallback to Haar Cascade if InsightFace found no face
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        h_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        for (x, y, fw, fh) in h_faces:
            mask[max(0, y):min(original.shape[0], y+fh), max(0, x):min(original.shape[1], x+fw)] = 0

    non_face_diff = compute_non_face_difference(original, processed, mask)
    scene_score = max(0.0, min(100.0, 100.0 * (1.0 - (non_face_diff / 255.0))))
    return round(non_face_diff, 2), round(scene_score, 2)


def evaluate_privacy(original: np.ndarray, blurred: Optional[np.ndarray], generative: Optional[np.ndarray]) -> dict:
    """Evaluates identity similarity for image anonymization."""
    face_app, _, _, _ = get_models()
    orig_emb = get_face_embedding(original, face_app)

    if orig_emb is None:
        return {
            "identity_similarity": {"blur": None, "generative": None},
            "interpretation": "No face detected in original image to extract embedding baseline."
        }

    blur_emb = get_face_embedding(blurred, face_app) if blurred is not None else None
    gen_emb = get_face_embedding(generative, face_app) if generative is not None else None

    blur_sim = cosine_similarity(orig_emb, blur_emb)
    gen_sim = cosine_similarity(orig_emb, gen_emb)

    return {
        "identity_similarity": {
            "blur": round(blur_sim, 4) if blur_sim is not None else None,
            "generative": round(gen_sim, 4) if gen_sim is not None else None
        },
        "interpretation": (
            "Cosine similarity between Deep ArcFace 512-d embeddings. "
            "Values range from -1.0 to 1.0. A lower similarity indicates substantial identity alteration. "
            "Note: Low similarity indicates identity modification, but does not provide a mathematical guarantee of zero re-identification."
        )
    }


def evaluate_utility(original: np.ndarray, blurred: Optional[np.ndarray], generative: Optional[np.ndarray]) -> dict:
    """Evaluates scene preservation and background stability."""
    blur_diff, blur_pres = compute_scene_preservation(original, blurred) if blurred is not None else (None, None)
    gen_diff, gen_pres = compute_scene_preservation(original, generative) if generative is not None else (None, None)

    return {
        "scene_preservation": {
            "blur": blur_pres,
            "generative": gen_pres
        },
        "non_face_difference": {
            "blur": blur_diff,
            "generative": gen_diff
        },
        "interpretation": (
            "Scene preservation score (0-100%) measures how cleanly non-face background, clothing, "
            "and environmental context are maintained without degradation."
        )
    }


def evaluate_video_sampled(
    original_video_path: str,
    anonymized_video_path: str,
    num_samples: int = 5
) -> dict:
    """
    Evaluates representative sampled frames across a processed video.
    Does not run full frame evaluation to conserve system resources.
    """
    cap_orig = cv2.VideoCapture(original_video_path)
    cap_anon = cv2.VideoCapture(anonymized_video_path)

    if not cap_orig.isOpened() or not cap_anon.isOpened():
        return {"error": "Could not open video files for evaluation."}

    total_frames = int(cap_orig.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap_orig.get(cv2.CAP_PROP_FPS) or 24.0

    if total_frames <= 0:
        total_frames = 30

    sample_indices = np.linspace(0, total_frames - 1, min(num_samples, total_frames), dtype=int)
    face_app, _, _, _ = get_models()

    similarities: List[float] = []
    preservations: List[float] = []
    sampled_details: List[Dict[str, Any]] = []

    for idx in sample_indices:
        cap_orig.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        cap_anon.set(cv2.CAP_PROP_POS_FRAMES, int(idx))

        ret_o, frame_o = cap_orig.read()
        ret_a, frame_a = cap_anon.read()

        if not ret_o or not ret_a or frame_o is None or frame_a is None:
            continue

        timestamp = round(float(idx) / fps, 2)
        emb_o = get_face_embedding(frame_o, face_app)
        emb_a = get_face_embedding(frame_a, face_app)
        sim = cosine_similarity(emb_o, emb_a)
        if sim is not None:
            similarities.append(sim)

        _, scene_score = compute_scene_preservation(frame_o, frame_a)
        if scene_score is not None:
            preservations.append(scene_score)

        sampled_details.append({
            "frame": int(idx),
            "timestamp_seconds": timestamp,
            "identity_similarity": round(sim, 4) if sim is not None else None,
            "scene_preservation": scene_score
        })

    cap_orig.release()
    cap_anon.release()

    avg_sim = round(float(np.mean(similarities)), 4) if similarities else None
    avg_pres = round(float(np.mean(preservations)), 2) if preservations else None

    return {
        "sampling_method": f"Uniform temporal sampling across {len(sampled_details)} keyframes",
        "average_identity_similarity": avg_sim,
        "average_scene_preservation": avg_pres,
        "samples": sampled_details,
        "interpretation": (
            "Evaluated on representative sampled frames. Lower similarity indicates consistent identity alteration. "
            "High scene preservation demonstrates visual context retention across video frames."
        )
    }
