"""
Training models for POORNASREE AI Platform
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, JSON, Float, Table, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrainingStatusEnum(str, enum.Enum):
    """Training status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TrainingTypeEnum(str, enum.Enum):
    """Training type enumeration"""
    FULL = "full"
    INCREMENTAL = "incremental"
    BATCH = "batch"
    REAL_TIME = "real_time"


class ModelTypeEnum(str, enum.Enum):
    """Model type enumeration"""
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    RETRIEVAL = "retrieval"


# Association table for many-to-many relationship between TrainingJob and Document
training_job_documents = Table(
    'training_job_documents',
    Base.metadata,
    Column('training_job_id', Integer, ForeignKey('training_jobs.id'), nullable=False),
    Column('document_id', Integer, ForeignKey('documents.id'), nullable=False)
)


class TrainingJob(Base):
    """Training job model for AI model training"""
    
    __tablename__ = "training_jobs"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Job configuration
    training_type = Column(Enum(TrainingTypeEnum), nullable=False)
    model_type = Column(Enum(ModelTypeEnum), nullable=False)
    knowledge_base_tier = Column(Integer, nullable=False)  # Which KB tier to train
    
    # Training parameters
    training_config = Column(JSON, nullable=False)  # Training hyperparameters
    model_config = Column(JSON, nullable=True)  # Model configuration
    dataset_config = Column(JSON, nullable=True)  # Dataset configuration
    
    # Status and progress
    status = Column(Enum(TrainingStatusEnum), default=TrainingStatusEnum.PENDING, nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    current_step = Column(String(255), nullable=True)
    total_steps = Column(Integer, nullable=True)
    
    # Results and metrics
    training_metrics = Column(JSON, nullable=True)  # Training metrics
    validation_metrics = Column(JSON, nullable=True)  # Validation metrics
    final_score = Column(Float, nullable=True)
    
    # File paths and artifacts
    model_path = Column(String(1000), nullable=True)
    checkpoint_path = Column(String(1000), nullable=True)
    log_path = Column(String(1000), nullable=True)
    artifacts_path = Column(String(1000), nullable=True)
    
    # Resource usage
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    cpu_usage_avg = Column(Float, nullable=True)
    memory_usage_avg = Column(Float, nullable=True)
    gpu_usage_avg = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # User information
    created_by = Column(String(255), nullable=False)  # User email
    approved_by = Column(String(255), nullable=True)  # For enterprise approval workflows
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    documents = relationship("Document", secondary=training_job_documents, back_populates="training_jobs")
    model_versions = relationship("ModelVersion", back_populates="training_job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TrainingJob(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert training job to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "training_type": self.training_type.value if self.training_type else None,
            "model_type": self.model_type.value if self.model_type else None,
            "knowledge_base_tier": self.knowledge_base_tier,
            "status": self.status.value if self.status else None,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "final_score": self.final_score,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "actual_duration_minutes": self.actual_duration_minutes,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ModelVersion(Base):
    """Model version model for tracking trained models"""
    
    __tablename__ = "model_versions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    training_job_id = Column(Integer, ForeignKey("training_jobs.id"), nullable=False, index=True)
    
    # Version information
    version_number = Column(String(50), nullable=False)
    version_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Model information
    model_type = Column(Enum(ModelTypeEnum), nullable=False)
    knowledge_base_tier = Column(Integer, nullable=False)
    model_size_mb = Column(Float, nullable=True)
    
    # Performance metrics
    accuracy_score = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    perplexity_score = Column(Float, nullable=True)
    bleu_score = Column(Float, nullable=True)
    
    # Deployment information
    is_deployed = Column(Boolean, default=False, nullable=False)
    deployment_environment = Column(String(255), nullable=True)  # dev, staging, prod
    deployment_endpoint = Column(String(1000), nullable=True)
    
    # File paths
    model_file_path = Column(String(1000), nullable=False)
    config_file_path = Column(String(1000), nullable=True)
    weights_file_path = Column(String(1000), nullable=True)
    
    # Metadata
    training_data_hash = Column(String(64), nullable=True)  # Hash of training data
    model_checksum = Column(String(64), nullable=True)  # Model file checksum
    training_config = Column(JSON, nullable=True)  # Training configuration used
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    deployed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    # Relationships
    training_job = relationship("TrainingJob", back_populates="model_versions")
    evaluations = relationship("ModelEvaluation", foreign_keys="[ModelEvaluation.model_version_id]", back_populates="model_version", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ModelVersion(id={self.id}, version='{self.version_number}', deployed={self.is_deployed})>"


class ModelEvaluation(Base):
    """Model evaluation model for A/B testing and performance tracking"""
    
    __tablename__ = "model_evaluations"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False, index=True)
    
    # Evaluation information
    evaluation_name = Column(String(255), nullable=False)
    evaluation_type = Column(String(100), nullable=False)  # ab_test, performance, quality
    description = Column(Text, nullable=True)
    
    # Test configuration
    test_config = Column(JSON, nullable=False)  # Test parameters and settings
    test_dataset = Column(String(1000), nullable=True)  # Path to test dataset
    baseline_model_id = Column(Integer, ForeignKey("model_versions.id"), nullable=True)  # For comparison
    
    # Results
    evaluation_results = Column(JSON, nullable=True)  # Detailed results
    overall_score = Column(Float, nullable=True)
    recommendation = Column(Text, nullable=True)  # Evaluation recommendation
    
    # Statistical significance
    confidence_level = Column(Float, nullable=True)  # 0.95 for 95% confidence
    p_value = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), default="pending", nullable=False)
    is_significant = Column(Boolean, nullable=True)  # Statistical significance
    
    # User information
    created_by = Column(String(255), nullable=False)
    reviewed_by = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    model_version = relationship("ModelVersion", foreign_keys="[ModelEvaluation.model_version_id]", back_populates="evaluations")
    
    def __repr__(self):
        return f"<ModelEvaluation(id={self.id}, name='{self.evaluation_name}', status='{self.status}')>"


class DatasetVersion(Base):
    """Dataset version model for tracking training datasets"""
    
    __tablename__ = "dataset_versions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Dataset information
    version_number = Column(String(50), nullable=False)
    knowledge_base_tier = Column(Integer, nullable=False)
    dataset_type = Column(String(100), nullable=False)  # training, validation, test
    
    # Statistics
    total_documents = Column(Integer, nullable=False)
    total_chunks = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=True)
    avg_chunk_size = Column(Float, nullable=True)
    
    # Quality metrics
    data_quality_score = Column(Float, nullable=True)
    duplication_percentage = Column(Float, nullable=True)
    language_distribution = Column(JSON, nullable=True)
    category_distribution = Column(JSON, nullable=True)
    
    # File information
    dataset_path = Column(String(1000), nullable=False)
    dataset_size_mb = Column(Float, nullable=True)
    data_hash = Column(String(64), nullable=True)  # Dataset hash for integrity
    
    # Processing information
    preprocessing_config = Column(JSON, nullable=True)
    preprocessing_log = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    
    # User information
    created_by = Column(String(255), nullable=False)
    validated_by = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    validated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<DatasetVersion(id={self.id}, name='{self.name}', version='{self.version_number}')>"
