"""
User models for POORNASREE AI Platform
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRoleEnum(str, enum.Enum):
    """User role enumeration"""
    CUSTOMER = "customer"
    ENGINEER = "engineer"
    ADMIN = "admin"


class UserStatusEnum(str, enum.Enum):
    """User status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    ACTIVE = "active"


class LanguageEnum(str, enum.Enum):
    """Supported language enumeration"""
    ENGLISH = "en"
    HINDI = "hi"


class User(Base):
    """User model for authentication and profile management"""
    
    __tablename__ = "users"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.CUSTOMER, nullable=False)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.ACTIVE, nullable=False)
    
    # Authentication fields
    hashed_password = Column(String(255), nullable=True)  # Nullable for OTP-only admin access
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile fields
    preferred_language = Column(Enum(LanguageEnum), default=LanguageEnum.ENGLISH, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Engineer-specific fields
    company_name = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    experience_years = Column(Integer, nullable=True)
    certifications = Column(JSON, nullable=True)  # Store as JSON array
    expertise_areas = Column(JSON, nullable=True)  # Store as JSON array
    employee_id = Column(String(100), nullable=True)
    manager_email = Column(String(255), nullable=True)
    
    # Registration metadata
    registration_data = Column(JSON, nullable=True)  # Store additional registration info
    approval_notes = Column(Text, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("UserQuery", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "role": self.role.value if self.role else None,
            "status": self.status.value if self.status else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "preferred_language": self.preferred_language.value if self.preferred_language else None,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "department": self.department,
            "experience_years": self.experience_years,
            "certifications": self.certifications,
            "expertise_areas": self.expertise_areas,
            "employee_id": self.employee_id,
            "manager_email": self.manager_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


class UserSession(Base):
    """User session model for tracking active sessions"""
    
    __tablename__ = "user_sessions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True, nullable=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    location_info = Column(JSON, nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    logged_out_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class UserQuery(Base):
    """User query model for tracking AI interactions"""
    
    __tablename__ = "user_queries"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for anonymous queries
    session_id = Column(String(255), index=True, nullable=True)
    
    # Query content
    query_text = Column(Text, nullable=False)
    query_language = Column(Enum(LanguageEnum), default=LanguageEnum.ENGLISH, nullable=False)
    query_type = Column(String(50), nullable=True)  # text, audio, image
    
    # AI Response
    response_text = Column(Text, nullable=True)
    response_language = Column(Enum(LanguageEnum), default=LanguageEnum.ENGLISH, nullable=False)
    response_type = Column(String(50), nullable=True)  # text, audio
    
    # Knowledge base access
    knowledge_base_tier = Column(Integer, nullable=False)  # 1=Customer, 2=Engineer, 3=Admin
    documents_referenced = Column(JSON, nullable=True)  # Document IDs used in response
    
    # Query metadata
    processing_time_ms = Column(Integer, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 rating
    feedback_text = Column(Text, nullable=True)
    
    # Analytics fields
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    responded_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="queries")
    
    def __repr__(self):
        return f"<UserQuery(id={self.id}, user_id={self.user_id}, kb_tier={self.knowledge_base_tier})>"


class UserPreferences(Base):
    """User preferences model for customization settings"""
    
    __tablename__ = "user_preferences"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # UI Preferences
    theme = Column(String(20), default="light", nullable=False)  # light, dark, auto
    language = Column(Enum(LanguageEnum), default=LanguageEnum.ENGLISH, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Audio Preferences
    enable_audio_input = Column(Boolean, default=True, nullable=False)
    enable_audio_output = Column(Boolean, default=True, nullable=False)
    audio_speed = Column(Integer, default=1, nullable=False)  # 1-3 speed multiplier
    audio_voice = Column(String(50), default="default", nullable=False)
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    sms_notifications = Column(Boolean, default=False, nullable=False)
    
    # Privacy Preferences
    analytics_tracking = Column(Boolean, default=True, nullable=False)
    session_recording = Column(Boolean, default=False, nullable=False)
    data_sharing = Column(Boolean, default=False, nullable=False)
    
    # Custom preferences (JSON)
    custom_settings = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id}, theme='{self.theme}')>"
