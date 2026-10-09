"""FastAPI application entry point for AI Nutrition Intelligence System.

Features:
- CORS middleware
- SlowAPI rate limiting
- Structured timing and latency logging
- Operational telemetry (/health and /version)
- Modular routers (/assess, /risk, /plan, /foods, /report)
- Clinical disclaimers embedded in OpenAPI documentation
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.routers import assess, auth, foods, plan, reports, risk
from api.schemas import HealthResponse, VersionResponse
from nutri.config import MODEL_PATH
from nutri.foods.food_db import get_food_db
from nutri.logging import setup_logger

logger = setup_logger(__name__)

# Initialize rate limiter: 120 requests/minute default per client IP
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

API_DESCRIPTION = """
### AI-Powered Nutrition Intelligence System API

A production-grade clinical nutrition intelligence backend combining:
1. **Anthropometric & Metabolic Assessment**: Mifflin-St Jeor BMR, WHO/Asian BMI, TDEE, macronutrient distribution, and safety gating.
2. **Calibrated Lifestyle Risk Screening**: LightGBM model trained on lifestyle habits (Height/Weight/BMI excluded) with SHAP explainability.
3. **Clinical Guideline Rules Engine**: Dynamic bounds for hypertension, diabetes, dyslipidemia with audit citations.
4. **Transparent Food Scoring & Swaps**: Health Score v2 (0-100) and strictly healthier same-category alternatives.
5. **Linear Programming Meal Optimization**: PuLP MILP solver generating caloric-exact (±5%) meal plans with tri-state allergen safety.
6. **Downloadable Clinical Reports**: Publication-grade PDF exports via ReportLab.
7. **Secure Authentication & User Management**: PBKDF2 salted passwords, JWT Bearer tokens, and clinical role permissions.

**Notice**: This system is designed for educational and informational purposes only. It is not medical advice.
"""

app = FastAPI(
    title="AI Nutrition Intelligence System API",
    description=API_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request_timing(request: Request, call_next: Callable) -> Response:
    """Log incoming request method, path, status, and response latency."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    logger.info(
        "%s %s -> Status %d (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# Include modular routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(assess.router)
app.include_router(risk.router)
app.include_router(plan.router)
app.include_router(foods.router)
app.include_router(reports.router)


@app.get("/health", response_model=HealthResponse, tags=["Telemetry"])
def health_check() -> HealthResponse:
    """Operational health status and connectivity check."""
    model_loaded = MODEL_PATH.exists()
    db = get_food_db()
    total_foods = 0
    db_connected = False
    try:
        total_foods = db.get_total_count()
        db_connected = total_foods > 0
    except Exception as e:
        logger.error("Health check database probe failed: %s", e)

    return HealthResponse(
        status="healthy" if (model_loaded and db_connected) else "degraded",
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_loaded=model_loaded,
        total_foods_indexed=total_foods,
        database_connected=db_connected,
    )


@app.get("/version", response_model=VersionResponse, tags=["Telemetry"])
def get_version() -> VersionResponse:
    """System version and core engine metadata."""
    return VersionResponse(
        system="AI Nutrition Intelligence System",
        version="1.0.0",
        model_architecture="Calibrated LightGBM (4-Tier Lifestyle Classifier)",
        optimizer_engine="PuLP Mixed-Integer Linear Programming (CBC Solver)",
    )


@app.get("/", tags=["Telemetry"])
def root():
    """Root redirect / information endpoint."""
    return {
        "system": "AI Nutrition Intelligence System API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
    }
