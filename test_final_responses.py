#!/usr/bin/env python3
"""
Test final responses
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_final_responses():
    """
    Test final responses
    """
    print("🔍 Test Final Responses")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    
    queries = [
        "¿Dónde está ubicado el centro?",
        "¿Qué cursos están disponibles?",
        "¿Cuáles son los cursos de idiomas?",
        "¿Cómo me inscribo?",
        "¿Hay noticias nuevas?",
        "¿Cuál es el teléfono del centro?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Consulta: {query}")
        print("-" * 60)
        
        response = orchestrator.process_question(query, session_id=f"test_{i}")
        
        print(f"Respuesta:")
        print(response.get('respuesta', 'N/A'))
        print(f"\nDocumentos: {len(response.get('documentos_recuperados', []))}")
        print(f"Intención: {response.get('intencion', 'N/A')}")

if __name__ == '__main__':
    try:
        test_final_responses()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()