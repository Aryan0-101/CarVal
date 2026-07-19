import sys
from pathlib import Path
scraper_path = Path(__file__).resolve().parent.parent / "scraper"
if str(scraper_path) not in sys.path:
    sys.path.append(str(scraper_path))
    
import joblib
model_dict = joblib.load(scraper_path / "models" / "model.pkl")
mapie_model = model_dict['model']
print(mapie_model.estimators_[0].feature_importances_)
