import os
import cv2
import json
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from services.models import get_models

SOURCE_DIR = os.path.join(ROOT, "data", "source_faces")
THUMB_DIR = os.path.join(ROOT, "data", "thumbnails")
os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

# 1. Update/Add realistic source faces from candidate crops
candidates = {
    "realistic_sophia.jpg": os.path.join(ROOT, "output", "portrait_candidates", "candidate_sophia.jpg"),
    "realistic_olivia.jpg": os.path.join(ROOT, "output", "portrait_candidates", "candidate_olivia.jpg"),
    "realistic_maya.jpg": os.path.join(ROOT, "output", "portrait_candidates", "candidate_833.jpg"),
}

for dest_name, src_path in candidates.items():
    if os.path.exists(src_path):
        dest_path = os.path.join(SOURCE_DIR, dest_name)
        shutil.copyfile(src_path, dest_path)
        print(f"Installed high-quality face: {dest_name}")

# 2. Remove obsolete / duplicate files
obsolete_files = ["synthetic_01.jpg", "synthetic_02.jpg", "synthetic_03.jpg", "synthetic_04.jpg"]
for f in obsolete_files:
    p = os.path.join(SOURCE_DIR, f)
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed redundant file: {f}")

# 3. Define curated identity metadata
identities_meta = [
    # REALISTIC PERSONAS
    {
        "id": "realistic_alex",
        "name": "Alex",
        "style": "realistic",
        "description": "Photorealistic neutral studio persona (female, brunette)",
        "file": "realistic_alex.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_alex_thumb.jpg"
    },
    {
        "id": "realistic_marcus",
        "name": "Marcus",
        "style": "realistic",
        "description": "Photorealistic executive persona (male, navy suit)",
        "file": "realistic_marcus.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_marcus_thumb.jpg"
    },
    {
        "id": "realistic_elena",
        "name": "Elena",
        "style": "realistic",
        "description": "Photorealistic natural portrait persona (female, long hair)",
        "file": "realistic_elena.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_elena_thumb.jpg"
    },
    {
        "id": "realistic_clara",
        "name": "Clara",
        "style": "realistic",
        "description": "Photorealistic bright studio persona (female, blonde)",
        "file": "realistic_clara.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_clara_thumb.jpg"
    },
    {
        "id": "realistic_liam",
        "name": "Liam",
        "style": "realistic",
        "description": "Photorealistic casual portrait persona (male, athletic)",
        "file": "realistic_liam.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_liam_thumb.jpg"
    },
    {
        "id": "realistic_sophia",
        "name": "Sophia",
        "style": "realistic",
        "description": "Photorealistic warm smiling portrait (female, hazel eyes)",
        "file": "realistic_sophia.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_sophia_thumb.jpg"
    },
    {
        "id": "realistic_olivia",
        "name": "Olivia",
        "style": "realistic",
        "description": "Photorealistic elegant portrait with headwear (female)",
        "file": "realistic_olivia.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_olivia_thumb.jpg"
    },
    {
        "id": "realistic_maya",
        "name": "Maya R.",
        "style": "realistic",
        "description": "Photorealistic smiling studio portrait (female, warm)",
        "file": "realistic_maya.jpg",
        "thumbnail": "/api/identities/thumbnail/realistic_maya_thumb.jpg"
    },
    # CARTOON PERSONAS
    {
        "id": "cartoon_finn",
        "name": "Finn",
        "style": "cartoon",
        "description": "3D animated cel persona (Pixar-style male)",
        "file": "cartoon_finn.jpg",
        "thumbnail": "/api/identities/thumbnail/cartoon_finn_thumb.jpg"
    },
    {
        "id": "cartoon_leo",
        "name": "Leo",
        "style": "cartoon",
        "description": "Graphic novel comic stylized persona (male)",
        "file": "cartoon_leo.jpg",
        "thumbnail": "/api/identities/thumbnail/cartoon_leo_thumb.jpg"
    },
    {
        "id": "cartoon_maya",
        "name": "Maya C.",
        "style": "cartoon",
        "description": "Graphic novel comic stylized persona (female)",
        "file": "cartoon_maya.jpg",
        "thumbnail": "/api/identities/thumbnail/cartoon_maya_thumb.jpg"
    },
    # ANIME PERSONAS
    {
        "id": "anime_hikari",
        "name": "Hikari",
        "style": "anime",
        "description": "Cel-shaded Japanese anime persona (female)",
        "file": "anime_hikari.jpg",
        "thumbnail": "/api/identities/thumbnail/anime_hikari_thumb.jpg"
    },
    {
        "id": "anime_ren",
        "name": "Ren",
        "style": "anime",
        "description": "Cel-shaded Japanese manga hero persona (male)",
        "file": "anime_ren.jpg",
        "thumbnail": "/api/identities/thumbnail/anime_ren_thumb.jpg"
    }
]

# Write JSON
json_path = os.path.join(ROOT, "data", "synthetic_identities.json")
with open(json_path, "w") as f:
    json.dump(identities_meta, f, indent=2)
print(f"Updated {json_path} with {len(identities_meta)} identities.")

# 4. Generate thumbnails (128x128 cropped to face)
face_app, _, _, _ = get_models(blocking=True)

for item in identities_meta:
    src_path = os.path.join(SOURCE_DIR, item["file"])
    thumb_name = item["thumbnail"].split("/")[-1]
    thumb_dest = os.path.join(THUMB_DIR, thumb_name)

    img = cv2.imread(src_path)
    if img is None:
        print(f"WARNING: Cannot read {src_path}")
        continue

    faces = face_app.get(img)
    if faces:
        f = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]))
        bbox = f.bbox.astype(int)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        cx = (bbox[0] + bbox[2]) // 2
        cy = (bbox[1] + bbox[3]) // 2
        pad = int(max(bw, bh) * 0.65)
        h, w = img.shape[:2]
        x1 = max(0, cx - pad)
        y1 = max(0, cy - pad)
        x2 = min(w, cx + pad)
        y2 = min(h, cy + pad)
        crop = img[y1:y2, x1:x2]
        thumb = cv2.resize(crop, (128, 128), interpolation=cv2.INTER_AREA)
    else:
        thumb = cv2.resize(img, (128, 128), interpolation=cv2.INTER_AREA)

    cv2.imwrite(thumb_dest, thumb)
    print(f"Generated thumbnail: {thumb_name}")

print("\nIdentity Library Rebuilt Successfully!")
