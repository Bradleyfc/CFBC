#!/usr/bin/env python
"""
Script para probar las respuestas mejoradas del chatbot
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_respuestas_mejoradas():
    """Probar las respuestas mejoradas"""
    
    print("🧪 Probando respuestas mejoradas del chatbot...")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    preguntas = [
        "¿Qué cursos están disponibles?",
        "¿Qué cursos de idiomas hay?", 
        "¿Cómo me inscribo?",
        "¿Cuándo empiezan las inscripciones?",
        "¿Qué es el Centro Fray Bartolomé de las Casas?"
    ]
    
    for i, pregunta in enumerate(preguntas, 1):
        print(f"\n{i}. 🤔 Pregunta: {pregunta}")
        print("-" * 50)
        
        try:
            response = orchestrator.process_question(
                pregunta=pregunta,
                session_id=f"test_session_{i}"
            )
            
            respuesta = response.get('respuesta', 'Sin respuesta')
            confianza = response.get('confianza', 0)
            documentos = len(response.get('documentos_recuperados', []))
            
            print(f"🤖 Respuesta:")
            print(f"   {respuesta}")
            print(f"📊 Confianza: {confianza:.2f}")
            print(f"📚 Documentos: {documentos}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Pruebas completadas")

if __name__ == "__main__":
    test_respuestas_mejoradas()