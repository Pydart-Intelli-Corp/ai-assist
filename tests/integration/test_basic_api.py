"""
Simple test to verify TestClient compatibility
"""
import pytest
from fastapi.testclient import TestClient
from main import app

def test_testclient_basic():
    """Test basic TestClient functionality"""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

def test_platform_info():
    """Test platform info endpoint"""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "platform" in data
        assert "version" in data
