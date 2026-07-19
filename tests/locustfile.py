from locust import HttpUser, task, between
import json
import random

class ValuationUser(HttpUser):
    # Wait between 1 and 3 seconds between requests
    wait_time = between(1, 3)

    @task
    def predict_valuation(self):
        # Generate some semi-random but valid input data
        makes = ["Hyundai", "Maruti Suzuki", "Honda", "Toyota", "BMW"]
        
        payload = {
            "make": random.choice(makes),
            "model": "Unknown",
            "year": random.randint(2018, 2024),
            "mileage": random.randint(5000, 100000),
            "fuel_type": random.choice(["Petrol", "Diesel", "CNG"]),
            "transmission": "Manual",
            "body_type": "Hatchback",
            "no_of_owners": random.randint(1, 3),
            "engine_transmission_chassis": random.uniform(6.0, 10.0),
            "fuel_ignition_other": random.uniform(6.0, 10.0),
            "interiors_ac": random.uniform(6.0, 10.0),
            "exteriors_lights": random.uniform(6.0, 10.0),
            "tyres_clutch_brakes": random.uniform(6.0, 10.0)
        }
        
        # We can pass the auth headers if needed, currently public
        self.client.post("/predict", json=payload, headers={'Content-Type': 'application/json'})

    @task(3)
    def view_history(self):
        # Browsing history happens more frequently than predicting
        self.client.get("/history")
