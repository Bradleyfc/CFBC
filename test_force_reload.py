#!/usr/bin/env python3
"""
Test force reload index
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService

def test_force_reload():
    """
    Test force reload index
    """
    print("🔍 Force Reload Test")
    print("=" * 40)
    
    # Create orchestrator
    orchestrator = ChatbotOrchestrator()
    
    # Force clear and reload index
    print("1. Clearing and reloading index...")
    orchestrator.semantic_search.clear_index()
    loaded = orchestrator.semantic_search.load_index()
    print(f"   Index reloaded: {loaded}")
    
    if loaded:
        stats = orchestrator.semantic_search.get_index_stats()
        print(f"   Stats: {stats}")
    
    # Test search
    query = "¿Dónde está ubicado el centro?"
    print(f"\n2. Testing search: {query}")
    
    # Direct search
    results = orchestrator.semantic_search.search(query, top_k=3, categoria='contacto')
    print(f"   Direct search results: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: '{result.get('categoria', 'unknown')}'")
        print(f"      Text: {result.get('text', '')[:60]}...")
    
    # Full orchestrator process
    print(f"\n3. Full orchestrator process:")
    response = orchestrator.process_question(query, session_id="force_reload_test")
    print(f"   Response: {response.get('respuesta', 'N/A')[:100]}...")
    print(f"   Documents: {len(response.get('documentos_recuperados', []))}")
    
    # Show documents if any
    docs = response.get('documentos_recuperados', [])
    if docs:
        print("   Documents found:")
        for i, doc in enumerate(docs, 1):
            print(f"   {i}. Score: {doc.get('score', 0):.3f} | Cat: '{doc.get('categoria', 'unknown')}'")
            print(f"      Text: {doc.get('text', '')[:60]}...")

if __name__ == '__main__':
    try:
        test_force_reload()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()