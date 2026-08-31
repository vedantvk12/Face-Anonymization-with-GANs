import cv2
import os

INPUT_DIR = "data/input"
OUTPUT_DIR = "output/blur"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

for filename in os.listdir(INPUT_DIR):

    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    image = cv2.imread(input_path)

    if image is None:
        print(f"Could not read: {filename}")
        continue

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40)
    )

    print(f"{filename}: {len(faces)} face(s) detected")

    for (x, y, w, h) in faces:

        face = image[y:y+h, x:x+w]

        # Strong Gaussian blur
        blurred_face = cv2.GaussianBlur(
            face,
            (51, 51),
            0
        )

        image[y:y+h, x:x+w] = blurred_face

    output_path = os.path.join(OUTPUT_DIR, f"blurred_{filename}")

    cv2.imwrite(output_path, image)

    print(f"Saved: {output_path}")

print("\nBlur anonymization completed!")