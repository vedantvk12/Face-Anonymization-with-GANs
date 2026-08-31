import os
import cv2
import uuid
import time
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from services.models import get_system_status, get_models
from services.anonymization import detect_faces, anonymize_generative, anonymize_blur
from services.evaluation import evaluate_privacy, evaluate_utility

app = FastAPI(title="PRIVAI Backend")

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
os.makedirs(RESULTS_DIR, exist_ok=True)

@app.get("/api/health")
def health_check():
    status = get_system_status()
    return status

@app.get("/api/synthetic-identities")
def list_synthetic_identities():
    try:
        _, _, _, synthetic_names = get_models()
        return {"identities": synthetic_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load identities")

@app.post("/api/anonymize")
async def anonymize(
    image: UploadFile = File(...),
    method: str = Form(...),
    synthetic_identity: str = Form(default="random")
):
    try:
        start_time = time.time()
        
        # Read image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_np is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
            
        # Detect faces
        faces = detect_faces(img_np)
        if not faces:
            raise HTTPException(status_code=400, detail="No face was detected. Try an image with a clearer or more visible face.")
            
        # Process
        if method == "generative":
            result = anonymize_generative(img_np, faces, synthetic_identity)
        elif method == "blur":
            result = anonymize_blur(img_np, faces)
        else:
            raise HTTPException(status_code=400, detail="Invalid method")
            
        # Save original and result for evaluation
        run_id = str(uuid.uuid4())
        orig_filename = f"{run_id}_original.jpg"
        result_filename = f"{run_id}_{method}.jpg"
        
        orig_path = os.path.join(RESULTS_DIR, orig_filename)
        result_path = os.path.join(RESULTS_DIR, result_filename)
        
        cv2.imwrite(orig_path, img_np)
        cv2.imwrite(result_path, result)
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "faces_detected": len(faces),
            "method": method,
            "synthetic_identity": synthetic_identity if method == "generative" else None,
            "processing_time": round(processing_time, 2),
            "result_url": f"/api/results/{result_filename}",
            "run_id": run_id, # return run_id to facilitate evaluation later
            "original_url": f"/api/results/{orig_filename}"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/evaluate")
async def evaluate(run_id: str = Form(...)):
    # Look for the original, blur and generative images for this run_id
    orig_path = os.path.join(RESULTS_DIR, f"{run_id}_original.jpg")
    gen_path = os.path.join(RESULTS_DIR, f"{run_id}_generative.jpg")
    blur_path = os.path.join(RESULTS_DIR, f"{run_id}_blur.jpg")
    
    if not os.path.exists(orig_path):
        raise HTTPException(status_code=404, detail="Original image not found for this run")
        
    original = cv2.imread(orig_path)
    
    # If the user only ran one method, we can only evaluate that one, but for full evaluation
    # we need both, or we can just evaluate what is available.
    # Let's generate the missing one if we want full evaluation, but the prompt says 
    # "Do not regenerate expensive comparisons unnecessarily."
    # So we'll evaluate what exists.
    generative = cv2.imread(gen_path) if os.path.exists(gen_path) else None
    blur = cv2.imread(blur_path) if os.path.exists(blur_path) else None
    
    # If blur is missing, let's create a quick blur just for baseline evaluation, it's fast
    if blur is None:
        faces = detect_faces(original)
        if faces:
            blur = anonymize_blur(original, faces)
            cv2.imwrite(blur_path, blur)
            
    # If generative is missing, we leave it as None
    if generative is None and blur is None:
        raise HTTPException(status_code=400, detail="No processed images found for evaluation")
    
    # For evaluate_privacy/utility they expect all 3 images, but let's handle if generative is missing
    # To keep it simple and safe, we can mock a dummy if generative is None but user might get error.
    # We will adjust evaluation to handle None
    
    # Let's wrap the logic
    privacy_res = {"identity_similarity": {"blur": None, "generative": None}}
    utility_res = {"scene_preservation": {"blur": None, "generative": None}}
    
    # We use a dummy for missing images inside evaluation if we modify evaluation.py
    # But since evaluation.py assumes arrays, we can just pass the original if missing and ignore the result.
    gen_to_pass = generative if generative is not None else original
    
    try:
        p_res = evaluate_privacy(original, blur, gen_to_pass)
        u_res = evaluate_utility(original, blur, gen_to_pass)
        
        if generative is None:
            p_res["identity_similarity"]["generative"] = None
            u_res["scene_preservation"]["generative"] = None
            
        privacy_res = p_res
        utility_res = u_res
        
    except Exception as e:
        print("Evaluation error:", e)
        # return partial or nulls
        pass

    return {
        "privacy": privacy_res,
        "utility": utility_res
    }

@app.get("/api/results/{filename}")
def get_result(filename: str):
    file_path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
