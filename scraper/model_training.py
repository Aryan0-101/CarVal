import sqlite3
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from mapie.regression import CrossConformalRegressor
import joblib

from features import FeatureEngineer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "data" / "vehicles.db"
MODELS_DIR = Path(__file__).resolve().parent / "models"

def train_models():
    conn = sqlite3.connect(DB_PATH)
    query = '''
    SELECT v.id, v.make, v.model, v.variant, v.year, v.mileage, v.price, v.fuel_type, v.transmission, v.body_type, v.no_of_owners, v.city,
           v.meter_not_tampered, v.non_flooded, v.core_structure_intact,
           i.engine_transmission_chassis, i.fuel_ignition_other, i.interiors_ac, i.exteriors_lights, i.tyres_clutch_brakes
    FROM vehicles v
    LEFT JOIN inspection i ON v.id = i.vehicle_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Drop records without price
    df = df.dropna(subset=['price'])
    
    # Use log price to handle heteroscedasticity (varying price ranges)
    y = np.log1p(df['price'])
    X = df.drop(columns=['price', 'id'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Define Column Transformer
    numeric_features = ['year', 'mileage', 'no_of_owners', 'vehicle_age', 'mileage_per_year', 'avg_inspection_score',
                        'engine_transmission_chassis', 'fuel_ignition_other', 'interiors_ac', 'exteriors_lights', 'tyres_clutch_brakes',
                        'meter_not_tampered', 'non_flooded', 'core_structure_intact']
    categorical_features = ['make', 'model', 'variant', 'fuel_type', 'transmission', 'body_type', 'city']
    
    preprocessor = Pipeline([
        ('engineer', FeatureEngineer()),
        ('col_trans', ColumnTransformer(
            transformers=[
                ('num', Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('scaler', StandardScaler())
                ]), numeric_features),
                ('cat', Pipeline([
                    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                    ('onehot', OneHotEncoder(handle_unknown='ignore'))
                ]), categorical_features)
            ]))
    ])
    
    logger.info("Fitting preprocessor...")
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
        
    models = {
        'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
        'XGBoost': XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        'LightGBM': LGBMRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        'CatBoost': CatBoostRegressor(iterations=100, learning_rate=0.1, random_state=42, verbose=0)
    }
    
    best_r2 = -float('inf')
    best_model_name = None
    best_mapie = None
    
    report_lines = ["# Model Benchmarks\n"]
    
    for name, model in models.items():
        logger.info(f"Training {name} with Mapie...")
        
        mapie_model = CrossConformalRegressor(estimator=model, confidence_level=0.90, cv=5, random_state=42)
        mapie_model.fit_conformalize(X_train_processed, y_train)
        
        preds, pis = mapie_model.predict_interval(X_test_processed)
        
        # Convert back to original scale for interpretable metrics
        y_test_exp = np.expm1(y_test)
        preds_exp = np.expm1(preds)
        
        r2 = r2_score(y_test_exp, preds_exp)
        mae = mean_absolute_error(y_test_exp, preds_exp)
        rmse = np.sqrt(np.mean((y_test_exp - preds_exp)**2))
        
        # Calculate coverage (Mapie returns intervals in log space, transform back)
        ci_lower = np.expm1(pis[:, 0, 0])
        ci_upper = np.expm1(pis[:, 1, 0])
        coverage = np.mean((y_test_exp >= ci_lower) & (y_test_exp <= ci_upper))
        avg_width = np.mean(ci_upper - ci_lower)
        
        result_str = f"{name} - MAE: {mae:,.2f}, RMSE: {rmse:,.2f}, R2: {r2:.4f}, Coverage: {coverage:.2%}, Avg Width: {avg_width:,.2f}"
        logger.info(result_str)
        report_lines.append(result_str + "\n")
        
        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name
            best_mapie = mapie_model
            
    best_str = f"\nBest model: {best_model_name} (R2: {best_r2:.4f})"
    logger.info(best_str)
    report_lines.append(best_str + "\n")
    
    MODELS_DIR.mkdir(exist_ok=True, parents=True)
    report_path = MODELS_DIR / "report.txt"
    with open(report_path, "w") as f:
        f.writelines(report_lines)
        
    model_path = MODELS_DIR / "model.pkl"
    # Save a dict so API can easily load preprocessor and mapie
    joblib.dump({
        'preprocessor': preprocessor,
        'model': best_mapie
    }, model_path)
    logger.info(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_models()
