#!/usr/bin/env python3
"""
Test orchestrator debug
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_orchestrator_debug():
    """
    Debug orchestrator process step by step
    """
    print("🔍 Orchestrator Debug")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    
    queries = [
        "¿Dónde está ubicado el centro?",
        "¿Qué cursos están disponibles?"
    ]
    
    for query in queries:
        print(f"\nConsulta: {query}")
        print("-" * 50)
        
        # Process the question
        response = orchestrator.process_question(query, session_id="debug_test")
        
        print(f"Respuesta: {response.get('respuesta', 'N/A')}")
        print(f"Documentos encontrados: {len(response.get('documentos_recuperados', []))}")
        print(f"Intención: {response.get('intencion', 'N/A')}")
        print(f"Confianza: {response.get('confianza', 0):.3f}")
        
        # Show documents if any
        docs = response.get('documentos_recuperados', [])
        if docs:
            print("Documentos:")
            for i, doc in enumerate(docs, 1):
                print(f"  {i}. Score: {doc.get('score', 0):.3f} | Cat: {doc.get('categoria', 'unknown')}")
                print(f"     Text: {doc.get('text', '')[:80]}...")

if __name__ == '__main__':
    try:
        test_orchestrator_debug()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()