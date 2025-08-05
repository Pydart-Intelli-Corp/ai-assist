"""
Models package for POORNASREE AI Platform
"""

# Import all models to ensure they are registered with SQLAlchemy
from .user import (
    User,
    UserSession,
    UserQuery,
    UserPreferences,
    UserRoleEnum,
    UserStatusEnum,
    LanguageEnum
)

from .knowledge_base import (
    Document,
    DocumentChunk,
    KnowledgeBaseStats,
    DocumentCategory,
    SearchQuery,
    DocumentTypeEnum,
    DocumentStatusEnum,
    KnowledgeBaseTierEnum
)

from .training import (
    TrainingJob,
    ModelVersion,
    ModelEvaluation,
    DatasetVersion,
    TrainingStatusEnum,
    TrainingTypeEnum,
    ModelTypeEnum,
    training_job_documents
)

from .analytics import (
    AnalyticsEvent,
    UserBehaviorMetrics,
    SystemMetrics,
    ErrorLog,
    PerformanceMetrics,
    UsageStatistics,
    FeedbackAnalytics,
    EventTypeEnum,
    ErrorSeverityEnum
)

__all__ = [
    # User models
    "User",
    "UserSession", 
    "UserQuery",
    "UserPreferences",
    "UserRoleEnum",
    "UserStatusEnum",
    "LanguageEnum",
    
    # Knowledge base models
    "Document",
    "DocumentChunk",
    "KnowledgeBaseStats",
    "DocumentCategory",
    "SearchQuery",
    "DocumentTypeEnum",
    "DocumentStatusEnum",
    "KnowledgeBaseTierEnum",
    
    # Training models
    "TrainingJob",
    "ModelVersion",
    "ModelEvaluation",
    "DatasetVersion",
    "TrainingStatusEnum",
    "TrainingTypeEnum",
    "ModelTypeEnum",
    "training_job_documents",
    
    # Analytics models
    "AnalyticsEvent",
    "UserBehaviorMetrics",
    "SystemMetrics",
    "ErrorLog",
    "PerformanceMetrics",
    "UsageStatistics",
    "FeedbackAnalytics",
    "EventTypeEnum",
    "ErrorSeverityEnum",
]
