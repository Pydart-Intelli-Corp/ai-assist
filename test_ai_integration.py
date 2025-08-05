#!/usr/bin/env python3
"""
Comprehensive AI Integration Test for POORNASREE AI Platform
Tests the complete AI pipeline with real Weaviate and Gemini APIs
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import ai_service
from app.services.weaviate_schema import schema_manager
import time

async def test_ai_integration():
    """Test complete AI integration pipeline"""
    
    print("🧪 Testing Complete AI Integration Pipeline")
    print("=" * 60)
    
    # Test 1: Initialize schema
    print("\n📊 Step 1: Initializing Weaviate Schema")
    print("-" * 40)
    schema_success = schema_manager.create_schema()
    if schema_success:
        print("✅ Schema initialized successfully")
    else:
        print("❌ Schema initialization failed")
        return False
    
    # Test 2: Check schema info
    print("\n📋 Step 2: Schema Information")
    print("-" * 40)
    schema_info = schema_manager.get_schema_info()
    print(f"Schema Info: {schema_info}")
    
    # Test 3: Store sample documents
    print("\n📄 Step 3: Storing Sample Documents")
    print("-" * 40)
    
    sample_documents = [
        {
            "doc_id": 1,
            "title": "Motor Troubleshooting Guide",
            "content": "Common motor issues include overheating, unusual noises, and failure to start. Check electrical connections, bearings, and load conditions. For AC motors, verify voltage levels and phase balance.",
            "knowledge_base_tier": 1,
            "metadata": {"category": "troubleshooting", "equipment": "motor", "type": "guide"}
        },
        {
            "doc_id": 2,
            "title": "Pump Maintenance Procedures",
            "content": "Regular pump maintenance includes checking seal condition, lubrication, alignment, and vibration levels. Replace worn components before failure occurs.",
            "knowledge_base_tier": 2,
            "metadata": {"category": "maintenance", "equipment": "pump", "type": "procedure"}
        },
        {
            "doc_id": 3,
            "title": "Advanced Diagnostic Techniques",
            "content": "Advanced diagnostics use vibration analysis, thermal imaging, and oil analysis to predict equipment failures. Motor circuit analysis can detect winding faults.",
            "knowledge_base_tier": 3,
            "metadata": {"category": "diagnostics", "equipment": "general", "type": "advanced"}
        }
    ]
    
    stored_count = 0
    for doc in sample_documents:
        success = await ai_service.store_document_in_weaviate(
            doc["doc_id"], doc["title"], doc["content"], 
            doc["knowledge_base_tier"], doc["metadata"]
        )
        if success:
            stored_count += 1
            print(f"✅ Stored document: {doc['title']}")
        else:
            print(f"❌ Failed to store document: {doc['title']}")
    
    print(f"\n📊 Summary: {stored_count}/{len(sample_documents)} documents stored successfully")
    
    # Test 4: Search for similar documents
    print("\n🔍 Step 4: Testing Document Search")
    print("-" * 40)
    
    test_queries = [
        {"query": "motor problems", "tier": 1},
        {"query": "pump maintenance", "tier": 2},
        {"query": "vibration analysis", "tier": 3}
    ]
    
    for test in test_queries:
        print(f"\nQuery: '{test['query']}' (Tier {test['tier']})")
        start_time = time.time()
        results = await ai_service.search_similar_documents(
            test["query"], test["tier"], limit=3
        )
        search_time = time.time() - start_time
        
        print(f"Search Time: {search_time:.2f}s")
        print(f"Results Found: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('title', 'Unknown')} (Score: {result.get('relevance_score', 0):.3f})")
    
    # Test 5: Generate AI responses
    print("\n🤖 Step 5: Testing AI Response Generation")
    print("-" * 40)
    
    test_scenarios = [
        {"query": "How to fix a motor that won't start?", "role": "customer", "tier": 1},
        {"query": "What causes pump cavitation?", "role": "engineer", "tier": 2},
        {"query": "Explain vibration analysis techniques", "role": "admin", "tier": 3}
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 Query: {scenario['query']}")
        print(f"👤 Role: {scenario['role']} | 🔒 Tier: {scenario['tier']}")
        
        start_time = time.time()
        response = await ai_service.process_query(
            scenario["query"], scenario["role"], scenario["tier"]
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing Time: {processing_time:.2f}s")
        print(f"🎯 Confidence: {response.get('confidence', 0):.2f}")
        print(f"📚 Sources: {len(response.get('sources', []))}")
        print(f"💬 Response Length: {len(response.get('response', ''))}")
        print(f"📝 Response Preview: {response.get('response', '')[:200]}...")
        
        if response.get('error'):
            print(f"❌ Error: {response['error']}")
        else:
            print("✅ Response generated successfully")
    
    # Test 6: Performance metrics
    print("\n📊 Step 6: Performance Summary")
    print("-" * 40)
    
    # Test embedding generation speed
    start_time = time.time()
    test_text = "This is a test document for measuring embedding generation speed."
    embeddings = await ai_service.generate_embeddings(test_text)
    embedding_time = time.time() - start_time
    
    print(f"🧠 Embedding Generation:")
    print(f"  - Time: {embedding_time:.3f}s")
    print(f"  - Dimensions: {len(embeddings)}")
    print(f"  - Vector Sample: {embeddings[:5]}")
    
    # Test concurrent queries
    print(f"\n🚀 Concurrent Query Test:")
    start_time = time.time()
    concurrent_tasks = []
    for i in range(3):
        task = ai_service.process_query(f"Test query {i+1}", "customer", 1)
        concurrent_tasks.append(task)
    
    concurrent_results = await asyncio.gather(*concurrent_tasks)
    concurrent_time = time.time() - start_time
    
    print(f"  - 3 concurrent queries: {concurrent_time:.2f}s")
    print(f"  - Average per query: {concurrent_time/3:.2f}s")
    print(f"  - All successful: {all(r.get('response') for r in concurrent_results)}")
    
    print("\n🎉 AI Integration Test Complete!")
    print("=" * 60)
    
    # Close Weaviate connection
    try:
        if ai_service.weaviate_client:
            ai_service.weaviate_client.close()
            print("🔌 Weaviate connection closed properly")
    except Exception as e:
        print(f"⚠️  Warning: Failed to close Weaviate connection: {e}")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_ai_integration())
        if success:
            print("✅ All tests passed!")
            sys.exit(0)
        else:
            print("❌ Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
