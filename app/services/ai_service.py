"""
AI Service for POORNASREE AI Platform
Integrates with Weaviate vector database and Google Gemini API
"""
# pylint: disable=import-error,no-name-in-module,logging-fstring-interpolation
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import json

import weaviate
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class AIService:
    """AI Service for query processing and document retrieval"""
    
    def __init__(self):
        self.weaviate_client = None
        self.embedding_model = None
        self.genai_model = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI service clients"""
        try:
            # Initialize Weaviate client v4
            if settings.weaviate_url.startswith('https://'):
                # Cloud Weaviate instance
                self.weaviate_client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=settings.weaviate_url,
                    auth_credentials=weaviate.auth.AuthApiKey(settings.weaviate_api_key),
                    additional_config=weaviate.classes.init.AdditionalConfig(
                        timeout=weaviate.classes.init.Timeout(init=60, query=120, insert=180),
                        grpc_host=settings.weaviate_grpc_url if settings.weaviate_grpc_url else None,
                        grpc_port=443
                    )
                )
            else:
                # Local Weaviate instance
                self.weaviate_client = weaviate.connect_to_local(
                    host=settings.weaviate_url.replace('http://', '').replace('https://', '').split(':')[0],
                    port=int(settings.weaviate_url.split(':')[-1]) if ':' in settings.weaviate_url else 8080,
                    headers={"X-OpenAI-Api-Key": settings.weaviate_api_key} if settings.weaviate_api_key else None
                )
            
            # Test Weaviate connection
            if self.weaviate_client.is_ready():
                logger.info("✅ Weaviate client initialized successfully")
            else:
                logger.warning("⚠️ Weaviate client not ready")
            
            # Initialize Google Gemini
            genai.configure(api_key=settings.google_api_key)
            self.genai_model = genai.GenerativeModel(settings.gemini_model)
            logger.info("✅ Google Gemini API initialized successfully")
            
            # Initialize sentence transformer for embeddings
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Sentence transformer model loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ Could not load sentence transformer: {e}")
                self.embedding_model = None
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI services: {e}")
            # Don't raise - allow graceful degradation
    
    def close_connections(self):
        """Properly close all AI service connections"""
        try:
            if self.weaviate_client:
                self.weaviate_client.close()
                logger.info("🔌 Weaviate connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Warning closing Weaviate connection: {e}")
    
    def __del__(self):
        """Destructor to ensure connections are closed"""
        try:
            self.close_connections()
        except Exception:
            pass  # Ignore errors during cleanup
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        try:
            if self.embedding_model is None:
                # Fallback: use simple hash-based embeddings
                import hashlib
                text_hash = hashlib.md5(text.encode()).hexdigest()
                # Convert to 384-dimensional vector (matching sentence transformer)
                embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, len(text_hash), 2)]
                embedding.extend([0.0] * (384 - len(embedding)))  # Pad to 384 dimensions
                return embedding[:384]
            
            # Use sentence transformer
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self.embedding_model.encode, text
            )
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            # Return zero vector as fallback
            return [0.0] * 384
    
    async def store_document_in_weaviate(self, doc_id: int, title: str, content: str, 
                                       knowledge_base_tier: int, metadata: Dict[str, Any]) -> bool:
        """Store document in Weaviate vector database"""
        try:
            if not self.weaviate_client or not self.weaviate_client.is_ready():
                logger.warning("Weaviate client not available, skipping vector storage")
                return False
            
            # Generate embeddings
            embeddings = await self.generate_embeddings(content)
            
            # Prepare document object
            document_object = {
                "doc_id": doc_id,
                "title": title,
                "content": content[:5000],  # Limit content size
                "knowledge_base_tier": knowledge_base_tier,
                "metadata": json.dumps(metadata)
            }
            
            # Store in Weaviate using v4 API
            documents_collection = self.weaviate_client.collections.get("Document")
            documents_collection.data.insert(
                properties=document_object,
                vector=embeddings
            )
            
            logger.info(f"✅ Document {doc_id} stored in Weaviate successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document in Weaviate: {e}")
            return False
    
    async def search_similar_documents(self, query: str, knowledge_base_tier: int, 
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        try:
            if not self.weaviate_client or not self.weaviate_client.is_ready():
                logger.warning("Weaviate client not available, returning empty results")
                return []
            
            # Generate query embeddings
            query_embeddings = await self.generate_embeddings(query)
            
            # Search in Weaviate using v4 API
            documents_collection = self.weaviate_client.collections.get("Document")
            
            # Use correct v4 API syntax - separate the filtering and vector search
            try:
                # First try with filtering
                result = documents_collection.query.near_vector(
                    near_vector=query_embeddings,
                    limit=limit,
                    return_metadata=weaviate.classes.query.MetadataQuery(distance=True)
                )
                
                # Apply filtering if possible (this might need different syntax)
                # For now, let's get all results and filter in Python
                all_results = result.objects
                filtered_results = []
                
                for obj in all_results:
                    tier = obj.properties.get("knowledge_base_tier", 999)
                    if tier <= knowledge_base_tier:
                        filtered_results.append(obj)
                
                # Limit the results
                filtered_results = filtered_results[:limit]
                
            except Exception as e:
                logger.warning(f"Filtering failed, trying without filter: {e}")
                # Fallback: search without filtering
                result = documents_collection.query.near_vector(
                    near_vector=query_embeddings,
                    limit=limit,
                    return_metadata=weaviate.classes.query.MetadataQuery(distance=True)
                )
                filtered_results = result.objects[:limit]
            
            formatted_results = []
            for obj in filtered_results:
                formatted_results.append({
                    "doc_id": obj.properties.get("doc_id"),
                    "title": obj.properties.get("title"),
                    "content": obj.properties.get("content", "")[:200],  # Preview
                    "relevance_score": 1.0 - obj.metadata.distance if obj.metadata.distance else 0.5,
                    "metadata": json.loads(obj.properties.get("metadata", "{}"))
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search documents in Weaviate: {e}")
            return []
    
    async def generate_ai_response(self, query: str, context_documents: List[Dict[str, Any]], 
                                 user_role: str = "customer") -> Dict[str, Any]:
        """Generate AI response using Google Gemini"""
        try:
            if not self.genai_model:
                logger.warning("Gemini model not available, using fallback response")
                return {
                    "response": f"I understand your query: '{query}'. However, the AI service is currently unavailable. Please try again later or contact support.",
                    "confidence": 0.3,
                    "sources": [],
                    "processing_time": 0.1
                }
            
            # Prepare context from documents
            context = ""
            sources = []
            
            for doc in context_documents:
                context += f"Document: {doc.get('title', 'Untitled')}\\n"
                context += f"Content: {doc.get('content', '')}\\n\\n"
                sources.append({
                    "document_id": doc.get('doc_id'),
                    "title": doc.get('title', 'Untitled'),
                    "relevance_score": doc.get('relevance_score', 0.5),
                    "content_preview": (doc.get('content', '')[:150] + "...") if len(doc.get('content', '')) > 150 else doc.get('content', '')
                })
            
            # Create prompt based on user role
            role_prompts = {
                "customer": "You are a helpful maintenance assistant. Provide clear, simple answers suitable for equipment operators.",
                "engineer": "You are a technical maintenance expert. Provide detailed technical information and troubleshooting steps.",
                "admin": "You are a comprehensive maintenance expert with access to all technical documentation."
            }
            
            system_prompt = role_prompts.get(user_role, role_prompts["customer"])
            
            # Generate response
            prompt = f"""
{system_prompt}

Context Information:
{context}

User Query: {query}

Please provide a helpful response based on the context information. If the context doesn't contain relevant information, provide general guidance and suggest consulting additional resources.
"""

            response = await asyncio.get_event_loop().run_in_executor(
                None, self.genai_model.generate_content, prompt
            )
            
            return {
                "response": response.text,
                "confidence": 0.8,  # Default confidence
                "sources": sources,
                "processing_time": 1.0,
                "model_used": settings.gemini_model
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return {
                "response": f"I encountered an error while processing your query: '{query}'. Please try rephrasing your question or contact support if the issue persists.",
                "confidence": 0.1,
                "sources": [],
                "processing_time": 0.1,
                "error": str(e)
            }
    
    async def process_query(self, query: str, user_role: str = "customer", 
                           knowledge_base_tier: int = 1) -> Dict[str, Any]:
        """Complete query processing pipeline"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Search for relevant documents
            relevant_docs = await self.search_similar_documents(
                query, knowledge_base_tier, limit=5
            )
            
            # Generate AI response
            ai_response = await self.generate_ai_response(
                query, relevant_docs, user_role
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            ai_response["processing_time"] = processing_time
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "response": "I'm sorry, I encountered an error while processing your query. Please try again later.",
                "confidence": 0.0,
                "sources": [],
                "processing_time": asyncio.get_event_loop().time() - start_time,
                "error": str(e)
            }

# Global AI service instance
ai_service = AIService()
