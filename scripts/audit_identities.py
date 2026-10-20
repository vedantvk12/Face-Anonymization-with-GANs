import os
import cv2
import json
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from services.models import get_models

def audit():
    print("=" * 80)
    print("AUDITING PRIVAI SYNTHETIC IDENTITY ASSETS & CONFIGURATION")
    print("=" * 80)

    face_app, swapper, syn_ids, syn_names = get_models(blocking=True)
    meta_path = os.path.join(ROOT, "data", "synthetic_identities.json")
    with open(meta_path, "r") as f:
        meta = json.load(f)

    print(f"Total entries in synthetic_identities.json: {len(meta)}")
    print(f"Total identities in models cache (syn_ids): {len(syn_ids)}")
    print(f"Model cache names: {syn_names}\n")

    report = []
    all_usable = True

    for item in meta:
        identity_id = item["id"]
        fname = item["file"]
        style = item["style"]
        fpath = os.path.join(ROOT, "data", "source_faces", fname)
        thumb_name = item.get("thumbnail", "").split("/")[-1]
        thumb_path = os.path.join(ROOT, "data", "thumbnails", thumb_name)

        exists = os.path.isfile(fpath)
        size = os.path.getsize(fpath) if exists else 0
        thumb_exists = os.path.isfile(thumb_path)
        in_cache = identity_id in syn_ids

        status = {
            "id": identity_id,
            "style": style,
            "file": fname,
            "exists": exists,
            "size_bytes": size,
            "thumb_exists": thumb_exists,
            "in_cache": in_cache,
            "detected_faces": 0,
            "det_score": 0.0,
            "has_embedding": False,
            "usable": False,
            "issue": None
        }

        if not exists:
            status["issue"] = "Source image file missing"
            all_usable = False
        else:
            img = cv2.imread(fpath)
            if img is None:
                status["issue"] = "OpenCV failed to decode image"
                all_usable = False
            else:
                faces = face_app.get(img)
                status["detected_faces"] = len(faces)
                if len(faces) == 0:
                    status["issue"] = "InsightFace detected 0 faces (Unusable for InSwapper donor)"
                    all_usable = False
                else:
                    best = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                    status["det_score"] = float(best.det_score)
                    status["has_embedding"] = (hasattr(best, "normed_embedding") and best.normed_embedding is not None)
                    if not status["has_embedding"]:
                        status["issue"] = "No ArcFace embedding extracted"
                        all_usable = False
                    else:
                        status["usable"] = True

        report.append(status)
        flag = "[OK] USABLE" if status["usable"] else f"[FAIL]: {status['issue']}"
        print(f"[{style.upper():<9}] {identity_id:<18} -> Faces: {status['detected_faces']}, Score: {status['det_score']:.2f}, Cache: {in_cache} | {flag}")

    # Also check any unlisted files in data/source_faces
    source_dir = os.path.join(ROOT, "data", "source_faces")
    disk_files = set(os.listdir(source_dir))
    meta_files = set(item["file"] for item in meta)
    unlisted = disk_files - meta_files
    if unlisted:
        print(f"\nUnlisted files in data/source_faces: {unlisted}")

    print("=" * 80)
    return report

if __name__ == "__main__":
    audit()
