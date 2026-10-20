import os
import cv2
import glob
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from services.models import get_models

face_app, _, _, _ = get_models(blocking=True)

for p in sorted(glob.glob(os.path.join(ROOT, "data", "input", "*.jpg"))):
    img = cv2.imread(p)
    if img is None:
        continue
    faces = face_app.get(img)
    print(f"{os.path.basename(p):<12} shape={img.shape} faces={len(faces)}", end="")
    if faces:
        best = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
        bw = int(best.bbox[2] - best.bbox[0])
        bh = int(best.bbox[3] - best.bbox[1])
        gender = getattr(best, "gender", -1)
        age = getattr(best, "age", -1)
        print(f" | score={best.det_score:.2f} box={bw}x{bh} gender={gender} age={age}")
    else:
        print()
