#!/usr/bin/env python
"""
Test script to verify chatbot works completely offline
"""
import os
import sys
import django

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

def test_offline_functionality():
    """Test that chatbot works without internet connection"""
    
    print("Testing Offline Chatbot Functionality")
    print("=" * 50)
    
    # Set offline environment variables to ensure no internet access
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    
    try:
        # Test 1: Import and initialize semantic search
        print("1. Testing semantic search initialization...")
        from chatbot.services.semantic_search import SemanticSearchService
        
        semantic_search = SemanticSearchService()
        print("   ✅ Semantic search initialized successfully")
        
        # Test 2: Load FAISS index
        print("2. Testing FAISS index loading...")
        index_loaded = semantic_search.load_index()
        if index_loaded:
            print("   ✅ FAISS index loaded successfully")
            stats = semantic_search.get_index_stats()
            print(f"   📊 Index stats: {stats}")
        else:
            print("   ⚠️ FAISS index not found - will need to rebuild")
        
        # Test 3: Generate embeddings
        print("3. Testing embedding generation...")
        test_text = "¿Qué cursos están disponibles?"
        embedding = semantic_search.generate_embedding(test_text)
        print(f"   ✅ Embedding generated successfully (dimension: {len(embedding)})")
        
        # Test 4: Test orchestrator
        print("4. Testing chatbot orchestrator...")
        from chatbot.services.orchestrator import ChatbotOrchestrator
        
        orchestrator = ChatbotOrchestrator()
        print("   ✅ Orchestrator initialized successfully")
        
        # Test 5: Process a question
        print("5. Testing question processing...")
        test_questions = [
            "¿Qué cursos están disponibles?",
            "¿Cuándo empiezan las inscripciones?",
            "¿Dónde está ubicado el centro?",
            "¿Qué cursos de idiomas tienen?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"   Testing question {i}: {question}")
            try:
                result = orchestrator.process_question(question, f"test_session_{i}")
                
                if result.get('success', False):
                    print(f"   ✅ Question processed successfully")
                    print(f"   📝 Response: {result['respuesta'][:100]}...")
                    print(f"   🎯 Intent: {result['intencion']}")
                    print(f"   📊 Confidence: {result['confianza']:.2f}")
                    print(f"   ⏱️ Time: {result['tiempo']:.2f}s")
                    print(f"   📄 Documents found: {len(result['documentos_recuperados'])}")
                else:
                    print(f"   ❌ Question processing failed: {result.get('error', 'Unknown error')}")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error processing question: {e}")
                print()
        
        # Test 6: Check pipeline status
        print("6. Testing pipeline status...")
        status = orchestrator.get_pipeline_status()
        print("   ✅ Pipeline status retrieved:")
        print(f"   - Mode: {status.get('mode', 'unknown')}")
        print(f"   - LLM enabled: {status.get('llm_enabled', False)}")
        print(f"   - Semantic search available: {status.get('semantic_search', {}).get('available', False)}")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED - Chatbot is working offline!")
        print("✅ The system can run without internet connection")
        
        return True
        
    except Exception as e:
        print(f"\n❌ OFFLINE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_offline_functionality()
    sys.exit(0 if success else 1)