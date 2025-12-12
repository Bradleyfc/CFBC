#!/usr/bin/env python3
"""
Check course documents format
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.semantic_search import SemanticSearchService

def check_course_docs():
    """
    Check course documents format
    """
    print("🔍 Course Documents Format")
    print("=" * 40)
    
    semantic_search = SemanticSearchService()
    semantic_search.load_index()
    
    # Search for courses
    query = "¿Qué cursos están disponibles?"
    results = semantic_search.search(query, top_k=5, categoria='cursos')
    
    print(f"Found {len(results)} course documents:")
    
    for i, doc in enumerate(results, 1):
        print(f"\n{i}. Course Document:")
        print(f"   Score: {doc.get('score', 0):.3f}")
        print(f"   Category: {doc.get('categoria', 'unknown')}")
        print(f"   Text: {repr(doc.get('text', ''))}")
        print(f"   Lines:")
        for j, line in enumerate(doc.get('text', '').split('\n'), 1):
            print(f"     {j}: {repr(line.strip())}")

if __name__ == '__main__':
    try:
        check_course_docs()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()