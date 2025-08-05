"""
Tests for Training API endpoints
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order

import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from main import app
from app.core.database import get_db, Base
from app.models.user import User, UserRoleEnum
from app.models.training import TrainingJob, ModelVersion, TrainingStatusEnum
from app.models.analytics import FeedbackAnalytics
from app.models.knowledge_base import Document, DocumentTypeEnum, DocumentStatusEnum, KnowledgeBaseTierEnum
from app.core.security import security_manager

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_training.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database
Base.metadata.create_all(bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Admin user headers for authentication"""
    # Create admin user directly in the database
    db = TestingSessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "admin@test.com").first()
        if existing_user:
            admin_user = existing_user
        else:
            admin_user = User(
                email="admin@test.com",
                full_name="Test Admin",
                phone_number="+1234567890",
                role=UserRoleEnum.ADMIN,
                is_verified=True,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        
        # Create token directly
        access_token = security_manager.create_access_token(data={"sub": str(admin_user.id)})
        return {"Authorization": f"Bearer {access_token}"}
    finally:
        db.close()


@pytest.fixture
def engineer_headers():
    """Engineer user headers for authentication"""
    # Create engineer user directly in the database
    db = TestingSessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "engineer@test.com").first()
        if existing_user:
            engineer_user = existing_user
        else:
            engineer_user = User(
                email="engineer@test.com",
                full_name="Test Engineer",
                phone_number="+1234567891",
                role=UserRoleEnum.ENGINEER,
                is_verified=True,
                is_active=True
            )
            db.add(engineer_user)
            db.commit()
            db.refresh(engineer_user)
        
        # Create token directly
        access_token = security_manager.create_access_token(data={"sub": str(engineer_user.id)})
        return {"Authorization": f"Bearer {access_token}"}
    finally:
        db.close()


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    db = TestingSessionLocal()
    try:
        docs = []
        for i in range(3):
            doc = Document(
                title=f"Test Document {i+1}",
                description=f"This is test document {i+1} description",
                filename=f"test_doc_{i+1}.pdf",
                original_filename=f"test_doc_{i+1}.pdf",
                file_path=f"/test/doc{i+1}.pdf",
                file_size=1024,
                file_type=DocumentTypeEnum.PDF,
                mime_type="application/pdf",
                file_hash=f"test_hash_{i+1}",
                extracted_text=f"This is test document {i+1} content for training",
                knowledge_base_tier=KnowledgeBaseTierEnum.CUSTOMER,  # All tier 1 documents
                category="maintenance",
                uploaded_by="test@example.com",
                status=DocumentStatusEnum.PROCESSED
            )
            db.add(doc)
            docs.append(doc)
        
        db.commit()
        doc_ids = [doc.id for doc in docs]
        return doc_ids
    finally:
        db.close()


class TestTrainingJobAPI:
    """Training job API tests"""
    
    def test_create_training_job_success(self, client, admin_headers, sample_documents):
        """Test successful training job creation"""
        job_data = {
            "name": "Test Training Job",
            "description": "Test job description",
            "training_type": "incremental",
            "model_type": "embedding",
            "knowledge_base_tier": 1,
            "training_config": {
                "batch_size": 32,
                "learning_rate": 0.001,
                "epochs": 5
            }
        }
        
        response = client.post("/v1/training/jobs", headers=admin_headers, json=job_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == job_data["name"]
        assert data["training_type"] == job_data["training_type"]
        assert data["model_type"] == job_data["model_type"]
        assert data["status"] == "pending"
        assert data["progress_percentage"] == 0.0
    
    def test_create_training_job_non_admin_forbidden(self, client, engineer_headers):
        """Test training job creation forbidden for non-admin users"""
        job_data = {
            "name": "Test Training Job",
            "training_type": "incremental",
            "model_type": "embedding",
            "knowledge_base_tier": 1
        }
        
        response = client.post("/v1/training/jobs", headers=engineer_headers, json=job_data)
        
        assert response.status_code == 403
        assert "Only admin users can create training jobs" in response.json()["error"]["message"]
    
    def test_create_training_job_invalid_data(self, client, admin_headers):
        """Test training job creation with invalid data"""
        job_data = {
            "name": "",  # Invalid: empty name
            "training_type": "invalid_type",  # Invalid type
            "model_type": "embedding",
            "knowledge_base_tier": 5  # Invalid tier
        }
        
        response = client.post("/v1/training/jobs", headers=admin_headers, json=job_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_start_training_job_success(self, client, admin_headers, sample_documents):
        """Test successful training job start"""
        # Create training job first
        job_data = {
            "name": "Test Training Job",
            "training_type": "incremental",
            "model_type": "embedding",
            "knowledge_base_tier": 1,
            "document_ids": sample_documents[:1]
        }
        
        create_response = client.post("/v1/training/jobs", headers=admin_headers, json=job_data)
        assert create_response.status_code == 200
        job_id = create_response.json()["id"]
        
        # Start the job
        start_response = client.post(f"/v1/training/jobs/{job_id}/start", headers=admin_headers)
        
        assert start_response.status_code == 200
        assert "started successfully" in start_response.json()["message"]
    
    def test_start_training_job_non_admin_forbidden(self, client, engineer_headers):
        """Test training job start forbidden for non-admin users"""
        response = client.post("/v1/training/jobs/1/start", headers=engineer_headers)
        
        assert response.status_code == 403
        assert "Only admin users can start training jobs" in response.json()["error"]["message"]
    
    def test_cancel_training_job_success(self, client, admin_headers, sample_documents):
        """Test successful training job cancellation"""
        # Create and start training job
        job_data = {
            "name": "Test Training Job",
            "training_type": "incremental",
            "model_type": "embedding",
            "knowledge_base_tier": 1,
            "document_ids": sample_documents[:1]
        }
        
        create_response = client.post("/v1/training/jobs", headers=admin_headers, json=job_data)
        job_id = create_response.json()["id"]
        
        # Start the job
        client.post(f"/v1/training/jobs/{job_id}/start", headers=admin_headers)
        
        # Cancel the job
        cancel_response = client.post(f"/v1/training/jobs/{job_id}/cancel", headers=admin_headers)
        
        assert cancel_response.status_code == 200
        assert "cancelled successfully" in cancel_response.json()["message"]
    
    def test_get_training_jobs_admin(self, client, admin_headers, sample_documents):
        """Test get training jobs for admin user"""
        # Create a training job
        job_data = {
            "name": "Test Training Job",
            "training_type": "incremental",
            "model_type": "embedding",
            "knowledge_base_tier": 1
        }
        
        client.post("/v1/training/jobs", headers=admin_headers, json=job_data)
        
        # Get jobs
        response = client.get("/v1/training/jobs", headers=admin_headers)
        
        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) >= 1
        assert jobs[0]["name"] == job_data["name"]
    
    def test_get_training_jobs_with_filters(self, client, admin_headers):
        """Test get training jobs with status filter"""
        response = client.get("/v1/training/jobs?status=pending&limit=10", headers=admin_headers)
        
        assert response.status_code == 200
        jobs = response.json()
        for job in jobs:
            assert job["status"] == "pending"


class TestModelVersionAPI:
    """Model version API tests"""
    
    def test_get_model_versions_admin(self, client, admin_headers):
        """Test get model versions for admin user"""
        response = client.get("/v1/training/models", headers=admin_headers)
        
        assert response.status_code == 200
        models = response.json()
        assert isinstance(models, list)
    
    def test_get_model_versions_engineer_filtered(self, client, engineer_headers):
        """Test get model versions filtered for engineer"""
        response = client.get("/v1/training/models", headers=engineer_headers)
        
        assert response.status_code == 200
        models = response.json()
        # Engineers should only see models up to tier 2
        for model in models:
            assert model["knowledge_base_tier"] <= 2
    
    def test_get_model_versions_deployed_only(self, client, admin_headers):
        """Test get only deployed model versions"""
        response = client.get("/v1/training/models?deployed_only=true", headers=admin_headers)
        
        assert response.status_code == 200
        models = response.json()
        for model in models:
            assert model["is_deployed"] == True


class TestFeedbackAPI:
    """Feedback API tests"""
    
    def test_submit_feedback_success(self, client, admin_headers):
        """Test successful feedback submission"""
        # First create a query to reference
        query_data = {
            "query": "Test query for feedback",
            "query_type": "technical",
            "language": "en"
        }
        
        query_response = client.post("/v1/query/ask", headers=admin_headers, json=query_data)
        assert query_response.status_code == 200
        query_id = query_response.json()["query_id"]
        
        # Submit feedback
        feedback_data = {
            "query_id": query_id,
            "feedback_type": "rating",
            "rating": 4,
            "feedback_text": "Good response, helpful information",
            "feature_used": "query_processing"
        }
        
        response = client.post("/v1/training/feedback", headers=admin_headers, json=feedback_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == query_id
        assert data["feedback_type"] == "rating"
        assert data["rating"] == 4
        assert data["sentiment"] in ["positive", "negative", "neutral"]
    
    def test_submit_feedback_invalid_query(self, client, admin_headers):
        """Test feedback submission with invalid query ID"""
        feedback_data = {
            "query_id": 99999,  # Non-existent query
            "feedback_type": "rating",
            "rating": 4
        }
        
        response = client.post("/v1/training/feedback", headers=admin_headers, json=feedback_data)
        
        assert response.status_code == 500  # Should fail due to invalid query
    
    def test_submit_feedback_validation_error(self, client, admin_headers):
        """Test feedback submission with validation errors"""
        feedback_data = {
            "query_id": 1,
            "feedback_type": "rating",
            # Missing required rating for rating type
        }
        
        response = client.post("/v1/training/feedback", headers=admin_headers, json=feedback_data)
        
        assert response.status_code == 422  # Validation error


class TestTrainingMetricsAPI:
    """Training metrics API tests"""
    
    def test_get_training_metrics_admin(self, client, admin_headers):
        """Test get training metrics for admin user"""
        response = client.get("/v1/training/metrics", headers=admin_headers)
        
        assert response.status_code == 200
        metrics = response.json()
        
        # Check required metric fields
        required_fields = [
            "total_jobs", "active_jobs", "completed_jobs", "failed_jobs",
            "success_rate", "total_feedback", "avg_user_rating"
        ]
        
        for field in required_fields:
            assert field in metrics
            assert isinstance(metrics[field], (int, float))
    
    def test_get_training_metrics_engineer(self, client, engineer_headers):
        """Test get training metrics for engineer user"""
        response = client.get("/v1/training/metrics", headers=engineer_headers)
        
        assert response.status_code == 200
        metrics = response.json()
        assert "total_jobs" in metrics
    
    def test_get_training_metrics_customer_forbidden(self, client):
        """Test training metrics forbidden for customer users"""
        # Create customer user
        user_data = {
            "email": "customer@test.com",
            "password": "customer123",
            "full_name": "Test Customer"
        }
        
        # Register customer
        register_response = client.post("/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Login
        login_response = client.post("/v1/auth/login", json={
            "email": "customer@test.com",
            "password": "customer123"
        })
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        customer_headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access metrics
        response = client.get("/v1/training/metrics", headers=customer_headers)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["error"]["message"]


class TestBatchProcessingAPI:
    """Batch processing API tests"""
    
    def test_start_batch_processing_admin(self, client, admin_headers, sample_documents):
        """Test start batch processing for admin user"""
        batch_data = {
            "document_ids": sample_documents[:2],
            "processing_type": "embedding",
            "knowledge_base_tier": 1,
            "batch_size": 10
        }
        
        response = client.post("/v1/training/batch", headers=admin_headers, json=batch_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert data["status"] == "processing"
        assert data["total_documents"] == 2
        assert data["processed_documents"] == 0
        assert data["progress_percentage"] == 0.0
    
    def test_start_batch_processing_engineer(self, client, engineer_headers, sample_documents):
        """Test start batch processing for engineer user"""
        batch_data = {
            "document_ids": sample_documents[:1],
            "processing_type": "embedding",
            "knowledge_base_tier": 2,  # Engineer can process tier 2
            "batch_size": 5
        }
        
        response = client.post("/v1/training/batch", headers=engineer_headers, json=batch_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
    
    def test_start_batch_processing_engineer_tier_forbidden(self, client, engineer_headers, sample_documents):
        """Test batch processing forbidden for engineer on tier 3"""
        batch_data = {
            "document_ids": sample_documents[:1],
            "processing_type": "embedding",
            "knowledge_base_tier": 3,  # Engineer cannot process tier 3
            "batch_size": 5
        }
        
        response = client.post("/v1/training/batch", headers=engineer_headers, json=batch_data)
        
        assert response.status_code == 403
        assert "Insufficient permissions for this knowledge base tier" in response.json()["error"]["message"]
    
    def test_get_batch_status_success(self, client, admin_headers, sample_documents):
        """Test get batch processing status"""
        # Start batch processing
        batch_data = {
            "document_ids": sample_documents[:1],
            "processing_type": "embedding",
            "knowledge_base_tier": 1,
            "batch_size": 5
        }
        
        start_response = client.post("/v1/training/batch", headers=admin_headers, json=batch_data)
        batch_id = start_response.json()["batch_id"]
        
        # Get status
        status_response = client.get(f"/v1/training/batch/{batch_id}", headers=admin_headers)
        
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["batch_id"] == batch_id
        assert "status" in data
        assert "progress_percentage" in data
    
    def test_get_batch_status_not_found(self, client, admin_headers):
        """Test get batch status for non-existent batch"""
        response = client.get("/v1/training/batch/invalid_batch_id", headers=admin_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"]


class TestTrainingIntegration:
    """Integration tests for training system"""
    
    @pytest.mark.asyncio
    async def test_complete_training_workflow(self, client, admin_headers, sample_documents):
        """Test complete training workflow from creation to completion"""
        # 1. Create training job
        job_data = {
            "name": "Integration Test Job",
            "description": "Complete workflow test",
            "training_type": "incremental",
            "model_type": "embedding",
            "knowledge_base_tier": 1,
            "document_ids": sample_documents[:1],
            "training_config": {"epochs": 1}
        }
        
        create_response = client.post("/v1/training/jobs", headers=admin_headers, json=job_data)
        assert create_response.status_code == 200
        job_id = create_response.json()["id"]
        
        # 2. Start training job
        start_response = client.post(f"/v1/training/jobs/{job_id}/start", headers=admin_headers)
        assert start_response.status_code == 200
        
        # 3. Wait for training to complete (simulate)
        await asyncio.sleep(1)
        
        # 4. Check job status
        jobs_response = client.get("/v1/training/jobs", headers=admin_headers)
        jobs = jobs_response.json()
        job = next((j for j in jobs if j["id"] == job_id), None)
        
        assert job is not None
        # Job should be running or completed
        assert job["status"] in ["running", "completed"]
        
        # 5. Check metrics
        metrics_response = client.get("/v1/training/metrics", headers=admin_headers)
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert metrics["total_jobs"] >= 1
