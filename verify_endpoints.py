import requests
import json

BASE_URL = "http://localhost:8080" # Assuming local dev server port
ENDPOINTS = [
    "/webhook/estados-unidos",
    "/webhook/latinoamerica",
    "/webhook/experiencia",
    "/webhook/recomendacion",
    "/webhook/machform"
]

def test_endpoint(endpoint):
    print(f"Testing {endpoint}...")
    url = f"{BASE_URL}{endpoint}"
    # Minimal data to pass "No data received" check
    data = {"test": "true"} 
    
    # TEST 1: JSON
    try:
        print(f"  [JSON] ", end="")
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ OK")
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # TEST 2: Form Data
    try:
        print(f"  [FORM] ", end="")
        response = requests.post(url, data=data) # 'data=' sends form-urlencoded
        if response.status_code == 200:
            print("✅ OK")
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Verifying Webhook Endpoints (Server must be running)")
    for ep in ENDPOINTS:
        test_endpoint(ep)
