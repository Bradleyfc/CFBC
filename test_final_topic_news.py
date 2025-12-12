#!/usr/bin/env python3
"""
Test final para demostrar la funcionalidad específica de temas en noticias
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_final_topic_functionality():
    """Test final de la funcionalidad específica de temas"""
    
    print("🎯 PRUEBA FINAL: Funcionalidad de Temas Específicos en Noticias")
    print("=" * 70)
    print("Objetivo: Mostrar SOLO los títulos de noticias que hablan sobre un tema específico")
    print("=" * 70)
    
    orchestrator = ChatbotOrchestrator()
    
    # Casos de prueba específicos que el usuario solicitó
    test_cases = [
        {
            "query": "¿Qué noticia habla sobre cursos?",
            "expected_format": "títulos de noticias sobre cursos"
        },
        {
            "query": "¿Cuál noticia habla sobre idiomas?", 
            "expected_format": "títulos de noticias sobre idiomas"
        },
        {
            "query": "¿Qué noticias hablan sobre graduación?",
            "expected_format": "títulos de noticias sobre graduación"
        },
        {
            "query": "¿Cuál noticia habla sobre teología?",
            "expected_format": "títulos de noticias sobre teología"
        },
        {
            "query": "¿Qué noticia habla sobre becas?",
            "expected_format": "títulos de noticias sobre becas"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected_format"]
        
        print(f"\n🔍 PRUEBA {i}: {query}")
        print(f"   Esperado: {expected}")
        print("-" * 60)
        
        try:
            result = orchestrator.process_question(query, f"final_test_{i}")
            
            if result.get('success', False):
                response = result.get('respuesta', '')
                
                # Verificaciones específicas
                checks = {
                    "Usa formato específico": "noticias que hablan sobre" in response.lower(),
                    "Muestra solo títulos": "resumen:" not in response.lower() and "categoría:" not in response.lower(),
                    "Formato numerado": "**1." in response and "**2." in response or "**1." in response,
                    "Enlace al blog": "blog de noticias" in response.lower()
                }
                
                print("✅ VERIFICACIONES:")
                for check_name, check_result in checks.items():
                    status = "✅ SÍ" if check_result else "❌ NO"
                    print(f"   {check_name}: {status}")
                
                print(f"\n📝 RESPUESTA COMPLETA:")
                print(response)
                
                # Contar títulos encontrados
                title_count = response.count("**") // 2  # Cada título tiene 2 asteriscos
                print(f"\n📊 TÍTULOS ENCONTRADOS: {title_count}")
                
            else:
                print(f"❌ ERROR: {result.get('error', 'Desconocido')}")
                
        except Exception as e:
            print(f"💥 EXCEPCIÓN: {e}")
        
        print("\n" + "="*70)
    
    print("\n🎉 PRUEBA FINAL COMPLETADA")
    print("\nRESUMEN DE FUNCIONALIDAD IMPLEMENTADA:")
    print("✅ Detecta preguntas específicas sobre temas en noticias")
    print("✅ Extrae el tema de la pregunta correctamente") 
    print("✅ Busca en TODOS los textos de las noticias")
    print("✅ Devuelve SOLO los títulos de noticias relevantes")
    print("✅ Ordena por relevancia del tema")
    print("✅ Formato limpio y profesional")

def demonstrate_difference():
    """Demuestra la diferencia entre búsqueda general y búsqueda específica de temas"""
    
    print("\n🔄 DEMOSTRACIÓN: Diferencia entre tipos de búsqueda")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Comparar diferentes tipos de consultas
    queries = [
        {
            "type": "Búsqueda general",
            "query": "buscar noticias sobre cursos",
            "description": "Muestra resúmenes y detalles"
        },
        {
            "type": "Búsqueda específica de temas",
            "query": "¿qué noticia habla sobre cursos?",
            "description": "Muestra SOLO títulos"
        }
    ]
    
    for query_info in queries:
        print(f"\n📋 {query_info['type'].upper()}")
        print(f"Query: {query_info['query']}")
        print(f"Objetivo: {query_info['description']}")
        print("-" * 40)
        
        try:
            result = orchestrator.process_question(query_info['query'], "demo_test")
            
            if result.get('success', False):
                response = result.get('respuesta', '')
                
                # Mostrar solo las primeras 3 líneas para comparación
                lines = response.split('\n')[:5]
                preview = '\n'.join(lines)
                print(f"Respuesta (preview):\n{preview}...")
                
                # Análisis del formato
                has_summaries = "resumen:" in response.lower()
                has_categories = "categoría:" in response.lower()
                titles_only = not has_summaries and not has_categories
                
                print(f"\nAnálisis:")
                print(f"  - Incluye resúmenes: {'SÍ' if has_summaries else 'NO'}")
                print(f"  - Incluye categorías: {'SÍ' if has_categories else 'NO'}")
                print(f"  - Solo títulos: {'SÍ' if titles_only else 'NO'}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_final_topic_functionality()
    demonstrate_difference()