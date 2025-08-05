"""
Training API endpoints for POORNASREE AI Platform
Handles model training, versioning, feedback collection, and batch processing
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import security_manager
from app.models.user import User, UserRoleEnum
from app.services.training_service import training_service
from app.api.training.schemas import (
    TrainingJobRequest, TrainingJobResponse, ModelVersionResponse,
    FeedbackRequest, FeedbackResponse, TrainingMetricsResponse,
    BatchProcessRequest, BatchProcessResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        payload = security_manager.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/jobs", response_model=TrainingJobResponse)
async def create_training_job(
    request: TrainingJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new training job
    Only admin users can create training jobs
    """
    try:
        # Check admin permissions
        if current_user.role != UserRoleEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create training jobs"
            )
        
        # Create training job
        training_job = await training_service.create_training_job(
            name=request.name,
            description=request.description,
            training_type=request.training_type,
            model_type=request.model_type,
            knowledge_base_tier=request.knowledge_base_tier,
            training_config=request.training_config,
            document_ids=request.document_ids,
            created_by=current_user.email,
            db=db
        )
        
        return TrainingJobResponse(
            id=training_job.id,
            name=training_job.name,
            description=training_job.description,
            training_type=training_job.training_type.value,
            model_type=training_job.model_type.value,
            knowledge_base_tier=training_job.knowledge_base_tier,
            status=training_job.status.value,
            progress_percentage=training_job.progress_percentage,
            current_step=training_job.current_step,
            total_steps=training_job.total_steps,
            final_score=training_job.final_score,
            estimated_duration_minutes=training_job.estimated_duration_minutes,
            actual_duration_minutes=training_job.actual_duration_minutes,
            error_message=training_job.error_message,
            created_by=training_job.created_by,
            created_at=training_job.created_at,
            started_at=training_job.started_at,
            completed_at=training_job.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create training job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/jobs/{job_id}/start")
async def start_training_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a training job
    Only admin users can start training jobs
    """
    try:
        # Check admin permissions
        if current_user.role != UserRoleEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can start training jobs"
            )
        
        success = await training_service.start_training_job(job_id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start training job"
            )
        
        return {"message": f"Training job {job_id} started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start training job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/jobs/{job_id}/cancel")
async def cancel_training_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a running training job
    Only admin users can cancel training jobs
    """
    try:
        # Check admin permissions
        if current_user.role != UserRoleEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can cancel training jobs"
            )
        
        success = training_service.cancel_training_job(job_id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel training job or job not found"
            )
        
        return {"message": f"Training job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel training job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/jobs", response_model=List[TrainingJobResponse])
async def get_training_jobs(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get training jobs with filters
    Admin users see all jobs, others see only their own
    """
    try:
        # Filter by user for non-admin users
        if current_user.role != UserRoleEnum.ADMIN:
            created_by = current_user.email
        
        training_jobs = training_service.get_training_jobs(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            created_by=created_by
        )
        
        return [
            TrainingJobResponse(
                id=job.id,
                name=job.name,
                description=job.description,
                training_type=job.training_type.value,
                model_type=job.model_type.value,
                knowledge_base_tier=job.knowledge_base_tier,
                status=job.status.value,
                progress_percentage=job.progress_percentage,
                current_step=job.current_step,
                total_steps=job.total_steps,
                final_score=job.final_score,
                estimated_duration_minutes=job.estimated_duration_minutes,
                actual_duration_minutes=job.actual_duration_minutes,
                error_message=job.error_message,
                created_by=job.created_by,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            )
            for job in training_jobs
        ]
        
    except Exception as e:
        logger.error(f"Failed to get training jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/models", response_model=List[ModelVersionResponse])
async def get_model_versions(
    skip: int = 0,
    limit: int = 20,
    knowledge_base_tier: Optional[int] = None,
    deployed_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get model versions with filters
    Engineers and admins can access based on their tier
    """
    try:
        # Filter by access tier for non-admin users
        if current_user.role == UserRoleEnum.CUSTOMER:
            knowledge_base_tier = 1
        elif current_user.role == UserRoleEnum.ENGINEER and knowledge_base_tier and knowledge_base_tier > 2:
            knowledge_base_tier = 2
        
        model_versions = training_service.get_model_versions(
            db=db,
            skip=skip,
            limit=limit,
            knowledge_base_tier=knowledge_base_tier,
            deployed_only=deployed_only
        )
        
        return [
            ModelVersionResponse(
                id=version.id,
                training_job_id=version.training_job_id,
                version_number=version.version_number,
                version_name=version.version_name,
                description=version.description,
                model_type=version.model_type.value,
                knowledge_base_tier=version.knowledge_base_tier,
                model_size_mb=version.model_size_mb,
                accuracy_score=version.accuracy_score,
                precision_score=version.precision_score,
                recall_score=version.recall_score,
                f1_score=version.f1_score,
                is_deployed=version.is_deployed,
                deployment_environment=version.deployment_environment,
                created_at=version.created_at,
                deployed_at=version.deployed_at
            )
            for version in model_versions
        ]
        
    except Exception as e:
        logger.error(f"Failed to get model versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit user feedback for training improvement
    All authenticated users can submit feedback
    """
    try:
        feedback = await training_service.collect_feedback(
            query_id=request.query_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            feedback_text=request.feedback_text,
            feature_used=request.feature_used,
            page_url=request.page_url,
            user_id=current_user.id,
            user_agent=req.headers.get("user-agent"),
            db=db
        )
        
        return FeedbackResponse(
            id=feedback.id,
            query_id=feedback.query_id,
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
            sentiment=feedback.sentiment,
            created_at=feedback.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/metrics", response_model=TrainingMetricsResponse)
async def get_training_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get training metrics and statistics
    Only admin and engineer users can access metrics
    """
    try:
        # Check permissions
        if current_user.role == UserRoleEnum.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access training metrics"
            )
        
        metrics = training_service.get_training_metrics(db)
        
        return TrainingMetricsResponse(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get training metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/batch", response_model=BatchProcessResponse)
async def start_batch_processing(
    request: BatchProcessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start batch processing of documents
    Admin and engineer users can start batch processing
    """
    try:
        # Check permissions
        if current_user.role == UserRoleEnum.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for batch processing"
            )
        
        # Engineers can only process up to their tier
        if current_user.role == UserRoleEnum.ENGINEER and request.knowledge_base_tier > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this knowledge base tier"
            )
        
        batch_id = await training_service.process_batch(
            document_ids=request.document_ids,
            processing_type=request.processing_type,
            knowledge_base_tier=request.knowledge_base_tier,
            batch_size=request.batch_size,
            db=db
        )
        
        batch_status = training_service.get_batch_status(batch_id)
        
        return BatchProcessResponse(
            batch_id=batch_id,
            status=batch_status["status"],
            total_documents=batch_status["total_documents"],
            processed_documents=batch_status["processed_documents"],
            progress_percentage=batch_status["progress_percentage"],
            estimated_completion=batch_status["estimated_completion"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start batch processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/batch/{batch_id}", response_model=BatchProcessResponse)
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch processing status
    Admin and engineer users can check batch status
    """
    try:
        # Check permissions
        if current_user.role == UserRoleEnum.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access batch status"
            )
        
        batch_status = training_service.get_batch_status(batch_id)
        
        if not batch_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_id} not found"
            )
        
        return BatchProcessResponse(
            batch_id=batch_id,
            status=batch_status["status"],
            total_documents=batch_status["total_documents"],
            processed_documents=batch_status["processed_documents"],
            progress_percentage=batch_status["progress_percentage"],
            estimated_completion=batch_status.get("estimated_completion")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
