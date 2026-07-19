import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path("data/vehicles.db")

def feature_engineering():
    conn = sqlite3.connect(DB_PATH)
    
    # Load data
    query = '''
    SELECT v.*, i.engine_transmission_chassis, i.fuel_ignition_other, 
           i.interiors_ac, i.exteriors_lights, i.tyres_clutch_brakes
    FROM vehicles v
    LEFT JOIN inspection i ON v.id = i.vehicle_id
    '''
    df = pd.read_sql_query(query, conn)
    logger.info(f"Loaded {len(df)} records.")
    
    # 1. Handle Missing & Duplicates
    df.drop_duplicates(subset=['id'], inplace=True)
    
    # Fill inspection missing scores with median
    inspection_cols = ['engine_transmission_chassis', 'fuel_ignition_other', 
                       'interiors_ac', 'exteriors_lights', 'tyres_clutch_brakes']
    for col in inspection_cols:
        df[col] = df[col].fillna(df[col].median())
        
    # Average inspection score
    df['avg_inspection_score'] = df[inspection_cols].mean(axis=1)
    
    # 2. Feature Engineering
    current_year = datetime.now().year
    
    # Vehicle Age
    df['vehicle_age'] = current_year - df['year']
    df['vehicle_age'] = df['vehicle_age'].replace(0, 1) # avoid div by zero
    
    # Mileage per Year
    df['mileage_per_year'] = df['mileage'] / df['vehicle_age']
    
    # Brand Premium (simple frequency/price mapping)
    brand_avg_price = df.groupby('make')['price'].transform('mean')
    df['brand_premium'] = df['price'] / brand_avg_price
    
    # 3. Categorical encoding (One-hot for model prep)
    categorical_cols = ['make', 'fuel_type', 'transmission', 'body_type']
    df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    
    # Save processed data
    df_encoded.to_sql('vehicles_processed', conn, if_exists='replace', index=False)
    logger.info("Processed data saved to 'vehicles_processed' table.")
    
    conn.close()
    
if __name__ == "__main__":
    feature_engineering()
