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
        
        # Conformal Prediction Intervals
        # CrossConformalRegressor returns (points, intervals)
        pred, pis = mapie_model.predict_interval(X_processed)
        pred_val = float(pred[0])
        
        # pis has shape (n_samples, 2, n_levels)
        ci_lower = float(pis[0, 0, 0])
        ci_upper = float(pis[0, 1, 0])
        
        # Pricing Factors (Feature Importances)
        shap_dict = {}
        try:
            try:
                feature_names = preprocessor.named_steps['col_trans'].get_feature_names_out()
            except:
                feature_names = []

            # Extract base estimator from Mapie wrapper
            est = getattr(mapie_model, "_mapie_regressor", None)
            if est and hasattr(est, "single_estimator_"):
                base_model = est.single_estimator_
            elif hasattr(mapie_model, "estimator_"):
                base_model = mapie_model.estimator_
            else:
                base_model = None

            if base_model and hasattr(base_model, "feature_importances_"):
                vals = base_model.feature_importances_
                # Normalize them to sum to 1.0 (or just return raw)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
