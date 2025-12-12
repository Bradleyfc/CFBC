#!/usr/bin/env python
"""
Script para probar que el problema del prompt LLM está solucionado
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_prompt_fix():
    """Probar que el LLM ya no devuelve instrucciones del prompt"""
    
    print("🧪 Probando corrección del problema del prompt LLM")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Preguntas de prueba
    preguntas = [
        "¿Cuáles son los requisitos para inscribirme?",
        "¿Qué cursos están disponibles?",
        "¿Cómo me inscribo?",
        "¿Dónde están ubicados?"
    ]
    
    for i, pregunta in enumerate(preguntas, 1):
        print(f"\n{i}. 🤔 Pregunta: {pregunta}")
        print("-" * 50)
        
        try:
            response = orchestrator.process_question(
                pregunta=pregunta,
                session_id=f"test_fix_{i}"
            )
            
            respuesta = response.get('respuesta', 'Sin respuesta')
            tiempo = response.get('tiempo', 0)
            
            # Verificar si la respuesta contiene instrucciones problemáticas
            problematic_phrases = [
                "Responde de manera clara y concisa",
                "Usa solo información del contexto",
                "Si el contexto no contiene la respuesta",
                "Sé útil y amigable",
                "Máximo 2-3 párrafos"
            ]
            
            has_problem = any(phrase in respuesta for phrase in problematic_phrases)
            
            if has_problem:
                print("❌ PROBLEMA: Respuesta contiene instrucciones del prompt")
                print(f"   Respuesta: {respuesta[:200]}...")
            else:
                print("✅ CORRECTO: Respuesta limpia y útil")
                print(f"   Respuesta: {respuesta[:150]}...")
            
            print(f"⚡ Tiempo: {tiempo:.2f}s")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Prueba de corrección del prompt completada")

if __name__ == "__main__":
    test_prompt_fix()