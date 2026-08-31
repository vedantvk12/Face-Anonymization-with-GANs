import cv2
import numpy as np
import insightface
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
# LOAD IMAGE
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
# RESIZE IF NECESSARY
# ============================================================

def match_size(image, reference):

    if image.shape != reference.shape:
        image = cv2.resize(
            image,
            (reference.shape[1], reference.shape[0])
        )

    return image


blurred = match_size(blurred, original)
generative = match_size(generative, original)


# ============================================================
# FACE DETECTION
# ============================================================

cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

gray = cv2.cvtColor(
    original,
    cv2.COLOR_BGR2GRAY
)

faces = cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(40, 40)
)

if len(faces) == 0:
    raise RuntimeError("No face detected.")


# Largest face
x, y, w, h = max(
    faces,
    key=lambda f: f[2] * f[3]
)


# Add padding around face
padding = int(0.25 * max(w, h))

x1 = max(0, x - padding)
y1 = max(0, y - padding)

x2 = min(
    original.shape[1],
    x + w + padding
)

y2 = min(
    original.shape[0],
    y + h + padding
)


# ============================================================
# FACE MASK
# ============================================================

face_mask = np.zeros(
    original.shape[:2],
    dtype=np.uint8
)

face_mask[y1:y2, x1:x2] = 1


non_face_mask = 1 - face_mask


# ============================================================
# PIXEL DIFFERENCE
# ============================================================

def pixel_difference(
    image1,
    image2,
    mask
):

    diff = np.abs(
        image1.astype(np.float32)
        -
        image2.astype(np.float32)
    )

    valid = mask == 1

    if np.sum(valid) == 0:
        return 0.0

    return float(
        diff[valid].mean()
    )


# Face change
blur_face_change = pixel_difference(
    original,
    blurred,
    face_mask
)

generative_face_change = pixel_difference(
    original,
    generative,
    face_mask
)


# Non-face change
blur_scene_change = pixel_difference(
    original,
    blurred,
    non_face_mask
)

generative_scene_change = pixel_difference(
    original,
    generative,
    non_face_mask
)


# ============================================================
# SCENE PRESERVATION
# ============================================================

blur_scene_score = max(
    0,
    100 * (1 - blur_scene_change / 255)
)

generative_scene_score = max(
    0,
    100 * (1 - generative_scene_change / 255)
)


# ============================================================
# INSIGHTFACE
# ============================================================

print("\nLoading InsightFace...")

app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)


# ============================================================
# EMBEDDING FUNCTION
# ============================================================

def get_embedding(image):

    faces = app.get(image)

    if len(faces) == 0:
        return None

    face = max(
        faces,
        key=lambda f:
        (f.bbox[2] - f.bbox[0])
        *
        (f.bbox[3] - f.bbox[1])
    )

    embedding = face.embedding.astype(
        np.float32
    )

    embedding /= (
        np.linalg.norm(embedding)
        + 1e-8
    )

    return embedding


def similarity(a, b):

    return float(
        np.dot(a, b)
        /
        (
            np.linalg.norm(a)
            *
            np.linalg.norm(b)
            +
            1e-8
        )
    )


# ============================================================
# IDENTITY SIMILARITY
# ============================================================

print("Extracting embeddings...")

original_embedding = get_embedding(original)
blur_embedding = get_embedding(blurred)
generative_embedding = get_embedding(generative)


blur_identity = (
    similarity(
        original_embedding,
        blur_embedding
    )
    if blur_embedding is not None
    else None
)

generative_identity = similarity(
    original_embedding,
    generative_embedding
)


# ============================================================
# SAVE MASK
# ============================================================

cv2.imwrite(
    os.path.join(
        OUTPUT_DIR,
        "face_region_mask.png"
    ),
    (face_mask * 255).astype(np.uint8)
)


# ============================================================
# RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("FINAL ANONYMIZATION EVALUATION")
print("=" * 70)

print("\nIDENTITY SIMILARITY")
print("-" * 70)

if blur_identity is not None:
    print(
        f"Blur          : {blur_identity:.4f}"
    )
else:
    print(
        "Blur          : unavailable"
    )

print(
    f"Generative    : {generative_identity:.4f}"
)


print("\nFACE REGION CHANGE")
print("-" * 70)

print(
    f"Blur          : {blur_face_change:.2f}"
)

print(
    f"Generative    : {generative_face_change:.2f}"
)


print("\nNON-FACE SCENE CHANGE")
print("-" * 70)

print(
    f"Blur          : {blur_scene_change:.2f}"
)

print(
    f"Generative    : {generative_scene_change:.2f}"
)


print("\nSCENE PRESERVATION")
print("-" * 70)

print(
    f"Blur          : {blur_scene_score:.2f}/100"
)

print(
    f"Generative    : {generative_scene_score:.2f}/100"
)


print("\nINTERPRETATION")
print("-" * 70)

print(
    "Lower identity similarity indicates greater "
    "identity alteration."
)

print(
    "Higher face-region change indicates that the "
    "original facial pixels were substantially modified."
)

print(
    "Lower non-face change indicates better preservation "
    "of the surrounding scene."
)

print(
    "\nThese metrics are experimental indicators and "
    "do not guarantee anonymity."
)

print("=" * 70)