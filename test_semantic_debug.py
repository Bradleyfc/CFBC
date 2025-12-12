#!/usr/bin/env python3
"""
Test semantic search debug
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.semantic_search import SemanticSearchService

def test_semantic_debug():
    """
    Debug semantic search filtering
    """
    print("🔍 Semantic Search Debug")
    print("=" * 40)
    
    semantic_search = SemanticSearchService()
    
    # Load index
    loaded = semantic_search.load_index()
    print(f"Index loaded: {loaded}")
    
    if not loaded:
        print("❌ Index not loaded!")
        return
    
    stats = semantic_search.get_index_stats()
    print(f"Index stats: {stats}")
    
    # Check metadata
    print("\nChecking metadata...")
    if hasattr(semantic_search, '_id_to_metadata') and semantic_search._id_to_metadata:
        print(f"Metadata entries: {len(semantic_search._id_to_metadata)}")
        
        # Show first few metadata entries
        print("\nFirst 10 metadata entries:")
        for i, (idx, metadata) in enumerate(list(semantic_search._id_to_metadata.items())[:10]):
            categoria = metadata.get('categoria', 'unknown')
            text = metadata.get('text', '')[:50]
            print(f"  {idx}: Cat='{categoria}' | Text='{text}...'")
        
        # Count by category
        print("\nDocuments by category:")
        categories = {}
        for metadata in semantic_search._id_to_metadata.values():
            cat = metadata.get('categoria', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"  '{cat}': {count} documents")
    
    # Test searches
    query = "¿Dónde está ubicado el centro?"
    
    print(f"\n🔎 Testing query: {query}")
    
    # Search without filter
    print("\n1. Search without filter:")
    results = semantic_search.search(query, top_k=5)
    print(f"   Results: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: '{result.get('categoria', 'unknown')}'")
        print(f"      Text: {result.get('text', '')[:60]}...")
    
    # Search with contacto filter
    print("\n2. Search with 'contacto' filter:")
    results_contacto = semantic_search.search(query, top_k=5, categoria='contacto')
    print(f"   Results: {len(results_contacto)}")
    for i, result in enumerate(results_contacto, 1):
        print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: '{result.get('categoria', 'unknown')}'")
        print(f"      Text: {result.get('text', '')[:60]}...")

if __name__ == '__main__':
    try:
        test_semantic_debug()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()