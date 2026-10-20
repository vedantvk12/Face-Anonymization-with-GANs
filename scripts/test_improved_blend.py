import os
import sys
import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from services.models import get_models
from services.detection import detect_faces
from insightface.utils import face_align

def transfer_color_calibrated(source_bgr: np.ndarray, target_bgr: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
    """
    Carefully transfers lighting and skin tone in LAB color space while preserving
    the synthetic donor's distinctive eye iris color, lip saturation, and facial contrast.
    """
    src_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    tgt_lab = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    valid_mask = (skin_mask > 0.5)
    if np.sum(valid_mask) < 50:
        valid_mask = np.ones((skin_mask.shape[0], skin_mask.shape[1]), dtype=bool)

    s_pixels = src_lab[valid_mask]
    t_pixels = tgt_lab[valid_mask]

    for c in range(3):
        s_mean, s_std = float(s_pixels[:, c].mean()), float(s_pixels[:, c].std()) + 1e-5
        t_mean, t_std = float(t_pixels[:, c].mean()), float(t_pixels[:, c].std()) + 1e-5

        if c == 0:
            # Luminance: adapt 80% to ambient lighting, keep 20% donor contrast
            scale = 0.80 * (t_std / s_std) + 0.20
            shift = 0.80 * t_mean + 0.20 * s_mean
            src_lab[:, :, c] = ((src_lab[:, :, c] - s_mean) * scale) + shift
        else:
            # Chroma: adapt 75% to skin tone hue, preserve 25% donor color characteristics
            scale = 0.75 * (t_std / s_std) + 0.25
            shift = 0.75 * t_mean + 0.25 * s_mean
            src_lab[:, :, c] = ((src_lab[:, :, c] - s_mean) * scale) + shift

    src_lab = np.clip(src_lab, 0, 255).astype(np.uint8)
    return cv2.cvtColor(src_lab, cv2.COLOR_LAB2BGR)


def generate_precision_mask(aligned_pts_106: np.ndarray, input_size: int = 128) -> np.ndarray:
    """
    Creates a precision anatomical mask:
    1. Core feature zone (eyes, nose, mouth) is guaranteed 1.0 (100% synthetic, zero leak).
    2. Outer jaw and forehead contour has smooth feathering (sigma=1.8, 7x7) that eliminates
       all rectangular artifacts without eating into the eyes or mouth.
    """
    outer_mask = np.zeros((input_size, input_size), dtype=np.float32)
    core_mask = np.zeros((input_size, input_size), dtype=np.float32)

    if aligned_pts_106 is not None and len(aligned_pts_106) == 106:
        jaw = aligned_pts_106[:33]
        left_brow = aligned_pts_106[33:43]
        right_brow = aligned_pts_106[64:73]
        brows = np.vstack([left_brow, right_brow])

        # Eye and brow coordinates
        eye_indices = [35, 36, 39, 42, 66, 67, 70, 71]
        valid_eye_idx = [i for i in eye_indices if i < len(aligned_pts_106)]
        eyes_y = float(np.mean(aligned_pts_106[valid_eye_idx, 1])) if valid_eye_idx else float(np.mean(brows[:, 1]) + 15.0)
        brows_y = float(np.mean(brows[:, 1]))
        brow_to_eye_dist = max(8.0, eyes_y - brows_y)
        forehead_dist = max(10, int(brow_to_eye_dist * 1.5))

        forehead_pts = brows.copy()
        forehead_pts[:, 1] = np.clip(forehead_pts[:, 1] - forehead_dist, 5.0, input_size - 5.0)

        # Outer contour (jaw + projected forehead)
        all_contour_pts = np.vstack([jaw, forehead_pts])
        hull = cv2.convexHull(all_contour_pts.astype(np.int32))
        cv2.fillPoly(outer_mask, [hull], 1.0)

        # Core facial feature polygon (inner eye corners, nose, mouth, inner cheeks)
        core_indices = list(range(33, 106))
        core_pts = aligned_pts_106[core_indices]
        core_hull = cv2.convexHull(core_pts.astype(np.int32))
        cv2.fillPoly(core_mask, [core_hull], 1.0)
    else:
        # Elliptical fallback
        center = (input_size // 2, int(input_size * 0.52))
        axes = (int(input_size * 0.38), int(input_size * 0.45))
        cv2.ellipse(outer_mask, center, axes, 0, 0, 360, 1.0, -1)
        core_axes = (int(input_size * 0.25), int(input_size * 0.30))
        cv2.ellipse(core_mask, center, core_axes, 0, 0, 360, 1.0, -1)

    # Feather outer boundary smoothly: kernel 7x7, sigma=2.0
    # Subtle 2px erosion on outer boundary
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    outer_eroded = cv2.erode(outer_mask, kernel, iterations=1)
    outer_feathered = cv2.GaussianBlur(outer_eroded, (7, 7), 2.0)

    # Combine: Ensure core facial features (eyes, nose, mouth) remain 100% synthetic (1.0)
    final_mask = np.maximum(outer_feathered, core_mask)
    return np.clip(final_mask, 0.0, 1.0)


# Test on two_people.jpg
face_app, swapper, syn_ids, syn_names = get_models(blocking=True)
img = cv2.imread(os.path.join(ROOT, "data", "input", "two_people.jpg"))
faces = detect_faces(img)

def run_precision_swap(image, target_face, source_face):
    h_img, w_img = image.shape[:2]
    aimg, M = face_align.norm_crop2(image, target_face.kps, 128)
    blob = cv2.dnn.blobFromImage(aimg, 1.0 / swapper.input_std, swapper.input_size,
                                  (swapper.input_mean, swapper.input_mean, swapper.input_mean), swapRB=True)
    latent = source_face.normed_embedding.reshape((1, -1))
    latent = np.dot(latent, swapper.emap)
    latent /= np.linalg.norm(latent)
    pred = swapper.session.run(swapper.output_names, {swapper.input_names[0]: blob, swapper.input_names[1]: latent})[0]
    bgr_fake = np.clip(255 * pred.transpose((0, 2, 3, 1))[0], 0, 255).astype(np.uint8)[:, :, ::-1]

    aligned_106 = None
    if hasattr(target_face, "landmark_2d_106") and target_face.landmark_2d_106 is not None:
        pts = target_face.landmark_2d_106
        pts_hom = np.hstack([pts, np.ones((len(pts), 1))])
        aligned_106 = np.dot(pts_hom, M.T).astype(np.float32)

    mask_128 = generate_precision_mask(aligned_106, 128)
    bgr_fake_corr = transfer_color_calibrated(bgr_fake, aimg, mask_128)

    IM = cv2.invertAffineTransform(M)
    warped_fake = cv2.warpAffine(bgr_fake_corr, IM, (w_img, h_img), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    warped_mask = cv2.warpAffine(mask_128, IM, (w_img, h_img), flags=cv2.INTER_LANCZOS4, borderValue=0.0)
    warped_mask = np.clip(warped_mask, 0.0, 1.0)[:, :, np.newaxis]

    res = (warped_mask * warped_fake.astype(np.float32) + (1.0 - warped_mask) * image.astype(np.float32)).astype(np.uint8)
    return res

res = img.copy()
res = run_precision_swap(res, faces[0], syn_ids["realistic_elena"])
res = run_precision_swap(res, faces[1], syn_ids["realistic_marcus"])

comp = np.hstack([img, res])
out_path = os.path.join(ROOT, "output", "verification", "two_people_precision_test.jpg")
cv2.imwrite(out_path, comp)
print(f"Saved {out_path}")
