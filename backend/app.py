from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sys
from pathlib import Path

scraper_path = Path(__file__).resolve().parent.parent / "scraper"
if str(scraper_path) not in sys.path:
    sys.path.append(str(scraper_path))
    
from features import FeatureEngineer
import joblib
import pandas as pd
import numpy as np
import shap
import json
import sqlite3
from datetime import datetime
import os

app = FastAPI(title="Vehicle Valuation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model pipeline dict
MODEL_PATH = scraper_path / "models" / "model.pkl"
DB_PATH = Path(__file__).resolve().parent / "history.db"

preprocessor = None
mapie_model = None

if MODEL_PATH.exists():
    model_dict = joblib.load(MODEL_PATH)
    preprocessor = model_dict['preprocessor']
    mapie_model = model_dict['model']


shared_path = Path(__file__).resolve().parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.append(str(shared_path))
from schema import PredictRequest

# Request schema matches the raw database columns exactly
# (Imported from shared/schema.py to maintain one canonical contract)

class HistoryResponse(BaseModel):
    id: int
    timestamp: str
    prediction: float

# Initialize history DB
conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY, timestamp TEXT, prediction REAL, request TEXT)")
conn.close()

@app.get("/")
def read_root():
    return {"status": "running", "model_loaded": mapie_model is not None}

@app.post("/predict")
def predict(req: PredictRequest):
    if mapie_model is None:
        raise HTTPException(status_code=500, detail="Model pipeline not loaded")
        
    try:
        req_dict = req.model_dump(by_alias=True)
        df = pd.DataFrame([req_dict])
        
        X_processed = preprocessor.transform(df)
        
        # Conformal Prediction Intervals (in log space)
        pred, pis = mapie_model.predict_interval(X_processed)
        
        # Transform back from log1p space to absolute rupees
        pred_val = float(np.expm1(pred[0]))
        ci_lower = max(0.0, float(np.expm1(pis[0, 0, 0])))
        ci_upper = float(np.expm1(pis[0, 1, 0]))
        
        # Pricing Factors (Feature Importances)
        shap_dict = {}
        try:
            try:
                feature_names = preprocessor.named_steps['col_trans'].get_feature_names_out()
            except:
                feature_names = []

            # Extract base estimator from Mapie wrapper
            est = getattr(mapie_model, "_mapie_regressor", None)
            base_model = None
            if est:
                base_model = getattr(getattr(est, "estimator_", None), "single_estimator_", None)
            
            if not base_model:
                base_model = getattr(mapie_model, "estimator_", None)

            if base_model and hasattr(base_model, "feature_importances_"):
                vals = base_model.feature_importances_
                # Normalize them to sum to 1.0
                total = sum(vals)
                if total > 0 and len(feature_names) == len(vals):
                    for i, col in enumerate(feature_names):
                        shap_dict[col] = float(vals[i] / total)
        except Exception as e:
            print(f"Feature importance extraction failed: {e}")
        
        # Save history
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO predictions (timestamp, prediction, request) VALUES (?, ?, ?)",
                     (datetime.now().isoformat(), pred_val, json.dumps(req_dict)))
        conn.commit()
        conn.close()
        
        return {
            "predicted_price": pred_val,
            "confidence_interval": [ci_lower, ci_upper],
            "feature_importance": shap_dict
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/history", response_model=list[HistoryResponse])
def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, timestamp, prediction FROM predictions ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/metadata")
def get_metadata():
    v_db_path = scraper_path / "data" / "vehicles.db"
    if not v_db_path.exists():
        return {}
    
    conn = sqlite3.connect(v_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT make, model, variant FROM vehicles WHERE make IS NOT NULL AND model IS NOT NULL")
    rows = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT city FROM vehicles WHERE city IS NOT NULL")
    city_rows = cursor.fetchall()
    conn.close()
    
    cities = sorted([r[0].strip().title() for r in city_rows])
    
    # Build hierarchy: Make -> Model -> List[Variant]
    hierarchy = {}
    for make, model, variant in rows:
        make = make.strip().title()
        model = model.strip()
        variant = variant.strip() if variant else "Standard"
        
        if make not in hierarchy:
            hierarchy[make] = {}
        if model not in hierarchy[make]:
            hierarchy[make][model] = set()
            
        hierarchy[make][model].add(variant)
        
    # Convert sets to sorted lists
    for make in hierarchy:
        for model in hierarchy[make]:
            hierarchy[make][model] = sorted(list(hierarchy[make][model]))
            
    return {
        "hierarchy": hierarchy,
        "cities": cities
    }

@app.get("/evaluation_metrics")
def get_metrics():
    report_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scraper", "models", "report.txt")
    if not os.path.exists(report_path):
        return {"error": "Report not found"}
    
    with open(report_path, "r") as f:
        content = f.read()
        
    return {"report_text": content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
