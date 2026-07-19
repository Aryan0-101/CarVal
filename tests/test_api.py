from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from app import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()

def test_predict_endpoint():
    # Provide exact feature names expected by the model
    payload = {
        "make": "Hyundai",
        "year": 2018,
        "mileage": 30000,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "body_type": "Hatchback",
        "no_of_owners": 1,
        "engine_transmission_chassis": 9.5,
        "fuel_ignition_other": 9.5,
        "interiors_ac": 9.5,
        "exteriors_lights": 9.5,
        "tyres_clutch_brakes": 9.5
    }
    response = client.post("/predict", json=payload)
    
    # In case model is not loaded (if running on a clean machine without models generated)
    if response.status_code == 500:
        assert "Model not loaded" in response.json()["detail"]
    else:
        if response.status_code != 200:
            print(response.json())
        assert response.status_code == 200
    data = response.json()
    assert "predicted_price" in data
    assert "confidence_interval" in data
    assert "feature_importance" in data
    assert len(data["confidence_interval"]) == 2
