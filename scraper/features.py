from sklearn.base import BaseEstimator, TransformerMixin

class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X_new = X.copy()
        current_year = 2026
        
        # vehicle_age
        X_new['vehicle_age'] = current_year - X_new['year']
        X_new['vehicle_age'] = X_new['vehicle_age'].replace(0, 1)
        
        # mileage_per_year
        X_new['mileage_per_year'] = X_new['mileage'] / X_new['vehicle_age']
        
        # average inspection score
        insp_cols = ['engine_transmission_chassis', 'fuel_ignition_other', 
                     'interiors_ac', 'exteriors_lights', 'tyres_clutch_brakes']
        X_new[insp_cols] = X_new[insp_cols].fillna(5.0)
        X_new['avg_inspection_score'] = X_new[insp_cols].mean(axis=1)
        
        return X_new
