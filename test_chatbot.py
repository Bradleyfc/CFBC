#!/usr/bin/env python
"""
Script de pruebas para verificar que el chatbot funciona correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

def test_semantic_search():
    """Probar búsqueda semántica"""
    print("🔍 Probando búsqueda semántica...")
    
    try:
        from chatbot.services.semantic_search import SemanticSearchService
        
        search = SemanticSearchService()
        
        # Probar embedding
        embedding = search.generate_embedding('¿Cuándo empiezan las inscripciones?')
        print(f"✅ Embeddings funcionando (dimensión: {len(embedding)})")
        
        # Probar búsqueda
        results = search.search('inscripciones', top_k=3)
        print(f"✅ Búsqueda funcionando ({len(results)} resultados)")
        
        for i, result in enumerate(results):
            score = result.get('score', 0)
            content = result.get('content', '')[:80]
            print(f"  {i+1}. Score: {score:.3f} - {content}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en búsqueda semántica: {e}")
        return False

def test_llm_generator():
    """Probar generador LLM"""
    print("\n🤖 Probando LLM...")
    
    try:
        from chatbot.services.llm_generator import LLMGeneratorService
        
        llm = LLMGeneratorService()
        print(f"✅ LLM disponible: {llm.is_available()}")
        
        if llm.is_available():
            response = llm.generate_response(
                '¿Cuándo empiezan las inscripciones?', 
                ['Las inscripciones para el Centro de Formación Bíblica Católica empiezan en enero de cada año.']
            )
            print(f"✅ LLM funcionando")
            print(f"   Respuesta: {response[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en LLM: {e}")
        return False

def test_orchestrator():
    """Probar orquestador completo"""
    print("\n🎭 Probando orquestador completo...")
    
    try:
        from chatbot.services.orchestrator import ChatbotOrchestrator
        
        orchestrator = ChatbotOrchestrator()
        
        # Probar pregunta sobre inscripciones
        response = orchestrator.process_question(
            pregunta="¿Cuándo empiezan las inscripciones?",
            session_id="test_session"
        )
        
        print("✅ Orquestador funcionando")
        print(f"   Respuesta: {response.get('respuesta', '')[:150]}...")
        print(f"   Fuentes: {len(response.get('fuentes', []))}")
        print(f"   Confianza: {response.get('confianza', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en orquestador: {e}")
        return False

def test_api_endpoints():
    """Probar endpoints de la API"""
    print("\n🌐 Probando API endpoints...")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Probar endpoint de pregunta
        response = client.post('/chatbot/ask/', {
            'pregunta': '¿Cuándo empiezan las inscripciones?'
        }, content_type='application/json')
        
        print(f"✅ API /chatbot/ask/ funcionando (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Respuesta: {data.get('respuesta', '')[:100]}...")
        
        # Probar endpoint de estado
        response = client.get('/chatbot/status/')
        print(f"✅ API /chatbot/status/ funcionando (status: {response.status_code})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en API: {e}")
        return False

def test_database():
    """Probar modelos de base de datos"""
    print("\n🗄️ Probando base de datos...")
    
    try:
        from chatbot.models import CategoriaFAQ, FAQ, FAQVariation
        
        # Contar registros
        categorias = CategoriaFAQ.objects.count()
        faqs = FAQ.objects.count()
        variaciones = FAQVariation.objects.count()
        
        print(f"✅ Base de datos funcionando")
        print(f"   Categorías: {categorias}")
        print(f"   FAQs: {faqs}")
        print(f"   Variaciones: {variaciones}")
        
        # Mostrar algunas FAQs
        print("\n📋 Primeras 3 FAQs:")
        for faq in FAQ.objects.all()[:3]:
            print(f"   - {faq.pregunta[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 Iniciando pruebas del chatbot semántico CFBC")
    print("=" * 60)
    
    tests = [
        test_database,
        test_semantic_search,
        test_llm_generator,
        test_orchestrator,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Error ejecutando {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El chatbot está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores anteriores.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)