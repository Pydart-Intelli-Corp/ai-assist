"""
Training API schemas for POORNASREE AI Platform
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TrainingJobRequest(BaseModel):
    """Training job creation request schema"""
    name: str = Field(..., min_length=1, max_length=500, description="Training job name")
    description: Optional[str] = Field(None, max_length=2000, description="Training job description")
    training_type: str = Field(..., description="Training type: full, incremental, batch, real_time")
    model_type: str = Field(..., description="Model type: embedding, classification, generation, retrieval")
    knowledge_base_tier: int = Field(..., ge=1, le=3, description="Knowledge base tier (1-3)")
    document_ids: Optional[List[int]] = Field(default=[], description="Specific document IDs to train on")
    training_config: Dict[str, Any] = Field(default={}, description="Training configuration parameters")
    
    @field_validator('training_type')
    @classmethod
    def validate_training_type(cls, v):
        valid_types = ['full', 'incremental', 'batch', 'real_time']
        if v not in valid_types:
            raise ValueError(f'Training type must be one of: {valid_types}')
        return v
    
    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v):
        valid_types = ['embedding', 'classification', 'generation', 'retrieval']
        if v not in valid_types:
            raise ValueError(f'Model type must be one of: {valid_types}')
        return v

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "Customer Knowledge Base Update",
                "description": "Incremental training on new customer documents",
                "training_type": "incremental",
                "model_type": "embedding",
                "knowledge_base_tier": 1,
                "document_ids": [1, 2, 3],
                "training_config": {
                    "batch_size": 32,
                    "learning_rate": 0.001,
                    "epochs": 5,
                    "validation_split": 0.2
                }
            }
        }
    )


class TrainingJobResponse(BaseModel):
    """Training job response schema"""
    id: int = Field(..., description="Training job ID")
    name: str = Field(..., description="Training job name")
    description: Optional[str] = Field(None, description="Training job description")
    training_type: str = Field(..., description="Training type")
    model_type: str = Field(..., description="Model type")
    knowledge_base_tier: int = Field(..., description="Knowledge base tier")
    status: str = Field(..., description="Current status")
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")
    current_step: Optional[str] = Field(None, description="Current training step")
    total_steps: Optional[int] = Field(None, description="Total training steps")
    final_score: Optional[float] = Field(None, description="Final training score")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    actual_duration_minutes: Optional[int] = Field(None, description="Actual duration in minutes")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_by: str = Field(..., description="Creator email")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Customer Knowledge Base Update",
                "description": "Incremental training on new customer documents",
                "training_type": "incremental",
                "model_type": "embedding",
                "knowledge_base_tier": 1,
                "status": "running",
                "progress_percentage": 45.0,
                "current_step": "Training embeddings",
                "total_steps": 5,
                "final_score": None,
                "estimated_duration_minutes": 30,
                "actual_duration_minutes": None,
                "error_message": None,
                "created_by": "admin@example.com",
                "created_at": "2025-08-06T10:00:00Z",
                "started_at": "2025-08-06T10:05:00Z",
                "completed_at": None
            }
        }


class ModelVersionResponse(BaseModel):
    """Model version response schema"""
    id: int = Field(..., description="Model version ID")
    training_job_id: int = Field(..., description="Training job ID")
    version_number: str = Field(..., description="Version number")
    version_name: Optional[str] = Field(None, description="Version name")
    description: Optional[str] = Field(None, description="Version description")
    model_type: str = Field(..., description="Model type")
    knowledge_base_tier: int = Field(..., description="Knowledge base tier")
    model_size_mb: Optional[float] = Field(None, description="Model size in MB")
    accuracy_score: Optional[float] = Field(None, description="Accuracy score")
    precision_score: Optional[float] = Field(None, description="Precision score")
    recall_score: Optional[float] = Field(None, description="Recall score")
    f1_score: Optional[float] = Field(None, description="F1 score")
    is_deployed: bool = Field(..., description="Is currently deployed")
    deployment_environment: Optional[str] = Field(None, description="Deployment environment")
    created_at: datetime = Field(..., description="Creation timestamp")
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "training_job_id": 1,
                "version_number": "v1.2.3",
                "version_name": "Customer KB Update Q3",
                "description": "Updated customer knowledge base with latest documents",
                "model_type": "embedding",
                "knowledge_base_tier": 1,
                "model_size_mb": 512.5,
                "accuracy_score": 0.94,
                "precision_score": 0.92,
                "recall_score": 0.93,
                "f1_score": 0.925,
                "is_deployed": True,
                "deployment_environment": "production",
                "created_at": "2025-08-06T11:00:00Z",
                "deployed_at": "2025-08-06T11:30:00Z"
            }
        }


class FeedbackRequest(BaseModel):
    """User feedback request schema"""
    query_id: int = Field(..., description="Query ID this feedback relates to")
    feedback_type: str = Field(..., description="Feedback type: rating, comment, bug_report")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5 stars)")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Feedback text")
    feature_used: Optional[str] = Field(None, max_length=255, description="Feature being used")
    page_url: Optional[str] = Field(None, max_length=1000, description="Page URL")
    
    @field_validator('feedback_type')
    @classmethod
    def validate_feedback_type(cls, v):
        valid_types = ['rating', 'comment', 'bug_report']
        if v not in valid_types:
            raise ValueError(f'Feedback type must be one of: {valid_types}')
        return v

    @field_validator('rating')
    @classmethod
    def validate_rating_required(cls, v, info):
        if info.data.get('feedback_type') == 'rating' and v is None:
            raise ValueError('Rating is required for rating feedback type')
        return v

    class Config:
        schema_extra = {
            "example": {
                "query_id": 123,
                "feedback_type": "rating",
                "rating": 4,
                "feedback_text": "The response was helpful but could be more specific",
                "feature_used": "query_processing",
                "page_url": "/query"
            }
        }


class FeedbackResponse(BaseModel):
    """User feedback response schema"""
    id: int = Field(..., description="Feedback ID")
    query_id: int = Field(..., description="Query ID")
    feedback_type: str = Field(..., description="Feedback type")
    rating: Optional[int] = Field(None, description="Rating")
    feedback_text: Optional[str] = Field(None, description="Feedback text")
    sentiment: Optional[str] = Field(None, description="Detected sentiment")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "query_id": 123,
                "feedback_type": "rating",
                "rating": 4,
                "feedback_text": "The response was helpful but could be more specific",
                "sentiment": "positive",
                "created_at": "2025-08-06T12:00:00Z"
            }
        }


class TrainingMetricsResponse(BaseModel):
    """Training metrics response schema"""
    total_jobs: int = Field(..., description="Total training jobs")
    active_jobs: int = Field(..., description="Active training jobs")
    completed_jobs: int = Field(..., description="Completed training jobs")
    failed_jobs: int = Field(..., description="Failed training jobs")
    avg_completion_time: Optional[float] = Field(None, description="Average completion time in minutes")
    success_rate: float = Field(..., description="Success rate percentage")
    total_feedback: int = Field(..., description="Total feedback entries")
    avg_user_rating: Optional[float] = Field(None, description="Average user rating")
    latest_model_version: Optional[str] = Field(None, description="Latest model version")
    
    class Config:
        schema_extra = {
            "example": {
                "total_jobs": 25,
                "active_jobs": 2,
                "completed_jobs": 20,
                "failed_jobs": 3,
                "avg_completion_time": 45.5,
                "success_rate": 80.0,
                "total_feedback": 150,
                "avg_user_rating": 4.2,
                "latest_model_version": "v1.2.5"
            }
        }


class BatchProcessRequest(BaseModel):
    """Batch processing request schema"""
    document_ids: List[int] = Field(..., min_length=1, description="Document IDs to process")
    processing_type: str = Field(..., description="Processing type: embedding, classification, indexing")
    knowledge_base_tier: int = Field(..., ge=1, le=3, description="Knowledge base tier")
    batch_size: int = Field(default=10, ge=1, le=100, description="Batch size for processing")
    
    @field_validator('processing_type')
    @classmethod
    def validate_processing_type(cls, v):
        valid_types = ['embedding', 'classification', 'indexing']
        if v not in valid_types:
            raise ValueError(f'Processing type must be one of: {valid_types}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "document_ids": [1, 2, 3, 4, 5],
                "processing_type": "embedding",
                "knowledge_base_tier": 2,
                "batch_size": 10
            }
        }


class BatchProcessResponse(BaseModel):
    """Batch processing response schema"""
    batch_id: str = Field(..., description="Batch processing ID")
    status: str = Field(..., description="Batch processing status")
    total_documents: int = Field(..., description="Total documents to process")
    processed_documents: int = Field(..., description="Documents processed so far")
    progress_percentage: float = Field(..., description="Progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_20250806_001",
                "status": "processing",
                "total_documents": 5,
                "processed_documents": 2,
                "progress_percentage": 40.0,
                "estimated_completion": "2025-08-06T12:30:00Z"
            }
        }
