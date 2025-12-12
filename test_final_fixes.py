#!/usr/bin/env python
"""
Script para probar las correcciones finales
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_final_fixes():
    """Probar las correcciones finales"""
    
    print("🧪 Probando correcciones finales")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    # Probar filtrado de profesores
    print("\n1. 🎓 Probando filtrado de profesores en cursos")
    print("-" * 40)
    
    try:
        response = orchestrator.process_question(
            "¿Qué cursos de idiomas hay?",
            "test_professors"
        )
        
        respuesta = response.get('respuesta', 'Sin respuesta')
        
        # Verificar si menciona profesores
        if 'mateo' in respuesta.lower() or 'profesor' in respuesta.lower():
            print("❌ PROBLEMA: Aún menciona profesores")
            print(f"   Respuesta: {respuesta[:200]}...")
        else:
            print("✅ CORRECTO: No menciona profesores")
            print(f"   Respuesta: {respuesta[:150]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Probar respuesta de requisitos
    print("\n2. 📋 Probando respuesta de requisitos")
    print("-" * 40)
    
    try:
        response = orchestrator.process_question(
            "¿Cuáles son los requisitos para inscribirme?",
            "test_requirements"
        )
        
        respuesta = response.get('respuesta', 'Sin respuesta')
        
        # Verificar si es una respuesta limpia
        if "Responde de manera clara" in respuesta:
            print("❌ PROBLEMA: Aún devuelve instrucciones del prompt")
        else:
            print("✅ CORRECTO: Respuesta limpia")
            print(f"   Respuesta: {respuesta[:150]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Pruebas completadas")

if __name__ == "__main__":
    test_final_fixes()