"""
Weaviate schema initialization for POORNASREE AI Platform
"""
# pylint: disable=import-error,logging-fstring-interpolation
import logging
import asyncio
from typing import Dict, Any

import weaviate
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class WeaviateSchemaManager:
    """Manages Weaviate schema creation and updates"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Weaviate client"""
        try:
            if settings.weaviate_url.startswith('https://'):
                # Cloud Weaviate instance
                self.client = weaviate.connect_to_weaviate_cloud(
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
                self.client = weaviate.connect_to_local(
                    host=settings.weaviate_url.replace('http://', '').replace('https://', '').split(':')[0],
                    port=int(settings.weaviate_url.split(':')[-1]) if ':' in settings.weaviate_url else 8080,
                    headers={"X-OpenAI-Api-Key": settings.weaviate_api_key} if settings.weaviate_api_key else None
                )
            
            if self.client.is_ready():
                logger.info("✅ Weaviate client initialized for schema management")
            else:
                logger.warning("⚠️ Weaviate client not ready")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Weaviate client: {e}")
            self.client = None
    
    def get_document_schema(self) -> Dict[str, Any]:
        """Get the Document class schema"""
        return {
            "class": "Document",
            "description": "Document storage for POORNASREE AI knowledge base",
            "vectorizer": "none",  # We'll provide our own vectors
            "properties": [
                {
                    "name": "doc_id",
                    "dataType": ["int"],
                    "description": "Document ID from the main database"
                },
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Document title"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "knowledge_base_tier",
                    "dataType": ["int"],
                    "description": "Knowledge base tier (1=Customer, 2=Engineer, 3=Admin)"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "JSON metadata about the document"
                },
                {
                    "name": "document_type",
                    "dataType": ["text"],
                    "description": "Type of document (PDF, DOC, etc.)"
                },
                {
                    "name": "category",
                    "dataType": ["text"],
                    "description": "Document category"
                },
                {
                    "name": "created_at",
                    "dataType": ["date"],
                    "description": "Document creation timestamp"
                }
            ]
        }
    
    def create_schema(self) -> bool:
        """Create the complete Weaviate schema"""
        try:
            if not self.client or not self.client.is_ready():
                logger.error("Weaviate client not available")
                return False
            
            # Check if Document class already exists
            try:
                existing_collections = self.client.collections.list_all()
                if "Document" in existing_collections:
                    logger.info("Document collection already exists in Weaviate")
                    return True
            except Exception:
                # Collection doesn't exist, continue with creation
                pass
            
            # Create Document collection using v4 API
            document_schema = self.get_document_schema()
            
            # Convert v3 schema to v4 collection configuration
            from weaviate.classes.config import Configure, Property, DataType
            
            properties = []
            for prop in document_schema["properties"]:
                if prop["dataType"] == ["int"]:
                    properties.append(Property(name=prop["name"], data_type=DataType.INT, description=prop["description"]))
                elif prop["dataType"] == ["text"]:
                    properties.append(Property(name=prop["name"], data_type=DataType.TEXT, description=prop["description"]))
                elif prop["dataType"] == ["date"]:
                    properties.append(Property(name=prop["name"], data_type=DataType.DATE, description=prop["description"]))
            
            self.client.collections.create(
                name="Document",
                description=document_schema["description"],
                properties=properties,
                vector_config=Configure.VectorIndex.none()  # We provide our own vectors
            )
            
            logger.info("✅ Document collection created successfully in Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Weaviate schema: {e}")
            return False
    
    def delete_schema(self) -> bool:
        """Delete the Weaviate schema (use with caution!)"""
        try:
            if not self.client or not self.client.is_ready():
                logger.error("Weaviate client not available")
                return False
            
            self.client.collections.delete("Document")
            logger.info("✅ Document collection deleted from Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete Weaviate schema: {e}")
            return False
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get current schema information"""
        try:
            if not self.client or not self.client.is_ready():
                return {"error": "Weaviate client not available"}
            
            collections = self.client.collections.list_all()
            return {
                "collections": len(collections),
                "collection_names": list(collections.keys()) if isinstance(collections, dict) else collections
            }
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return {"error": str(e)}

# Global schema manager
schema_manager = WeaviateSchemaManager()

async def initialize_weaviate_schema():
    """Initialize Weaviate schema on startup"""
    logger.info("Initializing Weaviate schema...")
    
    success = schema_manager.create_schema()
    if success:
        logger.info("✅ Weaviate schema initialized successfully")
    else:
        logger.warning("⚠️ Weaviate schema initialization failed")
    
    return success

if __name__ == "__main__":
    # For manual schema management
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create":
            schema_manager.create_schema()
        elif sys.argv[1] == "delete":
            confirm = input("Are you sure you want to delete the schema? (yes/no): ")
            if confirm.lower() == "yes":
                schema_manager.delete_schema()
        elif sys.argv[1] == "info":
            info = schema_manager.get_schema_info()
            print(f"Schema info: {info}")
    else:
        # Run initialization
        asyncio.run(initialize_weaviate_schema())
