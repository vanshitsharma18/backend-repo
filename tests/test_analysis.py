"""Tests for the /analyze endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyse_database_timeout():
    response = client.post("/analyze", json={"message": "Database connection timeout"})
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "high"
    assert "database" in data["possible_root_cause"].lower()
    assert "recommendation" in data


def test_analyse_oom():
    response = client.post("/analyze", json={"message": "Out of memory error detected"})
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "critical"


def test_analyse_cpu_spike():
    response = client.post("/analyze", json={"message": "CPU spike to 100% cpu usage"})
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "high"


def test_analyse_rate_limit():
    response = client.post("/analyze", json={"message": "Received 429 too many requests from upstream"})
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "medium"


def test_analyse_unknown_message_returns_default():
    response = client.post("/analyze", json={"message": "Something strange happened"})
    assert response.status_code == 200
    data = response.json()
    assert "severity" in data
    assert "possible_root_cause" in data
    assert "recommendation" in data


def test_analyse_empty_message_returns_422():
    response = client.post("/analyze", json={"message": ""})
    assert response.status_code == 422


def test_analyse_missing_message_returns_422():
    response = client.post("/analyze", json={})
    assert response.status_code == 422
