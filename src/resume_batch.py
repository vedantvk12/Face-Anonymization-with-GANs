import cv2
import os
import glob
import time
import insightface


# ============================================================
# PATHS
# ============================================================

INPUT_DIR = "data/dataset/input"
BLUR_DIR = "data/dataset/blur"
GAN_DIR = "data/dataset/gan"

SOURCE_DIR = "data/source_faces"
MODEL_PATH = "models/inswapper/inswapper_128.onnx"

os.makedirs(BLUR_DIR, exist_ok=True)
os.makedirs(GAN_DIR, exist_ok=True)


# ============================================================
# FIND SOURCE FACE
# ============================================================

source_files = []

for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
    source_files.extend(
        glob.glob(os.path.join(SOURCE_DIR, ext))
    )

source_files = [
    f for f in source_files
    if os.path.isfile(f) and os.path.getsize(f) > 0
]

if not source_files:
    raise FileNotFoundError(
        "No valid source face found."
    )

SOURCE_IMAGE = source_files[0]


# ============================================================
# LOAD MODELS
# ============================================================

print("=" * 70)
print("RESUME BATCH ANONYMIZATION")
print("=" * 70)

print("\nLoading InsightFace...")

app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

print("InsightFace loaded.")

print("\nLoading InSwapper...")

swapper = insightface.model_zoo.get_model(
    MODEL_PATH,
    download=False,
    providers=["CPUExecutionProvider"]
)

print("InSwapper loaded.")


# ============================================================
# SOURCE FACE
# ============================================================

source = cv2.imread(SOURCE_IMAGE)

if source is None:
    raise RuntimeError(
        "Could not read source image."
    )

source_faces = app.get(source)

if len(source_faces) == 0:
    raise RuntimeError(
        "No face detected in source image."
    )

source_face = source_faces[0]

print(f"\nSource face: {SOURCE_IMAGE}")


# ============================================================
# INPUT FILES
# ============================================================

input_files = []

for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
    input_files.extend(
        glob.glob(os.path.join(INPUT_DIR, ext))
    )

input_files.sort()


# ============================================================
# RESUME PROCESSING
# ============================================================

processed = 0
skipped = 0

for input_path in input_files:

    filename = os.path.basename(input_path)

    blur_output = os.path.join(
        BLUR_DIR,
        filename
    )

    gan_output = os.path.join(
        GAN_DIR,
        filename
    )

    # --------------------------------------------------------
    # SKIP IF BOTH OUTPUTS ALREADY EXIST
    # --------------------------------------------------------

    if (
        os.path.isfile(blur_output)
        and os.path.getsize(blur_output) > 0
        and
        os.path.isfile(gan_output)
        and os.path.getsize(gan_output) > 0
    ):
        print(f"\nSKIP: {filename} already processed.")
        skipped += 1
        continue

    print("\n" + "-" * 70)
    print(f"PROCESSING: {filename}")

    start_time = time.time()

    image = cv2.imread(input_path)

    if image is None:
        print("Could not read image. Skipping.")
        continue

    # --------------------------------------------------------
    # FACE DETECTION
    # --------------------------------------------------------

    faces = app.get(image)

    print(f"Faces detected: {len(faces)}")

    if len(faces) == 0:
        print("No face detected. Skipping.")
        continue

    # --------------------------------------------------------
    # BLUR
    # --------------------------------------------------------

    blurred = image.copy()

    for face in faces:

        x1, y1, x2, y2 = face.bbox.astype(int)

        width = x2 - x1
        height = y2 - y1

        px = int(width * 0.20)
        py = int(height * 0.30)

        x1 = max(0, x1 - px)
        y1 = max(0, y1 - py)
        x2 = min(image.shape[1], x2 + px)
        y2 = min(image.shape[0], y2 + py)

        crop = blurred[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        min_dimension = min(
            crop.shape[0],
            crop.shape[1]
        )

        kernel = max(
            31,
            (min_dimension // 2) * 2 + 1
        )

        crop_blurred = cv2.GaussianBlur(
            crop,
            (kernel, kernel),
            0
        )

        blurred[y1:y2, x1:x2] = crop_blurred

    cv2.imwrite(
        blur_output,
        blurred
    )

    # --------------------------------------------------------
    # GENERATIVE ANONYMIZATION
    # --------------------------------------------------------

    generative = image.copy()

    for face in faces:

        generative = swapper.get(
            generative,
            face,
            source_face,
            paste_back=True
        )

    cv2.imwrite(
        gan_output,
        generative
    )

    elapsed = time.time() - start_time

    print(f"Blur saved: {blur_output}")
    print(f"GAN saved : {gan_output}")
    print(f"Time      : {elapsed:.2f} seconds")

    processed += 1


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("RESUME PROCESSING COMPLETE")
print("=" * 70)

print(f"Newly processed : {processed}")
print(f"Already skipped : {skipped}")

print("\nCheck:")
print(GAN_DIR)
print(BLUR_DIR)

print("=" * 70)