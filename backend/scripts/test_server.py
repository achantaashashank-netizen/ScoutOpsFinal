"""
Test if the FastAPI server is accessible.
"""
import requests

try:
    # Test health endpoint
    print("Testing backend server...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"Health check: {response.status_code} - {response.json()}")

    # Test players endpoint
    response = requests.get("http://localhost:8000/api/players", timeout=5)
    print(f"Players endpoint: {response.status_code}")
    if response.status_code == 200:
        players = response.json()
        print(f"  Found {len(players)} players")
        for p in players:
            print(f"  - {p['name']}")
    else:
        print(f"  Error: {response.text}")

    print("\n[SUCCESS] Backend server is running!")

except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to backend server at http://localhost:8000")
    print("Please start the backend server with: python -m uvicorn app.main:app --reload")
except Exception as e:
    print(f"[ERROR] {e}")
