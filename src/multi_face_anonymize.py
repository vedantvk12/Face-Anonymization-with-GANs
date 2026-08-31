import cv2
import os
import glob
import random
import insightface


# ============================================================
# CONFIG
# ============================================================

INPUT_IMAGE = "data/input/test.jpg"

SOURCE_DIR = "data/source_faces"

MODEL_PATH = "models/inswapper/inswapper_128.onnx"

OUTPUT_DIR = "output/gan"

OUTPUT_IMAGE = os.path.join(
    OUTPUT_DIR,
    "multi_face_anonymized.jpg"
)


# ============================================================
# SETUP
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# FIND SYNTHETIC SOURCE FACES
# ============================================================

source_files = []

for ext in (
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.webp"
):

    source_files.extend(
        glob.glob(
            os.path.join(
                SOURCE_DIR,
                ext
            )
        )
    )


source_files = [
    f for f in source_files
    if os.path.isfile(f)
    and os.path.getsize(f) > 0
]


if not source_files:

    raise FileNotFoundError(
        "No synthetic source faces found."
    )


print("=" * 70)
print("MULTI-FACE GENERATIVE ANONYMIZATION")
print("=" * 70)

print(
    f"\nSynthetic identities available: "
    f"{len(source_files)}"
)


# ============================================================
# LOAD INSIGHTFACE
# ============================================================

print("\nLoading InsightFace...")

app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=[
        "CPUExecutionProvider"
    ]
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

swapper = insightface.model_zoo.get_model(
    MODEL_PATH,
    download=False,
    providers=[
        "CPUExecutionProvider"
    ]
)

print("InSwapper loaded.")


# ============================================================
# LOAD SOURCE FACES
# ============================================================

source_identities = []

for source_path in source_files:

    print(
        f"\nLoading synthetic identity:"
        f"\n{source_path}"
    )

    source_image = cv2.imread(
        source_path
    )

    if source_image is None:

        print(
            "Could not read. Skipping."
        )

        continue

    faces = app.get(
        source_image
    )

    if len(faces) == 0:

        print(
            "No face detected. Skipping."
        )

        continue

    source_identities.append(
        faces[0]
    )

    print("Face detected.")


if not source_identities:

    raise RuntimeError(
        "No valid synthetic source faces."
    )


# ============================================================
# LOAD TARGET
# ============================================================

print("\nLoading target image...")

target = cv2.imread(
    INPUT_IMAGE
)

if target is None:

    raise FileNotFoundError(
        INPUT_IMAGE
    )


# ============================================================
# DETECT TARGET FACES
# ============================================================

print("\nDetecting target faces...")

target_faces = app.get(
    target
)

print(
    f"Target faces detected: "
    f"{len(target_faces)}"
)


if len(target_faces) == 0:

    raise RuntimeError(
        "No faces detected."
    )


# ============================================================
# ANONYMIZE
# ============================================================

result = target.copy()

random.seed(42)

print("\nStarting anonymization...")


for index, target_face in enumerate(
    target_faces
):

    # Select a different synthetic
    # identity where possible

    source_face = source_identities[
        index % len(source_identities)
    ]

    print(
        f"Face {index + 1}: "
        f"synthetic identity "
        f"{(index % len(source_identities)) + 1}"
    )

    result = swapper.get(
        result,
        target_face,
        source_face,
        paste_back=True
    )


# ============================================================
# SAVE
# ============================================================

success = cv2.imwrite(
    OUTPUT_IMAGE,
    result
)


if not success:

    raise RuntimeError(
        "Failed to save output."
    )


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)

print(
    "MULTI-FACE ANONYMIZATION COMPLETE"
)

print("=" * 70)

print(
    f"\nFaces anonymized: "
    f"{len(target_faces)}"
)

print(
    f"Output:\n"
    f"{OUTPUT_IMAGE}"
)

print("\nDone.")