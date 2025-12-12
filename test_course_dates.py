#!/usr/bin/env python3
"""
Test course dates and availability
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_course_dates():
    """
    Test course dates and availability
    """
    print("🔍 Test Course Dates and Availability")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    
    queries = [
        "¿Cuándo empiezan las inscripciones?",
        "¿Hasta cuándo puedo inscribirme?",
        "¿Qué cursos tienen inscripciones abiertas?",
        "¿Cuándo empieza el curso de inglés?",
        "¿Cuál es la fecha límite para inscribirse al curso de diseño?",
        "¿Hay cursos disponibles para inscribirse ahora?"
    ]
    
    for query in queries:
        print(f"\nConsulta: {query}")
        print("-" * 50)
        
        response = orchestrator.process_question(query, session_id="dates_test")
        print(f"Respuesta:\n{response.get('respuesta', 'N/A')}")
        print(f"Documentos: {len(response.get('documentos_recuperados', []))}")

if __name__ == '__main__':
    try:
        test_course_dates()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()