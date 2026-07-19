from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict
import re

class VehicleRecord(BaseModel):
    # This is the single source of truth for the data model across scraper, DB, and API.
    id: int = Field(0)
    make: str = Field(..., alias="make")
    model_name: str = Field("Unknown", alias="model")
    variant: Optional[str] = None
    year: int = Field(..., ge=1990, le=2027)
    mileage: int = Field(..., ge=0)
    price: int = Field(0)
    fuel_type: str = Field(...)
    transmission: str = Field("Manual")
    body_type: str = Field("Hatchback")
    city: str = Field("Unknown")
    no_of_owners: int = Field(1, ge=1)
    permanent_url: Optional[str] = None
    condition_ratings: Optional[Dict[str, float]] = Field(default_factory=dict)
    
    # Inspection parameters (used in API and flattened in DB)
    engine_transmission_chassis: float = Field(5.0)
    fuel_ignition_other: float = Field(5.0)
    interiors_ac: float = Field(5.0)
    exteriors_lights: float = Field(5.0)
    tyres_clutch_brakes: float = Field(5.0)

    @model_validator(mode='before')
    @classmethod
    def populate_year(cls, data):
        # Handle 'make_year' from scraper vs 'year' from API
        if isinstance(data, dict):
            if 'make_year' in data and 'year' not in data:
                data['year'] = data['make_year']
        return data

    @field_validator('make', 'fuel_type', 'transmission', 'body_type', mode='before')
    @classmethod
    def normalize_string(cls, v):
        if not isinstance(v, str):
            return "Unknown"
        return v.strip().title()

    @field_validator('fuel_type')
    @classmethod
    def validate_fuel(cls, v):
        allowed = {"Petrol", "Diesel", "Cng", "Electric"}
        return v if v in allowed else "Other"
        
    @field_validator('transmission')
    @classmethod
    def validate_transmission(cls, v):
        allowed = {"Manual", "Automatic"}
        return v if v in allowed else "Manual"

# The API Request matches exactly the required inference subset
class PredictRequest(VehicleRecord):
    price: Optional[int] = 0
