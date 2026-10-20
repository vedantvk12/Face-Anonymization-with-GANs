import os
import requests

API_BASE = "http://127.0.0.1:8000/api"
TEST_IMG = os.path.join(os.path.dirname(__file__), "..", "data", "input", "test.jpg")

def test_api():
    print("Testing /api/health...")
    r = requests.get(f"{API_BASE}/health")
    print("  Health:", r.status_code, r.json())

    print("\nTesting /api/identities...")
    r = requests.get(f"{API_BASE}/identities")
    data = r.json()
    print("  Identities:", r.status_code, f"Loaded {len(data.get('identities', []))} identities")

    for method in ["realistic", "cartoon", "anime", "blur"]:
        print(f"\nTesting /api/anonymize with method={method}...")
        with open(TEST_IMG, "rb") as f:
            files = {"image": ("test.jpg", f, "image/jpeg")}
            data = {"method": method, "synthetic_identity": "random", "unique_faces": "true"}
            r = requests.post(f"{API_BASE}/anonymize", files=files, data=data)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                resp = r.json()
                print(f"  Success: {resp.get('success')}, Time: {resp.get('processing_time')}s, Result: {resp.get('result_url')}")
            else:
                print("  Error:", r.text)

if __name__ == "__main__":
    test_api()
