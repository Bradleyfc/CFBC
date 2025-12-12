#!/usr/bin/env python3
"""
Debug search method
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.semantic_search import SemanticSearchService
import numpy as np

def debug_search_method():
    """
    Debug search method step by step
    """
    print("🔍 Debug Search Method")
    print("=" * 40)
    
    semantic_search = SemanticSearchService()
    
    # Load index
    loaded = semantic_search.load_index()
    print(f"Index loaded: {loaded}")
    
    if not loaded:
        return
    
    query = "¿Dónde está ubicado el centro?"
    categoria = 'contacto'
    top_k = 3
    
    print(f"Query: {query}")
    print(f"Category filter: {categoria}")
    print(f"Top K: {top_k}")
    
    # Step 1: Generate embedding
    print("\n1. Generating embedding...")
    query_embedding = semantic_search.generate_embedding(query)
    query_embedding_2d = query_embedding.reshape(1, -1).astype('float32')
    print(f"   Embedding shape: {query_embedding_2d.shape}")
    
    # Step 2: Search in FAISS
    print("\n2. Searching in FAISS...")
    search_k = top_k * 10 if categoria else top_k  # Buscar más resultados
    print(f"   Search K: {search_k}")
    
    scores, indices = semantic_search._index.search(query_embedding_2d, min(search_k, semantic_search._index.ntotal))
    print(f"   Raw results: {len(scores[0])} scores, {len(indices[0])} indices")
    
    # Step 3: Process results
    print("\n3. Processing results...")
    results = []
    
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        print(f"\n   Result {i+1}:")
        print(f"     Score: {score:.3f}")
        print(f"     Index: {idx}")
        
        if idx == -1:
            print("     ❌ Empty slot, skipping")
            continue
        
        metadata = semantic_search._id_to_metadata.get(int(idx))
        if metadata is None:
            print("     ❌ No metadata found, skipping")
            continue
        
        print(f"     Metadata categoria: '{metadata.get('categoria', 'unknown')}'")
        print(f"     Text: {metadata.get('text', '')[:50]}...")
        
        # Filter by category if specified
        if categoria and metadata.get('categoria') != categoria:
            print(f"     ❌ Category mismatch: '{metadata.get('categoria')}' != '{categoria}', skipping")
            continue
        
        print("     ✅ Category match, adding to results")
        
        result = {
            'doc_id': metadata['doc_id'],
            'score': float(score),
            'text': metadata.get('text', ''),
            'categoria': metadata.get('categoria', ''),
            'content_type': metadata.get('content_type', ''),
            'object_id': metadata.get('object_id', 0),
            'destacada': False,
            'prioridad': 0
        }
        
        results.append(result)
        
        if len(results) >= top_k * 2:
            break
    
    print(f"\n4. Final results: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Score: {result['score']:.3f} | Cat: '{result['categoria']}'")
        print(f"      Text: {result['text'][:50]}...")

if __name__ == '__main__':
    try:
        debug_search_method()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()