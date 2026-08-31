import cv2
import os

ORIGINAL = "data/input/test.jpg"
BLURRED = "output/blur/blurred_test.jpg"
GENERATIVE = "output/gan/gan_test.jpg"

OUTPUT = "output/evaluation/final_comparison.jpg"


def load(path):
    image = cv2.imread(path)

    if image is None:
        raise FileNotFoundError(f"Could not load: {path}")

    return image


original = load(ORIGINAL)
blurred = load(BLURRED)
generative = load(GENERATIVE)


# Make all images the same size
height, width = original.shape[:2]

blurred = cv2.resize(
    blurred,
    (width, height)
)

generative = cv2.resize(
    generative,
    (width, height)
)


# Add labels
def add_label(image, text):

    result = image.copy()

    cv2.rectangle(
        result,
        (0, 0),
        (width, 45),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        result,
        text,
        (15, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    return result


original = add_label(
    original,
    "ORIGINAL"
)

blurred = add_label(
    blurred,
    "BLUR"
)

generative = add_label(
    generative,
    "GENERATIVE"
)


# Side-by-side
comparison = cv2.hconcat(
    [
        original,
        blurred,
        generative
    ]
)


os.makedirs(
    "output/evaluation",
    exist_ok=True
)

cv2.imwrite(
    OUTPUT,
    comparison
)


print("=" * 60)
print("COMPARISON CREATED")
print("=" * 60)
print(f"Saved to: {OUTPUT}")
print("=" * 60)