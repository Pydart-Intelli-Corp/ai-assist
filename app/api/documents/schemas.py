"""
Document API schemas for POORNASREE AI Platform
"""
# pylint: disable=import-error,no-name-in-module,trailing-whitespace,no-self-argument
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator

from app.models.knowledge_base import DocumentTypeEnum, DocumentStatusEnum


class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    document_id: int
    title: str
    filename: str
    file_size: int
    document_type: DocumentTypeEnum
    knowledge_base_tier: int
    status: DocumentStatusEnum
    upload_timestamp: datetime
    processing_queue_position: int


class DocumentListItem(BaseModel):
    """Document item in list view"""
    document_id: int
    title: str
    filename: str
    document_type: DocumentTypeEnum
    category: Optional[str]
    knowledge_base_tier: int
    status: DocumentStatusEnum
    file_size: int
    created_at: datetime
    processed_at: Optional[datetime]


class DocumentListResponse(BaseModel):
    """Response for document list"""
    documents: List[DocumentListItem]
    total_count: int
    has_more: bool


class DocumentChunkPreview(BaseModel):
    """Document chunk preview"""
    chunk_id: int
    content_preview: str
    chunk_index: int


class DocumentDetailResponse(BaseModel):
    """Detailed document information"""
    document_id: int
    title: str
    filename: str
    description: Optional[str]
    document_type: DocumentTypeEnum
    category: Optional[str]
    knowledge_base_tier: int
    status: DocumentStatusEnum
    file_size: int
    mime_type: str
    created_at: datetime
    processed_at: Optional[datetime]
    content_preview: Optional[str]
    chunks_count: int
    chunks_preview: List[DocumentChunkPreview]
    metadata: Optional[Dict[str, Any]]


class SortByEnum(str, Enum):
    """Sort options for document search"""
    RELEVANCE = "relevance"
    DATE = "date"
    TITLE = "title"


class DocumentSearchRequest(BaseModel):
    """Request for document search"""
    query: Optional[str] = Field(None, description="Search query")
    document_type: Optional[DocumentTypeEnum] = Field(None, description="Filter by document type")
    category: Optional[str] = Field(None, description="Filter by category")
    status: Optional[DocumentStatusEnum] = Field(None, description="Filter by status")
    knowledge_base_tier: Optional[int] = Field(None, description="Filter by knowledge base tier")
    date_from: Optional[datetime] = Field(None, description="Filter documents from this date")
    date_to: Optional[datetime] = Field(None, description="Filter documents to this date")
    sort_by: SortByEnum = Field(SortByEnum.DATE, description="Sort results by")
    limit: int = Field(20, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    @validator('knowledge_base_tier')
    def validate_knowledge_base_tier(cls, v):
        """Validate knowledge base tier"""
        if v is not None and (v < 1 or v > 3):
            raise ValueError('Knowledge base tier must be between 1 and 3')
        return v


class DocumentSearchItem(BaseModel):
    """Document item in search results"""
    document_id: int
    title: str
    filename: str
    content_preview: Optional[str]
    document_type: DocumentTypeEnum
    category: Optional[str]
    knowledge_base_tier: int
    status: DocumentStatusEnum
    created_at: datetime
    relevance_score: float
    highlight_snippets: List[str]


class DocumentSearchResponse(BaseModel):
    """Response for document search"""
    documents: List[DocumentSearchItem]
    total_count: int
    has_more: bool
    search_time: float
    filters_applied: Dict[str, Any]


class DocumentUpdateRequest(BaseModel):
    """Request to update document metadata"""
    title: Optional[str] = Field(None, description="New document title")
    description: Optional[str] = Field(None, description="New document description")
    category: Optional[str] = Field(None, description="New document category")
    knowledge_base_tier: Optional[int] = Field(None, description="New knowledge base tier")
    
    @validator('knowledge_base_tier')
    def validate_knowledge_base_tier(cls, v):
        """Validate knowledge base tier"""
        if v is not None and (v < 1 or v > 3):
            raise ValueError('Knowledge base tier must be between 1 and 3')
        return v


class DocumentCategoryResponse(BaseModel):
    """Document category information"""
    category_id: int
    name: str
    description: Optional[str]
    document_count: int
    icon: Optional[str]


class DocumentStatsResponse(BaseModel):
    """Document statistics"""
    total_documents: int
    processed_documents: int
    pending_documents: int
    documents_by_type: Dict[str, int]
    recent_uploads: int
    knowledge_base_tier: int
    accessible_tiers: List[int]


class ProcessingStatusResponse(BaseModel):
    """Document processing status"""
    document_id: int
    status: DocumentStatusEnum
    progress_percentage: int
    processing_stage: str
    estimated_completion: Optional[datetime]
    error_message: Optional[str]


class BulkActionRequest(BaseModel):
    """Request for bulk actions on documents"""
    document_ids: List[int] = Field(..., description="List of document IDs")
    action: str = Field(..., description="Action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    
    @validator('document_ids')
    def validate_document_ids(cls, v):
        """Validate document IDs list"""
        if not v or len(v) == 0:
            raise ValueError('At least one document ID is required')
        if len(v) > 100:
            raise ValueError('Maximum 100 documents can be processed at once')
        return v


class BulkActionResponse(BaseModel):
    """Response for bulk actions"""
    successful_count: int
    failed_count: int
    successful_ids: List[int]
    failed_ids: List[int]
    errors: Dict[int, str]
