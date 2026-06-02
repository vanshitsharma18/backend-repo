# =============================================================
# Multi-stage Dockerfile
# Target: Google Cloud Run (port 8080)
# Base:   python:3.12-slim
# =============================================================

# -------------------------------------------------------------
# Stage 1 — dependency builder
# -------------------------------------------------------------
FROM python:3.12-slim AS builder

# Security: do not run pip as root in the final image
WORKDIR /build

# Install build tools needed for some native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# -------------------------------------------------------------
# Stage 2 — production image
# -------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="incident-management-backend"
LABEL org.opencontainers.image.description="FastAPI + Firestore Incident Management API"
LABEL org.opencontainers.image.version="1.0.0"

# Cloud Run expects the app to listen on PORT (default 8080)
ENV PORT=8080 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ ./app/

# Create a non-root user for security
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

USER appuser

# Cloud Run health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

EXPOSE 8080

# Start uvicorn with the number of workers auto-tuned to available CPUs
CMD ["sh", "-c", \
     "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --log-level info"]
