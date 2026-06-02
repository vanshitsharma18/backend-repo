"""
Tests for the /incidents CRUD endpoints.

Firestore is mocked so these tests run without a live GCP project.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.incident import IncidentResponse, IncidentSummary
from app.services.firestore_service import get_firestore_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_INCIDENT = IncidentResponse(
    incident_id="INC-001",
    service="payment-service",
    severity="high",
    message="Database connection timeout",
    status="open",
    created_at=datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc),
)

SAMPLE_SUMMARY = IncidentSummary(
    incident_id="INC-001",
    service="payment-service",
    severity="high",
    status="open",
)


def _make_mock_service(**overrides):
    svc = MagicMock()
    svc.create_incident = AsyncMock(return_value="INC-001")
    svc.get_all_incidents = AsyncMock(return_value=[SAMPLE_SUMMARY])
    svc.get_incident = AsyncMock(return_value=SAMPLE_INCIDENT)
    svc.update_incident = AsyncMock(return_value=None)
    svc.delete_incident = AsyncMock(return_value=None)
    for k, v in overrides.items():
        setattr(svc, k, v)
    return svc


# ---------------------------------------------------------------------------
# POST /incidents
# ---------------------------------------------------------------------------

class TestCreateIncident:
    def test_create_returns_201(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.post(
            "/incidents",
            json={
                "service": "payment-service",
                "severity": "high",
                "message": "Database connection timeout",
            },
        )
        assert response.status_code == 201

    def test_create_returns_incident_id(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.post(
            "/incidents",
            json={
                "service": "payment-service",
                "severity": "high",
                "message": "Database connection timeout",
            },
        )
        data = response.json()
        assert data["incident_id"] == "INC-001"
        assert data["message"] == "Incident created successfully"

    def test_create_missing_service_returns_422(self):
        client = TestClient(app)
        response = client.post(
            "/incidents",
            json={"severity": "high", "message": "Some error"},
        )
        assert response.status_code == 422

    def test_create_invalid_severity_returns_422(self):
        client = TestClient(app)
        response = client.post(
            "/incidents",
            json={
                "service": "auth-service",
                "severity": "extreme",  # invalid
                "message": "Something broke",
            },
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /incidents
# ---------------------------------------------------------------------------

class TestListIncidents:
    def test_list_returns_200(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.get("/incidents")
        assert response.status_code == 200

    def test_list_returns_array(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.get("/incidents")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["incident_id"] == "INC-001"


# ---------------------------------------------------------------------------
# GET /incidents/{incident_id}
# ---------------------------------------------------------------------------

class TestGetIncident:
    def test_get_existing_returns_200(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.get("/incidents/INC-001")
        assert response.status_code == 200

    def test_get_existing_returns_full_details(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.get("/incidents/INC-001")
        data = response.json()
        assert data["incident_id"] == "INC-001"
        assert data["service"] == "payment-service"
        assert data["message"] == "Database connection timeout"

    def test_get_missing_returns_404(self):
        from fastapi import HTTPException
        mock_svc = _make_mock_service(
            get_incident=AsyncMock(
                side_effect=HTTPException(status_code=404, detail="Not found")
            )
        )
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.get("/incidents/INC-999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /incidents/{incident_id}
# ---------------------------------------------------------------------------

class TestUpdateIncident:
    def test_update_status_returns_200(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.patch("/incidents/INC-001", json={"status": "resolved"})
        assert response.status_code == 200
        assert response.json()["message"] == "Incident updated successfully"

    def test_update_invalid_status_returns_422(self):
        client = TestClient(app)
        response = client.patch("/incidents/INC-001", json={"status": "unknown"})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /incidents/{incident_id}
# ---------------------------------------------------------------------------

class TestDeleteIncident:
    def test_delete_returns_200(self):
        mock_svc = _make_mock_service()
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.delete("/incidents/INC-001")
        assert response.status_code == 200
        assert response.json()["message"] == "Incident deleted successfully"

    def test_delete_not_found_returns_404(self):
        from fastapi import HTTPException
        mock_svc = _make_mock_service(
            delete_incident=AsyncMock(
                side_effect=HTTPException(status_code=404, detail="Not found")
            )
        )
        app.dependency_overrides[get_firestore_service] = lambda: mock_svc
        client = TestClient(app)

        response = client.delete("/incidents/INC-999")
        assert response.status_code == 404
