"""
Simple test to verify the AI service is working correctly
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import ai_service

async def simple_ai_test():
    """Simple test of the AI service functionality"""
    print("🧪 Testing AI Service Integration")
    print("=" * 50)
    
    # Test query processing
    print("\n🤖 Testing Query Processing...")
    try:
        response = await ai_service.process_query(
            "How to troubleshoot motor problems?",
            user_role="customer",
            knowledge_base_tier=1
        )
        
        print(f"✅ Query processed successfully!")
        print(f"📊 Confidence: {response.get('confidence', 0):.2f}")
        print(f"⏱️  Processing Time: {response.get('processing_time', 0):.2f}s")
        print(f"📝 Response Length: {len(response.get('response', ''))}")
        print(f"📚 Sources: {len(response.get('sources', []))}")
        print(f"💬 Response Preview: {response.get('response', '')[:200]}...")
        
        if response.get('error'):
            print(f"⚠️  Error: {response['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query processing failed: {e}")
        return False
    
    finally:
        # Close connections
        try:
            if ai_service.weaviate_client:
                ai_service.weaviate_client.close()
                print("🔌 Weaviate connection closed")
        except Exception as e:
            print(f"⚠️  Warning: {e}")

if __name__ == "__main__":
    success = asyncio.run(simple_ai_test())
    if success:
        print("\n✅ AI Service Test Completed Successfully!")
    else:
        print("\n❌ AI Service Test Failed!")
        sys.exit(1)
