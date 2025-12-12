#!/usr/bin/env python3
"""
Test específico para consultas de inscripciones
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_inscripciones():
    """
    Probar consultas específicas sobre inscripciones
    """
    print("🧪 Probando Consultas de Inscripciones")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    # Consultas sobre inscripciones
    queries = [
        "¿Cómo me inscribo a un curso?",
        "¿Qué pasos debo seguir para inscribirme?",
        "¿Necesito registrarme primero?",
        "¿Puedo inscribirme sin crear una cuenta?",
        "¿Dónde me registro?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Consulta: {query}")
        print("-" * 60)
        
        try:
            response = orchestrator.process_question(query, session_id="test_inscripciones")
            
            print(f"✅ Éxito: {response.get('success', False)}")
            print(f"📝 Respuesta completa:")
            print(f"   {response.get('respuesta', 'N/A')}")
            print(f"📊 Confianza: {response.get('confianza', 0):.3f}")
            print(f"🔍 Documentos encontrados: {len(response.get('documentos_recuperados', []))}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Pruebas completadas")

if __name__ == '__main__':
    try:
        test_inscripciones()
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()