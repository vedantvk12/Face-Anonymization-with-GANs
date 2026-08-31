import cv2
import os
import glob
import time
import insightface


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = "data/dataset/input"
BLUR_DIR = "data/dataset/blur"
GAN_DIR = "data/dataset/gan"

SOURCE_DIR = "data/source_faces"
MODEL_PATH = "models/inswapper/inswapper_128.onnx"


# ============================================================
# CREATE OUTPUT DIRECTORIES
# ============================================================

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
        "No valid source face found in data/source_faces"
    )

SOURCE_IMAGE = source_files[0]


# ============================================================
# CHECK MODEL
# ============================================================

if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(
        f"InSwapper model not found:\n{MODEL_PATH}"
    )


# ============================================================
# FIND INPUT IMAGES
# ============================================================

input_files = []

for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
    input_files.extend(
        glob.glob(os.path.join(INPUT_DIR, ext))
    )

input_files.sort()

if not input_files:
    raise FileNotFoundError(
        f"No images found in {INPUT_DIR}"
    )


# ============================================================
# LOAD INSIGHTFACE
# ============================================================

print("=" * 70)
print("BATCH FACE ANONYMIZATION")
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


# ============================================================
# LOAD INSWAPPER
# ============================================================

print("\nLoading InSwapper...")

swapper = insightface.model_zoo.get_model(
    MODEL_PATH,
    download=False,
    providers=["CPUExecutionProvider"]
)

print("InSwapper loaded.")

print(f"\nSource identity: {SOURCE_IMAGE}")
print(f"Images found: {len(input_files)}")


# ============================================================
# LOAD SOURCE FACE
# ============================================================

source = cv2.imread(SOURCE_IMAGE)

if source is None:
    raise RuntimeError(
        "Could not read source face image."
    )

source_faces = app.get(source)

if len(source_faces) == 0:
    raise RuntimeError(
        "No face detected in source face image."
    )

source_face = source_faces[0]

print("Source face detected.")


# ============================================================
# BLUR FUNCTION
# ============================================================

def blur_faces(image, faces):

    result = image.copy()

    for face in faces:

        x1, y1, x2, y2 = face.bbox.astype(int)

        # Add padding
        width = x2 - x1
        height = y2 - y1

        padding_x = int(width * 0.20)
        padding_y = int(height * 0.30)

        x1 = max(0, x1 - padding_x)
        y1 = max(0, y1 - padding_y)

        x2 = min(result.shape[1], x2 + padding_x)
        y2 = min(result.shape[0], y2 + padding_y)

        face_crop = result[y1:y2, x1:x2]

        if face_crop.size == 0:
            continue

        # Strong Gaussian blur
        kernel_size = max(
            31,
            min(face_crop.shape[0], face_crop.shape[1]) // 2 * 2 + 1
        )

        blurred = cv2.GaussianBlur(
            face_crop,
            (kernel_size, kernel_size),
            0
        )

        result[y1:y2, x1:x2] = blurred

    return result


# ============================================================
# PROCESS DATASET
# ============================================================

successful = 0
skipped = 0

overall_start = time.time()

for index, input_path in enumerate(input_files, start=1):

    filename = os.path.basename(input_path)

    print("\n" + "-" * 70)
    print(f"[{index}/{len(input_files)}] Processing: {filename}")

    image = cv2.imread(input_path)

    if image is None:
        print("ERROR: Could not read image. Skipping.")
        skipped += 1
        continue

    # --------------------------------------------------------
    # FACE DETECTION
    # --------------------------------------------------------

    start = time.time()

    faces = app.get(image)

    print(f"Faces detected: {len(faces)}")

    if len(faces) == 0:
        print("No faces found. Skipping.")
        skipped += 1
        continue

    # --------------------------------------------------------
    # BLUR
    # --------------------------------------------------------

    blurred = blur_faces(
        image,
        faces
    )

    blur_output = os.path.join(
        BLUR_DIR,
        filename
    )

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

    gan_output = os.path.join(
        GAN_DIR,
        filename
    )

    cv2.imwrite(
        gan_output,
        generative
    )

    elapsed = time.time() - start

    print(f"Blur saved: {blur_output}")
    print(f"GAN saved : {gan_output}")
    print(f"Time      : {elapsed:.2f} seconds")

    successful += 1


# ============================================================
# SUMMARY
# ============================================================

total_time = time.time() - overall_start

print("\n")
print("=" * 70)
print("BATCH PROCESSING COMPLETE")
print("=" * 70)

print(f"\nTotal images : {len(input_files)}")
print(f"Successful   : {successful}")
print(f"Skipped      : {skipped}")
print(f"Total time   : {total_time:.2f} seconds")

print("\nOutputs:")

print(f"Blur:")
print(f"  {BLUR_DIR}")

print(f"\nGenerative:")
print(f"  {GAN_DIR}")

print("\nDone.")
print("=" * 70)