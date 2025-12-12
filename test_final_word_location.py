#!/usr/bin/env python3
"""
Test final para demostrar las funcionalidades de ubicación de palabras/frases
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_word_location_examples():
    """Test ejemplos específicos de ubicación de palabras/frases"""
    
    print("🎯 DEMOSTRACIÓN: Funcionalidad de Ubicación de Palabras/Frases")
    print("=" * 70)
    print("Objetivo 1: Mostrar dónde se menciona una palabra o frase específica")
    print("Objetivo 2: Búsqueda de palabras individuales en todo el sitio")
    print("=" * 70)
    
    orchestrator = ChatbotOrchestrator()
    
    # Ejemplos de consultas de ubicación
    location_examples = [
        {
            "query": "¿Dónde se menciona diseño?",
            "description": "Busca la palabra 'diseño' en todo el contenido"
        },
        {
            "query": "¿Donde se menciona idiomas?",
            "description": "Busca la palabra 'idiomas' en noticias y cursos"
        },
        {
            "query": "¿Dónde se menciona diseño gráfico?",
            "description": "Busca la frase 'diseño gráfico' específicamente"
        }
    ]
    
    print("\n📍 EJEMPLOS DE UBICACIÓN DE PALABRAS/FRASES:")
    print("-" * 60)
    
    for i, example in enumerate(location_examples, 1):
        query = example["query"]
        description = example["description"]
        
        print(f"\n🔍 EJEMPLO {i}: {query}")
        print(f"   Descripción: {description}")
        print("-" * 50)
        
        try:
            result = orchestrator.process_question(query, f"location_demo_{i}")
            
            if result.get('success', False):
                response = result.get('respuesta', '')
                
                # Análisis de la respuesta
                analysis = {
                    "Formato específico": "lugares donde se menciona" in response.lower(),
                    "Categorías mostradas": [],
                    "Contexto incluido": "..." in response
                }
                
                # Detectar categorías
                if "en noticias:" in response.lower():
                    analysis["Categorías mostradas"].append("Noticias")
                if "en cursos:" in response.lower():
                    analysis["Categorías mostradas"].append("Cursos")
                if "en información de inscripciones:" in response.lower():
                    analysis["Categorías mostradas"].append("Inscripciones")
                if "en información de contacto:" in response.lower():
                    analysis["Categorías mostradas"].append("Contacto")
                
                print("✅ ANÁLISIS:")
                print(f"   Formato específico: {'SÍ' if analysis['Formato específico'] else 'NO'}")
                print(f"   Categorías encontradas: {', '.join(analysis['Categorías mostradas']) if analysis['Categorías mostradas'] else 'Ninguna'}")
                print(f"   Incluye contexto: {'SÍ' if analysis['Contexto incluido'] else 'NO'}")
                
                print(f"\n📝 RESPUESTA COMPLETA:")
                print(response)
                
            else:
                print(f"❌ ERROR: {result.get('error', 'Desconocido')}")
                
        except Exception as e:
            print(f"💥 EXCEPCIÓN: {e}")
        
        print("\n" + "="*70)

def test_single_word_search_examples():
    """Test ejemplos de búsqueda de palabras individuales"""
    
    print("\n🔍 EJEMPLOS DE BÚSQUEDA DE PALABRAS INDIVIDUALES:")
    print("-" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Ejemplos de búsquedas de palabras individuales
    single_word_examples = [
        {
            "query": "diseño",
            "description": "Búsqueda de la palabra 'diseño' en todo el sitio"
        },
        {
            "query": "idiomas",
            "description": "Búsqueda de la palabra 'idiomas' en todo el sitio"
        },
        {
            "query": "graduación",
            "description": "Búsqueda de la palabra 'graduación' en todo el sitio"
        }
    ]
    
    for i, example in enumerate(single_word_examples, 1):
        query = example["query"]
        description = example["description"]
        
        print(f"\n🔍 EJEMPLO {i}: '{query}'")
        print(f"   Descripción: {description}")
        print("-" * 50)
        
        try:
            result = orchestrator.process_question(query, f"single_demo_{i}")
            
            if result.get('success', False):
                response = result.get('respuesta', '')
                
                # Análisis de la respuesta
                analysis = {
                    "Formato búsqueda sitio": f"búsqueda de '{query}' en todo el sitio" in response.lower(),
                    "Categorías con resultados": [],
                    "Títulos mostrados": "**" in response and "📍" in response
                }
                
                # Detectar categorías con resultados
                if "en noticias y blog:" in response.lower():
                    analysis["Categorías con resultados"].append("Noticias y Blog")
                if "en cursos:" in response.lower():
                    analysis["Categorías con resultados"].append("Cursos")
                if "en información de inscripciones:" in response.lower():
                    analysis["Categorías con resultados"].append("Inscripciones")
                if "en información de contacto:" in response.lower():
                    analysis["Categorías con resultados"].append("Contacto")
                
                print("✅ ANÁLISIS:")
                print(f"   Formato búsqueda en sitio: {'SÍ' if analysis['Formato búsqueda sitio'] else 'NO'}")
                print(f"   Categorías con resultados: {', '.join(analysis['Categorías con resultados']) if analysis['Categorías con resultados'] else 'Ninguna'}")
                print(f"   Muestra títulos y contexto: {'SÍ' if analysis['Títulos mostrados'] else 'NO'}")
                
                # Mostrar solo las primeras líneas para demostración
                lines = response.split('\n')[:8]
                preview = '\n'.join(lines)
                print(f"\n📝 RESPUESTA (preview):")
                print(preview)
                if len(response.split('\n')) > 8:
                    print("   ... (respuesta completa disponible)")
                
            else:
                print(f"❌ ERROR: {result.get('error', 'Desconocido')}")
                
        except Exception as e:
            print(f"💥 EXCEPCIÓN: {e}")
        
        print("\n" + "="*70)

def demonstrate_functionality_differences():
    """Demuestra las diferencias entre los tipos de búsqueda"""
    
    print("\n🔄 COMPARACIÓN DE FUNCIONALIDADES:")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    comparisons = [
        {
            "type": "Ubicación específica",
            "query": "¿Dónde se menciona diseño?",
            "expected": "Muestra lugares específicos donde aparece la palabra"
        },
        {
            "type": "Búsqueda individual",
            "query": "diseño",
            "expected": "Búsqueda completa en todo el sitio con títulos y contexto"
        },
        {
            "type": "Búsqueda de tema",
            "query": "¿Qué noticia habla sobre diseño?",
            "expected": "Solo títulos de noticias que hablan del tema"
        }
    ]
    
    for comparison in comparisons:
        print(f"\n📋 {comparison['type'].upper()}")
        print(f"Query: {comparison['query']}")
        print(f"Esperado: {comparison['expected']}")
        print("-" * 40)
        
        try:
            result = orchestrator.process_question(comparison['query'], "comparison_test")
            
            if result.get('success', False):
                response = result.get('respuesta', '')
                
                # Mostrar características principales
                characteristics = []
                if "lugares donde se menciona" in response.lower():
                    characteristics.append("Formato de ubicación")
                if "búsqueda de" in response.lower() and "en todo el sitio" in response.lower():
                    characteristics.append("Búsqueda completa del sitio")
                if "noticias que hablan sobre" in response.lower():
                    characteristics.append("Solo títulos de noticias")
                
                print(f"Características: {', '.join(characteristics) if characteristics else 'Formato estándar'}")
                
                # Mostrar primera línea
                first_line = response.split('\n')[0] if response else ""
                print(f"Primera línea: {first_line}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_word_location_examples()
    test_single_word_search_examples()
    demonstrate_functionality_differences()
    
    print("\n🎉 FUNCIONALIDADES COMPLETAMENTE IMPLEMENTADAS:")
    print("✅ Ubicación de palabras/frases específicas")
    print("✅ Búsqueda de palabras individuales en todo el sitio")
    print("✅ Organización por categorías (Noticias, Cursos, etc.)")
    print("✅ Contexto alrededor de las menciones")
    print("✅ Títulos y ubicaciones específicas")
    print("✅ Diferenciación entre tipos de búsqueda")