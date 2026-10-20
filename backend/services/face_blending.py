import cv2
import numpy as np
from typing import Optional, Tuple, Callable, Any
from insightface.utils import face_align


def transfer_color_calibrated(
    source_bgr: np.ndarray,
    target_bgr: np.ndarray,
    skin_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Carefully transfers scene lighting and skin tone in CIELAB color space while
    preserving the synthetic donor's distinctive eye iris color, lip saturation,
    and unique facial contrast.
    """
    if source_bgr is None or target_bgr is None:
        return source_bgr

    src_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    tgt_lab = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    if skin_mask is not None and skin_mask.size > 0:
        valid_mask = (skin_mask > 0.40)
        if np.sum(valid_mask) < 60:
            valid_mask = np.ones((skin_mask.shape[0], skin_mask.shape[1]), dtype=bool)
    else:
        valid_mask = np.ones((src_lab.shape[0], src_lab.shape[1]), dtype=bool)

    s_pixels = src_lab[valid_mask]
    t_pixels = tgt_lab[valid_mask]

    for c in range(3):
        s_mean = float(s_pixels[:, c].mean())
        s_std = float(s_pixels[:, c].std()) + 1e-5
        t_mean = float(t_pixels[:, c].mean())
        t_std = float(t_pixels[:, c].std()) + 1e-5

        if c == 0:
            # Luminance: 80% adaptation to ambient scene illumination, 20% donor contrast retention
            scale = 0.80 * (t_std / s_std) + 0.20
            shift = 0.80 * t_mean + 0.20 * s_mean
            src_lab[:, :, c] = ((src_lab[:, :, c] - s_mean) * scale) + shift
        else:
            # Chroma: 75% adaptation to target skin undertone, 25% donor color characteristics
            scale = 0.75 * (t_std / s_std) + 0.25
            shift = 0.75 * t_mean + 0.25 * s_mean
            src_lab[:, :, c] = ((src_lab[:, :, c] - s_mean) * scale) + shift

    src_lab = np.clip(src_lab, 0, 255).astype(np.uint8)
    return cv2.cvtColor(src_lab, cv2.COLOR_LAB2BGR)


def generate_precision_mask(
    aligned_pts_106: Optional[np.ndarray],
    input_size: int = 128
) -> np.ndarray:
    """
    Creates a precision dual-zone anatomical mask:
    1. Core facial feature zone (eyes, eyebrows, nose, mouth) is guaranteed 1.0
       (100% synthetic donor identity replacement, zero leakage of original biometrics).
    2. Outer boundary (jawline, chin, forehead) has a smooth, compact feathering zone
       (3x3 erosion, 7x7 Gaussian blur with sigma=2.0) that eliminates all rectangular
       seams while seamlessly merging with target hair and neck.
    """
    outer_mask = np.zeros((input_size, input_size), dtype=np.float32)
    core_mask = np.zeros((input_size, input_size), dtype=np.float32)

    if aligned_pts_106 is not None and len(aligned_pts_106) == 106:
        # 1. Jawline points (0 to 32)
        jaw = aligned_pts_106[:33]

        # 2. Eyebrow points
        left_brow = aligned_pts_106[33:43]
        right_brow = aligned_pts_106[64:73]
        brows = np.vstack([left_brow, right_brow])

        # 3. Eye to eyebrow distance for forehead boundary
        eye_indices = [35, 36, 39, 42, 66, 67, 70, 71]
        valid_eye_idx = [i for i in eye_indices if i < len(aligned_pts_106)]
        if valid_eye_idx:
            eyes_y = float(np.mean(aligned_pts_106[valid_eye_idx, 1]))
        else:
            eyes_y = float(np.mean(brows[:, 1]) + 15.0)

        brows_y = float(np.mean(brows[:, 1]))
        brow_to_eye_dist = max(8.0, eyes_y - brows_y)
        forehead_dist = max(10, int(brow_to_eye_dist * 1.5))

        forehead_pts = brows.copy()
        forehead_pts[:, 1] = np.clip(forehead_pts[:, 1] - forehead_dist, 5.0, input_size - 5.0)

        # Outer contour (jaw + forehead curve)
        all_contour_pts = np.vstack([jaw, forehead_pts])
        hull = cv2.convexHull(all_contour_pts.astype(np.int32))
        cv2.fillPoly(outer_mask, [hull], 1.0)

        # Core facial feature polygon: all inner landmarks (eyes, brows, nose, mouth)
        core_pts = aligned_pts_106[33:106]
        core_hull = cv2.convexHull(core_pts.astype(np.int32))
        cv2.fillPoly(core_mask, [core_hull], 1.0)
    else:
        # Anatomical elliptical fallback
        center = (input_size // 2, int(input_size * 0.52))
        axes = (int(input_size * 0.38), int(input_size * 0.46))
        cv2.ellipse(outer_mask, center, axes, 0, 0, 360, 1.0, -1)

        core_axes = (int(input_size * 0.26), int(input_size * 0.32))
        cv2.ellipse(core_mask, center, core_axes, 0, 0, 360, 1.0, -1)

    # Feather outer boundary smoothly without eating into facial features
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    outer_eroded = cv2.erode(outer_mask, kernel, iterations=1)
    outer_feathered = cv2.GaussianBlur(outer_eroded, (7, 7), 2.0)

    # Core features are locked to 1.0 (guaranteeing 100% synthetic features in eyes, nose, mouth)
    final_mask = np.maximum(outer_feathered, core_mask)
    return np.clip(final_mask, 0.0, 1.0)


def swap_face_anatomical(
    swapper: Any,
    image: np.ndarray,
    target_face: Any,
    source_face: Any,
    style_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
    return_intermediate: bool = False
) -> Tuple[np.ndarray, Optional[dict]]:
    """
    Performs high-fidelity generative face replacement with precision anatomical masking,
    calibrated CIELAB color transfer, and Lanczos4 inverse affine projection.
    """
    h_img, w_img = image.shape[:2]

    # 1. Align and crop target face to 128x128
    aimg, M = face_align.norm_crop2(image, target_face.kps, swapper.input_size[0])

    # 2. InSwapper ONNX inference
    blob = cv2.dnn.blobFromImage(
        aimg,
        1.0 / swapper.input_std,
        swapper.input_size,
        (swapper.input_mean, swapper.input_mean, swapper.input_mean),
        swapRB=True
    )

    latent = source_face.normed_embedding.reshape((1, -1))
    latent = np.dot(latent, swapper.emap)
    latent /= np.linalg.norm(latent)

    pred = swapper.session.run(
        swapper.output_names,
        {swapper.input_names[0]: blob, swapper.input_names[1]: latent}
    )[0]

    img_fake = pred.transpose((0, 2, 3, 1))[0]
    bgr_fake = np.clip(255 * img_fake, 0, 255).astype(np.uint8)[:, :, ::-1]

    # 3. Optional stylization on the synthetic replacement face
    if style_fn is not None:
        bgr_fake = style_fn(bgr_fake)

    # 4. Transform 106 facial landmarks into 128x128 aligned space
    aligned_106 = None
    if hasattr(target_face, "landmark_2d_106") and target_face.landmark_2d_106 is not None:
        pts = target_face.landmark_2d_106
        pts_hom = np.hstack([pts, np.ones((len(pts), 1))])
        aligned_106 = np.dot(pts_hom, M.T).astype(np.float32)

    # 5. Build precision dual-zone mask
    mask_128 = generate_precision_mask(aligned_106, swapper.input_size[0])

    # 6. Calibrated CIELAB color transfer
    bgr_fake_corr = transfer_color_calibrated(bgr_fake, aimg, mask_128)

    # 7. Warp replacement and mask back using high-precision INTER_LANCZOS4
    IM = cv2.invertAffineTransform(M)
    warped_fake = cv2.warpAffine(
        bgr_fake_corr,
        IM,
        (w_img, h_img),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REFLECT
    )
    warped_mask = cv2.warpAffine(
        mask_128,
        IM,
        (w_img, h_img),
        flags=cv2.INTER_LANCZOS4,
        borderValue=0.0
    )
    warped_mask = np.clip(warped_mask, 0.0, 1.0)[:, :, np.newaxis]

    # 8. Seamless alpha composition
    result = (
        warped_mask * warped_fake.astype(np.float32) +
        (1.0 - warped_mask) * image.astype(np.float32)
    ).astype(np.uint8)

    intermediate = None
    if return_intermediate:
        intermediate = {
            "aimg": aimg,
            "bgr_fake": bgr_fake,
            "bgr_fake_corr": bgr_fake_corr,
            "mask_128": mask_128,
            "warped_mask": warped_mask[:, :, 0],
            "warped_fake": warped_fake
        }

    return result, intermediate
