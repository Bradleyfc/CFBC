#!/usr/bin/env python3
"""
Test Spanish filter
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService

def test_spanish_filter():
    """
    Test Spanish content filtering
    """
    print("🔍 Spanish Filter Debug")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    
    query = "¿Dónde está ubicado el centro?"
    
    # Get documents with contacto category
    results = semantic_search.search(query, top_k=5, categoria='contacto')
    
    print(f"Found {len(results)} documents in 'contacto' category:")
    
    for i, doc in enumerate(results, 1):
        text = doc.get('text', '')
        print(f"\n{i}. Document:")
        print(f"   Score: {doc.get('score', 0):.3f}")
        print(f"   Category: {doc.get('categoria', 'unknown')}")
        print(f"   Text: {text}")
        
        # Test Spanish filter
        is_spanish = orchestrator._is_spanish_content(text)
        print(f"   Is Spanish: {is_spanish}")
        
        if not is_spanish:
            print("   ❌ This document would be filtered out!")

if __name__ == '__main__':
    try:
        test_spanish_filter()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()