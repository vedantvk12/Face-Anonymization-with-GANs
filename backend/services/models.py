import os
import glob
import time
import threading
import cv2
import insightface
import onnxruntime as ort
from typing import Dict, Any, List, Tuple, Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(ROOT, "models", "inswapper", "inswapper_128.onnx")
SOURCE_DIR = os.path.join(ROOT, "data", "source_faces")

_models_loaded = False
_model_load_in_progress = False
_model_lock = threading.Lock()

_face_app = None
_swapper = None
_active_provider = "CPU"
_execution_providers = ["CPUExecutionProvider"]

_synthetic_identities: Dict[str, Any] = {}
_synthetic_names: List[str] = []


def detect_execution_providers() -> Tuple[List[str], str]:
    """Detects available hardware acceleration providers (DirectML/CUDA/CPU)."""
    available = ort.get_available_providers()
    if "DmlExecutionProvider" in available:
        # DirectML GPU acceleration on Windows 11 (e.g. NVIDIA GeForce RTX 4070)
        return ["DmlExecutionProvider", "CPUExecutionProvider"], "GPU (DirectML - RTX 4070)"
    elif "CUDAExecutionProvider" in available:
        return ["CUDAExecutionProvider", "CPUExecutionProvider"], "GPU (CUDA)"
    else:
        return ["CPUExecutionProvider"], "CPU"


def _load_models_in_background():
    global _model_load_in_progress
    try:
        time.sleep(0.05)
        load_system()
    except Exception as exc:
        print(f"Model warm-up failed: {exc}")
    finally:
        _model_load_in_progress = False


def get_models(blocking: bool = False):
    """Returns the loaded face_app, swapper, synthetic identities dict, and names list."""
    global _models_loaded, _face_app, _swapper, _synthetic_identities, _synthetic_names, _model_load_in_progress
    
    if not _models_loaded:
        if not _model_load_in_progress:
            _model_load_in_progress = True
            threading.Thread(target=_load_models_in_background, daemon=True).start()
        if blocking:
            load_system()
        
    return _face_app, _swapper, _synthetic_identities, _synthetic_names


def load_system():
    global _models_loaded, _face_app, _swapper, _synthetic_identities, _synthetic_names
    global _active_provider, _execution_providers
    
    with _model_lock:
        if _models_loaded:
            return

        if not os.path.isfile(MODEL_PATH):
            raise FileNotFoundError(f"InSwapper model not found: {MODEL_PATH}")

        _execution_providers, _active_provider = detect_execution_providers()
        print(f"[Model Loader] Initializing models with provider: {_active_provider} {_execution_providers}")

        # 1. Initialize FaceAnalysis (buffalo_l)
        _face_app = insightface.app.FaceAnalysis(
            name="buffalo_l",
            providers=_execution_providers
        )
        _face_app.prepare(ctx_id=0, det_size=(640, 640))

        # 2. Initialize InSwapper 128
        _swapper = insightface.model_zoo.get_model(
            MODEL_PATH,
            download=False,
            providers=_execution_providers
        )

        # 3. Load Synthetic Identities
        source_files = []
        for extension in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            source_files.extend(glob.glob(os.path.join(SOURCE_DIR, extension)))

        _synthetic_identities = {}
        _synthetic_names = []

        for path in sorted(source_files):
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                continue

            image = cv2.imread(path)
            if image is None:
                continue

            faces = _face_app.get(image)
            if not faces:
                continue

            # Pick largest detected face
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            name = os.path.splitext(os.path.basename(path))[0]
            
            _synthetic_identities[name] = face
            _synthetic_names.append(name)

        _models_loaded = True
        print(f"[Model Loader] System initialized successfully. Synthetic identities cached: {len(_synthetic_names)}")


def get_system_status() -> dict:
    global _models_loaded, _face_app, _swapper, _synthetic_names, _model_load_in_progress, _active_provider

    if not _models_loaded:
        if not _model_load_in_progress:
            _model_load_in_progress = True
            threading.Thread(target=_load_models_in_background, daemon=True).start()

        providers, prov_name = detect_execution_providers()
        return {
            "status": "warming",
            "face_detection": _face_app is not None,
            "inswapper": _swapper is not None,
            "synthetic_identities": len(_synthetic_names),
            "inference": prov_name,
            "message": f"Loading AI models with {prov_name}..."
        }

    return {
        "status": "online",
        "face_detection": _face_app is not None,
        "inswapper": _swapper is not None,
        "synthetic_identities": len(_synthetic_names),
        "inference": _active_provider
    }
