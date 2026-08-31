# Face Anonymization with GANs

A privacy-preserving face anonymization project that combines face detection, synthetic identity replacement, and evaluation metrics to help anonymize identities in images while preserving the surrounding scene.

## Project overview

This project contains a full-stack anonymization workflow:

- A FastAPI backend for image upload, face detection, anonymization, and evaluation
- A Vite + React frontend for interacting with the anonymization pipeline
- A Streamlit prototype for local/manual image anonymization
- A GAN-based anonymization pipeline and supporting utilities under the project source folders

## Features

- Blur-based anonymization baseline
- Generative face anonymization using InsightFace / InSwapper-style synthetic identity replacement
- Face detection and model loading with CPU execution support
- Image evaluation for privacy-preservation and utility-preservation metrics
- Frontend dashboard for uploading images and comparing methods

## Repository structure

```text
.
├── backend/                 # FastAPI backend service
│   ├── main.py
│   ├── requirements.txt
│   └── services/
├── frontend/                # React + Vite frontend
│   ├── package.json
│   └── src/
├── src/                     # Local scripts and notebook-style workflows
├── data/                    # Dataset/input/source face assets
├── models/                  # Model weights (large files, tracked via Git LFS)
├── output/                  # Generated results and evaluation outputs
├── deep_privacy2/           # Reference GAN anonymization implementation
├── README.md
├── .gitignore
├── .gitattributes
└── requirements.txt
```

## Tech stack

- Python 3.10+
- FastAPI
- OpenCV
- InsightFace
- NumPy
- React + Vite + TypeScript
- Streamlit (prototype UI)

## Setup

### 1) Clone the repository

```bash
git clone https://github.com/vedantvk12/Face-Anonymization-with-GANs.git
cd Face-Anonymization-with-GANs
```

### 2) Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3) Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

### 4) Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5) Run the backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6) Run the frontend

```bash
cd frontend
npm run dev
```

### 7) Run the Streamlit app (optional)

```bash
streamlit run src/app.py
```

## Model note

This project depends on the InsightFace model file:

```text
models/inswapper/inswapper_128.onnx
```

Because this file is large, the repository is configured to use Git LFS for ONNX model assets. Make sure Git LFS is installed before pushing:

```bash
git lfs install
```

If the model is missing locally, place it inside `models/inswapper/` before running the backend.

## Usage

1. Launch the backend and frontend.
2. Upload an image in the web app.
3. Select a method:
   - blur
   - generative
4. Choose a synthetic identity if using the generative method.
5. Review the anonymized output and evaluation results.

## License

This project is intended for research and educational use. Please check the original model and library licenses before redistribution or production deployment.

## Notes

- The evaluation metrics are experimental and intended for relative comparison.
- Generated outputs and large datasets are excluded from version control by default.
- The repository includes source code and the app scaffold, but the heavyweight model and runtime artifacts should be managed with Git LFS or a separate release artifact strategy.
