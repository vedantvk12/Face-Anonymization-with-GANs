import os
import cv2
import numpy as np
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from services.models import get_models
from services.detection import detect_faces
from services.anonymization import anonymize_generative
from services.face_blending import swap_face_anatomical
from services.evaluation import get_face_embedding, cosine_similarity

face_app, swapper, syn_ids, syn_names = get_models(blocking=True)

img_path = os.path.join(ROOT, "data", "input", "two_people.jpg")
img = cv2.imread(img_path)
faces = detect_faces(img)

# Now test: Person 1 gets realistic_elena, Person 2 gets realistic_marcus
res = img.copy()
res, _ = swap_face_anatomical(swapper, res, faces[0], syn_ids["realistic_elena"])
res, _ = swap_face_anatomical(swapper, res, faces[1], syn_ids["realistic_marcus"])

cv2.imwrite("output/verification/two_people_distinct_realistic.jpg", res)
comp = np.hstack([img, res])
cv2.imwrite("output/verification/two_people_comparison.jpg", comp)

res_faces = detect_faces(res)
for i, rf in enumerate(res_faces):
    orig_f = faces[i]
    sim = cosine_similarity(orig_f.normed_embedding, rf.normed_embedding)
    print(f"Face {i+1}: Original vs Anonymized Cosine Sim = {sim:.4f}")
    
# Compare vs Elena and Marcus
sim_p1_elena = cosine_similarity(res_faces[0].normed_embedding, syn_ids["realistic_elena"].normed_embedding)
sim_p2_marcus = cosine_similarity(res_faces[1].normed_embedding, syn_ids["realistic_marcus"].normed_embedding)
print(f"Person 1 vs Elena: {sim_p1_elena:.4f} (Target > 0.65 for successful identity transfer)")
print(f"Person 2 vs Marcus: {sim_p2_marcus:.4f} (Target > 0.65 for successful identity transfer)")
