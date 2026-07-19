import sqlite3
import json
from pathlib import Path
import logging
from pydantic import BaseModel, ValidationError, Field, field_validator
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

import sys
shared_path = Path(__file__).resolve().parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.append(str(shared_path))
from schema import VehicleRecord

DB_PATH = Path(__file__).resolve().parent / "data" / "vehicles.db"


# VehicleRecord is imported from shared.schema for canonical validation


def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vehicles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            make TEXT,
            model TEXT,
            variant TEXT,
            year INTEGER,
            mileage INTEGER,
            price INTEGER,
            fuel_type TEXT,
            transmission TEXT,
            body_type TEXT,
            city TEXT,
            no_of_owners INTEGER,
            permanent_url TEXT,
            meter_not_tampered INTEGER,
            non_flooded INTEGER,
            core_structure_intact INTEGER
        )
    ''')
    
    # Inspection table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspection (
            vehicle_id INTEGER PRIMARY KEY,
            engine_transmission_chassis REAL,
            fuel_ignition_other REAL,
            interiors_ac REAL,
            exteriors_lights REAL,
            tyres_clutch_brakes REAL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    ''')
    
    conn.commit()
    logger.info("Database schema initialized.")
    return conn

def insert_data(conn):
    input_file = Path("data/cars_fast.json")
    if not input_file.exists():
        input_file = Path("data/cars_clean.json")
        if not input_file.exists():
            input_file = Path("data/cars_with_scores.json")
            if not input_file.exists():
                logger.error("No valid dataset found.")
                return
        
    with open(input_file, "r", encoding="utf-8") as f:
        cars = json.load(f)
        
    cursor = conn.cursor()
    valid_count = 0
    invalid_count = 0
    
    for car in cars:
        try:
            # Map 'model' if present to 'model_name' for alias
            if 'model' in car:
                car['model_name'] = car['model']
            
            validated = VehicleRecord(**car)
            v_id = validated.id
            
            # Upsert vehicle
            cursor.execute('''
                INSERT OR REPLACE INTO vehicles 
                (id, make, model, variant, year, mileage, price, fuel_type, transmission, body_type, city, no_of_owners, permanent_url, meter_not_tampered, non_flooded, core_structure_intact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (v_id, validated.make, validated.model_name, validated.variant, validated.year, 
                  validated.mileage, validated.price, validated.fuel_type, validated.transmission, 
                  validated.body_type, validated.city, validated.no_of_owners, validated.permanent_url,
                  validated.meter_not_tampered, validated.non_flooded, validated.core_structure_intact))
            
            # Insert inspection
            scores = validated.condition_ratings or {}
            cursor.execute('''
                INSERT OR REPLACE INTO inspection 
                (vehicle_id, engine_transmission_chassis, fuel_ignition_other, interiors_ac, exteriors_lights, tyres_clutch_brakes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                v_id, 
                scores.get('engine_transmission_chassis'),
                scores.get('fuel_ignition_other'),
                scores.get('interiors_ac'),
                scores.get('exteriors_lights'),
                scores.get('tyres_clutch_brakes')
            ))
            
            valid_count += 1
        except ValidationError as e:
            invalid_count += 1
            # logger.warning(f"Invalid record {car.get('id')}: {e}")
            pass
        except Exception as e:
            invalid_count += 1
            pass
            
    conn.commit()
    logger.info(f"Inserted {valid_count} valid vehicles. Skipped {invalid_count} invalid records.")

if __name__ == "__main__":
    conn = setup_db()
    insert_data(conn)
    conn.close()
