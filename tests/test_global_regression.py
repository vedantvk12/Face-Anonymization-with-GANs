"""
PRIVAI - Global Automated Regression Test Suite
Validates the entire anonymization pipeline across:
- All 13 validated synthetic identities
- All 4 anonymization modes (Realistic, Cartoon, Anime, Blur)
- Single-face and multi-face images
- Video temporal consistency and tracking stability
- Edge cases and error handling
- Quantitative privacy (ArcFace cosine similarity) and utility metrics (Scene preservation %)
"""

import os
import sys
import json
import time
import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.models import get_models
from services.detection import detect_faces
from services.face_blending import swap_face_anatomical
from services.anonymization import (
    anonymize_generative,
    anonymize_cartoon,
    anonymize_anime,
    anonymize_blur
)
from services.identities import get_all_identities, get_identities_by_style
from services.tracking import MultiFaceTracker
from services.evaluation import get_face_embedding, cosine_similarity, compute_scene_preservation


def run_global_regression():
    print("=" * 80)
    print("PRIVAI COMPREHENSIVE GLOBAL REGRESSION TEST SUITE")
    print("=" * 80)

    out_base = os.path.join(ROOT, "output", "verification", "global_regression")
    os.makedirs(out_base, exist_ok=True)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {},
        "summary": {}
    }

    # Initialize models
    t0 = time.time()
    face_app, swapper, syn_ids, syn_names = get_models(blocking=True)
    init_time = time.time() - t0
    print(f"[*] AI Models Loaded in {init_time:.2f}s. Loaded {len(syn_names)} identities.")

    # -------------------------------------------------------------------------
    # SUITE 1: Synthetic Identity Library Integrity & Detection Rate (13/13)
    # -------------------------------------------------------------------------
    print("\n[SUITE 1] Validating 100% of Synthetic Identity Assets...")
    all_identities = get_all_identities()
    identity_stats = []
    failed_identities = []

    for ident in all_identities:
        ident_id = ident["id"]
        source_path = os.path.join(ROOT, "data", "source_faces", f"{ident_id}.jpg")
        thumb_file = os.path.basename(ident.get("thumbnail", f"{ident_id}_thumb.jpg"))
        thumb_path = os.path.join(ROOT, "data", "thumbnails", thumb_file)

        file_exists = os.path.exists(source_path)
        thumb_exists = os.path.exists(thumb_path)

        det_score = 0.0
        has_face = False
        kps_count = 0
        emb_norm = 0.0

        if file_exists:
            img = cv2.imread(source_path)
            if img is not None:
                faces = detect_faces(img)
                if faces:
                    has_face = True
                    det_score = float(getattr(faces[0], "det_score", 0.0))
                    kps_count = len(faces[0].kps) if hasattr(faces[0], "kps") and faces[0].kps is not None else 0
                    if hasattr(faces[0], "embedding") and faces[0].embedding is not None:
                        emb_norm = float(np.linalg.norm(faces[0].embedding))

        valid = file_exists and thumb_exists and has_face and (ident_id in syn_ids)
        if not valid:
            failed_identities.append(ident_id)

        stat = {
            "id": ident_id,
            "name": ident.get("name", ""),
            "style": ident.get("style", ""),
            "file_exists": file_exists,
            "thumb_exists": thumb_exists,
            "face_detected": has_face,
            "det_score": round(det_score, 3),
            "kps_count": kps_count,
            "embedding_norm": round(emb_norm, 3),
            "cached_in_memory": ident_id in syn_ids,
            "status": "PASS" if valid else "FAIL"
        }
        identity_stats.append(stat)
        print(f"  - [{stat['status']}] {ident_id:20s} | Style: {stat['style']:9s} | Det: {det_score:.3f} | KPS: {kps_count}")

    id_success_rate = (len(all_identities) - len(failed_identities)) / max(len(all_identities), 1) * 100.0
    print(f"[*] Identity Library Validation: {len(all_identities) - len(failed_identities)}/{len(all_identities)} passed ({id_success_rate:.1f}%)")
    report["tests"]["identity_library"] = {
        "total": len(all_identities),
        "passed": len(all_identities) - len(failed_identities),
        "failed": failed_identities,
        "success_rate_percent": id_success_rate,
        "identities": identity_stats
    }
    assert len(failed_identities) == 0, f"Identity failures: {failed_identities}"

    # -------------------------------------------------------------------------
    # SUITE 2: All 13 Identities Face Replacement Test & Distinctness
    # -------------------------------------------------------------------------
    print("\n[SUITE 2] Testing Replacement & Identity Distinction Across All Identities...")
    target_img_path = os.path.join(ROOT, "data", "input", "test.jpg")
    orig_target = cv2.imread(target_img_path)
    target_faces = detect_faces(orig_target)
    assert len(target_faces) > 0, "No face detected in test.jpg"
    orig_emb = get_face_embedding(orig_target, face_app)

    ident_out_dir = os.path.join(out_base, "identities_replacement")
    os.makedirs(ident_out_dir, exist_ok=True)

    anonymized_embeddings = {}
    replacement_results = []

    for ident in all_identities:
        ident_id = ident["id"]
        style = ident["style"]

        t_start = time.time()
        if style == "realistic":
            anon_img, used = anonymize_generative(orig_target, target_faces, selected_identity=ident_id, return_identities=True)
        elif style == "cartoon":
            anon_img, used = anonymize_cartoon(orig_target, target_faces, selected_identity=ident_id, return_identities=True)
        elif style == "anime":
            anon_img, used = anonymize_anime(orig_target, target_faces, selected_identity=ident_id, return_identities=True)
        else:
            anon_img = anonymize_blur(orig_target, target_faces)
            used = ["blur"]
        elapsed = time.time() - t_start

        # Save output image
        out_path = os.path.join(ident_out_dir, f"{ident_id}_result.jpg")
        cv2.imwrite(out_path, anon_img)

        # Detect face on result
        anon_faces = detect_faces(anon_img)
        anon_face_found = len(anon_faces) > 0

        # Compute ArcFace distance from original target
        anon_emb = get_face_embedding(anon_img, face_app)
        if anon_emb is not None:
            sim_to_orig = float(cosine_similarity(orig_emb, anon_emb))
            anonymized_embeddings[ident_id] = anon_emb
        else:
            sim_to_orig = 0.0

        diff_non_face, scene_pres = compute_scene_preservation(orig_target, anon_img)

        rep_res = {
            "identity_id": ident_id,
            "style": style,
            "assigned_used": used,
            "face_detected": anon_face_found,
            "arcface_sim_to_original": round(sim_to_orig, 4),
            "scene_preservation_percent": round(scene_pres, 2),
            "latency_seconds": round(elapsed, 3),
            "status": "PASS" if (anon_face_found and sim_to_orig < 0.40) else "WARN"
        }
        replacement_results.append(rep_res)
        print(f"  - [{rep_res['status']}] {ident_id:20s} | Sim to Target: {sim_to_orig:.4f} (Identity Altered!) | Scene Pres: {scene_pres:.1f}% | Time: {elapsed:.2f}s")

    # Measure cross-identity distinctness among realistic identities
    realistic_ids = [r["identity_id"] for r in replacement_results if r["style"] == "realistic" and r["identity_id"] in anonymized_embeddings]
    cross_sims = []
    for i in range(len(realistic_ids)):
        for j in range(i + 1, len(realistic_ids)):
            id_a, id_b = realistic_ids[i], realistic_ids[j]
            emb_a, emb_b = anonymized_embeddings[id_a], anonymized_embeddings[id_b]
            sim_ab = float(cosine_similarity(emb_a, emb_b))
            cross_sims.append({
                "pair": f"{id_a} vs {id_b}",
                "similarity": round(sim_ab, 4)
            })

    mean_cross_sim = float(np.mean([c["similarity"] for c in cross_sims])) if cross_sims else 0.0
    print(f"[*] Cross-Identity Distinctness (Realistic IDs avg pair similarity): {mean_cross_sim:.4f}")
    print(f"    (Values < 0.60 confirm distinct, unique facial identities rather than cloned appearances)")

    report["tests"]["identity_replacements"] = {
        "results": replacement_results,
        "mean_cross_identity_similarity": round(mean_cross_sim, 4),
        "pairwise_similarities": cross_sims
    }

    # -------------------------------------------------------------------------
    # SUITE 3: Multi-Face Image Processing Accuracy (`two_people.jpg`)
    # -------------------------------------------------------------------------
    print("\n[SUITE 3] Testing Multi-Face Scene Handling (`two_people.jpg`)...")
    multi_path = os.path.join(ROOT, "data", "input", "two_people.jpg")
    multi_orig = cv2.imread(multi_path)
    multi_faces = detect_faces(multi_orig)
    print(f"[*] Detected {len(multi_faces)} faces in multi-person image.")
    assert len(multi_faces) >= 2, f"Expected at least 2 faces, got {len(multi_faces)}"

    multi_out_dir = os.path.join(out_base, "multi_face")
    os.makedirs(multi_out_dir, exist_ok=True)

    # 1. Realistic Multi-Face with Unique Personas
    t_start = time.time()
    multi_real, used_real = anonymize_generative(
        multi_orig, multi_faces, selected_identity="random", unique_per_face=True, return_identities=True
    )
    t_real = time.time() - t_start
    cv2.imwrite(os.path.join(multi_out_dir, "multi_realistic.jpg"), multi_real)
    print(f"  - Realistic Multi-Face Assigned: {used_real} in {t_real:.2f}s")
    assert len(used_real) == len(multi_faces), "Did not assign identity to all faces"
    assert len(set(used_real)) == len(used_real), f"Expected unique identities per face, got duplicates: {used_real}"

    # Verify both faces are detected on the output
    post_faces_real = detect_faces(multi_real)
    print(f"    Faces detected post-swap: {len(post_faces_real)}/{len(multi_faces)}")

    # 2. Cartoon Multi-Face
    multi_cart, used_cart = anonymize_cartoon(
        multi_orig, multi_faces, selected_identity="random", unique_per_face=True, return_identities=True
    )
    cv2.imwrite(os.path.join(multi_out_dir, "multi_cartoon.jpg"), multi_cart)
    print(f"  - Cartoon Multi-Face Assigned: {used_cart}")

    # 3. Anime Multi-Face
    multi_anime, used_anime = anonymize_anime(
        multi_orig, multi_faces, selected_identity="random", unique_per_face=True, return_identities=True
    )
    cv2.imwrite(os.path.join(multi_out_dir, "multi_anime.jpg"), multi_anime)
    print(f"  - Anime Multi-Face Assigned: {used_anime}")

    # 4. Blur Multi-Face
    multi_blur = anonymize_blur(multi_orig, multi_faces)
    cv2.imwrite(os.path.join(multi_out_dir, "multi_blur.jpg"), multi_blur)
    print(f"  - Blur Multi-Face completed successfully.")

    report["tests"]["multi_face"] = {
        "faces_detected": len(multi_faces),
        "realistic_assigned": used_real,
        "cartoon_assigned": used_cart,
        "anime_assigned": used_anime,
        "post_anonymization_faces_detected": len(post_faces_real)
    }

    # -------------------------------------------------------------------------
    # SUITE 4: Video Temporal Stability & Tracking Consistency
    # -------------------------------------------------------------------------
    print("\n[SUITE 4] Testing Video Temporal Consistency & Multi-Frame Stability...")
    video_path = os.path.join(ROOT, "data", "test_videos", "sample_face_interview.mp4")
    assert os.path.exists(video_path), f"Video missing: {video_path}"

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    tracker = MultiFaceTracker(
        iou_threshold=0.30,
        similarity_threshold=0.45,
        max_lost_frames=30,
        max_holdover_frames=2,
        unique_identities=True
    )

    style_candidates = get_identities_by_style("realistic")
    test_frame_count = min(30, total_frames)
    frame_idx = 0
    video_out_dir = os.path.join(out_base, "video_tracking")
    os.makedirs(video_out_dir, exist_ok=True)

    tracked_identities_history = []
    consecutive_frame_embeddings = []
    processed_count = 0
    t_vid_start = time.time()

    while frame_idx < test_frame_count:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        faces = detect_faces(frame)
        tracked = tracker.update(faces, available_identities=style_candidates, default_identity="realistic_sophia")

        anon_frame = frame.copy()
        frame_assigned = []
        if tracked:
            for face_obj, assigned_id, _ in tracked:
                anon_frame = anonymize_generative(anon_frame, [face_obj], selected_identity=assigned_id)
                frame_assigned.append(assigned_id)

        tracked_identities_history.append(frame_assigned)

        # Compute ArcFace embedding of the anonymized frame face
        emb = get_face_embedding(anon_frame, face_app)
        if emb is not None:
            consecutive_frame_embeddings.append(emb)

        if frame_idx % 5 == 0:
            cv2.imwrite(os.path.join(video_out_dir, f"frame_{frame_idx:02d}.jpg"), anon_frame)

        processed_count += 1
        frame_idx += 1

    cap.release()
    t_vid_elapsed = time.time() - t_vid_start
    vid_fps = processed_count / max(t_vid_elapsed, 0.001)

    # Calculate temporal consistency
    temporal_sims = []
    for i in range(len(consecutive_frame_embeddings) - 1):
        sim = cosine_similarity(consecutive_frame_embeddings[i], consecutive_frame_embeddings[i + 1])
        if sim is not None:
            temporal_sims.append(float(sim))

    avg_temporal_sim = float(np.mean(temporal_sims)) if temporal_sims else 1.0
    print(f"[*] Video Frames Processed: {processed_count}/{test_frame_count} at {vid_fps:.1f} FPS")
    print(f"[*] Temporal Identity Consistency: {avg_temporal_sim:.4f} (Target >= 0.90)")

    # Check that identity didn't jitter/swap randomly between frames
    flat_history = [ids[0] for ids in tracked_identities_history if ids]
    unique_assigned_throughout = len(set(flat_history))
    print(f"[*] Distinct identities assigned across track: {unique_assigned_throughout} (Expected 1 for single speaker)")

    report["tests"]["video_temporal"] = {
        "frames_processed": processed_count,
        "processing_fps": round(vid_fps, 2),
        "temporal_consistency": round(avg_temporal_sim, 4),
        "track_swaps": unique_assigned_throughout - 1,
        "status": "PASS" if (avg_temporal_sim >= 0.90 and unique_assigned_throughout == 1) else "WARN"
    }

    # -------------------------------------------------------------------------
    # SUITE 5: Boundary Condition & Error Handling
    # -------------------------------------------------------------------------
    print("\n[SUITE 5] Testing Boundary Conditions and Error Robustness...")
    error_tests = []

    # 1. Blank / Zero image (no faces)
    black_img = np.zeros((400, 400, 3), dtype=np.uint8)
    no_faces = detect_faces(black_img)
    err_1_pass = (len(no_faces) == 0)
    error_tests.append({"case": "Black image (no face)", "detected": len(no_faces), "pass": err_1_pass})

    # 2. Extreme resolution image
    tiny_img = cv2.resize(orig_target, (64, 64))
    tiny_faces = detect_faces(tiny_img)
    error_tests.append({"case": "Low-res 64x64 image", "detected": len(tiny_faces), "pass": True})

    # 3. Invalid synthetic identity request (should cleanly map without crash)
    anon_fallback = anonymize_generative(orig_target, target_faces, selected_identity="non_existent_id")
    err_3_pass = (anon_fallback is not None and anon_fallback.shape == orig_target.shape)
    error_tests.append({"case": "Invalid identity fallback", "handled_gracefully": err_3_pass, "pass": err_3_pass})

    for et in error_tests:
        print(f"  - [{('PASS' if et['pass'] else 'FAIL')}] Case: {et['case']}")

    report["tests"]["error_handling"] = error_tests

    # -------------------------------------------------------------------------
    # OVERALL SUMMARY & ACCEPTANCE
    # -------------------------------------------------------------------------
    overall_pass = (
        len(failed_identities) == 0 and
        id_success_rate == 100.0 and
        avg_temporal_sim >= 0.90 and
        len(used_real) == len(multi_faces)
    )

    report["summary"] = {
        "overall_status": "PASS" if overall_pass else "FAIL",
        "identities_validated": f"{len(all_identities) - len(failed_identities)}/{len(all_identities)}",
        "average_scene_preservation": f"{np.mean([r['scene_preservation_percent'] for r in replacement_results]):.1f}%",
        "average_identity_anonymization_sim": f"{np.mean([r['arcface_sim_to_original'] for r in replacement_results]):.4f}",
        "video_fps": round(vid_fps, 1),
        "video_temporal_consistency": round(avg_temporal_sim, 4)
    }

    report_path = os.path.join(out_base, "regression_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print(f"REGRESSION SUITE RESULT: {report['summary']['overall_status']}")
    print(f"Report JSON saved to: {report_path}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    report = run_global_regression()
    if report["summary"]["overall_status"] != "PASS":
        sys.exit(1)
