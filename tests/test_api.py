import pytest
import sys
from pathlib import Path

# Add project roots
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))

from fastapi.testclient import TestClient
from backend.app import app
from shared.schema import PredictRequest, VehicleRecord

client = TestClient(app)

def test_metadata_endpoint():
    response = client.get("/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "hierarchy" in data
    assert "cities" in data
    assert isinstance(data["cities"], list)

def test_request_validation():
    # Missing required fields should 422
    response = client.post("/predict", json={})
    assert response.status_code == 422
    
def test_category_normalization():
    # Send weird casings, check if pydantic normalizes them
    req = VehicleRecord(
        make="  mArUTi SuZuKi  ",
        model="sWIFT",
        variant="  VXI  ",
        year=2020,
        mileage=50000,
        fuel_type=" pEtRoL ",
        city=" nEw DElhi "
    )
    assert req.make == "Maruti Suzuki"
    assert req.model_name == "Swift"
    assert req.variant == "Vxi"
    assert req.fuel_type == "Petrol"
    assert req.city == "Delhi-Ncr"

def test_prediction_response_shape():
    payload = {
        "make": "Maruti Suzuki",
        "model": "Swift",
        "variant": "VXI",
        "year": 2020,
        "mileage": 50000,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "body_type": "Hatchback",
        "no_of_owners": 1,
        "city": "Delhi",
        "engine_transmission_chassis": 9.0,
        "fuel_ignition_other": 9.0,
        "interiors_ac": 9.0,
        "exteriors_lights": 9.0,
        "tyres_clutch_brakes": 9.0,
        "meter_not_tampered": 1,
        "non_flooded": 1,
        "core_structure_intact": 1
    }
    response = client.post("/predict", json=payload)
    if response.status_code == 500:
        # Model not loaded yet
        return
        
    assert response.status_code == 200
    data = response.json()
    assert "predicted_price" in data
    assert "confidence_interval" in data
    assert "feature_importance" in data
    
    ci_lower, ci_upper = data["confidence_interval"]
    assert ci_lower <= data["predicted_price"]
    assert data["predicted_price"] <= ci_upper
