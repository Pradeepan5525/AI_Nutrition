# ============================================================================
# Multi-Service Dockerfile for AI Nutrition Intelligence System
# ============================================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src

WORKDIR /app

# Install native dependencies including Coin-OR CBC solver for PuLP and OpenMP for LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    coinor-cbc \
    coinor-libcbc-dev \
    libgomp1 \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and artifacts
COPY src/ ./src/
COPY api/ ./api/
COPY app/ ./app/
COPY artifacts/ ./artifacts/
COPY data/processed/ ./data/processed/
COPY data/raw/ ./data/raw/
COPY docs/ ./docs/
COPY reports/ ./reports/
COPY Makefile ./

# Expose API (8000) and Streamlit UI (8501) ports
EXPOSE 8000 8501

# Default execution starts FastAPI backend
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
