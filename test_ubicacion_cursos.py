#!/usr/bin/env python3
"""
Test específico para ubicación y cursos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService

def test_ubicacion_cursos():
    """
    Probar consultas sobre ubicación y cursos disponibles
    """
    print("🧪 Probando Ubicación y Cursos")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    
    queries = [
        "¿Dónde está ubicado el centro?",
        "¿Cuál es la dirección del centro?",
        "¿Qué cursos están disponibles?",
        "¿Qué cursos ofrecen?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Consulta: {query}")
        print("-" * 50)
        
        # Búsqueda semántica directa
        print("🔍 Búsqueda semántica:")
        results = semantic_search.search(query, top_k=5)
        
        for j, result in enumerate(results, 1):
            score = result.get('score', 0)
            text = result.get('text', '')[:100]
            content_type = result.get('content_type', 'unknown')
            categoria = result.get('categoria', 'unknown')
            
            print(f"   {j}. Score: {score:.3f} | Tipo: {content_type} | Cat: {categoria}")
            print(f"      Texto: {text}...")
        
        # Respuesta del orchestrator
        print("\n🤖 Respuesta del orchestrator:")
        response = orchestrator.process_question(query, session_id="test_ubicacion")
        
        print(f"   Respuesta: {response.get('respuesta', 'N/A')}")
        print(f"   Documentos: {len(response.get('documentos_recuperados', []))}")

if __name__ == '__main__':
    try:
        test_ubicacion_cursos()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()