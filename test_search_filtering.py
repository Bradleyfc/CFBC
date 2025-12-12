#!/usr/bin/env python3
"""
Test search filtering
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.semantic_search import SemanticSearchService

def test_search_filtering():
    """
    Test search with and without filtering
    """
    print("🔍 Search Filtering Debug")
    print("=" * 40)
    
    semantic_search = SemanticSearchService()
    query = "¿Dónde está ubicado el centro?"
    
    # Test without category filter
    print("1. Search without category filter:")
    results_no_filter = semantic_search.search(query, top_k=5)
    print(f"   Results: {len(results_no_filter)}")
    
    for i, result in enumerate(results_no_filter, 1):
        print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: '{result.get('categoria', 'unknown')}'")
        print(f"      Text: {result.get('text', '')[:80]}...")
    
    # Test with 'contacto' filter
    print("\n2. Search with 'contacto' filter:")
    results_contacto = semantic_search.search(query, top_k=5, categoria='contacto')
    print(f"   Results: {len(results_contacto)}")
    
    for i, result in enumerate(results_contacto, 1):
        print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: '{result.get('categoria', 'unknown')}'")
        print(f"      Text: {result.get('text', '')[:80]}...")
    
    # Test with other categories
    categories_to_test = ['Información General', 'cursos', 'inscripciones']
    
    for cat in categories_to_test:
        print(f"\n3. Search with '{cat}' filter:")
        results_cat = semantic_search.search(query, top_k=3, categoria=cat)
        print(f"   Results: {len(results_cat)}")
        
        for i, result in enumerate(results_cat, 1):
            print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: '{result.get('categoria', 'unknown')}'")
            print(f"      Text: {result.get('text', '')[:50]}...")

if __name__ == '__main__':
    try:
        test_search_filtering()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()