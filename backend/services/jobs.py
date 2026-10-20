import time
import uuid
import threading
from typing import Dict, Any, Optional, List

class VideoJob:
    def __init__(self, filename: str, method: str, identity: str, resolution: str = "original"):
        self.id = str(uuid.uuid4())
        self.filename = filename
        self.method = method
        self.identity = identity
        self.resolution = resolution
        
        self.status = "queued" # queued, processing, completed, cancelled, failed
        self.current_frame = 0
        self.total_frames = 0
        self.progress_percent = 0.0
        self.fps = 0.0
        self.elapsed_time = 0.0
        self.eta_seconds: Optional[float] = None
        
        self.result_url: Optional[str] = None
        self.original_url: Optional[str] = None
        self.error_message: Optional[str] = None
        
        self.cancel_requested = False
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "method": self.method,
            "identity": self.identity,
            "resolution": self.resolution,
            "status": self.status,
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "progress_percent": round(self.progress_percent, 1),
            "fps": round(self.fps, 1),
            "elapsed_time": round(self.elapsed_time, 1),
            "eta_seconds": round(self.eta_seconds, 1) if self.eta_seconds is not None else None,
            "result_url": self.result_url,
            "original_url": self.original_url,
            "error_message": self.error_message,
            "created_at": self.created_at
        }


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, VideoJob] = {}
        self._lock = threading.Lock()

    def create_job(self, filename: str, method: str, identity: str, resolution: str = "original") -> VideoJob:
        with self._lock:
            job = VideoJob(filename, method, identity, resolution)
            self._jobs[job.id] = job
            return job

    def get_job(self, job_id: str) -> Optional[VideoJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status in ("queued", "processing"):
                job.cancel_requested = True
                job.status = "cancelled"
                return True
            return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [j.to_dict() for j in self._jobs.values()]


# Global job manager instance
job_manager = JobManager()
