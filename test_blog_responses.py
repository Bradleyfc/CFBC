#!/usr/bin/env python3
"""
Test blog responses
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_blog_responses():
    """
    Test blog responses
    """
    print("🔍 Test Blog Responses")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    
    queries = [
        "¿Hay noticias nuevas?",
        "¿Qué noticias tienen?",
        "¿Hay eventos próximos?",
        "¿Cuándo empiezan las inscripciones para idiomas?"
    ]
    
    for query in queries:
        print(f"\nConsulta: {query}")
        print("-" * 50)
        
        response = orchestrator.process_question(query, session_id="blog_test")
        print(f"Respuesta:\n{response.get('respuesta', 'N/A')}")
        print(f"Documentos: {len(response.get('documentos_recuperados', []))}")
        print(f"Intención: {response.get('intencion', 'N/A')}")

if __name__ == '__main__':
    try:
        test_blog_responses()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()