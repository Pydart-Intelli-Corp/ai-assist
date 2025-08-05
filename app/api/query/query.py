"""
Query processing API endpoints for POORNASREE AI Platform
Handles AI-powered query processing and knowledge base interactions
"""
# pylint: disable=import-error,no-name-in-module,trailing-whitespace,logging-fstring-interpolation
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import security_manager, get_user_role
from app.core.config import settings, UserRole, KnowledgeBaseTier
from app.models.user import User, UserQuery, UserRoleEnum
from app.models.knowledge_base import Document, KnowledgeBaseTierEnum, DocumentStatusEnum
from app.services.ai_service import ai_service
from app.api.query.schemas import (
    QueryRequest,
    QueryResponse,
    QueryHistoryResponse,
    KnowledgeBaseSearchRequest,
    KnowledgeBaseSearchResponse,
    DocumentSuggestionResponse
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/query", tags=["Query Processing"])
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
        
    except Exception as e:
        logger.error("Token verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def determine_knowledge_base_tier(user_role: UserRoleEnum) -> KnowledgeBaseTierEnum:
    """Determine knowledge base access tier based on user role"""
    role_to_tier = {
        UserRoleEnum.CUSTOMER: KnowledgeBaseTierEnum.CUSTOMER,
        UserRoleEnum.ENGINEER: KnowledgeBaseTierEnum.ENGINEER,
        UserRoleEnum.ADMIN: KnowledgeBaseTierEnum.ADMIN
    }
    return role_to_tier.get(user_role, KnowledgeBaseTierEnum.CUSTOMER)


@router.post("/ask", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process AI-powered query with knowledge base integration
    """
    try:
        logger.info("Processing query from user: %s", current_user.email)
        
        # Determine knowledge base tier based on user role
        kb_tier = determine_knowledge_base_tier(current_user.role)
        
        # Record the query in database
        user_query = UserQuery(
            user_id=current_user.id,
            query_text=request.query,
            query_type=request.query_type,
            knowledge_base_tier=kb_tier,
            query_metadata={
                "ip_address": req.client.host if req.client else None,
                "user_agent": req.headers.get("user-agent"),
                "language": request.language or "en",
                "context": request.context
            }
        )
        
        db.add(user_query)
        db.commit()
        db.refresh(user_query)
        
        # Process query using AI service
        ai_result = await ai_service.process_query(
            query=request.query,
            user_role=current_user.role.value,
            knowledge_base_tier=kb_tier.value
        )
        
        # Update query with response
        user_query.ai_response = ai_result.get("response", "No response generated")
        user_query.response_time = ai_result.get("processing_time", 0.0)
        user_query.status = "completed"
        
        db.commit()
        
        logger.info("Query processed successfully for user: %s", current_user.email)
        
        return QueryResponse(
            query_id=user_query.id,
            response=ai_result.get("response", "No response generated"),
            confidence_score=ai_result.get("confidence", 0.5),
            sources=ai_result.get("sources", []),
            response_time=ai_result.get("processing_time", 0.0),
            knowledge_base_tier=kb_tier.value,
            suggestions=await get_query_suggestions(request.query, current_user.role, db)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query processing error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/history", response_model=List[QueryHistoryResponse])
async def get_query_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's query history
    """
    try:
        queries = db.query(UserQuery).filter(
            UserQuery.user_id == current_user.id
        ).order_by(
            desc(UserQuery.created_at)
        ).offset(offset).limit(limit).all()
        
        return [
            QueryHistoryResponse(
                query_id=query.id,
                query_text=query.query_text,
                query_type=query.query_type,
                response_summary=query.ai_response[:200] + "..." if query.ai_response and len(query.ai_response) > 200 else query.ai_response,
                created_at=query.created_at,
                response_time=query.response_time,
                status=query.status
            )
            for query in queries
        ]
        
    except Exception as e:
        logger.error("Error fetching query history: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/search", response_model=KnowledgeBaseSearchResponse)
async def search_knowledge_base(
    request: KnowledgeBaseSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search knowledge base documents
    """
    try:
        kb_tier = determine_knowledge_base_tier(current_user.role)
        
        # Build query based on knowledge base tier
        query = db.query(Document).filter(
            Document.knowledge_base_tier <= kb_tier.value,
            Document.status == DocumentStatusEnum.PROCESSED
        )
        
        # Apply search filters
        if request.query:
            query = query.filter(
                Document.title.contains(request.query) |
                Document.content.contains(request.query)
            )
        
        if request.document_type:
            query = query.filter(Document.document_type == request.document_type)
        
        if request.category:
            query = query.filter(Document.category == request.category)
        
        # Apply pagination
        total_count = query.count()
        documents = query.offset(request.offset).limit(request.limit).all()
        
        return KnowledgeBaseSearchResponse(
            documents=[
                {
                    "id": doc.id,
                    "title": doc.title,
                    "content_preview": doc.content[:300] + "..." if doc.content and len(doc.content) > 300 else doc.content,
                    "document_type": doc.document_type,
                    "category": doc.category,
                    "created_at": doc.created_at,
                    "relevance_score": 0.8  # TODO: Calculate actual relevance
                }
                for doc in documents
            ],
            total_count=total_count,
            has_more=total_count > request.offset + request.limit
        )
        
    except Exception as e:
        logger.error("Knowledge base search error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def get_query_suggestions(
    query: str,
    user_role: UserRoleEnum,
    db: Session
) -> List[str]:
    """
    Get related query suggestions using AI service
    """
    try:
        # Get recent queries from same user role for context
        recent_queries = db.query(UserQuery.query_text)\
            .join(User)\
            .filter(User.role == user_role)\
            .filter(UserQuery.status == "completed")\
            .order_by(desc(UserQuery.created_at))\
            .limit(10)\
            .all()
        
        # Use AI service to generate contextual suggestions
        context_queries = [q[0] for q in recent_queries if q[0] != query]
        
        # Generate suggestions based on query keywords and role
        query_words = query.lower().split()
        role_based_suggestions = {
            UserRoleEnum.CUSTOMER: [
                f"How to {' '.join(query_words[:2])}?",
                f"Troubleshooting {query_words[-1] if query_words else 'issues'}",
                "Step-by-step instructions",
                "Common problems and solutions"
            ],
            UserRoleEnum.ENGINEER: [
                f"Technical analysis of {' '.join(query_words[:2])}",
                f"Diagnostic procedures for {query_words[-1] if query_words else 'equipment'}",
                "Maintenance protocols",
                "Performance optimization"
            ],
            UserRoleEnum.ADMIN: [
                f"System configuration for {' '.join(query_words[:2])}",
                f"Administrative controls for {query_words[-1] if query_words else 'system'}",
                "User management and permissions",
                "Analytics and reporting"
            ]
        }
        
        return role_based_suggestions.get(user_role, [
            "General troubleshooting",
            "Best practices",
            "Documentation guides",
            "Support resources"
        ])
        
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}")
        return [
            "Related topics",
            "Troubleshooting guides", 
            "Best practices",
            "Documentation"
        ]
    
    return suggestions[:3]  # Return top 3 suggestions
