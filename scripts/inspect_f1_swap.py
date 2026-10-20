import os
import sys
import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from services.models import get_models
from services.detection import detect_faces
from services.face_blending import swap_face_anatomical
from insightface.utils import face_align

face_app, swapper, syn_ids, syn_names = get_models(blocking=True)
img = cv2.imread(os.path.join(ROOT, "data", "input", "two_people.jpg"))
f1 = detect_faces(img)[0]

donor = syn_ids["realistic_elena"]
res, inter = swap_face_anatomical(swapper, img, f1, donor, return_intermediate=True)

out_dir = os.path.join(ROOT, "output", "verification")
cv2.imwrite(os.path.join(out_dir, "f1_aimg.jpg"), inter["aimg"])
cv2.imwrite(os.path.join(out_dir, "f1_raw_fake.jpg"), inter["bgr_fake"])
cv2.imwrite(os.path.join(out_dir, "f1_color_corr.jpg"), inter["bgr_fake_corr"])
cv2.imwrite(os.path.join(out_dir, "f1_mask_128.jpg"), (inter["mask_128"] * 255).astype(np.uint8))
print("Saved f1 debug images to output/verification")
