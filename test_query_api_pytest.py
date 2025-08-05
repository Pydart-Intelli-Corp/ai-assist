"""
Pytest tests for Query API with real AI integration
"""
import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture 
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

def test_query_endpoint_basic(client):
    """Test basic query endpoint functionality"""
    # Test the query endpoint
    response = client.post(
        "/v1/query/ask",
        json={
            "query": "How to troubleshoot motor issues?",
            "query_type": "technical",
            "language": "en"
        }
    )
    
    print(f"Status: {response.status_code}")
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

def test_query_different_roles(client):
    """Test query processing with different user roles"""
    test_cases = [
        {"role": "customer", "tier": 1},
        {"role": "engineer", "tier": 2}, 
        {"role": "admin", "tier": 3}
    ]
    
    for case in test_cases:
        response = client.post(
            "/v1/query/ask",
            json={
                "query": "What causes pump vibration?",
                "query_type": "technical",
                "language": "en",
                "user_role": case["role"],
                "knowledge_base_tier": case["tier"]
            }
        )
        
        print(f"Role: {case['role']}, Status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0

def test_query_different_languages(client):
    """Test query processing with different languages"""
    # English query
    response_en = client.post(
        "/v1/query/ask",
        json={
            "query": "How to maintain equipment?",
            "query_type": "technical", 
            "language": "en"
        }
    )
    
    assert response_en.status_code == 200
    
    # Hindi query (if supported)
    response_hi = client.post(
        "/v1/query/ask",
        json={
            "query": "उपकरण की देखभाल कैसे करें?",
            "query_type": "technical",
            "language": "hi"
        }
    )
    
    assert response_hi.status_code == 200

def test_query_validation(client):
    """Test query input validation"""
    # Empty query
    response = client.post(
        "/v1/query/ask",
        json={
            "query": "",
            "query_type": "technical",
            "language": "en"
        }
    )
    
    assert response.status_code == 422  # Validation error
    
    # Missing required fields
    response = client.post(
        "/v1/query/ask",
        json={
            "query_type": "technical"
        }
    )
    
    assert response.status_code == 422

def test_query_performance(client):
    """Test query processing performance"""
    import time
    
    start_time = time.time()
    
    response = client.post(
        "/v1/query/ask",
        json={
            "query": "Explain motor startup procedures",
            "query_type": "technical",
            "language": "en"
        }
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    assert response.status_code == 200
    assert processing_time < 30  # Should respond within 30 seconds
    
    data = response.json()
    assert "processing_time" in data
    
    print(f"Query processing time: {processing_time:.2f}s")
    print(f"Reported processing time: {data.get('processing_time', 0):.2f}s")
