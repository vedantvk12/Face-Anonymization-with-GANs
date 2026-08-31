import cv2
import os

# Paths
INPUT_DIR = "data/input"
OUTPUT_DIR = "data/faces"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load OpenCV's pre-trained face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Process all images in input folder
for filename in os.listdir(INPUT_DIR):

    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    input_path = os.path.join(INPUT_DIR, filename)

    image = cv2.imread(input_path)

    if image is None:
        print(f"Could not read: {filename}")
        continue

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40)
    )

    print(f"{filename}: {len(faces)} face(s) detected")

    for i, (x, y, w, h) in enumerate(faces):

        # Crop face
        face = image[y:y+h, x:x+w]

        # Save detected face
        face_name = f"{os.path.splitext(filename)[0]}_face_{i+1}.jpg"
        face_path = os.path.join(OUTPUT_DIR, face_name)

        cv2.imwrite(face_path, face)

        # Draw bounding box
        cv2.rectangle(
            image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    # Save image with detected faces
    result_name = f"detected_{filename}"
    result_path = os.path.join(OUTPUT_DIR, result_name)

    cv2.imwrite(result_path, image)

print("\nFace detection completed!")