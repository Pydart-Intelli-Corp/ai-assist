"""
Training service for POORNASREE AI Platform
Handles model training, versioning, and feedback collection
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order

import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.training import (
    TrainingJob, ModelVersion, ModelEvaluation, DatasetVersion,
    TrainingStatusEnum, TrainingTypeEnum, ModelTypeEnum
)
from app.models.user import UserQuery
from app.models.analytics import FeedbackAnalytics
from app.models.knowledge_base import Document
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class TrainingService:
    """Training service for managing AI model training and feedback"""
    
    def __init__(self):
        self.active_jobs = {}  # Track active training jobs
        self.batch_processors = {}  # Track batch processing jobs
    
    async def create_training_job(
        self,
        name: str,
        description: str,
        training_type: str,
        model_type: str,
        knowledge_base_tier: int,
        training_config: Dict[str, Any],
        document_ids: List[int],
        created_by: str,
        db: Session
    ) -> TrainingJob:
        """Create a new training job"""
        try:
            # Validate document access for the tier
            if document_ids:
                valid_docs = db.query(Document).filter(
                    Document.id.in_(document_ids),
                    Document.knowledge_base_tier <= knowledge_base_tier
                ).count()
                
                if valid_docs != len(document_ids):
                    raise ValueError(f"Some documents are not accessible for tier {knowledge_base_tier}")
            
            # Create training job
            training_job = TrainingJob(
                name=name,
                description=description,
                training_type=TrainingTypeEnum(training_type),
                model_type=ModelTypeEnum(model_type),
                knowledge_base_tier=knowledge_base_tier,
                training_config=training_config,
                status=TrainingStatusEnum.PENDING,
                created_by=created_by,
                estimated_duration_minutes=self._estimate_training_duration(
                    training_type, len(document_ids) if document_ids else 0
                )
            )
            
            db.add(training_job)
            db.commit()
            db.refresh(training_job)
            
            # Link documents if specified
            if document_ids:
                documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
                training_job.documents.extend(documents)
                db.commit()
            
            logger.info(f"Created training job {training_job.id}: {name}")
            return training_job
            
        except Exception as e:
            logger.error(f"Failed to create training job: {e}")
            db.rollback()
            raise
    
    async def start_training_job(self, job_id: int, db: Session) -> bool:
        """Start a training job"""
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if not job:
                raise ValueError(f"Training job {job_id} not found")
            
            if job.status != TrainingStatusEnum.PENDING:
                raise ValueError(f"Training job {job_id} is not in pending status")
            
            # Update job status
            job.status = TrainingStatusEnum.RUNNING
            job.started_at = datetime.utcnow()
            job.current_step = "Initializing training"
            job.progress_percentage = 0.0
            db.commit()
            
            # Start training in background
            self.active_jobs[job_id] = asyncio.create_task(
                self._execute_training_job(job_id, db)
            )
            
            logger.info(f"Started training job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start training job {job_id}: {e}")
            return False
    
    async def _execute_training_job(self, job_id: int, db: Session):
        """Execute training job in background"""
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if not job:
                return
            
            # Training steps
            steps = [
                ("Preparing data", 10),
                ("Generating embeddings", 30),
                ("Training model", 40),
                ("Validating model", 15),
                ("Finalizing", 5)
            ]
            
            total_progress = 0
            job.total_steps = len(steps)
            
            for step_num, (step_name, step_weight) in enumerate(steps, 1):
                job.current_step = step_name
                job.progress_percentage = total_progress
                db.commit()
                
                logger.info(f"Training job {job_id}: {step_name}")
                
                # Simulate training step
                await asyncio.sleep(2)  # Simulated processing time
                
                # Update progress
                total_progress += step_weight
                job.progress_percentage = min(total_progress, 100)
                db.commit()
            
            # Complete training
            job.status = TrainingStatusEnum.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100.0
            job.final_score = 0.85 + (0.1 * (job.knowledge_base_tier / 3))  # Simulated score
            job.actual_duration_minutes = int(
                (job.completed_at - job.started_at).total_seconds() / 60
            )
            
            # Create model version
            version_number = f"v{job.knowledge_base_tier}.{job.id}.0"
            model_version = ModelVersion(
                training_job_id=job.id,
                version_number=version_number,
                version_name=f"{job.name} - {version_number}",
                description=f"Model trained from job: {job.name}",
                model_type=job.model_type,
                knowledge_base_tier=job.knowledge_base_tier,
                model_size_mb=256.0 + (job.knowledge_base_tier * 128),  # Simulated size
                accuracy_score=job.final_score,
                precision_score=job.final_score - 0.02,
                recall_score=job.final_score + 0.01,
                f1_score=job.final_score - 0.005,
                model_file_path=f"/models/{job.id}/{version_number}/model.bin",
                is_active=True
            )
            
            db.add(model_version)
            db.commit()
            
            logger.info(f"Training job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Training job {job_id} failed: {e}")
            job.status = TrainingStatusEnum.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        finally:
            # Clean up
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def cancel_training_job(self, job_id: int, db: Session) -> bool:
        """Cancel a running training job"""
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if not job:
                return False
            
            if job.status == TrainingStatusEnum.RUNNING:
                job.status = TrainingStatusEnum.CANCELLED
                job.completed_at = datetime.utcnow()
                db.commit()
                
                # Cancel background task
                if job_id in self.active_jobs:
                    self.active_jobs[job_id].cancel()
                    del self.active_jobs[job_id]
                
                logger.info(f"Cancelled training job {job_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel training job {job_id}: {e}")
            return False
    
    def get_training_jobs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> List[TrainingJob]:
        """Get training jobs with filters"""
        query = db.query(TrainingJob)
        
        if status:
            query = query.filter(TrainingJob.status == TrainingStatusEnum(status))
        
        if created_by:
            query = query.filter(TrainingJob.created_by == created_by)
        
        return query.order_by(desc(TrainingJob.created_at)).offset(skip).limit(limit).all()
    
    def get_model_versions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        knowledge_base_tier: Optional[int] = None,
        deployed_only: bool = False
    ) -> List[ModelVersion]:
        """Get model versions with filters"""
        query = db.query(ModelVersion)
        
        if knowledge_base_tier:
            query = query.filter(ModelVersion.knowledge_base_tier == knowledge_base_tier)
        
        if deployed_only:
            query = query.filter(ModelVersion.is_deployed == True)
        
        return query.order_by(desc(ModelVersion.created_at)).offset(skip).limit(limit).all()
    
    async def collect_feedback(
        self,
        query_id: int,
        feedback_type: str,
        rating: Optional[int],
        feedback_text: Optional[str],
        feature_used: Optional[str],
        page_url: Optional[str],
        user_id: Optional[int],
        user_agent: Optional[str],
        db: Session
    ) -> FeedbackAnalytics:
        """Collect user feedback for training improvement"""
        try:
            # Verify query exists
            query = db.query(UserQuery).filter(UserQuery.id == query_id).first()
            if not query:
                raise ValueError(f"Query {query_id} not found")
            
            # Analyze sentiment if text provided
            sentiment = None
            if feedback_text:
                sentiment = await self._analyze_sentiment(feedback_text)
            
            feedback = FeedbackAnalytics(
                user_id=user_id,
                query_id=query_id,
                feedback_type=feedback_type,
                rating=rating,
                feedback_text=feedback_text,
                feature_used=feature_used,
                page_url=page_url,
                user_agent=user_agent,
                sentiment=sentiment
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            logger.info(f"Collected feedback for query {query_id}: {feedback_type}")
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            db.rollback()
            raise
    
    async def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of feedback text"""
        try:
            # Simple sentiment analysis based on keywords
            positive_words = ['good', 'great', 'excellent', 'helpful', 'useful', 'accurate', 'clear']
            negative_words = ['bad', 'poor', 'terrible', 'unhelpful', 'useless', 'wrong', 'confusing']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    def get_training_metrics(self, db: Session) -> Dict[str, Any]:
        """Get training metrics and statistics"""
        try:
            # Training job metrics
            total_jobs = db.query(TrainingJob).count()
            active_jobs = db.query(TrainingJob).filter(
                TrainingJob.status == TrainingStatusEnum.RUNNING
            ).count()
            completed_jobs = db.query(TrainingJob).filter(
                TrainingJob.status == TrainingStatusEnum.COMPLETED
            ).count()
            failed_jobs = db.query(TrainingJob).filter(
                TrainingJob.status == TrainingStatusEnum.FAILED
            ).count()
            
            # Average completion time
            avg_duration = db.query(func.avg(TrainingJob.actual_duration_minutes)).filter(
                TrainingJob.status == TrainingStatusEnum.COMPLETED
            ).scalar() or 0
            
            # Success rate
            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            
            # Feedback metrics
            total_feedback = db.query(FeedbackAnalytics).count()
            avg_rating = db.query(func.avg(FeedbackAnalytics.rating)).filter(
                FeedbackAnalytics.rating.isnot(None)
            ).scalar() or 0
            
            # Latest model version
            latest_model = db.query(ModelVersion).order_by(desc(ModelVersion.created_at)).first()
            latest_version = latest_model.version_number if latest_model else None
            
            return {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "avg_completion_time": round(avg_duration, 2),
                "success_rate": round(success_rate, 2),
                "total_feedback": total_feedback,
                "avg_user_rating": round(avg_rating, 2),
                "latest_model_version": latest_version
            }
            
        except Exception as e:
            logger.error(f"Failed to get training metrics: {e}")
            return {}
    
    async def process_batch(
        self,
        document_ids: List[int],
        processing_type: str,
        knowledge_base_tier: int,
        batch_size: int,
        db: Session
    ) -> str:
        """Process documents in batches"""
        try:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Validate documents
            documents = db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.knowledge_base_tier <= knowledge_base_tier
            ).all()
            
            if len(documents) != len(document_ids):
                raise ValueError("Some documents are not accessible or don't exist")
            
            # Start batch processing
            self.batch_processors[batch_id] = {
                "status": "processing",
                "total_documents": len(documents),
                "processed_documents": 0,
                "progress_percentage": 0.0,
                "started_at": datetime.utcnow(),
                "estimated_completion": datetime.utcnow() + timedelta(minutes=len(documents) * 2)
            }
            
            # Process in background
            asyncio.create_task(self._execute_batch_processing(batch_id, documents, processing_type))
            
            logger.info(f"Started batch processing {batch_id} for {len(documents)} documents")
            return batch_id
            
        except Exception as e:
            logger.error(f"Failed to start batch processing: {e}")
            raise
    
    async def _execute_batch_processing(self, batch_id: str, documents: List[Document], processing_type: str):
        """Execute batch processing in background"""
        try:
            batch_info = self.batch_processors[batch_id]
            
            for i, document in enumerate(documents):
                # Simulate processing
                await asyncio.sleep(1)  # Simulated processing time
                
                # Update progress
                batch_info["processed_documents"] = i + 1
                batch_info["progress_percentage"] = ((i + 1) / len(documents)) * 100
                
                logger.debug(f"Batch {batch_id}: Processed document {document.id}")
            
            # Complete batch
            batch_info["status"] = "completed"
            batch_info["progress_percentage"] = 100.0
            batch_info["completed_at"] = datetime.utcnow()
            
            logger.info(f"Batch processing {batch_id} completed")
            
        except Exception as e:
            logger.error(f"Batch processing {batch_id} failed: {e}")
            if batch_id in self.batch_processors:
                self.batch_processors[batch_id]["status"] = "failed"
                self.batch_processors[batch_id]["error"] = str(e)
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch processing status"""
        return self.batch_processors.get(batch_id)
    
    def _estimate_training_duration(self, training_type: str, document_count: int) -> int:
        """Estimate training duration in minutes"""
        base_time = {
            "full": 60,
            "incremental": 30,
            "batch": 45,
            "real_time": 15
        }
        
        return base_time.get(training_type, 30) + (document_count * 2)


# Global training service instance
training_service = TrainingService()
