#!/usr/bin/env python3
"""
Test specific course date queries
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_specific_course_dates():
    """
    Test specific course date queries
    """
    print("🔍 Test Specific Course Date Queries")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    
    queries = [
        "¿Cuándo empieza el curso de inglés?",
        "¿Cuál es la fecha límite para inscribirse al curso de diseño?",
        "¿Cuándo inicia el curso de alemán?",
        "¿Hasta cuándo puedo inscribirme al curso de teología?"
    ]
    
    for query in queries:
        print(f"\nConsulta: {query}")
        print("-" * 50)
        
        response = orchestrator.process_question(query, session_id="specific_dates_test")
        print(f"Respuesta:\n{response.get('respuesta', 'N/A')}")

if __name__ == '__main__':
    try:
        test_specific_course_dates()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()