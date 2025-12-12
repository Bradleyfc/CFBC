#!/usr/bin/env python3
"""
Test index status
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService

def test_index_status():
    """
    Test index status and loading
    """
    print("🔍 Index Status Debug")
    print("=" * 40)
    
    # Test direct semantic search service
    print("1. Direct SemanticSearchService:")
    semantic_search = SemanticSearchService()
    
    # Check if index is loaded
    index_loaded = semantic_search.load_index()
    print(f"   Index loaded: {index_loaded}")
    
    if index_loaded:
        stats = semantic_search.get_index_stats()
        print(f"   Index stats: {stats}")
    
    # Test search
    query = "¿Dónde está ubicado el centro?"
    results = semantic_search.search(query, top_k=3, categoria='contacto')
    print(f"   Search results: {len(results)}")
    
    # Test orchestrator's semantic search
    print("\n2. Orchestrator's SemanticSearchService:")
    orchestrator = ChatbotOrchestrator()
    
    # Check orchestrator's semantic search
    orch_stats = orchestrator.semantic_search.get_index_stats()
    print(f"   Orchestrator index stats: {orch_stats}")
    
    # Test search through orchestrator
    orch_results = orchestrator.semantic_search.search(query, top_k=3, categoria='contacto')
    print(f"   Orchestrator search results: {len(orch_results)}")
    
    # Compare instances
    print(f"\n3. Instance comparison:")
    print(f"   Same instance: {semantic_search is orchestrator.semantic_search}")
    print(f"   Direct service ID: {id(semantic_search)}")
    print(f"   Orchestrator service ID: {id(orchestrator.semantic_search)}")

if __name__ == '__main__':
    try:
        test_index_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()