import cv2
import insightface

# Create InsightFace application
app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

# Prepare model
app.prepare(ctx_id=0, det_size=(640, 640))

# Load image
image_path = "data/input/test.jpg"
image = cv2.imread(image_path)

if image is None:
    raise FileNotFoundError(f"Could not load image: {image_path}")

# Detect faces
faces = app.get(image)

print(f"\nDetected {len(faces)} face(s)\n")

for i, face in enumerate(faces):

    print(f"Face {i + 1}")
    print(f"  Bounding box: {face.bbox}")
    print(f"  Detection score: {face.det_score:.4f}")
    print(f"  Embedding size: {len(face.embedding)}")

# Draw detections
for face in faces:

    x1, y1, x2, y2 = face.bbox.astype(int)

    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

output_path = "data/faces/insightface_detected.jpg"

cv2.imwrite(output_path, image)

print(f"\nSaved result to: {output_path}")