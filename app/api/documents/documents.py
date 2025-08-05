"""
Document management API endpoints for POORNASREE AI Platform
Handles file upload, processing, search, and knowledge base management
"""
# pylint: disable=import-error,no-name-in-module,trailing-whitespace,logging-fstring-interpolation
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.core.database import get_db
from app.core.security import security_manager
from app.core.config import settings
from app.models.user import User, UserRoleEnum
from app.models.knowledge_base import (
    Document, DocumentChunk, DocumentCategory, KnowledgeBaseStats,
    DocumentTypeEnum, DocumentStatusEnum, KnowledgeBaseTierEnum
)
from app.api.documents.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentUpdateRequest,
    DocumentCategoryResponse,
    DocumentStatsResponse,
    ProcessingStatusResponse
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/documents", tags=["Document Management"])
security = HTTPBearer()

# Allowed file types and sizes
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'txt': 'text/plain',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav'
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


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


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file"""
    # Check file extension
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"File type .{file_ext} not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS.keys())}"
    
    # Check file size (this is approximate as we haven't read the file yet)
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, ""


def get_upload_path(user_id: int, filename: str) -> str:
    """Generate upload path for file"""
    upload_dir = Path(settings.upload_dir) / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename to avoid conflicts
    file_ext = filename.split('.')[-1] if '.' in filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    
    return str(upload_dir / unique_filename)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    knowledge_base_tier: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document to the knowledge base
    """
    try:
        logger.info("Document upload request from user: %s", current_user.email)
        
        # Validate file
        is_valid, error_message = validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Determine knowledge base tier
        user_kb_tier = determine_knowledge_base_tier(current_user.role)
        
        # Admin can specify tier, others use their role tier
        if current_user.role == UserRoleEnum.ADMIN and knowledge_base_tier is not None:
            kb_tier = KnowledgeBaseTierEnum(knowledge_base_tier)
        else:
            kb_tier = user_kb_tier
        
        # Save file
        file_path = get_upload_path(current_user.id, file.filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            buffer.write(content)
        
        # Determine document type
        file_ext = file.filename.split('.')[-1].lower()
        doc_type = DocumentTypeEnum.TXT  # Default
        if file_ext in ['pdf']:
            doc_type = DocumentTypeEnum.PDF
        elif file_ext in ['doc']:
            doc_type = DocumentTypeEnum.DOC
        elif file_ext in ['docx']:
            doc_type = DocumentTypeEnum.DOCX
        elif file_ext in ['jpg', 'jpeg', 'png']:
            doc_type = DocumentTypeEnum.IMAGE
        elif file_ext in ['mp3', 'wav']:
            doc_type = DocumentTypeEnum.AUDIO
        elif file_ext == 'txt':
            doc_type = DocumentTypeEnum.TXT
        
        # Create document record
        document = Document(
            title=title or file.filename,
            filename=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            file_type=doc_type,
            mime_type=ALLOWED_EXTENSIONS.get(file_ext, 'application/octet-stream'),
            file_hash="",  # TODO: Calculate SHA-256 hash
            knowledge_base_tier=kb_tier,
            category=category,
            description=description,
            uploaded_by=current_user.email,
            status=DocumentStatusEnum.UPLOADED,
            doc_metadata={
                "original_filename": file.filename,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "user_agent": None,  # Can be added if needed
                "file_extension": file_ext
            }
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # TODO: Queue document for processing (text extraction, vectorization)
        await queue_document_processing(document.id, db)
        
        logger.info("Document uploaded successfully: %s", document.id)
        
        return DocumentUploadResponse(
            document_id=document.id,
            title=document.title,
            filename=document.filename,
            file_size=document.file_size,
            document_type=document.file_type,
            knowledge_base_tier=document.knowledge_base_tier.value,
            status=document.status,
            upload_timestamp=document.created_at,
            processing_queue_position=1  # TODO: Calculate actual queue position
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document upload error: %s", str(e))
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
    document_type: Optional[DocumentTypeEnum] = None,
    document_status: Optional[DocumentStatusEnum] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List documents accessible to the current user
    """
    try:
        user_kb_tier = determine_knowledge_base_tier(current_user.role)
        
        # Build query based on user's access level
        query = db.query(Document).filter(
            Document.knowledge_base_tier <= user_kb_tier.value
        )
        
        # Apply filters
        if category:
            query = query.filter(Document.category == category)
        
        if document_type:
            query = query.filter(Document.file_type == document_type)
        
        if document_status:
            query = query.filter(Document.status == document_status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        documents = query.order_by(desc(Document.created_at)).offset(offset).limit(limit).all()
        
        return DocumentListResponse(
            documents=[
                {
                    "document_id": doc.id,
                    "title": doc.title,
                    "filename": doc.filename,
                    "document_type": doc.file_type,
                    "category": doc.category,
                    "knowledge_base_tier": doc.knowledge_base_tier.value,
                    "status": doc.status,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at,
                    "processed_at": doc.processed_at
                }
                for doc in documents
            ],
            total_count=total_count,
            has_more=total_count > offset + limit
        )
        
    except Exception as e:
        logger.error("Error listing documents: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_detail(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific document
    """
    try:
        user_kb_tier = determine_knowledge_base_tier(current_user.role)
        
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.knowledge_base_tier <= user_kb_tier.value
            )
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        # Get document chunks for processed documents
        chunks = []
        if document.status == DocumentStatusEnum.PROCESSED:
            document_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).limit(5).all()  # Limit preview chunks
            
            chunks = [
                {
                    "chunk_id": chunk.id,
                    "content_preview": chunk.chunk_text[:200] + "..." if len(chunk.chunk_text) > 200 else chunk.chunk_text,
                    "chunk_index": chunk.chunk_index
                }
                for chunk in document_chunks
            ]
        
        return DocumentDetailResponse(
            document_id=document.id,
            title=document.title,
            filename=document.filename,
            description=document.description,
            document_type=document.file_type,
            category=document.category,
            knowledge_base_tier=document.knowledge_base_tier.value,
            status=document.status,
            file_size=document.file_size,
            mime_type=document.mime_type,
            created_at=document.created_at,
            processed_at=document.processed_at,
            content_preview=document.extracted_text[:500] + "..." if document.extracted_text and len(document.extracted_text) > 500 else document.extracted_text,
            chunks_count=len(chunks),
            chunks_preview=chunks,
            metadata=document.doc_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting document detail: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a document file
    """
    try:
        user_kb_tier = determine_knowledge_base_tier(current_user.role)
        
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.knowledge_base_tier <= user_kb_tier.value
            )
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        if not os.path.exists(document.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found on server"
            )
        
        return FileResponse(
            path=document.file_path,
            filename=document.filename,
            media_type=document.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading document: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search documents with advanced filtering
    """
    try:
        user_kb_tier = determine_knowledge_base_tier(current_user.role)
        
        # Build base query
        query = db.query(Document).filter(
            Document.knowledge_base_tier <= user_kb_tier.value
        )
        
        # Apply search filters
        if request.query:
            search_filter = or_(
                Document.title.contains(request.query),
                Document.extracted_text.contains(request.query),
                Document.description.contains(request.query)
            )
            query = query.filter(search_filter)
        
        if request.document_type:
            query = query.filter(Document.file_type == request.document_type)
        
        if request.category:
            query = query.filter(Document.category == request.category)
        
        if request.status:
            query = query.filter(Document.status == request.status)
        
        if request.knowledge_base_tier is not None:
            query = query.filter(Document.knowledge_base_tier == request.knowledge_base_tier)
        
        # Apply date filters
        if request.date_from:
            query = query.filter(Document.created_at >= request.date_from)
        
        if request.date_to:
            query = query.filter(Document.created_at <= request.date_to)
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting and pagination
        if request.sort_by == "relevance":
            # TODO: Implement relevance-based sorting using vector similarity
            query = query.order_by(desc(Document.created_at))
        elif request.sort_by == "date":
            query = query.order_by(desc(Document.created_at))
        elif request.sort_by == "title":
            query = query.order_by(Document.title)
        
        documents = query.offset(request.offset).limit(request.limit).all()
        
        return DocumentSearchResponse(
            documents=[
                {
                    "document_id": doc.id,
                    "title": doc.title,
                    "filename": doc.filename,
                    "content_preview": doc.extracted_text[:300] + "..." if doc.extracted_text and len(doc.extracted_text) > 300 else doc.extracted_text,
                    "document_type": doc.file_type,
                    "category": doc.category,
                    "knowledge_base_tier": doc.knowledge_base_tier.value,
                    "status": doc.status,
                    "created_at": doc.created_at,
                    "relevance_score": 0.85,  # TODO: Calculate actual relevance score
                    "highlight_snippets": []  # TODO: Add search highlighting
                }
                for doc in documents
            ],
            total_count=total_count,
            has_more=total_count > request.offset + request.limit,
            search_time=0.1,  # TODO: Calculate actual search time
            filters_applied={
                "query": request.query,
                "document_type": request.document_type.value if request.document_type else None,
                "category": request.category,
                "knowledge_base_tier": request.knowledge_base_tier
            }
        )
        
    except Exception as e:
        logger.error("Document search error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/categories/", response_model=List[DocumentCategoryResponse])
async def list_document_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all available document categories
    """
    try:
        categories = db.query(DocumentCategory).all()
        
        return [
            DocumentCategoryResponse(
                category_id=cat.id,
                name=cat.name,
                description=cat.description,
                document_count=cat.document_count,
                icon=cat.icon
            )
            for cat in categories
        ]
        
    except Exception as e:
        logger.error("Error listing categories: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats/", response_model=DocumentStatsResponse)
async def get_document_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get document statistics for the current user's access level
    """
    try:
        user_kb_tier = determine_knowledge_base_tier(current_user.role)
        
        # Get basic counts
        total_documents = db.query(Document).filter(
            Document.knowledge_base_tier <= user_kb_tier.value
        ).count()
        
        processed_documents = db.query(Document).filter(
            and_(
                Document.knowledge_base_tier <= user_kb_tier.value,
                Document.status == DocumentStatusEnum.PROCESSED
            )
        ).count()
        
        # Get counts by type
        type_counts = {}
        for doc_type in DocumentTypeEnum:
            count = db.query(Document).filter(
                and_(
                    Document.knowledge_base_tier <= user_kb_tier.value,
                    Document.file_type == doc_type
                )
            ).count()
            type_counts[doc_type.value] = count
        
        # Get recent uploads
        recent_count = db.query(Document).filter(
            and_(
                Document.knowledge_base_tier <= user_kb_tier.value,
                Document.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            )
        ).count()
        
        return DocumentStatsResponse(
            total_documents=total_documents,
            processed_documents=processed_documents,
            pending_documents=total_documents - processed_documents,
            documents_by_type=type_counts,
            recent_uploads=recent_count,
            knowledge_base_tier=user_kb_tier.value,
            accessible_tiers=list(range(1, user_kb_tier.value + 1))
        )
        
    except Exception as e:
        logger.error("Error getting document stats: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def queue_document_processing(document_id: int, db: Session):
    """
    Queue document for background processing
    TODO: Integrate with actual background task system (Celery/RQ)
    """
    try:
        # For now, just log that processing is queued
        logger.info("Document %s queued for processing", document_id)
        
        # TODO: Add to processing queue
        # TODO: Extract text content
        # TODO: Generate vector embeddings
        # TODO: Create document chunks
        # TODO: Update document status
        
        return True
        
    except Exception as e:
        logger.error("Error queueing document processing: %s", str(e))
        return False
