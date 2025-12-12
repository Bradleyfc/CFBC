#!/usr/bin/env python3
"""
Test intent classification for date queries
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.intent_classifier import IntentClassifier
from chatbot.services.semantic_search import SemanticSearchService

def test_intent_dates():
    """
    Test intent classification for date queries
    """
    print("🔍 Intent Classification for Date Queries")
    print("=" * 40)
    
    intent_classifier = IntentClassifier()
    semantic_search = SemanticSearchService()
    semantic_search.load_index()
    
    queries = [
        "¿Cuándo empiezan las inscripciones?",
        "¿Hasta cuándo puedo inscribirme?",
        "¿Cuál es la fecha límite para inscribirse al curso de diseño?",
        "¿Cuándo empieza el curso de inglés?"
    ]
    
    for query in queries:
        print(f"\n📝 Consulta: {query}")
        print("-" * 50)
        
        # Intent classification
        should_filter, intent = intent_classifier.should_filter_by_intent(query)
        primary_intent, confidence = intent_classifier.get_primary_intent(query)
        
        print(f"Intent: {primary_intent} (confidence: {confidence:.3f})")
        print(f"Should filter: {should_filter}")
        print(f"Filter intent: {intent}")
        
        # Direct search without filter
        print("\nDirect search (no filter):")
        results_no_filter = semantic_search.search(query, top_k=3)
        for i, result in enumerate(results_no_filter, 1):
            print(f"  {i}. Score: {result.get('score', 0):.3f} | Cat: {result.get('categoria', 'unknown')}")
            print(f"     Text: {result.get('text', '')[:80]}...")
        
        # Search with filter if applicable
        if should_filter and intent:
            print(f"\nSearch with '{intent}' filter:")
            results_filtered = semantic_search.search(query, top_k=3, categoria=intent)
            print(f"  Results: {len(results_filtered)}")
            for i, result in enumerate(results_filtered, 1):
                print(f"  {i}. Score: {result.get('score', 0):.3f} | Cat: {result.get('categoria', 'unknown')}")
                print(f"     Text: {result.get('text', '')[:80]}...")

if __name__ == '__main__':
    try:
        test_intent_dates()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()