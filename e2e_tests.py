import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_endpoint(name, url, method="GET", data=None):
    print(f"Testing {name}...")
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as response:
            res = response.read().decode('utf-8')
            print(f"[{name}] SUCCESS")
            print(f"Response snippet: {res[:200]}")
            return True
    except Exception as e:
        print(f"[{name}] FAILED: {e}")
        return False

print("Waiting for backend to boot (downloading HuggingFace models)...")
for _ in range(30):
    try:
        with urllib.request.urlopen("http://localhost:8000/") as response:
            if response.status == 200:
                print("Backend is UP!")
                break
    except:
        pass
    time.sleep(5)
else:
    print("Backend failed to start in time.")
    exit(1)

chat_data = {
    "user_id": "test_user_1",
    "session_id": "sess_1",
    "message": "Hello, Architect. Who are you?"
}

test_endpoint("Health Check", "http://localhost:8000/")
test_endpoint("Chat API", f"{BASE_URL}/chat", method="POST", data=chat_data)
test_endpoint("Frontend Health", "http://localhost:3000/")

print("E2E tests finished.")
