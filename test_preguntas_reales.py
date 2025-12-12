#!/usr/bin/env python
"""
Script para probar el chatbot con preguntas reales sobre el Centro Fray Bartolomé de las Casas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_preguntas_reales():
    """Probar el chatbot con preguntas reales"""
    
    orchestrator = ChatbotOrchestrator()
    
    preguntas_test = [
        "¿Qué cursos de idiomas tienen?",
        "¿Cómo me inscribo?", 
        "¿Qué es el Centro Fray Bartolomé de las Casas?",
        "¿Dónde están ubicados?",
        "¿Cuándo empiezan las inscripciones?",
        "¿Qué cursos de diseño hay?",
        "¿Hay cursos de teología?",
        "¿Cuáles son los requisitos?"
    ]
    
    print("🧪 Probando chatbot con preguntas reales sobre el Centro Fray Bartolomé de las Casas")
    print("=" * 80)
    
    for i, pregunta in enumerate(preguntas_test, 1):
        print(f"\n{i}. 🤔 Pregunta: {pregunta}")
        print("-" * 50)
        
        try:
            response = orchestrator.process_question(
                pregunta=pregunta,
                session_id=f"test_session_{i}"
            )
            
            respuesta = response.get('respuesta', 'Sin respuesta')
            confianza = response.get('confianza', 0)
            fuentes = len(response.get('fuentes', []))
            
            print(f"🤖 Respuesta: {respuesta[:200]}...")
            print(f"📊 Confianza: {confianza:.2f}")
            print(f"📚 Fuentes: {fuentes}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 Pruebas completadas")

if __name__ == "__main__":
    test_preguntas_reales()