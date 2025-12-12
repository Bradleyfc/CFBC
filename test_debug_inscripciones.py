#!/usr/bin/env python3
"""
Test de debug para inscripciones
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService

def test_debug_inscripciones():
    """
    Debug específico para inscripciones
    """
    print("🔍 Debug de Inscripciones")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    
    query = "¿Cómo me inscribo a un curso?"
    
    print(f"Consulta: {query}")
    print("-" * 40)
    
    # 1. Búsqueda semántica directa
    print("1. Búsqueda semántica:")
    results = semantic_search.search(query, top_k=5)
    
    for i, result in enumerate(results, 1):
        score = result.get('score', 0)
        text = result.get('text', '')
        content_type = result.get('content_type', 'unknown')
        categoria = result.get('categoria', 'unknown')
        chunk_type = result.get('chunk_type', 'unknown')
        
        print(f"   {i}. Score: {score:.3f}")
        print(f"      Tipo: {content_type}")
        print(f"      Categoría: {categoria}")
        print(f"      Chunk: {chunk_type}")
        print(f"      Texto: {text}")
        print()
    
    # 2. Respuesta del orchestrator
    print("2. Respuesta del orchestrator:")
    response = orchestrator.process_question(query, session_id="debug")
    
    print(f"   Éxito: {response.get('success', False)}")
    print(f"   Respuesta: {response.get('respuesta', 'N/A')}")
    print(f"   Confianza: {response.get('confianza', 0):.3f}")
    print(f"   Documentos: {len(response.get('documentos_recuperados', []))}")
    
    # 3. Detalles de documentos recuperados
    print("\n3. Documentos recuperados por orchestrator:")
    for i, doc in enumerate(response.get('documentos_recuperados', []), 1):
        print(f"   {i}. Score: {doc.get('score', 0):.3f}")
        print(f"      Tipo: {doc.get('content_type', 'unknown')}")
        print(f"      Texto: {doc.get('text', '')}")
        print()

if __name__ == '__main__':
    try:
        test_debug_inscripciones()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()