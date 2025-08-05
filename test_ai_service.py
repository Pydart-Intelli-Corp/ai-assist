"""
Test AI Service Integration
"""
import asyncio
import logging
from app.services.ai_service import ai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_service():
    """Test AI service functionality"""
    print("🧪 Testing AI Service Integration")
    print("=" * 50)
    
    # Test query processing
    query = "How to troubleshoot motor issues?"
    
    try:
        result = await ai_service.process_query(
            query=query,
            user_role="engineer",
            knowledge_base_tier=2
        )
        
        print(f"Query: {query}")
        print(f"Response: {result.get('response', 'No response')}")
        print(f"Confidence: {result.get('confidence', 0.0)}")
        print(f"Processing Time: {result.get('processing_time', 0.0):.2f}s")
        print(f"Sources: {len(result.get('sources', []))} documents")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ai_service())
