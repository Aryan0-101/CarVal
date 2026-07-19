# Use Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY scraper/requirements.txt ./
# Also we need fastapi, uvicorn, shap, etc.
RUN pip install --no-cache-dir fastapi uvicorn pydantic scikit-learn pandas numpy shap joblib mapie xgboost lightgbm catboost

# Copy models and backend code
# Assuming this Dockerfile is at project root
# Copy shared schemas
COPY shared/ /app/shared/
# Copy entire scraper directory for features.py and models
COPY scraper/ /app/scraper/
# Copy backend code
COPY backend/ /app/backend/

# Expose port
EXPOSE 8000

# Run API
WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
