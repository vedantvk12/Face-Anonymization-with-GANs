import cv2
import numpy as np
import random
from .models import get_models

def detect_faces(image: np.ndarray):
    face_app, _, _, _ = get_models()
    return face_app.get(image)

def anonymize_generative(image: np.ndarray, target_faces: list, selected_identity: str) -> np.ndarray:
    _, swapper, synthetic_identities, synthetic_names = get_models()
    
    if not synthetic_identities:
        raise ValueError("No synthetic identities available.")
        
    result = image.copy()
    
    # Check if a specific identity was requested, otherwise use a random one per face, or cycling if multiple.
    is_random = (selected_identity == "random")
    
    if not is_random and selected_identity not in synthetic_identities:
        # Fallback to random if not found
        is_random = True
        
    for i, target_face in enumerate(target_faces):
        if is_random:
            source_face_name = synthetic_names[i % len(synthetic_names)]
            source_face = synthetic_identities[source_face_name]
        else:
            source_face = synthetic_identities[selected_identity]
            
        result = swapper.get(result, target_face, source_face, paste_back=True)
        
    return result

def anonymize_blur(image: np.ndarray, target_faces: list) -> np.ndarray:
    result = image.copy()
    
    for target_face in target_faces:
        x1, y1, x2, y2 = target_face.bbox.astype(int)
        
        # Ensure coordinates are within image boundaries
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        y2 = min(image.shape[0], y2)
        
        # Extract face region
        face_region = result[y1:y2, x1:x2]
        
        # Apply strong blur
        blurred_face = cv2.GaussianBlur(face_region, (99, 99), 30)
        
        # Replace face region
        result[y1:y2, x1:x2] = blurred_face
        
    return result
