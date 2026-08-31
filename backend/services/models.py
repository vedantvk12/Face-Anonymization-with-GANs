import os
import glob
import cv2
import insightface
from typing import Dict, Any, List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(ROOT, "models", "inswapper", "inswapper_128.onnx")
SOURCE_DIR = os.path.join(ROOT, "data", "source_faces")

_models_loaded = False
_face_app = None
_swapper = None
_synthetic_identities: Dict[str, Any] = {}
_synthetic_names: List[str] = []

def get_models():
    """Returns the loaded face_app, swapper, and synthetic identities dictionary."""
    global _models_loaded, _face_app, _swapper, _synthetic_identities, _synthetic_names
    
    if not _models_loaded:
        load_system()
        
    return _face_app, _swapper, _synthetic_identities, _synthetic_names

def load_system():
    global _models_loaded, _face_app, _swapper, _synthetic_identities, _synthetic_names
    
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(f"InSwapper model not found: {MODEL_PATH}")

    # Load InsightFace
    _face_app = insightface.app.FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )
    _face_app.prepare(ctx_id=0, det_size=(640, 640))

    # Load InSwapper
    _swapper = insightface.model_zoo.get_model(
        MODEL_PATH,
        download=False,
        providers=["CPUExecutionProvider"]
    )

    # Load Synthetic Identities
    source_files = []
    for extension in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        source_files.extend(glob.glob(os.path.join(SOURCE_DIR, extension)))

    _synthetic_identities = {}
    _synthetic_names = []

    for path in sorted(source_files):
        if not os.path.isfile(path):
            continue
        if os.path.getsize(path) == 0:
            continue

        image = cv2.imread(path)
        if image is None:
            continue

        faces = _face_app.get(image)
        if not faces:
            continue

        # Use the largest face
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        
        # Get filename without extension as the identity name (e.g. synthetic_01)
        name = os.path.splitext(os.path.basename(path))[0]
        
        _synthetic_identities[name] = face
        _synthetic_names.append(name)
        
    _models_loaded = True

def get_system_status():
    global _models_loaded, _face_app, _swapper, _synthetic_names
    
    if not _models_loaded:
        try:
            load_system()
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    return {
        "status": "online",
        "face_detection": _face_app is not None,
        "inswapper": _swapper is not None,
        "synthetic_identities": len(_synthetic_names),
        "inference": "CPU"
    }
