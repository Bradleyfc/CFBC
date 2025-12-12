#!/usr/bin/env python
"""
Script para probar el sistema híbrido del chatbot
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_sistema_hibrido():
    """Probar el sistema híbrido: LLM para preguntas complejas, estructuradas para simples"""
    
    print("🧪 Probando Sistema Híbrido del Chatbot")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Verificar estado del sistema
    status = orchestrator.get_pipeline_status()
    print(f"🔧 LLM disponible: {status['llm_generator']['available']}")
    print(f"🔧 Modo híbrido: {status['llm_generator'].get('hybrid_mode', 'No configurado')}")
    print(f"🔧 Umbral complejidad: {status['llm_generator'].get('complex_threshold', 'No configurado')}")
    print()
    
    # Preguntas simples (deberían usar respuestas estructuradas)
    preguntas_simples = [
        "¿Qué cursos hay?",
        "¿Cómo me inscribo?",
        "¿Dónde están ubicados?",
        "¿Cuándo empiezan las clases?"
    ]
    
    # Preguntas complejas (deberían usar LLM)
    preguntas_complejas = [
        "¿Cuál es la diferencia entre el curso de inglés y el de alemán y cuál me recomendarías para alguien que nunca ha estudiado idiomas?",
        "Explícame por qué debería elegir el Centro Fray Bartolomé de las Casas en lugar de otros centros de estudio",
        "¿Cómo puedo comparar los diferentes cursos de diseño que ofrecen y cuál sería mejor para mi perfil profesional?",
        "Describe detalladamente el proceso completo desde la inscripción hasta la graduación"
    ]
    
    print("📝 PREGUNTAS SIMPLES (Respuestas Estructuradas)")
    print("-" * 50)
    
    for i, pregunta in enumerate(preguntas_simples, 1):
        print(f"\n{i}. 🤔 Pregunta: {pregunta}")
        
        try:
            response = orchestrator.process_question(
                pregunta=pregunta,
                session_id=f"test_simple_{i}"
            )
            
            tiempo = response.get('tiempo', 0)
            respuesta = response.get('respuesta', 'Sin respuesta')[:150] + "..."
            
            print(f"⚡ Tiempo: {tiempo:.2f}s")
            print(f"🤖 Respuesta: {respuesta}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🧠 PREGUNTAS COMPLEJAS (LLM)")
    print("-" * 50)
    
    for i, pregunta in enumerate(preguntas_complejas, 1):
        print(f"\n{i}. 🤔 Pregunta: {pregunta}")
        
        try:
            response = orchestrator.process_question(
                pregunta=pregunta,
                session_id=f"test_complex_{i}"
            )
            
            tiempo = response.get('tiempo', 0)
            respuesta = response.get('respuesta', 'Sin respuesta')[:200] + "..."
            
            print(f"⚡ Tiempo: {tiempo:.2f}s")
            print(f"🤖 Respuesta: {respuesta}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Pruebas del Sistema Híbrido Completadas")
    print("\n📊 Resumen:")
    print("• Preguntas simples → Respuestas rápidas y estructuradas")
    print("• Preguntas complejas → LLM para respuestas naturales")
    print("• Fallback automático si LLM falla o es muy lento")

if __name__ == "__main__":
    test_sistema_hibrido()