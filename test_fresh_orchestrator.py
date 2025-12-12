#!/usr/bin/env python3
"""
Test fresh orchestrator instance
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

def test_fresh_orchestrator():
    """
    Test fresh orchestrator instance
    """
    print("🔍 Fresh Orchestrator Test")
    print("=" * 40)
    
    # Import after Django setup
    from chatbot.services.orchestrator import ChatbotOrchestrator
    from chatbot.services.semantic_search import SemanticSearchService
    
    # Create fresh instances
    print("1. Creating fresh instances...")
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    
    # Check index loading
    print("2. Checking index loading...")
    index_loaded = semantic_search.load_index()
    print(f"   Index loaded: {index_loaded}")
    
    if index_loaded:
        stats = semantic_search.get_index_stats()
        print(f"   Index stats: {stats}")
    
    # Test direct search
    print("3. Testing direct search...")
    query = "¿Dónde está ubicado el centro?"
    
    # Without filter
    results_no_filter = semantic_search.search(query, top_k=3)
    print(f"   No filter: {len(results_no_filter)} results")
    
    # With contacto filter
    results_contacto = semantic_search.search(query, top_k=3, categoria='contacto')
    print(f"   With 'contacto' filter: {len(results_contacto)} results")
    
    # Test orchestrator search
    print("4. Testing orchestrator search...")
    orch_results = orchestrator.semantic_search.search(query, top_k=3, categoria='contacto')
    print(f"   Orchestrator search: {len(orch_results)} results")
    
    # Test full orchestrator process
    print("5. Testing full orchestrator process...")
    response = orchestrator.process_question(query, session_id="fresh_test")
    print(f"   Response: {response.get('respuesta', 'N/A')[:100]}...")
    print(f"   Documents: {len(response.get('documentos_recuperados', []))}")

if __name__ == '__main__':
    try:
        test_fresh_orchestrator()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()