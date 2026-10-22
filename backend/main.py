import os
import sys
import cv2
import uuid
import time
import threading
import numpy as np

# Ensure backend directory is in sys.path so 'services.*' imports work from anywhere
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List

from services.models import get_system_status, get_models
from services.detection import detect_faces
from services.anonymization import (
    anonymize_generative,
    anonymize_cartoon,
    anonymize_anime,
    anonymize_blur
)
from services.identities import get_all_identities, get_thumbnail_path
from services.evaluation import evaluate_privacy, evaluate_utility, evaluate_video_sampled
from services.jobs import job_manager
from services.video import process_video_job

app = FastAPI(title="PRIVAI Enterprise Platform", version="2.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(ROOT, "output", "api_results")
TEMP_UPLOADS_DIR = os.path.join(ROOT, "output", "temp_uploads")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".mov", ".avi"}


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "status": "online",
        "service": "PRIVAI Enterprise API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.api_route("/api/health", methods=["GET", "HEAD"])
def health_check():
    return get_system_status()


@app.get("/api/identities")
def list_identities(style: Optional[str] = Query(default=None)):
    """Returns curated synthetic identities with thumbnails and metadata."""
    identities = get_all_identities(style=style)
    return {"identities": identities}


@app.get("/api/identities/thumbnail/{filename}")
def get_thumbnail(filename: str):
    path = get_thumbnail_path(filename)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(path, media_type="image/jpeg")


@app.get("/api/synthetic-identities")
def list_synthetic_identities():
    """Backward-compatible endpoint returning plain list of identity names."""
    try:
        _, _, _, synthetic_names = get_models()
        return {"identities": synthetic_names}
    except Exception:
        # If warming, return configured IDs from JSON
        ids = [item["id"] for item in get_all_identities()]
        return {"identities": ids}


@app.post("/api/anonymize")
async def anonymize(
    image: UploadFile = File(...),
    method: str = Form(...),
    synthetic_identity: str = Form(default="random"),
    unique_faces: bool = Form(default=True)
):
    try:
        start_time = time.time()
        filename = image.filename or "upload.jpg"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format '{ext}'. Supported: JPG, JPEG, PNG, WEBP."
            )

        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_np is None:
            raise HTTPException(status_code=400, detail="Corrupted or invalid image file.")

        # Detect faces
        faces = detect_faces(img_np)
        if not faces:
            raise HTTPException(
                status_code=400,
                detail="No face was detected. Please try an image with a clearer or more visible face."
            )

        # Anonymize according to selected workflow
        method_clean = method.lower()
        used_ids = []
        if method_clean in ("generative", "realistic"):
            result, used_ids = anonymize_generative(
                img_np, faces, selected_identity=synthetic_identity, unique_per_face=unique_faces, return_identities=True
            )
        elif method_clean == "cartoon":
            result, used_ids = anonymize_cartoon(
                img_np, faces, selected_identity=synthetic_identity, unique_per_face=unique_faces, return_identities=True
            )
        elif method_clean == "anime":
            result, used_ids = anonymize_anime(
                img_np, faces, selected_identity=synthetic_identity, unique_per_face=unique_faces, return_identities=True
            )
        elif method_clean == "blur":
            result = anonymize_blur(img_np, faces)
            used_ids = ["blur"]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid method '{method}'. Supported: generative (realistic), cartoon, anime, blur."
            )

        run_id = str(uuid.uuid4())
        orig_filename = f"{run_id}_original{ext}"
        result_filename = f"{run_id}_{method_clean}{ext}"

        orig_path = os.path.join(RESULTS_DIR, orig_filename)
        result_path = os.path.join(RESULTS_DIR, result_filename)

        cv2.imwrite(orig_path, img_np)
        cv2.imwrite(result_path, result)

        processing_time = time.time() - start_time
        resolved_identity = ", ".join(used_ids) if used_ids else (synthetic_identity if method_clean != "blur" else None)

        return {
            "success": True,
            "faces_detected": len(faces),
            "method": method_clean,
            "synthetic_identity": resolved_identity,
            "identities_used": used_ids,
            "processing_time": round(processing_time, 2),
            "result_url": f"/api/results/{result_filename}",
            "original_url": f"/api/results/{orig_filename}",
            "run_id": run_id
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image anonymization failed: {str(e)}")


@app.post("/api/video/anonymize")
async def anonymize_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    method: str = Form(default="generative"),
    synthetic_identity: str = Form(default="random"),
    resolution: str = Form(default="original")
):
    """Enqueues asynchronous video anonymization job with multi-face tracking."""
    filename = video.filename or "video.mp4"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Supported: MP4, MOV, AVI."
        )

    job = job_manager.create_job(
        filename=filename,
        method=method.lower(),
        identity=synthetic_identity,
        resolution=resolution
    )

    temp_in_path = os.path.join(TEMP_UPLOADS_DIR, f"{job.id}_input{ext}")
    final_out_path = os.path.join(RESULTS_DIR, f"{job.id}_anonymized.mp4")

    # Stream upload to disk
    with open(temp_in_path, "wb") as f:
        while chunk := await video.read(1024 * 1024 * 2): # 2MB chunks
            f.write(chunk)

    job.original_url = f"/api/results/{os.path.basename(temp_in_path)}"
    job.result_url = f"/api/results/{os.path.basename(final_out_path)}"

    # Run background processing thread
    background_tasks.add_task(
        process_video_job,
        job.id,
        temp_in_path,
        final_out_path
    )

    return {
        "job_id": job.id,
        "status": "queued",
        "message": "Video uploaded successfully. Processing started in background."
    }


@app.get("/api/video/status/{job_id}")
def get_video_status(job_id: str):
    """Polls status, progress, FPS, and ETA of background video processing."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.post("/api/video/cancel/{job_id}")
def cancel_video_job(job_id: str):
    """Cancels a running or queued video job."""
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled (may have already completed or failed).")
    return {"message": "Job cancellation requested successfully."}


@app.post("/api/evaluate")
async def evaluate(run_id: str = Form(...)):
    """Evaluates identity similarity and scene preservation for image run."""
    orig_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith(f"{run_id}_original")]
    if not orig_files:
        raise HTTPException(status_code=404, detail="Original image not found for this run ID.")

    orig_path = os.path.join(RESULTS_DIR, orig_files[0])
    original = cv2.imread(orig_path)
    if original is None:
        raise HTTPException(status_code=400, detail="Could not read original image.")

    gen_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith(f"{run_id}_generative") or f.startswith(f"{run_id}_cartoon") or f.startswith(f"{run_id}_anime")]
    blur_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith(f"{run_id}_blur")]

    generative = cv2.imread(os.path.join(RESULTS_DIR, gen_files[0])) if gen_files else None
    blur = cv2.imread(os.path.join(RESULTS_DIR, blur_files[0])) if blur_files else None

    # Generate baseline blur for comparison if absent
    if blur is None:
        faces = detect_faces(original)
        if faces:
            blur = anonymize_blur(original, faces)

    gen_to_eval = generative if generative is not None else original

    privacy_res = evaluate_privacy(original, blur, gen_to_eval)
    utility_res = evaluate_utility(original, blur, gen_to_eval)

    if generative is None:
        privacy_res["identity_similarity"]["generative"] = None
        utility_res["scene_preservation"]["generative"] = None
        utility_res["non_face_difference"]["generative"] = None

    return {
        "privacy": privacy_res,
        "utility": utility_res
    }


@app.post("/api/video/evaluate")
async def evaluate_video(job_id: str = Form(...)):
    """Runs sampled evaluation on a processed video job."""
    job = job_manager.get_job(job_id)
    if not job or job.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed or does not exist.")

    # Find input and result files
    temp_files = [f for f in os.listdir(TEMP_UPLOADS_DIR) if f.startswith(f"{job_id}_input")]
    out_file = os.path.join(RESULTS_DIR, f"{job_id}_anonymized.mp4")

    if not temp_files or not os.path.exists(out_file):
        raise HTTPException(status_code=404, detail="Video files for evaluation not found.")

    in_file = os.path.join(TEMP_UPLOADS_DIR, temp_files[0])
    eval_results = evaluate_video_sampled(in_file, out_file, num_samples=5)
    return eval_results


@app.get("/api/results/{filename}")
def get_result(filename: str):
    """Serves processed media file from results or temp uploads."""
    file_path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(TEMP_UPLOADS_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    ext = os.path.splitext(filename)[1].lower()
    media_type = "video/mp4" if ext in (".mp4", ".mov", ".avi") else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)
