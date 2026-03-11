import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

response = client.get('/dem/raw/statistics?url=data/dem.tif')
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.json()}")
