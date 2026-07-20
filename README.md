<div align="center">
  <img src="https://img.shields.io/badge/Status-Production_Ready-0A84FF?style=for-the-badge" alt="Status Badge"/>
  <img src="https://img.shields.io/badge/Framework-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/ML-XGBoost_&_Mapie-FFCC00?style=for-the-badge" alt="ML"/>
  <img src="https://img.shields.io/badge/UI-Vite_&_Tailwind-646CFF?style=for-the-badge" alt="UI"/>

  <br><br>

  <h1 align="center">CarVal - Vehicle Valuation Engine</h1>
  <p align="center">
    <strong>An enterprise-grade, full-stack vehicle valuation platform powered by Machine Learning and Conformal Prediction.</strong>
  </p>
</div>

---

## ✦ Vision

The **Precision Valuation Engine** predicts the true market value of used vehicles with production-level accuracy. We don't just output a single point estimate; we use **Mapie (Conformal Prediction)** wrapped around Gradient Boosting to guarantee mathematically rigorous confidence intervals. 

---

## 📸 Platform Showcase

### 1. Cinematic Landing Experience
* **Design Philosophy:** Minimalist, deep contrast dark mode (`#0b1326`), glassmorphism panels, and a high-performance `<canvas>` background that scrubs through a 200-frame 3D cinematic vehicle render based on `window.scrollY`.
* **Architecture:** A dedicated, multi-section landing page that educates the user on Empirical Market Calibration and Data-Driven Architecture before launching the valuation engine.

### 2. Predict Interface & Analytics
* **Valuation UI:** A pristine light-mode form with tactile inputs, custom slider tracks, and instant visual feedback. 
* **Explainability:** Using SHAP-inspired feature importances, the engine outputs the exact percentage impact of each factor (like Engine Condition or Make), rendering them dynamically.
* **History Dashboard:** A beautifully crafted table tracks prediction history in real-time, backed by SQLite.

---

## 🏗 System Architecture

The system features a decoupled, globally distributed architecture:

```mermaid
graph TD
    subgraph Data Collection
        A[Playwright Async Scraper] -->|Cleaned Data| C[(SQLite: vehicles.db)]
    end

    subgraph ML Pipeline
        C --> D[Feature Engineering]
        D --> E[XGBoost / LightGBM]
        E --> F[Mapie Conformal Wrapper]
        F -->|joblib| G((model.pkl))
    end

    subgraph Production Backend AWS EC2
        G --> H[FastAPI API]
        H -->|Let's Encrypt / Nginx| I[Exposed REST Endpoints]
        H -->|Log Request| J[(SQLite: history.db)]
    end

    subgraph Edge Frontend Cloudflare Pages
        I --> K[Vite Built SPA]
        K --> L[Landing Page / Predict UI]
    end

    style A fill:#0A84FF,stroke:#0A84FF,color:#fff
    style H fill:#009688,stroke:#009688,color:#fff
    style K fill:#646CFF,stroke:#646CFF,color:#fff
```

---

## 🚀 Deployment & CI/CD

### 1. Edge Frontend (Cloudflare Pages)
The Vite frontend is automatically deployed to Cloudflare Pages via GitHub integration. Every push to `main` triggers an edge build, ensuring the UI is served with zero latency globally.

### 2. Backend API (AWS EC2)
The backend is fully containerized and hosted on an AWS EC2 instance behind an Nginx reverse proxy secured by Certbot (Let's Encrypt). 

### 3. Continuous Deployment (GitHub Actions)
A strict CI/CD pipeline is configured in `.github/workflows/deploy.yml`. When ML models or backend code are pushed to the `main` branch, a GitHub Action securely SSHes into the EC2 instance, pulls the latest code, and rebuilds the Docker containers (`docker-compose.backend.yml`) with zero manual intervention.

---

## 🧠 Model Intelligence

### Conformal Prediction
Standard ML models are often overconfident. We integrated `mapie.regression.CrossConformalRegressor` to output strict **90% Confidence Intervals**. If the model hasn't seen enough data for a specific 15-year-old vehicle, the interval dynamically widens to reflect structural uncertainty.

### Explainability (Pricing Factors)
Using the base estimator's `feature_importances_`, the API extracts the exact localized impact of features and renders them in the UI as progress bars, allowing the user to understand *why* the car is priced the way it is.

---
<div align="center">
  <p><i>Engineered for precision. Designed for impact.</i></p>
</div>
