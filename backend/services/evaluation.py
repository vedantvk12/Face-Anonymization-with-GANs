import cv2
import numpy as np
from .models import get_models

def get_face_embedding(image: np.ndarray, face_app) -> np.ndarray:
    faces = face_app.get(image)
    if not faces:
        return None
        
    # Use the largest detected face
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    embedding = face.embedding.astype(np.float32)
    embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
    return embedding

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return None
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

def evaluate_privacy(original: np.ndarray, blurred: np.ndarray, generative: np.ndarray) -> dict:
    face_app, _, _, _ = get_models()
    
    orig_emb = get_face_embedding(original, face_app)
    if orig_emb is None:
        return {"identity_similarity": {"blur": None, "generative": None}}
        
    blur_emb = get_face_embedding(blurred, face_app)
    gen_emb = get_face_embedding(generative, face_app)
    
    blur_sim = cosine_similarity(orig_emb, blur_emb)
    gen_sim = cosine_similarity(orig_emb, gen_emb)
    
    return {
        "identity_similarity": {
            "blur": round(blur_sim, 4) if blur_sim is not None else None,
            "generative": round(gen_sim, 4) if gen_sim is not None else None
        }
    }

def non_face_difference(original: np.ndarray, output: np.ndarray, mask: np.ndarray) -> float:
    original_float = original.astype(np.float32)
    output_float = output.astype(np.float32)
    difference = np.abs(original_float - output_float)
    
    valid_pixels = mask == 1
    if not np.any(valid_pixels):
        return 0.0
        
    score = difference[valid_pixels].mean()
    return float(score)

def evaluate_utility(original: np.ndarray, blurred: np.ndarray, generative: np.ndarray) -> dict:
    # Resize to original if needed
    if blurred.shape != original.shape:
        blurred = cv2.resize(blurred, (original.shape[1], original.shape[0]))
    if generative.shape != original.shape:
        generative = cv2.resize(generative, (original.shape[1], original.shape[0]))
        
    # Detect face region for mask
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    
    if len(faces) == 0:
        return {"scene_preservation": {"blur": None, "generative": None}}
        
    # Use largest face
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    
    mask = np.ones(original.shape[:2], dtype=np.uint8)
    padding = int(0.25 * max(w, h))
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(original.shape[1], x + w + padding)
    y2 = min(original.shape[0], y + h + padding)
    mask[y1:y2, x1:x2] = 0
    
    blur_diff = non_face_difference(original, blurred, mask)
    gen_diff = non_face_difference(original, generative, mask)
    
    MAX_DIFFERENCE = 255.0
    blur_utility = max(0, 100 * (1 - blur_diff / MAX_DIFFERENCE))
    gen_utility = max(0, 100 * (1 - gen_diff / MAX_DIFFERENCE))
    
    return {
        "scene_preservation": {
            "blur": round(blur_utility, 2),
            "generative": round(gen_utility, 2)
        }
    }
