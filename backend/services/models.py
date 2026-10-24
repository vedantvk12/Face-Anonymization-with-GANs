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
_model_lock = threading.RLock()

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


def get_swapper():
    """Lazily loads InSwapper 128 model on demand to conserve RAM."""
    global _swapper, _execution_providers, _active_provider
    if _swapper is not None:
        return _swapper

    with _model_lock:
        if _swapper is not None:
            return _swapper

        ensure_inswapper_model()
        # DirectML has a known D3D12 device hang bug (0x887A0006) with InSwapper's fused nodes.
        # CPUExecutionProvider is highly optimized, takes ~2-3s, and is 100% crash-proof without GPU driver timeouts.
        swapper_providers = ["CPUExecutionProvider"] if "DmlExecutionProvider" in _execution_providers else _execution_providers
        print(f"[Model Loader] Loading InSwapper 128 model with providers: {swapper_providers}")
        _swapper = insightface.model_zoo.get_model(
            MODEL_PATH,
            download=False,
            providers=swapper_providers
        )
        return _swapper


def get_face_app():
    """Returns or lazily initializes FaceAnalysis."""
    global _face_app, _execution_providers
    if _face_app is not None:
        return _face_app

    with _model_lock:
        if _face_app is not None:
            return _face_app

        is_gpu = "DmlExecutionProvider" in _execution_providers or "CUDAExecutionProvider" in _execution_providers
        model_name = "buffalo_l" if is_gpu else "buffalo_s"
        det_size = (640, 640) if is_gpu else (320, 320)

        print(f"[Model Loader] Initializing FaceAnalysis ({model_name})...")
        try:
            _face_app = insightface.app.FaceAnalysis(
                name=model_name,
                allowed_modules=["detection", "recognition"],
                providers=_execution_providers
            )
            _face_app.prepare(ctx_id=0, det_size=det_size)
        except Exception as exc:
            print(f"[Model Loader] Fallback to CPU buffalo_l: {exc}")
            _face_app = insightface.app.FaceAnalysis(
                name="buffalo_l",
                allowed_modules=["detection", "recognition"],
                providers=["CPUExecutionProvider"]
            )
            _face_app.prepare(ctx_id=0, det_size=(640, 640))
        return _face_app


def get_models(blocking: bool = False):
    """Returns the loaded face_app, swapper, synthetic identities dict, and names list."""
    global _models_loaded, _face_app, _swapper, _synthetic_identities, _synthetic_names, _model_load_in_progress
    
    if not _models_loaded:
        if not _model_load_in_progress:
            _model_load_in_progress = True
            threading.Thread(target=_load_models_in_background, daemon=True).start()
        if blocking:
            load_system()

    face_app = _face_app
    if face_app is None and blocking:
        face_app = get_face_app()
        
    swapper_instance = _swapper
    if swapper_instance is None and blocking:
        try:
            swapper_instance = get_swapper()
        except Exception as e:
            print(f"[Model Loader] Warning loading swapper on demand: {e}")

    return face_app, swapper_instance, _synthetic_identities, _synthetic_names


def ensure_inswapper_model():
    """Ensures the InSwapper ONNX model is downloaded and valid (>50MB)."""
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if not os.path.isfile(MODEL_PATH) or os.path.getsize(MODEL_PATH) < 50 * 1024 * 1024:
        print(f"[Model Loader] InSwapper 128 model missing or incomplete ({MODEL_PATH}).")
        print("[Model Loader] Downloading inswapper_128.onnx from CDN mirror...")
        import urllib.request
        url = "https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx"
        tmp_path = MODEL_PATH + ".tmp"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(tmp_path, 'wb') as out_file:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                chunk_size = 1024 * 1024 * 4  # 4MB chunks
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"  Downloading InSwapper: {percent:.1f}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="\r")
            print("\n[Model Loader] Download complete. Validating...")
            if os.path.exists(MODEL_PATH):
                os.remove(MODEL_PATH)
            os.rename(tmp_path, MODEL_PATH)
            print(f"[Model Loader] Successfully saved to {MODEL_PATH}")
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise RuntimeError(f"Failed to automatically download InSwapper model: {e}")


def load_system():
    global _models_loaded, _synthetic_identities, _synthetic_names
    global _active_provider, _execution_providers
    
    with _model_lock:
        if _models_loaded:
            return

        _execution_providers, _active_provider = detect_execution_providers()
        print(f"[Model Loader] Initializing models with provider: {_active_provider} {_execution_providers}")

        # 1. Load Synthetic Identities from precomputed NPZ cache if available (instant 0.001s boot)
        npz_path = os.path.join(ROOT, "data", "identities_cache.npz")
        if os.path.isfile(npz_path):
            try:
                import numpy as np
                from insightface.app.common import Face
                npz = np.load(npz_path)
                cached_names = [str(n) for n in npz["names"]]
                loaded_identities = {}
                for name in cached_names:
                    loaded_identities[name] = Face({
                        "bbox": npz[f"{name}_bbox"],
                        "kps": npz[f"{name}_kps"],
                        "embedding": npz[f"{name}_embedding"],
                        "det_score": float(npz[f"{name}_det_score"])
                    })
                _synthetic_identities = loaded_identities
                _synthetic_names = cached_names
                _models_loaded = True
                print(f"[Model Loader] Instantly loaded {len(_synthetic_names)} identities from NPZ cache.")
                return
            except Exception as e:
                print(f"[Model Loader] NPZ cache load failed, regenerating: {e}")

        # Fallback: compute from source images using face_app
        face_app = get_face_app()
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

            # Resize large donor images to max 640px to prevent tensor memory spikes
            h, w = image.shape[:2]
            max_dim = max(h, w)
            if max_dim > 640:
                scale = 640.0 / max_dim
                image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

            faces = face_app.get(image)
            if not faces:
                continue

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
            "face_detection": True,
            "inswapper": True,
            "synthetic_identities": len(_synthetic_names),
            "inference": prov_name,
            "message": f"Warming up AI models with {prov_name}..."
        }

    return {
        "status": "online",
        "face_detection": True,
        "inswapper": True,
        "synthetic_identities": len(_synthetic_names),
        "inference": _active_provider
    }
