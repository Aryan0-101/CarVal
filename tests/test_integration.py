import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

from app import app, mapie_model

client = TestClient(app)

def test_health_check_model_loaded():
    """Verify that the API starts and the model artifact is loaded."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    # Ensure the model was actually found and loaded at startup
    assert data["model_loaded"] is True
    assert mapie_model is not None

def test_prediction_flow_with_loaded_artifact():
    """Verify that a prediction request successfully executes through the loaded mapie model."""
    payload = {
        "make": "Hyundai",
        "model": "i20",
        "year": 2018,
        "mileage": 30000,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "body_type": "Hatchback",
        "city": "Delhi",
        "no_of_owners": 1,
        "engine_transmission_chassis": 9.5,
        "fuel_ignition_other": 9.5,
        "interiors_ac": 9.5,
        "exteriors_lights": 9.5,
        "tyres_clutch_brakes": 9.5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "predicted_price" in data
    assert "confidence_interval" in data
    assert len(data["confidence_interval"]) == 2
    assert "feature_importance" in data
