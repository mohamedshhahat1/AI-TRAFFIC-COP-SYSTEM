"""Tests for backend API."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestHealthEndpoints:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "websocket_clients" in data

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Traffic Cop" in response.text


class TestViolationsAPI:
    def test_list_violations(self, client):
        response = client.get("/api/violations/")
        assert response.status_code == 200
        data = response.json()
        assert "violations" in data
        assert "total" in data

    def test_create_violation(self, client, sample_violation):
        response = client.post("/api/violations/", json=sample_violation)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["violation"]["type"] == "speed_violation"
        assert data["violation"]["speed"] == 85.5

    def test_create_violation_validation(self, client):
        # Missing required 'type' field
        response = client.post("/api/violations/", json={"severity": "low"})
        assert response.status_code == 422

    def test_get_violation_not_found(self, client):
        response = client.get("/api/violations/nonexistent")
        assert response.status_code == 404

    def test_filter_by_type(self, client, sample_violation):
        # Create a violation first
        client.post("/api/violations/", json=sample_violation)
        # Filter by type
        response = client.get("/api/violations/?type=speed_violation")
        assert response.status_code == 200

    def test_filter_by_severity(self, client, sample_violation):
        client.post("/api/violations/", json=sample_violation)
        response = client.get("/api/violations/?severity=high")
        assert response.status_code == 200

    def test_today_summary(self, client):
        response = client.get("/api/violations/summary/today")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_type" in data


class TestVehiclesAPI:
    def test_list_vehicles(self, client):
        response = client.get("/api/vehicles/")
        assert response.status_code == 200
        data = response.json()
        assert "vehicles" in data
        assert "total" in data

    def test_get_vehicle_not_found(self, client):
        response = client.get("/api/vehicles/99999")
        assert response.status_code == 404


class TestAnalyticsAPI:
    def test_analytics(self, client):
        response = client.get("/api/analytics/")
        assert response.status_code == 200

    def test_system_health(self, client):
        response = client.get("/api/analytics/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_system_metrics(self, client):
        response = client.get("/api/analytics/metrics")
        assert response.status_code == 200

    def test_heatmap(self, client):
        response = client.get("/api/analytics/heatmap")
        assert response.status_code == 200
        assert "zones" in response.json()

    def test_logs(self, client):
        response = client.get("/api/analytics/logs")
        assert response.status_code == 200


class TestCameraAPI:
    def test_camera_stats(self, client):
        response = client.get("/api/camera/stats")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data or "fps" in data

    def test_camera_info(self, client):
        response = client.get("/api/camera/info")
        assert response.status_code == 200


class TestEventAPIs:
    def test_event_metrics(self, client):
        response = client.get("/api/events/metrics")
        assert response.status_code == 200

    def test_event_history(self, client):
        response = client.get("/api/events/history")
        assert response.status_code == 200
        assert "events" in response.json()


class TestRateLimiting:
    def test_rate_limit_not_triggered_for_health(self, client):
        """Health endpoint should be exempt from rate limiting."""
        for _ in range(100):
            response = client.get("/api/health")
            assert response.status_code == 200
