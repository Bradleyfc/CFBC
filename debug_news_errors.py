#!/usr/bin/env python3
"""
Debug script to identify specific errors in news search functionality
"""
import os
import sys
import django
import traceback

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def debug_specific_queries():
    """Debug the specific queries that are failing"""
    
    print("🐛 Debugging News Search Errors")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = ChatbotOrchestrator()
    
    # Queries that were failing
    failing_queries = [
        "¿Cuáles son las últimas noticias?",
        "Muéstrame las noticias más recientes",
        "¿Hay alguna noticia que hable sobre eventos?"
    ]
    
    for i, query in enumerate(failing_queries, 1):
        print(f"\n🔍 Debug Test {i}: {query}")
        print("-" * 40)
        
        try:
            # Process the question with detailed error tracking
            result = orchestrator.process_question(query, f"debug_session_{i}")
            
            if result.get('success', False):
                print(f"✅ Success!")
                print(f"Intent: {result.get('intencion', 'N/A')}")
                print(f"Confidence: {result.get('confianza', 0):.2f}")
                print(f"Documents: {len(result.get('documentos_recuperados', []))}")
                print(f"Response: {result.get('respuesta', 'No response')[:100]}...")
            else:
                print(f"❌ Failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")
                print(f"Response: {result.get('respuesta', 'No response')}")
                
        except Exception as e:
            print(f"💥 Exception occurred:")
            print(f"Error: {e}")
            print(f"Type: {type(e).__name__}")
            print("Traceback:")
            traceback.print_exc()
        
        print("\n" + "="*50)

def test_intent_detection():
    """Test intent detection specifically for news queries"""
    
    print("\n🧠 Testing Intent Detection for News Queries")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    test_queries = [
        "¿Cuáles son las últimas noticias?",
        "Muéstrame las noticias más recientes", 
        "¿Hay alguna noticia que hable sobre eventos?",
        "noticias",
        "últimas noticias",
        "blog"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            # Test intent classification
            should_filter, intent = orchestrator.intent_classifier.should_filter_by_intent(query)
            primary_intent, confidence = orchestrator.intent_classifier.get_primary_intent(query)
            
            print(f"  Should filter: {should_filter}")
            print(f"  Intent: {intent}")
            print(f"  Primary intent: {primary_intent}")
            print(f"  Confidence: {confidence:.2f}")
            
            # Test enhanced detection
            query_lower = query.lower()
            if any(word in query_lower for word in ['noticia', 'noticias', 'últimas noticias', 'ultimas noticias', 'blog', 'eventos', 'actividades', 'novedades', 'qué hay de nuevo', 'que hay de nuevo']):
                print(f"  Enhanced detection: YES (eventos)")
            else:
                print(f"  Enhanced detection: NO")
                
        except Exception as e:
            print(f"  Error: {e}")
            traceback.print_exc()

def test_semantic_search():
    """Test semantic search for news queries"""
    
    print("\n🔍 Testing Semantic Search for News Queries")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    test_queries = [
        "¿Cuáles son las últimas noticias?",
        "noticias"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            # Test semantic search directly
            documents = orchestrator.semantic_search.search(
                query=query,
                top_k=5,
                categoria='blog'
            )
            
            print(f"  Documents found: {len(documents)}")
            for i, doc in enumerate(documents[:3]):
                print(f"    {i+1}. Score: {doc.get('score', 0):.3f}")
                print(f"       Type: {doc.get('content_type', 'N/A')}")
                print(f"       Category: {doc.get('categoria', 'N/A')}")
                print(f"       Text: {doc.get('text', 'N/A')[:100]}...")
                
        except Exception as e:
            print(f"  Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    debug_specific_queries()
    test_intent_detection()
    test_semantic_search()