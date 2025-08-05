"""
Pytest configuration and shared fixtures for POORNASREE AI Platform tests
"""
import os
import sys
import pytest
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

@pytest.fixture(scope="session")
def test_db_path():
    """Path to test database"""
    return Path(__file__).parent / "fixtures" / "test_documents.db"

@pytest.fixture(scope="session") 
def api_base_url():
    """Base URL for API testing"""
    return "http://localhost:8000"

@pytest.fixture(scope="session")
def api_url(api_base_url):
    """API v1 URL for testing"""
    return f"{api_base_url}/v1"

# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests that require authentication"
    )
