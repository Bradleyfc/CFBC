#!/usr/bin/env python3
"""
Check new course documents with dates
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.semantic_search import SemanticSearchService

def check_new_course_docs():
    """
    Check new course documents with dates
    """
    print("🔍 New Course Documents with Dates")
    print("=" * 40)
    
    semantic_search = SemanticSearchService()
    semantic_search.load_index()
    
    # Search for enrollment dates
    queries = [
        "fecha límite inscripción",
        "fecha de inicio",
        "inscripciones para",
        "estado actual"
    ]
    
    for query in queries:
        print(f"\n🔎 Búsqueda: {query}")
        print("-" * 30)
        
        results = semantic_search.search(query, top_k=3, categoria='cursos')
        
        for i, doc in enumerate(results, 1):
            print(f"{i}. Score: {doc.get('score', 0):.3f}")
            print(f"   Text: {doc.get('text', '')}")
            print()

if __name__ == '__main__':
    try:
        check_new_course_docs()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()