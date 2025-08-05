"""
Analytics models for POORNASREE AI Platform
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventTypeEnum(str, enum.Enum):
    """Analytics event type enumeration"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    QUERY_SUBMITTED = "query_submitted"
    QUERY_RESPONDED = "query_responded"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    MODEL_DEPLOYED = "model_deployed"
    ERROR_OCCURRED = "error_occurred"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    FEATURE_USED = "feature_used"


class ErrorSeverityEnum(str, enum.Enum):
    """Error severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalyticsEvent(Base):
    """Analytics event model for tracking user interactions"""
    
    __tablename__ = "analytics_events"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(Enum(EventTypeEnum), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)
    
    # User and session information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    
    # Event data
    event_data = Column(JSON, nullable=True)  # Event-specific data
    event_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(String(1000), nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Geolocation (if available)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Device information
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    operating_system = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    screen_resolution = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, type='{self.event_type}', user_id={self.user_id})>"


class UserBehaviorMetrics(Base):
    """User behavior metrics model for aggregated analytics"""
    
    __tablename__ = "user_behavior_metrics"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Session metrics
    total_sessions = Column(Integer, default=0, nullable=False)
    total_session_duration_minutes = Column(Integer, default=0, nullable=False)
    avg_session_duration_minutes = Column(Float, nullable=True)
    
    # Query metrics
    total_queries = Column(Integer, default=0, nullable=False)
    successful_queries = Column(Integer, default=0, nullable=False)
    failed_queries = Column(Integer, default=0, nullable=False)
    avg_query_response_time_ms = Column(Float, nullable=True)
    
    # Knowledge base usage
    customer_kb_queries = Column(Integer, default=0, nullable=False)
    engineer_kb_queries = Column(Integer, default=0, nullable=False)
    admin_kb_queries = Column(Integer, default=0, nullable=False)
    
    # Language preferences
    english_queries = Column(Integer, default=0, nullable=False)
    hindi_queries = Column(Integer, default=0, nullable=False)
    
    # Feature usage
    audio_input_usage = Column(Integer, default=0, nullable=False)
    audio_output_usage = Column(Integer, default=0, nullable=False)
    document_upload_count = Column(Integer, default=0, nullable=False)
    
    # Satisfaction metrics
    feedback_count = Column(Integer, default=0, nullable=False)
    avg_satisfaction_rating = Column(Float, nullable=True)
    positive_feedback_count = Column(Integer, default=0, nullable=False)
    negative_feedback_count = Column(Integer, default=0, nullable=False)
    
    # Error metrics
    error_count = Column(Integer, default=0, nullable=False)
    error_types = Column(JSON, nullable=True)  # Error type distribution
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserBehaviorMetrics(user_id={self.user_id}, date={self.date}, queries={self.total_queries})>"


class SystemMetrics(Base):
    """System metrics model for monitoring platform performance"""
    
    __tablename__ = "system_metrics"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False)  # counter, gauge, histogram
    
    # Metric data
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)
    metric_tags = Column(JSON, nullable=True)  # Additional tags for filtering
    
    # System information
    service_name = Column(String(255), nullable=True)
    instance_id = Column(String(255), nullable=True)
    environment = Column(String(50), nullable=True)  # dev, staging, prod
    
    # Timestamps
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<SystemMetrics(name='{self.metric_name}', value={self.metric_value}, timestamp={self.timestamp})>"


class ErrorLog(Base):
    """Error log model for tracking system errors"""
    
    __tablename__ = "error_logs"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    error_code = Column(String(100), nullable=True, index=True)
    error_message = Column(Text, nullable=False)
    
    # Error details
    error_type = Column(String(255), nullable=False)
    severity = Column(Enum(ErrorSeverityEnum), nullable=False, index=True)
    stack_trace = Column(Text, nullable=True)
    
    # Context information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Request details
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    request_data = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True)
    
    # System information
    service_name = Column(String(255), nullable=True)
    function_name = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)
    file_path = Column(String(1000), nullable=True)
    
    # Environment
    environment = Column(String(50), nullable=True)
    server_instance = Column(String(255), nullable=True)
    
    # Status
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, type='{self.error_type}', severity='{self.severity}')>"


class PerformanceMetrics(Base):
    """Performance metrics model for monitoring API and system performance"""
    
    __tablename__ = "performance_metrics"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    endpoint = Column(String(500), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    
    # Request information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=False)
    database_time_ms = Column(Integer, nullable=True)
    ai_processing_time_ms = Column(Integer, nullable=True)
    external_api_time_ms = Column(Integer, nullable=True)
    
    # Response information
    status_code = Column(Integer, nullable=False)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Resource usage
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    
    # Caching
    cache_hit = Column(Boolean, nullable=True)
    cache_key = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<PerformanceMetrics(endpoint='{self.endpoint}', response_time={self.response_time_ms}ms)>"


class UsageStatistics(Base):
    """Usage statistics model for business intelligence"""
    
    __tablename__ = "usage_statistics"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # User statistics
    total_users = Column(Integer, default=0, nullable=False)
    active_users = Column(Integer, default=0, nullable=False)
    new_users = Column(Integer, default=0, nullable=False)
    customer_users = Column(Integer, default=0, nullable=False)
    engineer_users = Column(Integer, default=0, nullable=False)
    admin_users = Column(Integer, default=0, nullable=False)
    
    # Session statistics
    total_sessions = Column(Integer, default=0, nullable=False)
    avg_session_duration_minutes = Column(Float, nullable=True)
    bounce_rate_percentage = Column(Float, nullable=True)
    
    # Query statistics
    total_queries = Column(Integer, default=0, nullable=False)
    successful_queries = Column(Integer, default=0, nullable=False)
    failed_queries = Column(Integer, default=0, nullable=False)
    avg_response_time_ms = Column(Float, nullable=True)
    
    # Knowledge base statistics
    customer_kb_usage = Column(Integer, default=0, nullable=False)
    engineer_kb_usage = Column(Integer, default=0, nullable=False)
    admin_kb_usage = Column(Integer, default=0, nullable=False)
    
    # Document statistics
    documents_uploaded = Column(Integer, default=0, nullable=False)
    documents_processed = Column(Integer, default=0, nullable=False)
    total_document_size_mb = Column(Float, default=0, nullable=False)
    
    # Training statistics
    training_jobs_started = Column(Integer, default=0, nullable=False)
    training_jobs_completed = Column(Integer, default=0, nullable=False)
    models_deployed = Column(Integer, default=0, nullable=False)
    
    # Feature usage
    audio_feature_usage = Column(Integer, default=0, nullable=False)
    multilingual_usage = Column(Integer, default=0, nullable=False)
    
    # Error statistics
    total_errors = Column(Integer, default=0, nullable=False)
    critical_errors = Column(Integer, default=0, nullable=False)
    
    # Business metrics
    customer_satisfaction_avg = Column(Float, nullable=True)
    support_resolution_rate = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UsageStatistics(date={self.date}, period='{self.period_type}', active_users={self.active_users})>"


class FeedbackAnalytics(Base):
    """Feedback analytics model for user satisfaction tracking"""
    
    __tablename__ = "feedback_analytics"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True)
    query_id = Column(Integer, ForeignKey("user_queries.id"), nullable=True, index=True)  # Reference to UserQuery
    
    # Feedback information
    feedback_type = Column(String(100), nullable=False)  # rating, comment, bug_report
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    feedback_text = Column(Text, nullable=True)
    
    # Context information
    feature_used = Column(String(255), nullable=True)
    page_url = Column(String(1000), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Classification
    sentiment = Column(String(20), nullable=True)  # positive, negative, neutral
    feedback_category = Column(String(255), nullable=True)  # auto-classified category
    priority = Column(String(20), nullable=True)  # low, medium, high
    
    # Response tracking
    is_responded = Column(Boolean, default=False, nullable=False)
    response_text = Column(Text, nullable=True)
    responded_by = Column(String(255), nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<FeedbackAnalytics(id={self.id}, type='{self.feedback_type}', rating={self.rating})>"
