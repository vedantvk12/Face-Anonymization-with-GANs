import os
import cv2
import time
import subprocess
import numpy as np
import imageio_ffmpeg
from typing import Optional, Tuple

from .models import get_models
from .detection import detect_faces
from .tracking import MultiFaceTracker
from .anonymization import (
    anonymize_generative,
    anonymize_cartoon,
    anonymize_anime,
    anonymize_blur
)
from .identities import get_identities_by_style
from .jobs import job_manager, VideoJob

def get_ffmpeg_binary() -> str:
    """Returns the path to the verified FFmpeg executable."""
    return imageio_ffmpeg.get_ffmpeg_exe()


def compute_target_resolution(w: int, h: int, resolution_preset: str) -> Tuple[int, int]:
    """Calculates scaled resolution based on target quality preset."""
    if resolution_preset == "720p" and h > 720:
        scale = 720.0 / h
        new_w = int(w * scale)
        # Ensure dimensions are even numbers for H.264 codecs
        return (new_w // 2) * 2, 720
    elif resolution_preset == "480p" and h > 480:
        scale = 480.0 / h
        new_w = int(w * scale)
        return (new_w // 2) * 2, 480
    else:
        return (w // 2) * 2, (h // 2) * 2


def process_video_job(
    job_id: str,
    input_video_path: str,
    output_video_path: str
):
    """
    Asynchronous video anonymization worker with multi-face tracking,
    consistent synthetic identity assignment, progress tracking, and FFmpeg audio muxing.
    """
    job = job_manager.get_job(job_id)
    if not job:
        return

    job.status = "processing"
    job.started_at = time.time()
    temp_raw_video = output_video_path + ".raw.mp4"

    cap = None
    writer = None

    try:
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError("Could not open input video file.")

        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or np.isnan(fps):
            fps = 24.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            total_frames = 1
        job.total_frames = total_frames

        target_w, target_h = compute_target_resolution(orig_w, orig_h, job.resolution)
        resize_needed = (target_w != orig_w or target_h != orig_h)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_raw_video, fourcc, fps, (target_w, target_h))
        if not writer.isOpened():
            raise RuntimeError("Failed to initialize video writer.")

        # Multi-face tracker setup
        is_unique = (job.identity == "random" or job.identity == "unique_per_person")
        tracker = MultiFaceTracker(
            iou_threshold=0.30,
            similarity_threshold=0.45,
            max_lost_frames=30,
            max_holdover_frames=2,
            unique_identities=is_unique
        )

        # Style candidates
        style_key = job.method
        if style_key == "generative":
            style_key = "realistic"
        available_ids = get_identities_by_style(style_key)
        if not available_ids:
            _, _, _, all_names = get_models()
            available_ids = all_names

        frame_idx = 0
        start_time = time.time()

        while True:
            # Check for user cancellation
            if job.cancel_requested:
                job.status = "cancelled"
                break

            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if resize_needed:
                frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

            # 1. Detect faces in frame
            faces = detect_faces(frame)

            # 2. Update multi-face tracker for consistent identity retention
            tracked_results = tracker.update(
                faces,
                available_identities=available_ids,
                default_identity=job.identity
            )

            # 3. Anonymize frame preserving consistent identity per track
            if job.method == "blur":
                blur_faces = [f for f, _, _ in tracked_results] if tracked_results else faces
                if blur_faces:
                    frame = anonymize_blur(frame, blur_faces)
            elif job.method == "cartoon":
                if tracked_results:
                    for face, assigned_id, _ in tracked_results:
                        frame = anonymize_cartoon(frame, [face], selected_identity=assigned_id)
            elif job.method == "anime":
                if tracked_results:
                    for face, assigned_id, _ in tracked_results:
                        frame = anonymize_anime(frame, [face], selected_identity=assigned_id)
            else: # generative / realistic
                if tracked_results:
                    for face, assigned_id, _ in tracked_results:
                        frame = anonymize_generative(frame, [face], selected_identity=assigned_id)

            writer.write(frame)
            frame_idx += 1

            # Update progress & throughput metrics
            elapsed = time.time() - start_time
            proc_fps = frame_idx / max(elapsed, 0.001)
            remaining_frames = max(0, total_frames - frame_idx)
            eta = remaining_frames / max(proc_fps, 0.001)

            job.current_frame = frame_idx
            job.progress_percent = min(100.0, (frame_idx / total_frames) * 100.0)
            job.fps = proc_fps
            job.elapsed_time = elapsed
            job.eta_seconds = eta

        # Cleanup video streams
        cap.release()
        writer.release()
        cap = None
        writer = None

        if job.status == "cancelled":
            if os.path.exists(temp_raw_video):
                os.remove(temp_raw_video)
            return

        # 4. FFmpeg Audio Multiplexing and H.264 Web Browser Encoding
        ffmpeg_exe = get_ffmpeg_binary()
        cmd = [
            ffmpeg_exe, "-y",
            "-i", temp_raw_video,
            "-i", input_video_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p", # Critical for web browser HTML5 video playback!
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-map", "0:v:0",
            "-map", "1:a:0?", # Preserve audio stream if present, ignore if silent
            "-shortest",
            output_video_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("FFmpeg muxing warning:", result.stderr.decode("utf-8", errors="ignore"))
            # Fallback: rename raw video
            if os.path.exists(temp_raw_video) and not os.path.exists(output_video_path):
                os.rename(temp_raw_video, output_video_path)
        else:
            if os.path.exists(temp_raw_video):
                os.remove(temp_raw_video)

        job.status = "completed"
        job.progress_percent = 100.0
        job.eta_seconds = 0.0
        job.completed_at = time.time()

    except Exception as e:
        import traceback
        traceback.print_exc()
        job.status = "failed"
        job.error_message = str(e)
    finally:
        if cap is not None:
            cap.release()
        if writer is not None:
            writer.release()
        if os.path.exists(temp_raw_video):
            try:
                os.remove(temp_raw_video)
            except Exception:
                pass
