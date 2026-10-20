import os
import cv2
import numpy as np
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from services.models import get_models
from services.detection import detect_faces
from services.anonymization import anonymize_generative
from services.evaluation import get_face_embedding, cosine_similarity
from insightface.utils import face_align

face_app, swapper, syn_ids, syn_names = get_models(blocking=True)

img_path = os.path.join(ROOT, "data", "input", "two_people.jpg")
img = cv2.imread(img_path)
faces = detect_faces(img)
print(f"Detected {len(faces)} faces in two_people.jpg")

for i, f in enumerate(faces):
    x1, y1, x2, y2 = f.bbox.astype(int)
    print(f"Face {i+1}: bbox=[{x1}, {y1}, {x2}, {y2}] det_score={f.det_score:.3f}")
    emb = f.normed_embedding if hasattr(f, "normed_embedding") else None
    crop, _ = face_align.norm_crop2(img, f.kps, 128)
    cv2.imwrite(f"output/verification/diag_orig_face_{i+1}.jpg", crop)

# Run anonymize_generative with random / unique_per_face=True
res = anonymize_generative(img, faces, selected_identity="random", unique_per_face=True)
cv2.imwrite("output/verification/diag_two_people_res.jpg", res)

res_faces = detect_faces(res)
print(f"Detected {len(res_faces)} faces in result")

for i, rf in enumerate(res_faces):
    orig_f = faces[i]
    crop, _ = face_align.norm_crop2(res, rf.kps, 128)
    cv2.imwrite(f"output/verification/diag_anon_face_{i+1}.jpg", crop)
    sim = cosine_similarity(orig_f.normed_embedding, rf.normed_embedding)
    print(f"Face {i+1}: Original vs Anonymized Cosine Similarity = {sim:.4f}")

# Compare against each synthetic identity in the library
for i, rf in enumerate(res_faces):
    print(f"\nComparing Anon Face {i+1} against synthetic library:")
    for s_name, s_face in syn_ids.items():
        sim_donor = cosine_similarity(rf.normed_embedding, s_face.normed_embedding)
        print(f"  vs {s_name:<18}: {sim_donor:.4f}")
