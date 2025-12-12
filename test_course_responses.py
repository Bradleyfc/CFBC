#!/usr/bin/env python3
"""
Test course responses
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_course_responses():
    """
    Test course responses
    """
    print("🔍 Test Course Responses")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    
    queries = [
        "¿Qué cursos están disponibles?",
        "¿Cuáles son los cursos de idiomas?",
        "¿Hay cursos de diseño?",
        "¿Cómo me inscribo a un curso?"
    ]
    
    for query in queries:
        print(f"\nConsulta: {query}")
        print("-" * 50)
        
        response = orchestrator.process_question(query, session_id="course_test")
        print(f"Respuesta:\n{response.get('respuesta', 'N/A')}")
        print(f"Documentos: {len(response.get('documentos_recuperados', []))}")

if __name__ == '__main__':
    try:
        test_course_responses()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()