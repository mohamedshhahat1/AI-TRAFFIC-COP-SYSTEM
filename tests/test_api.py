"""Tests for backend API."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestAPI:
    def test_health(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
    
    def test_list_violations(self):
        response = client.get("/api/violations/")
        assert response.status_code == 200
        assert "violations" in response.json()
    
    def test_analytics(self):
        response = client.get("/api/analytics/")
        assert response.status_code == 200
