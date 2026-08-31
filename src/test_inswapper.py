import os
import cv2
import insightface

MODEL_PATH = "models/inswapper/inswapper_128.onnx"

print("Checking model...")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

print("Model found.")
print("Loading InSwapper on CPU...")

swapper = insightface.model_zoo.get_model(
    MODEL_PATH,
    download=False,
    providers=["CPUExecutionProvider"]
)

print("INSwapper loaded successfully!")
print("Model test complete.")