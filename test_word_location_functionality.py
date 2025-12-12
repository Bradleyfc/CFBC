#!/usr/bin/env python3
"""
Test script for word/phrase location functionality
Testing queries like "¿dónde se menciona [palabra]?" and single word searches
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_word_location_queries():
    """Test the new word location functionality"""
    
    print("🎯 Testing Word/Phrase Location Functionality")
    print("Testing: '¿dónde se menciona [palabra/frase]?' functionality")
    print("=" * 70)
    
    orchestrator = ChatbotOrchestrator()
    
    # Test cases for word/phrase location queries
    test_queries = [
        # Word location questions
        "¿Dónde se menciona diseño?",
        "¿Donde se menciona idiomas?",
        "¿En qué lugar se menciona graduación?",
        "¿Dónde aparece teología?",
        "¿Donde se menciona laboratorio?",
        "¿Dónde se menciona becas?",
        "¿En qué lugar se menciona inglés?",
        "¿Donde aparece renovación?",
        
        # Phrase location questions
        "¿Dónde se menciona diseño gráfico?",
        "¿Donde se menciona cursos de idiomas?",
        "¿Dónde aparece centro fray bartolomé?",
        "¿En qué lugar se menciona programa de becas?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 50)
        
        try:
            # Process the question
            result = orchestrator.process_question(query, f"location_test_{i}")
            
            if result.get('success', False):
                intent = result.get('intencion', 'N/A')
                confidence = result.get('confianza', 0)
                docs_count = len(result.get('documentos_recuperados', []))
                response = result.get('respuesta', '')
                
                print(f"✅ Intent: {intent} (confidence: {confidence:.2f})")
                print(f"✅ Documents found: {docs_count}")
                
                # Check if it's using the word location format
                if "lugares donde se menciona" in response.lower():
                    print(f"✅ Using word location format: YES")
                else:
                    print(f"⚠️  Using word location format: NO")
                
                # Check if it shows locations by category
                categories_found = []
                if "en noticias:" in response.lower():
                    categories_found.append("Noticias")
                if "en cursos:" in response.lower():
                    categories_found.append("Cursos")
                if "en información de inscripciones:" in response.lower():
                    categories_found.append("Inscripciones")
                if "en información de contacto:" in response.lower():
                    categories_found.append("Contacto")
                
                print(f"✅ Categories found: {', '.join(categories_found) if categories_found else 'None'}")
                
                # Show response preview
                preview = response[:200].replace('\n', ' ')
                print(f"\n📝 Response preview: {preview}...")
                
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                print(f"📝 Response: {result.get('respuesta', 'No response')}")
                
        except Exception as e:
            print(f"💥 Exception: {e}")
        
        print("\n" + "="*70)
    
    print("\n🎯 Word Location Testing Complete!")

def test_single_word_searches():
    """Test single word search functionality"""
    
    print("\n🔍 Testing Single Word Search Functionality")
    print("Testing: Single word searches across the entire site")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Test cases for single word searches
    single_word_queries = [
        # Relevant words that should trigger site-wide search
        "diseño",
        "idiomas",
        "graduación",
        "teología",
        "becas",
        "laboratorio",
        "inscripción",
        "centro",
        
        # Course names
        "inglés",
        "alemán",
        
        # Common words that should use regular search
        "curso",
        "programa"
    ]
    
    for i, query in enumerate(single_word_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Process the question
            result = orchestrator.process_question(query, f"single_word_test_{i}")
            
            if result.get('success', False):
                response = result.get('respuesta', '')
                
                # Check if it's using single word search format
                if f"búsqueda de '{query}' en todo el sitio" in response.lower():
                    print(f"✅ Using single word search format: YES")
                    
                    # Count categories found
                    categories = []
                    if "en noticias y blog:" in response.lower():
                        categories.append("Noticias")
                    if "en cursos:" in response.lower():
                        categories.append("Cursos")
                    if "en información de inscripciones:" in response.lower():
                        categories.append("Inscripciones")
                    if "en información de contacto:" in response.lower():
                        categories.append("Contacto")
                    
                    print(f"✅ Categories with results: {', '.join(categories)}")
                    
                else:
                    print(f"⚠️  Using single word search format: NO")
                    print(f"   (Using regular search instead)")
                
                # Show brief preview
                lines = response.split('\n')[:3]
                preview = ' '.join(lines).replace('  ', ' ')[:150]
                print(f"📝 Preview: {preview}...")
                
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"💥 Exception: {e}")
    
    print("\n🎯 Single Word Search Testing Complete!")

def test_helper_methods():
    """Test the helper methods for word extraction and detection"""
    
    print("\n🔧 Testing Helper Methods")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    # Test word/phrase extraction
    print("📝 Testing Word/Phrase Extraction:")
    extraction_tests = [
        "¿Dónde se menciona diseño gráfico?",
        "¿Donde aparece centro fray bartolomé?",
        "¿En qué lugar se menciona programa de becas del centro?",
        "¿Dónde se menciona idiomas en el blog?"
    ]
    
    for query in extraction_tests:
        extracted = orchestrator._extract_word_phrase_from_question(query)
        print(f"  '{query}' → '{extracted}'")
    
    print("\n🔍 Testing Single Word Detection:")
    detection_tests = [
        ("diseño", True),
        ("¿qué es diseño?", False),
        ("idiomas centro", True),
        ("¿dónde está el centro?", False),
        ("graduación 2024", True),
        ("¿cuándo es la graduación?", False)
    ]
    
    for query, expected in detection_tests:
        is_single = orchestrator._is_single_word_search(query)
        status = "✅" if is_single == expected else "❌"
        print(f"  {status} '{query}' → {is_single} (expected: {expected})")
    
    print("\n🎯 Helper Methods Testing Complete!")

if __name__ == "__main__":
    test_word_location_queries()
    test_single_word_searches()
    test_helper_methods()