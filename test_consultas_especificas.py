#!/usr/bin/env python3
"""
Test específico para consultas que están fallando
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService

def test_consultas_especificas():
    """
    Probar consultas específicas que están fallando
    """
    print("🧪 Probando Consultas Específicas")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    
    # Consultas problemáticas
    problematic_queries = [
        "¿Cómo me inscribo?",
        "¿Qué necesito para inscribirme?",
        "¿Cuál es el proceso de inscripción?"
    ]
    
    for i, query in enumerate(problematic_queries, 1):
        print(f"\n{i}. Consulta: {query}")
        print("-" * 40)
        
        try:
            # Primero probar búsqueda semántica directa
            print("🔍 Búsqueda semántica directa:")
            results = semantic_search.search(query, top_k=3)
            print(f"   Resultados encontrados: {len(results)}")
            
            for j, result in enumerate(results, 1):
                score = result.get('score', 0)
                text = result.get('text', '')[:60]
                content_type = result.get('content_type', 'unknown')
                categoria = result.get('categoria', 'unknown')
                print(f"   {j}. Score: {score:.3f} | Tipo: {content_type} | Cat: {categoria}")
                print(f"      Texto: {text}...")
            
            # Ahora probar con orchestrator
            print("\n🤖 Respuesta del orchestrator:")
            response = orchestrator.process_question(query, session_id="test_debug")
            
            print(f"   ✅ Éxito: {response.get('success', False)}")
            print(f"   📝 Respuesta: {response.get('respuesta', 'N/A')[:100]}...")
            print(f"   📊 Confianza: {response.get('confianza', 0):.3f}")
            print(f"   🔍 Documentos: {len(response.get('documentos_recuperados', []))}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Pruebas completadas")

if __name__ == '__main__':
    try:
        test_consultas_especificas()
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()