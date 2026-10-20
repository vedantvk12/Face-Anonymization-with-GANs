import os
import time
import requests

API_BASE = "http://127.0.0.1:8000/api"
TEST_VID = os.path.join(os.path.dirname(__file__), "..", "data", "test_videos", "sample_face_interview.mp4")

def test_video_job():
    print("Submitting video job to /api/video/anonymize...")
    with open(TEST_VID, "rb") as f:
        files = {"video": ("sample_face_interview.mp4", f, "video/mp4")}
        data = {
            "method": "generative",
            "synthetic_identity": "random",
            "resolution": "original"
        }
        r = requests.post(f"{API_BASE}/video/anonymize", files=files, data=data)
        print("  Status:", r.status_code)
        assert r.status_code == 200, f"Submission failed: {r.text}"
        job_info = r.json()
        job_id = job_info["job_id"]
        print(f"  Job created with ID: {job_id}")

    # Poll status
    for _ in range(60):
        r = requests.get(f"{API_BASE}/video/status/{job_id}")
        data = r.json()
        status = data.get("status")
        progress = data.get("progress_percent", 0)
        fps = data.get("fps", 0)
        print(f"  Status: {status} | Progress: {progress:.1f}% | FPS: {fps:.1f}")

        if status == "completed":
            print(f"  Job Completed! Result URL: {data.get('result_url')}")
            # Also test video evaluation
            print("  Testing /api/video/evaluate...")
            ev_r = requests.post(f"{API_BASE}/video/evaluate", data={"job_id": job_id})
            print("  Video Evaluation Status:", ev_r.status_code)
            if ev_r.status_code == 200:
                print("  Video Evaluation Data:", ev_r.json())
            return True
        elif status == "failed":
            print(f"  Job Failed: {data.get('error')}")
            return False
        time.sleep(1)

    print("Job timed out.")
    return False

if __name__ == "__main__":
    test_video_job()
