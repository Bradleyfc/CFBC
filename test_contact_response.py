#!/usr/bin/env python3
"""
Test contact response
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_contact_response():
    """
    Test contact response
    """
    print("🔍 Test Contact Response")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    
    queries = [
        "¿Dónde está ubicado el centro?",
        "¿Cuál es la dirección del centro?",
        "¿Cuál es el teléfono?",
        "¿Cómo puedo contactar al centro?"
    ]
    
    for query in queries:
        print(f"\nConsulta: {query}")
        print("-" * 50)
        
        response = orchestrator.process_question(query, session_id="contact_test")
        print(f"Respuesta:\n{response.get('respuesta', 'N/A')}")

if __name__ == '__main__':
    try:
        test_contact_response()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()