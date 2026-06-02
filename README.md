# 🚨 Incident Management Backend

> A production-style, cloud-native REST API for reporting, tracking, and analyzing operational incidents — built with **FastAPI** and **Google Firestore**, designed to run on **Google Cloud Run**.

---

## ✨ Features

| Feature | Details |
|---|---|
| **REST API** | FastAPI with auto-generated OpenAPI / Swagger docs |
| **Database** | Google Cloud Firestore (NoSQL, serverless) |
| **Validation** | Pydantic v2 models with strict field constraints |
| **AI Analysis** | Rule-based incident analysis (Phase 1) — Gemini-ready (Phase 2) |
| **Containerized** | Multi-stage Docker build, non-root user |
| **Cloud Run Ready** | Port 8080, `/health` probe, ADC auth |
| **Structured Logging** | stdout JSON-compatible logging |
| **Full Test Suite** | Pytest with mocked Firestore |

---

## 📁 Project Structure

```
incident-management-backend/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, exception handlers
│   ├── config/
│   │   └── settings.py          # Pydantic BaseSettings (env vars)
│   ├── models/
│   │   └── incident.py          # Request / Response Pydantic models + Enums
│   ├── routes/
│   │   ├── health.py            # GET /health
│   │   ├── incidents.py         # POST/GET/PATCH/DELETE /incidents
│   │   └── analysis.py          # POST /analyze
│   ├── services/
│   │   ├── firestore_service.py # Firestore data access layer
│   │   └── analysis_service.py  # Rule-based analysis engine
│   └── utils/                   # Shared utilities (extensible)
├── tests/
│   ├── test_health.py
│   ├── test_incidents.py        # Full CRUD tests with mocked Firestore
│   └── test_analysis.py
├── Dockerfile                   # Multi-stage production build
├── .dockerignore
├── .gitignore
├── .env.example                 # Environment variable template
├── requirements.txt
├── pyproject.toml               # Pytest config
└── README.md
```

---

## 🚀 Quick Start — Local Development

### Prerequisites

- Python 3.12+
- A Google Cloud project with Firestore enabled **OR** the [Firestore Emulator](https://firebase.google.com/docs/emulator-suite/install_and_configure)

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd incident-management-backend

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your PROJECT_ID
```

### 3. Authenticate with Google Cloud (for live Firestore)

```bash
gcloud auth application-default login
```

Or use the **Firestore Emulator** for fully offline dev:

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Start emulator
firebase emulators:start --only firestore

# Add to .env
FIRESTORE_EMULATOR_HOST=localhost:8085
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8080
```

### 5. Explore the API

| URL | Description |
|---|---|
| http://localhost:8080/docs | Swagger UI |
| http://localhost:8080/redoc | ReDoc |
| http://localhost:8080/health | Health check |

---

## 🔌 API Reference

### Health

```http
GET /health
```
```json
{ "status": "healthy" }
```

---

### Create Incident

```http
POST /incidents
Content-Type: application/json

{
  "service": "payment-service",
  "severity": "high",
  "message": "Database connection timeout"
}
```

**Severity values:** `low` | `medium` | `high` | `critical`

```json
{
  "message": "Incident created successfully",
  "incident_id": "INC-001"
}
```

---

### List Incidents

```http
GET /incidents
```
```json
[
  {
    "incident_id": "INC-001",
    "service": "payment-service",
    "severity": "high",
    "status": "open"
  }
]
```

---

### Get Incident

```http
GET /incidents/INC-001
```
```json
{
  "incident_id": "INC-001",
  "service": "payment-service",
  "severity": "high",
  "message": "Database connection timeout",
  "status": "open",
  "created_at": "2026-06-02T10:00:00Z"
}
```

---

### Update Incident Status

```http
PATCH /incidents/INC-001
Content-Type: application/json

{ "status": "resolved" }
```

**Status values:** `open` | `investigating` | `resolved`

```json
{ "message": "Incident updated successfully" }
```

---

### Delete Incident

```http
DELETE /incidents/INC-001
```
```json
{ "message": "Incident deleted successfully" }
```

---

### Analyse Incident (AI)

```http
POST /analyze
Content-Type: application/json

{ "message": "Database connection timeout" }
```
```json
{
  "severity": "high",
  "possible_root_cause": "Database connection timeout — network latency or overloaded DB host",
  "recommendation": "Check database server load and network round-trip time. ..."
}
```

---

## 🐳 Docker

### Build

```bash
docker build -t incident-api:latest .
```

### Run

```bash
docker run -p 8080:8080 \
  -e PROJECT_ID=your-gcp-project-id \
  -e ENVIRONMENT=production \
  incident-api:latest
```

### With ADC credentials mounted

```bash
docker run -p 8080:8080 \
  -e PROJECT_ID=your-gcp-project-id \
  -v "$HOME/.config/gcloud:/home/appuser/.config/gcloud:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/home/appuser/.config/gcloud/application_default_credentials.json \
  incident-api:latest
```

---

## ☁️ Google Cloud Run Deployment

### Push to Artifact Registry

```bash
# Authenticate Docker with Artifact Registry
gcloud auth configure-docker REGION-docker.pkg.dev

# Build and push
docker build -t REGION-docker.pkg.dev/PROJECT_ID/REPO/incident-api:latest .
docker push REGION-docker.pkg.dev/PROJECT_ID/REPO/incident-api:latest
```

### Deploy to Cloud Run

```bash
gcloud run deploy incident-api \
  --image REGION-docker.pkg.dev/PROJECT_ID/REPO/incident-api:latest \
  --region REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=PROJECT_ID,ENVIRONMENT=production \
  --service-account incident-api-sa@PROJECT_ID.iam.gserviceaccount.com
```

### Required IAM Permissions for the Service Account

| Role | Purpose |
|---|---|
| `roles/datastore.user` | Read/write Firestore |
| `roles/logging.logWriter` | Write structured logs |
| `roles/monitoring.metricWriter` | Export metrics |

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_incidents.py -v

# Run with coverage
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

> **Note:** Tests mock Firestore — no live GCP project needed.

---

## 🔮 Roadmap

| Phase | Feature |
|---|---|
| ✅ **Phase 1** | Core API + Rule-based analysis |
| 🔄 **Phase 2** | Google Gemini AI analysis |
| 📋 **Phase 3** | Authentication & Authorization (OAuth2 / API keys) |
| 📊 **Phase 4** | Incident dashboards |
| 📈 **Phase 5** | Metrics & Observability (Cloud Monitoring) |
| 📡 **Phase 6** | Prometheus integration |
| 🔔 **Phase 7** | Alerting & Notifications (PagerDuty, Slack) |

---

## 🏗️ Infrastructure (IaC)

The deployment infrastructure is managed using:

- **Terraform** — Infrastructure as Code for GCP resources
- **Terragrunt** — DRY Terraform wrapper for multi-environment configs
- **Workload Identity Federation** — Keyless authentication for GitHub Actions
- **Artifact Registry** — Docker image storage
- **GitHub Actions** — CI/CD pipeline (build → test → push → deploy)

---

## 📄 License

MIT
