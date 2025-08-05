"""
Knowledge base models for POORNASREE AI Platform
"""
# pylint: disable=not-callable,no-member,import-error,no-name-in-module,trailing-whitespace,unused-import,wrong-import-order
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, JSON, Float, LargeBinary, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentTypeEnum(str, enum.Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class DocumentStatusEnum(str, enum.Enum):
    """Document status enumeration"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class KnowledgeBaseTierEnum(int, enum.Enum):
    """Knowledge base tier enumeration"""
    CUSTOMER = 1
    ENGINEER = 2
    ADMIN = 3


class LanguageEnum(str, enum.Enum):
    """Language enumeration"""
    ENGLISH = "en"
    HINDI = "hi"
    MIXED = "mixed"


class Document(Base):
    """Document model for knowledge base storage"""
    
    __tablename__ = "documents"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(Enum(DocumentTypeEnum), nullable=False)
    mime_type = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    
    # Content information
    extracted_text = Column(Text, nullable=True)
    language = Column(Enum(LanguageEnum), default=LanguageEnum.ENGLISH, nullable=False)
    word_count = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Knowledge base classification
    knowledge_base_tier = Column(Enum(KnowledgeBaseTierEnum), nullable=False)
    category = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    keywords = Column(JSON, nullable=True)  # Extracted keywords
    
    # Processing status
    status = Column(Enum(DocumentStatusEnum), default=DocumentStatusEnum.UPLOADED, nullable=False)
    processing_log = Column(JSON, nullable=True)  # Processing steps and errors
    
    # Vector embedding information
    is_vectorized = Column(Boolean, default=False, nullable=False)
    vector_count = Column(Integer, default=0, nullable=False)
    weaviate_document_id = Column(String(255), nullable=True, index=True)
    
    # Document metadata
    doc_metadata = Column(JSON, nullable=True)  # Additional document metadata
    source_url = Column(String(1000), nullable=True)
    version = Column(String(50), default="1.0", nullable=False)
    
    # Access control
    uploaded_by = Column(String(255), nullable=False)  # User email
    is_public = Column(Boolean, default=False, nullable=False)
    access_permissions = Column(JSON, nullable=True)  # User/role permissions
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    training_jobs = relationship("TrainingJob", secondary="training_job_documents", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', tier={self.knowledge_base_tier})>"
    
    def to_dict(self):
        """Convert document to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_type": self.file_type.value if self.file_type else None,
            "mime_type": self.mime_type,
            "language": self.language.value if self.language else None,
            "word_count": self.word_count,
            "page_count": self.page_count,
            "knowledge_base_tier": self.knowledge_base_tier.value if self.knowledge_base_tier else None,
            "category": self.category,
            "tags": self.tags,
            "keywords": self.keywords,
            "status": self.status.value if self.status else None,
            "is_vectorized": self.is_vectorized,
            "vector_count": self.vector_count,
            "version": self.version,
            "uploaded_by": self.uploaded_by,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


class DocumentChunk(Base):
    """Document chunk model for vector storage"""
    
    __tablename__ = "document_chunks"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Chunk information
    chunk_index = Column(Integer, nullable=False)  # Order within document
    chunk_text = Column(Text, nullable=False)
    chunk_size = Column(Integer, nullable=False)  # Character count
    
    # Position information
    start_position = Column(Integer, nullable=True)  # Start character position
    end_position = Column(Integer, nullable=True)  # End character position
    page_number = Column(Integer, nullable=True)  # For PDF documents
    
    # Vector information
    weaviate_chunk_id = Column(String(255), nullable=True, index=True)
    embedding_model = Column(String(255), nullable=True)
    embedding_dimension = Column(Integer, nullable=True)
    
    # Metadata
    chunk_metadata = Column(JSON, nullable=True)  # Chunk-specific metadata
    language = Column(Enum(LanguageEnum), default=LanguageEnum.ENGLISH, nullable=False)
    
    # Quality metrics
    readability_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class KnowledgeBaseStats(Base):
    """Knowledge base statistics model"""
    
    __tablename__ = "knowledge_base_stats"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    knowledge_base_tier = Column(Enum(KnowledgeBaseTierEnum), nullable=False, index=True)
    
    # Document statistics
    total_documents = Column(Integer, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    total_words = Column(Integer, default=0, nullable=False)
    total_size_bytes = Column(Integer, default=0, nullable=False)
    
    # Type distribution
    pdf_count = Column(Integer, default=0, nullable=False)
    doc_count = Column(Integer, default=0, nullable=False)
    txt_count = Column(Integer, default=0, nullable=False)
    image_count = Column(Integer, default=0, nullable=False)
    audio_count = Column(Integer, default=0, nullable=False)
    
    # Language distribution
    english_count = Column(Integer, default=0, nullable=False)
    hindi_count = Column(Integer, default=0, nullable=False)
    mixed_count = Column(Integer, default=0, nullable=False)
    
    # Quality metrics
    average_readability = Column(Float, nullable=True)
    average_relevance = Column(Float, nullable=True)
    
    # Usage statistics
    total_queries = Column(Integer, default=0, nullable=False)
    successful_queries = Column(Integer, default=0, nullable=False)
    average_response_time = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    stats_date = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<KnowledgeBaseStats(tier={self.knowledge_base_tier}, total_docs={self.total_documents})>"


class DocumentCategory(Base):
    """Document category model for organization"""
    
    __tablename__ = "document_categories"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy
    parent_id = Column(Integer, ForeignKey("document_categories.id"), nullable=True, index=True)
    path = Column(String(1000), nullable=False)  # Full category path
    level = Column(Integer, default=0, nullable=False)
    
    # Knowledge base access
    knowledge_base_tiers = Column(JSON, nullable=False)  # Which tiers can access
    
    # Metadata
    icon = Column(String(255), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    document_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DocumentCategory(id={self.id}, name='{self.name}', level={self.level})>"


class SearchQuery(Base):
    """Search query model for analytics and optimization"""
    
    __tablename__ = "search_queries"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_normalized = Column(Text, nullable=False)  # Normalized for analysis
    query_language = Column(Enum(LanguageEnum), default=LanguageEnum.ENGLISH, nullable=False)
    query_intent = Column(String(255), nullable=True)  # Detected intent
    
    # Search parameters
    knowledge_base_tier = Column(Enum(KnowledgeBaseTierEnum), nullable=False)
    search_filters = Column(JSON, nullable=True)  # Applied filters
    search_scope = Column(JSON, nullable=True)  # Categories, tags, etc.
    
    # Results
    results_count = Column(Integer, default=0, nullable=False)
    top_result_score = Column(Float, nullable=True)
    results_data = Column(JSON, nullable=True)  # Top results metadata
    
    # Performance
    search_time_ms = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    total_time_ms = Column(Integer, nullable=True)
    
    # User interaction
    clicked_results = Column(JSON, nullable=True)  # Which results were clicked
    user_satisfaction = Column(Integer, nullable=True)  # 1-5 rating
    user_feedback = Column(Text, nullable=True)
    
    # Analytics
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(String(1000), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SearchQuery(id={self.id}, tier={self.knowledge_base_tier}, results={self.results_count})>"
