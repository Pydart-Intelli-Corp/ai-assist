"""
Weaviate schema setup for POORNASREE AI Platform
"""
# pylint: disable=import-error,logging-fstring-interpolation
import logging
import weaviate
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_weaviate_schema():
    """Set up Weaviate schema for documents"""
    try:
        # Initialize Weaviate client
        client = weaviate.Client(
            url=settings.weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(api_key=settings.weaviate_api_key),
            timeout_config=(5, 15),
        )
        
        if not client.is_ready():
            logger.error("❌ Weaviate client is not ready")
            return False
        
        # Define Document class schema
        document_schema = {
            "class": "Document",
            "description": "Document objects for POORNASREE AI Platform",
            "vectorizer": "none",  # We'll provide our own vectors
            "properties": [
                {
                    "name": "doc_id",
                    "dataType": ["int"],
                    "description": "Unique document ID from database"
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
                    "description": "Knowledge base tier (1=Customer, 2=Engineer, 3=Master)"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "Additional metadata as JSON string"
                }
            ]
        }
        
        # Check if class already exists
        if client.schema.exists("Document"):
            logger.info("✅ Document class already exists in Weaviate")
            return True
        
        # Create the class
        client.schema.create_class(document_schema)
        logger.info("✅ Document class created in Weaviate successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Weaviate schema: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_weaviate_schema()
