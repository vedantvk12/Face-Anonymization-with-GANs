import cv2
import numpy as np
import insightface


# ============================================================
# FILES
# ============================================================

ORIGINAL_IMAGE = "data/input/test.jpg"
BLURRED_IMAGE = "output/blur/blurred_test.jpg"
ANONYMIZED_IMAGE = "output/gan/gan_test.jpg"


# ============================================================
# LOAD INSIGHTFACE
# ============================================================

print("Loading InsightFace...")

app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

print("InsightFace loaded.")


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(path):

    image = cv2.imread(path)

    if image is None:
        raise FileNotFoundError(
            f"Could not load image:\n{path}"
        )

    return image


# ============================================================
# GET FACE EMBEDDING
# ============================================================

def get_face_embedding(image, image_name):

    faces = app.get(image)

    if len(faces) == 0:
        raise RuntimeError(
            f"No face detected in {image_name}"
        )

    # Use the largest detected face
    face = max(
        faces,
        key=lambda f: (f.bbox[2] - f.bbox[0])
        * (f.bbox[3] - f.bbox[1])
    )

    embedding = face.embedding.astype(np.float32)

    # Normalize embedding
    embedding = embedding / (
        np.linalg.norm(embedding) + 1e-8
    )

    return embedding


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(a, b):

    return float(
        np.dot(a, b)
        / (
            np.linalg.norm(a)
            * np.linalg.norm(b)
            + 1e-8
        )
    )


# ============================================================
# LOAD IMAGES
# ============================================================

print("\nLoading images...")

original = load_image(ORIGINAL_IMAGE)
blurred = load_image(BLURRED_IMAGE)
anonymized = load_image(ANONYMIZED_IMAGE)

print("All images loaded.")


# ============================================================
# EXTRACT EMBEDDINGS
# ============================================================

print("\nExtracting original face embedding...")

original_embedding = get_face_embedding(
    original,
    "original image"
)

print("Original embedding extracted.")


print("\nExtracting blurred face embedding...")

try:

    blurred_embedding = get_face_embedding(
        blurred,
        "blurred image"
    )

    blur_similarity = cosine_similarity(
        original_embedding,
        blurred_embedding
    )

except RuntimeError:

    blurred_embedding = None
    blur_similarity = None

    print(
        "No reliable face detected after blurring."
    )


print("\nExtracting anonymized face embedding...")

anonymized_embedding = get_face_embedding(
    anonymized,
    "anonymized image"
)

print("Anonymized embedding extracted.")


# ============================================================
# CALCULATE SIMILARITY
# ============================================================

gan_similarity = cosine_similarity(
    original_embedding,
    anonymized_embedding
)


# ============================================================
# RESULTS
# ============================================================

print("\n")
print("=" * 60)
print("PRIVACY EVALUATION")
print("=" * 60)

print("\nOriginal vs Anonymized:")
print(
    f"Cosine similarity: {gan_similarity:.4f}"
)

if blur_similarity is not None:

    print("\nOriginal vs Blurred:")
    print(
        f"Cosine similarity: {blur_similarity:.4f}"
    )

else:

    print(
        "\nOriginal vs Blurred:"
        "\nFace embedding unavailable"
    )


print("\nInterpretation:")

print(
    "\nHigher similarity → more identity information may remain."
)

print(
    "Lower similarity → stronger identity alteration."
)

print(
    "\nIMPORTANT: This score is an experimental"
    " identity-leakage indicator, not a guarantee"
    " of anonymity."
)

print("=" * 60)