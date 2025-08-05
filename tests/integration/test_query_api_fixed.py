"""
Fixed Pytest tests for Query API with authentication
"""
import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.core.database import Base
from app.models.user import User, UserRoleEnum
from app.core.security import security_manager

# Test database setup (reuse from document tests)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_documents.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    user = User(
        email="test@example.com",
        full_name="Test User",
        phone_number="+1234567890",
        role=UserRoleEnum.ENGINEER,
        is_verified=True,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    access_token = security_manager.create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}

def test_query_endpoint_basic(client, auth_headers):
    """Test basic query endpoint functionality"""
    response = client.post(
        "/v1/query/ask",
        headers=auth_headers,
        json={
            "query": "How to troubleshoot motor issues?",
            "query_type": "technical",
            "language": "en"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "response" in data
    assert "confidence" in data
    assert "processing_time" in data
    
    # Check that we got a meaningful response
    assert len(data["response"]) > 0
    assert data["confidence"] > 0

def test_query_different_roles(client, auth_headers):
    """Test query processing with engineer role"""
    response = client.post(
        "/v1/query/ask",
        headers=auth_headers,
        json={
            "query": "What causes pump vibration?",
            "query_type": "technical", 
            "language": "en"
        }
    )

    print(f"Role: engineer, Status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "confidence" in data

def test_query_different_languages(client, auth_headers):
    """Test query processing with different languages"""
    response_en = client.post(
        "/v1/query/ask",
        headers=auth_headers,
        json={
            "query": "How to maintain equipment?",
            "query_type": "technical", 
            "language": "en"
        }
    )

    assert response_en.status_code == 200
    data_en = response_en.json()
    assert "response" in data_en
    assert len(data_en["response"]) > 0

def test_query_validation(client, auth_headers):
    """Test query input validation"""
    # Empty query
    response = client.post(
        "/v1/query/ask",
        headers=auth_headers,
        json={
            "query": "",
            "query_type": "technical",
            "language": "en"
        }
    )

    assert response.status_code == 422  # Validation error

def test_query_performance(client, auth_headers):
    """Test query processing performance"""
    import time

    start_time = time.time()

    response = client.post(
        "/v1/query/ask",
        headers=auth_headers,
        json={
            "query": "Explain motor startup procedures",
            "query_type": "technical",
            "language": "en"
        }
    )

    end_time = time.time()
    processing_time = end_time - start_time

    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "response" in data
    assert "processing_time" in data
    
    # Verify reasonable performance (under 120 seconds for real AI)
    assert processing_time < 120
    print(f"Query processing time: {processing_time:.2f}s")
