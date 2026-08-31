import cv2
import numpy as np
import os


# ============================================================
# FILES
# ============================================================

ORIGINAL = "data/input/test.jpg"
BLURRED = "output/blur/blurred_test.jpg"
GENERATIVE = "output/gan/gan_test.jpg"

OUTPUT_DIR = "output/evaluation"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# LOAD IMAGES
# ============================================================

def load_image(path):

    image = cv2.imread(path)

    if image is None:
        raise FileNotFoundError(f"Could not load: {path}")

    return image


original = load_image(ORIGINAL)
blurred = load_image(BLURRED)
generative = load_image(GENERATIVE)


# ============================================================
# MAKE SURE SIZES MATCH
# ============================================================

if blurred.shape != original.shape:
    blurred = cv2.resize(
        blurred,
        (original.shape[1], original.shape[0])
    )

if generative.shape != original.shape:
    generative = cv2.resize(
        generative,
        (original.shape[1], original.shape[0])
    )


# ============================================================
# DETECT FACE REGION
# ============================================================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(40, 40)
)

if len(faces) == 0:
    raise RuntimeError("No face detected in original image.")


# Use largest face
x, y, w, h = max(
    faces,
    key=lambda f: f[2] * f[3]
)


# ============================================================
# CREATE FACE MASK
# ============================================================

mask = np.ones(
    original.shape[:2],
    dtype=np.uint8
)

# Expand face region slightly
padding = int(0.25 * max(w, h))

x1 = max(0, x - padding)
y1 = max(0, y - padding)
x2 = min(original.shape[1], x + w + padding)
y2 = min(original.shape[0], y + h + padding)

mask[y1:y2, x1:x2] = 0


# ============================================================
# CALCULATE NON-FACE DIFFERENCE
# ============================================================

def non_face_difference(original, output, mask):

    original_float = original.astype(np.float32)
    output_float = output.astype(np.float32)

    difference = np.abs(
        original_float - output_float
    )

    # Average RGB difference outside face
    valid_pixels = mask == 1

    score = difference[valid_pixels].mean()

    return float(score)


blur_difference = non_face_difference(
    original,
    blurred,
    mask
)

generative_difference = non_face_difference(
    original,
    generative,
    mask
)


# ============================================================
# CALCULATE UTILITY SCORE
# ============================================================

# Lower difference = better preservation.
# Convert to an easy-to-read preservation score.

MAX_DIFFERENCE = 255.0

blur_utility = max(
    0,
    100 * (1 - blur_difference / MAX_DIFFERENCE)
)

generative_utility = max(
    0,
    100 * (1 - generative_difference / MAX_DIFFERENCE)
)


# ============================================================
# SAVE FACE MASK
# ============================================================

mask_image = (mask * 255).astype(np.uint8)

cv2.imwrite(
    os.path.join(
        OUTPUT_DIR,
        "non_face_mask.png"
    ),
    mask_image
)


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 60)
print("SCENE UTILITY EVALUATION")
print("=" * 60)

print(f"\nFace detected:")
print(f"  x={x}, y={y}, width={w}, height={h}")

print("\nNon-face pixel difference:")
print(f"  Blur        : {blur_difference:.2f}")
print(f"  Generative  : {generative_difference:.2f}")

print("\nScene preservation score:")
print(f"  Blur        : {blur_utility:.2f}/100")
print(f"  Generative  : {generative_utility:.2f}/100")

print("\nInterpretation:")
print("  Lower pixel difference = better scene preservation.")
print("  Higher preservation score = better utility.")

print("\nNote:")
print("This is an image-preservation metric, not a complete")
print("measure of human-perceived scene usefulness.")

print("=" * 60)