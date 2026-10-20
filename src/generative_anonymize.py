import cv2
import os
import glob
import time
import insightface
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.face_blending import swap_face_anatomical
from services.models import detect_execution_providers


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_IMAGE = "data/input/test.jpg"
SOURCE_DIR = "data/source_faces"
MODEL_PATH = "models/inswapper/inswapper_128.onnx"

OUTPUT_DIR = "output/gan"
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, "gan_test.jpg")
DEBUG_IMAGE = os.path.join(OUTPUT_DIR, "gan_detection_debug.jpg")


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# CHECK INPUT IMAGE
# ============================================================

if not os.path.isfile(INPUT_IMAGE):
    raise FileNotFoundError(
        f"\nTarget image not found:\n{INPUT_IMAGE}\n"
        f"\nPut your test image inside data/input/"
    )


# ============================================================
# CHECK INSWAPPER MODEL
# ============================================================

if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(
        f"\nInSwapper model not found:\n{MODEL_PATH}\n"
        f"\nExpected:\n"
        f"models/inswapper/inswapper_128.onnx"
    )


# ============================================================
# FIND SOURCE FACE IMAGE
# ============================================================

source_candidates = []

for extension in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
    source_candidates.extend(
        glob.glob(os.path.join(SOURCE_DIR, extension))
    )

# Remove empty files
source_candidates = [
    path for path in source_candidates
    if os.path.getsize(path) > 0
]

if not source_candidates:
    raise FileNotFoundError(
        "\nNo valid source face image found.\n"
        "Put a valid synthetic/non-identifying face image inside:\n"
        f"{SOURCE_DIR}\n"
    )

SOURCE_IMAGE = source_candidates[0]

print("=" * 60)
print("FACE ANONYMIZATION WITH INSWAPPER")
print("=" * 60)

print(f"\nTarget image : {INPUT_IMAGE}")
print(f"Source face  : {SOURCE_IMAGE}")
print(f"Model        : {MODEL_PATH}")


# ============================================================
# LOAD TARGET IMAGE
# ============================================================

print("\nLoading target image...")

target = cv2.imread(INPUT_IMAGE)

if target is None:
    raise ValueError(
        f"OpenCV could not read target image:\n{INPUT_IMAGE}"
    )

print(f"Target image size: {target.shape[1]} x {target.shape[0]}")


# ============================================================
# LOAD SOURCE IMAGE
# ============================================================

print("\nLoading source face...")

source = cv2.imread(SOURCE_IMAGE)

if source is None:
    raise ValueError(
        f"OpenCV could not read source image:\n{SOURCE_IMAGE}\n"
        f"Check that the file is a valid JPG/PNG image."
    )

print(f"Source image size: {source.shape[1]} x {source.shape[0]}")


# ============================================================
# LOAD INSIGHTFACE
# ============================================================

print("\nLoading InsightFace...")

providers, prov_name = detect_execution_providers()
print(f"Hardware execution provider: {prov_name} {providers}")

app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=providers
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

print("InsightFace loaded.")


# ============================================================
# LOAD INSWAPPER
# ============================================================

print("\nLoading InSwapper...")

start_time = time.time()

swapper = insightface.model_zoo.get_model(
    MODEL_PATH,
    download=False,
    providers=providers
)

print(
    f"InSwapper loaded in "
    f"{time.time() - start_time:.2f} seconds."
)


# ============================================================
# DETECT TARGET FACES
# ============================================================

print("\nDetecting faces in target image...")

start_time = time.time()

target_faces = app.get(target)

print(
    f"Target faces detected: {len(target_faces)}"
)

print(
    f"Detection time: "
    f"{time.time() - start_time:.2f} seconds."
)


if len(target_faces) == 0:
    raise RuntimeError(
        "\nNo face detected in the target image.\n"
        "Try a clearer image with a visible face."
    )


# ============================================================
# DETECT SOURCE FACE
# ============================================================

print("\nDetecting source face...")

source_faces = app.get(source)

print(
    f"Source faces detected: {len(source_faces)}"
)


if len(source_faces) == 0:
    raise RuntimeError(
        "\nNo face detected in the source image.\n"
        "Use a clear synthetic face image."
    )


# ============================================================
# SELECT SOURCE IDENTITY
# ============================================================

source_face = source_faces[0]

print("\nSource identity selected.")


# ============================================================
# SAVE DEBUG IMAGE
# ============================================================

debug_image = target.copy()

for i, face in enumerate(target_faces):

    x1, y1, x2, y2 = face.bbox.astype(int)

    cv2.rectangle(
        debug_image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    cv2.putText(
        debug_image,
        f"Face {i + 1}",
        (x1, max(y1 - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

cv2.imwrite(
    DEBUG_IMAGE,
    debug_image
)

print(f"\nDebug detection image saved:")
print(DEBUG_IMAGE)


# ============================================================
# GENERATIVE ANONYMIZATION
# ============================================================

print("\nStarting generative anonymization...")

result = target.copy()

start_time = time.time()

for i, target_face in enumerate(target_faces):

    print(
        f"Anonymizing face "
        f"{i + 1}/{len(target_faces)}..."
    )

    try:
        result, _ = swap_face_anatomical(
            swapper,
            result,
            target_face,
            source_face
        )
    except Exception as e:
        print(f"Anatomical blend exception ({e}), falling back to default paste_back.")
        result = swapper.get(
            result,
            target_face,
            source_face,
            paste_back=True
        )


processing_time = time.time() - start_time


# ============================================================
# SAVE RESULT
# ============================================================

success = cv2.imwrite(
    OUTPUT_IMAGE,
    result
)

if not success:
    raise RuntimeError(
        f"Failed to save output image:\n{OUTPUT_IMAGE}"
    )


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 60)
print("GENERATIVE ANONYMIZATION COMPLETE")
print("=" * 60)

print(f"\nFaces anonymized : {len(target_faces)}")
print(f"Processing time  : {processing_time:.2f} seconds")
print(f"Output image     : {OUTPUT_IMAGE}")
print(f"Debug image      : {DEBUG_IMAGE}")

print("\nOpen the output image and compare it with:")
print("1. Original  -> data/input/test.jpg")
print("2. Blur      -> output/blur/blurred_test.jpg")
print("3. Generative -> output/gan/gan_test.jpg")

print("\nDone.")