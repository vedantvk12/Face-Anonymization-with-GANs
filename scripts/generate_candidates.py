import os
import cv2
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from services.models import get_models

face_app, _, _, _ = get_models(blocking=True)

def crop_portrait(img_path, out_path, target_size=640):
    img = cv2.imread(img_path)
    if img is None:
        return False
    faces = face_app.get(img)
    if not faces:
        return False
    f = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]))
    bbox = f.bbox.astype(int)
    
    # Add 45% margin around face to create a natural bust portrait
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    
    pad = int(max(bw, bh) * 0.75)
    h, w = img.shape[:2]
    
    x1 = max(0, cx - pad)
    y1 = max(0, cy - int(pad * 0.9)) # slightly more chest
    x2 = min(w, cx + pad)
    y2 = min(h, cy + int(pad * 1.2))
    
    crop = img[y1:y2, x1:x2]
    crop_resized = cv2.resize(crop, (target_size, target_size), interpolation=cv2.INTER_AREA)
    
    # Check that face is detected in the cropped portrait
    sub_faces = face_app.get(crop_resized)
    if sub_faces:
        cv2.imwrite(out_path, crop_resized)
        print(f"Saved {out_path} (det_score={sub_faces[0].det_score:.3f})")
        return True
    return False

out_dir = os.path.join(ROOT, "output", "portrait_candidates")
os.makedirs(out_dir, exist_ok=True)

crop_portrait(os.path.join(ROOT, "data", "input", "830.jpg"), os.path.join(out_dir, "candidate_sophia.jpg"))
crop_portrait(os.path.join(ROOT, "data", "input", "831.jpg"), os.path.join(out_dir, "candidate_eva.jpg"))
crop_portrait(os.path.join(ROOT, "data", "input", "834.jpg"), os.path.join(out_dir, "candidate_olivia.jpg"))
crop_portrait(os.path.join(ROOT, "data", "input", "835.jpg"), os.path.join(out_dir, "candidate_david.jpg"))
