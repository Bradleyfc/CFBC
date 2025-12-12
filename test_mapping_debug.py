#!/usr/bin/env python3
"""
Test mapping debug
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService
from chatbot.services.intent_classifier import IntentClassifier

def test_mapping_debug():
    """
    Debug mapping process
    """
    print("🔍 Mapping Debug")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    intent_classifier = IntentClassifier()
    
    query = "¿Dónde está ubicado el centro?"
    
    print(f"Consulta: {query}")
    print("-" * 40)
    
    # 1. Intent classification
    should_filter, intent = intent_classifier.should_filter_by_intent(query)
    print(f"1. Intent: {intent}")
    print(f"   Should filter: {should_filter}")
    
    # 2. Test mapping
    if should_filter and intent:
        mapped_category = orchestrator._map_intent_to_category(intent)
        print(f"2. Mapping: '{intent}' -> '{mapped_category}'")
        
        # 3. Test search with mapped category
        print(f"3. Searching with category '{mapped_category}':")
        results = semantic_search.search(query, top_k=5, categoria=mapped_category)
        print(f"   Results: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result.get('score', 0):.3f}")
            print(f"      Cat: {result.get('categoria', 'unknown')}")
            print(f"      Text: {result.get('text', '')[:80]}...")
        
        # 4. Test search with 'contacto' directly
        print(f"4. Searching with 'contacto' directly:")
        results_contacto = semantic_search.search(query, top_k=5, categoria='contacto')
        print(f"   Results: {len(results_contacto)}")
        
        for i, result in enumerate(results_contacto, 1):
            print(f"   {i}. Score: {result.get('score', 0):.3f}")
            print(f"      Cat: {result.get('categoria', 'unknown')}")
            print(f"      Text: {result.get('text', '')[:80]}...")

if __name__ == '__main__':
    try:
        test_mapping_debug()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()