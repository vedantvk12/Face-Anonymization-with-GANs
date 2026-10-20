import cv2
import numpy as np
from typing import Callable, Any

def apply_cartoon_filter(face_img: np.ndarray) -> np.ndarray:
    """
    Applies bilateral smoothing, color quantization, and adaptive edge contouring
    to achieve a rich, expressive cel-shaded cartoon aesthetic.
    Compatible with both full-resolution crops and 128x128 face patches.
    """
    if face_img is None or face_img.size == 0:
        return face_img

    h, w = face_img.shape[:2]

    # 1. Edge mask using bilateral filter + adaptive thresholding
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    k_blur = 5 if min(h, w) <= 128 else 7
    gray_blur = cv2.medianBlur(gray, k_blur)
    block_size = 7 if min(h, w) <= 128 else 9
    edges = cv2.adaptiveThreshold(
        gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, 2
    )

    # 2. Smooth colors while preserving edges
    color = face_img.copy()
    d_val = 5 if min(h, w) <= 128 else 7
    for _ in range(2):
        color = cv2.bilateralFilter(color, d=d_val, sigmaColor=50, sigmaSpace=50)

    # 3. Quantize colors with k-means
    data = color.reshape((-1, 3)).astype(np.float32)
    k = 8 if min(h, w) <= 128 else 10
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 0.3)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS)
    quantized = centers[labels.flatten()].reshape((h, w, 3)).astype(np.uint8)

    # 4. Combine delicate edges and quantized color
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(quantized, edges_bgr)
    return cartoon


def apply_anime_filter(face_img: np.ndarray) -> np.ndarray:
    """
    Applies edge-preserving smoothing, vibrancy boost, and delicate cel-shading contours
    to produce an expressive Japanese anime character aesthetic.
    Compatible with both full-resolution crops and 128x128 face patches.
    """
    if face_img is None or face_img.size == 0:
        return face_img

    h, w = face_img.shape[:2]

    # 1. Edge-preserving skin smoothing
    sigma_s = 25 if min(h, w) <= 128 else 40
    smoothed = cv2.edgePreservingFilter(face_img, flags=1, sigma_s=sigma_s, sigma_r=0.38)

    # 2. Color tone grading: boost saturation and brightness for luminous anime look
    hsv = cv2.cvtColor(smoothed, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.35, 0, 255) # Vibrancy
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.08, 0, 255) # Luminance
    vibrant = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # 3. Delicate ink outlines
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 35, 95)
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    inv_edges = cv2.bitwise_not(edges)
    edge_bgr = cv2.cvtColor(inv_edges, cv2.COLOR_GRAY2BGR)

    # 4. Multiply with vibrant cel color
    anime = cv2.bitwise_and(vibrant, edge_bgr)
    return anime


def blend_stylized_face(
    base_img: np.ndarray,
    face: Any,
    style_fn: Callable[[np.ndarray], np.ndarray]
) -> np.ndarray:
    """
    Blends a stylized facial region back into the image using a soft feathered elliptical mask.
    Used as a fallback when generative donor swapping is bypassed.
    """
    h, w = base_img.shape[:2]
    x1, y1, x2, y2 = face.bbox.astype(int)

    pad_x = int((x2 - x1) * 0.12)
    pad_y = int((y2 - y1) * 0.12)

    x1_pad = max(0, x1 - pad_x)
    y1_pad = max(0, y1 - pad_y)
    x2_pad = min(w, x2 + pad_x)
    y2_pad = min(h, y2 + pad_y)

    roi = base_img[y1_pad:y2_pad, x1_pad:x2_pad]
    if roi.size == 0:
        return base_img

    stylized_roi = style_fn(roi)

    # Soft elliptical mask for feathered alpha blend
    roi_h, roi_w = roi.shape[:2]
    mask = np.zeros((roi_h, roi_w), dtype=np.float32)
    center = (roi_w // 2, int(roi_h * 0.52))
    axes = (int(roi_w * 0.40), int(roi_h * 0.44))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (21, 21), 8)
    mask_3c = np.repeat(mask[:, :, np.newaxis], 3, axis=2)

    blended_roi = (stylized_roi.astype(np.float32) * mask_3c + roi.astype(np.float32) * (1.0 - mask_3c)).astype(np.uint8)

    result = base_img.copy()
    result[y1_pad:y2_pad, x1_pad:x2_pad] = blended_roi
    return result
