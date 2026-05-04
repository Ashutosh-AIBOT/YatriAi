import requests

data = {
    "message": "plan_trip",
    "session_id": "test",
    "target_agent": "psychology",
    "wanderlust_enabled": False,
    "wanderlust_intensity": 50,
    "psychology_enabled": True
}

try:
    res = requests.post("http://127.0.0.1:8001/api/v1/chat", json=data)
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
