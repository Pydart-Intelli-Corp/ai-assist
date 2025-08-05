"""
Pydantic schemas for query processing API endpoints
"""
# pylint: disable=no-self-argument,no-member,import-error,no-name-in-module
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from app.models.knowledge_base import DocumentTypeEnum


class QueryRequest(BaseModel):
    """Query request schema"""
    query: str = Field(..., min_length=1, max_length=2000, description="User query text")
    query_type: str = Field(default="general", description="Type of query")
    language: Optional[str] = Field(default="en", pattern="^(en|hi)$", description="Query language")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "query": "How do I troubleshoot machine overheating issues?",
                "query_type": "technical",
                "language": "en",
                "context": {
                    "machine_type": "industrial_pump",
                    "urgency": "high"
                }
            }
        }


class DocumentSource(BaseModel):
    """Document source reference"""
    document_id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    content_preview: str = Field(..., max_length=200, description="Content preview")


class QueryResponse(BaseModel):
    """Query response schema"""
    query_id: int = Field(..., description="Query ID for tracking")
    response: str = Field(..., description="AI-generated response")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Response confidence")
    sources: List[DocumentSource] = Field(default=[], description="Source documents")
    response_time: float = Field(..., description="Response time in seconds")
    knowledge_base_tier: int = Field(..., description="Knowledge base tier used")
    suggestions: List[str] = Field(default=[], description="Related query suggestions")
    
    class Config:
        schema_extra = {
            "example": {
                "query_id": 123,
                "response": "For machine overheating issues, first check the cooling system...",
                "confidence_score": 0.85,
                "sources": [
                    {
                        "document_id": 456,
                        "title": "Machine Cooling Systems Guide",
                        "relevance_score": 0.92,
                        "content_preview": "This guide covers troubleshooting steps for cooling systems..."
                    }
                ],
                "response_time": 2.34,
                "knowledge_base_tier": 2,
                "suggestions": [
                    "How to maintain cooling systems?",
                    "Preventive maintenance for overheating",
                    "Temperature monitoring best practices"
                ]
            }
        }


class QueryHistoryResponse(BaseModel):
    """Query history item schema"""
    query_id: int = Field(..., description="Query ID")
    query_text: str = Field(..., description="Original query text")
    query_type: str = Field(..., description="Query type")
    response_summary: Optional[str] = Field(None, description="Response summary")
    created_at: datetime = Field(..., description="Query timestamp")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    status: str = Field(..., description="Query processing status")
    
    class Config:
        schema_extra = {
            "example": {
                "query_id": 123,
                "query_text": "How to troubleshoot pump issues?",
                "query_type": "technical",
                "response_summary": "For pump troubleshooting, first check pressure levels...",
                "created_at": "2025-08-05T10:30:00Z",
                "response_time": 2.1,
                "status": "completed"
            }
        }


class KnowledgeBaseSearchRequest(BaseModel):
    """Knowledge base search request"""
    query: Optional[str] = Field(None, max_length=500, description="Search query")
    document_type: Optional[DocumentTypeEnum] = Field(None, description="Document type filter")
    category: Optional[str] = Field(None, max_length=100, description="Category filter")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Result offset")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "maintenance procedures",
                "document_type": "manual",
                "category": "technical",
                "limit": 10,
                "offset": 0
            }
        }


class DocumentSearchResult(BaseModel):
    """Document search result item"""
    id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content_preview: str = Field(..., description="Content preview")
    document_type: DocumentTypeEnum = Field(..., description="Document type")
    category: Optional[str] = Field(None, description="Document category")
    created_at: datetime = Field(..., description="Document creation date")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Search relevance score")


class KnowledgeBaseSearchResponse(BaseModel):
    """Knowledge base search response"""
    documents: List[DocumentSearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    has_more: bool = Field(..., description="Whether more results are available")
    
    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": 123,
                        "title": "Pump Maintenance Manual",
                        "content_preview": "This manual covers routine maintenance procedures...",
                        "document_type": "manual",
                        "category": "maintenance",
                        "created_at": "2025-07-01T00:00:00Z",
                        "relevance_score": 0.95
                    }
                ],
                "total_count": 45,
                "has_more": True
            }
        }


class DocumentSuggestionResponse(BaseModel):
    """Document suggestion response"""
    suggestions: List[DocumentSearchResult] = Field(..., description="Suggested documents")
    reason: str = Field(..., description="Suggestion reason")
    
    class Config:
        schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "id": 456,
                        "title": "Troubleshooting Guide",
                        "content_preview": "Common issues and solutions...",
                        "document_type": "guide",
                        "category": "troubleshooting",
                        "created_at": "2025-07-15T00:00:00Z",
                        "relevance_score": 0.88
                    }
                ],
                "reason": "Based on your recent queries about machine maintenance"
            }
        }
