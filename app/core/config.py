"""
Configuration management for POORNASREE AI Platform
"""
# pylint: disable=import-error,no-name-in-module
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_version: str = Field(default="v1", alias="API_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Database Configuration
    database_url: str = Field(alias="DATABASE_URL")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")
    
    # JWT Configuration
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Admin Configuration
    admin_email: str = Field(alias="ADMIN_EMAIL")
    admin_otp_expire_minutes: int = Field(default=5, alias="ADMIN_OTP_EXPIRE_MINUTES")
    
    # Weaviate Configuration
    weaviate_url: str = Field(alias="WEAVIATE_URL")
    weaviate_grpc_url: Optional[str] = Field(default=None, alias="WEAVIATE_GRPC_URL")
    weaviate_api_key: str = Field(alias="WEAVIATE_API_KEY")
    weaviate_cluster_name: Optional[str] = Field(default=None, alias="WEAVIATE_CLUSTER_NAME")
    
    # Google AI Configuration
    google_api_key: str = Field(alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash-lite", alias="GEMINI_MODEL")
    
    # Email Configuration
    smtp_host: str = Field(alias="SMTP_HOST")
    smtp_port: int = Field(alias="SMTP_PORT")
    smtp_username: str = Field(alias="SMTP_USERNAME")
    smtp_password: str = Field(alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")
    
    # File Upload Configuration
    max_file_size: str = Field(default="50MB", alias="MAX_FILE_SIZE")
    allowed_file_types: str = Field(default="pdf,doc,docx,txt,jpg,jpeg,png,mp3,wav", alias="ALLOWED_FILE_TYPES")
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    
    # Knowledge Base Configuration
    customer_kb_class: str = Field(default="CustomerKnowledgeBase", alias="CUSTOMER_KB_CLASS")
    engineer_kb_class: str = Field(default="EngineerKnowledgeBase", alias="ENGINEER_KB_CLASS")
    admin_kb_class: str = Field(default="AdminKnowledgeBase", alias="ADMIN_KB_CLASS")
    master_kb_class: str = Field(default="MasterKnowledgeBase", alias="MASTER_KB_CLASS")
    
    # Vector Configuration
    vector_embedding_size: int = Field(default=1536, alias="VECTOR_EMBEDDING_SIZE")
    
    # Audio Configuration
    audio_sample_rate: int = Field(default=16000, alias="AUDIO_SAMPLE_RATE")
    audio_channels: int = Field(default=1, alias="AUDIO_CHANNELS")
    tts_language_en: str = Field(default="en", alias="TTS_LANGUAGE_EN")
    tts_language_hi: str = Field(default="hi", alias="TTS_LANGUAGE_HI")
    
    # Analytics Configuration
    analytics_retention_days: int = Field(default=365, alias="ANALYTICS_RETENTION_DAYS")
    enable_analytics: bool = Field(default=True, alias="ENABLE_ANALYTICS")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, alias="RATE_LIMIT_BURST")
    
    # Multi-language Support
    default_language: str = Field(default="en", alias="DEFAULT_LANGUAGE")
    supported_languages: List[str] = Field(default=["en", "hi"], alias="SUPPORTED_LANGUAGES")
    
    # White-label Configuration
    platform_name: str = Field(default="POORNASREE AI", alias="PLATFORM_NAME")
    platform_version: str = Field(default="2.0", alias="PLATFORM_VERSION")
    enable_white_label: bool = Field(default=True, alias="ENABLE_WHITE_LABEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size string to bytes"""
        size_str = str(self.max_file_size).upper()
        if size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert allowed file types string to list"""
        return [ext.strip().lower() for ext in str(self.allowed_file_types).split(",")]


# Global settings instance
settings = Settings()


# Knowledge Base Access Levels
class KnowledgeBaseAccess:
    """Knowledge base access level constants"""
    CUSTOMER = "customer"
    ENGINEER = "engineer"
    ADMIN = "admin"


# User Roles
class UserRole:
    """User role constants"""
    CUSTOMER = "customer"
    ENGINEER = "engineer"
    ADMIN = "admin"


# Knowledge Base Tiers
class KnowledgeBaseTier:
    """Knowledge base tier constants"""
    TIER_1_CUSTOMER = 1  # Customer knowledge base
    TIER_2_ENGINEER = 2  # Service engineer knowledge base
    TIER_3_ADMIN = 3     # Admin knowledge base
