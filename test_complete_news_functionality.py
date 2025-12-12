#!/usr/bin/env python3
"""
Comprehensive test for the complete news search functionality
Testing all the requirements from the user query
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_news_search_requirements():
    """Test all the specific requirements mentioned by the user"""
    
    print("🎯 Testing Complete News Search Functionality")
    print("Testing: buscar una palabra dentro de las noticias")
    print("Testing: mostrar las últimas noticias") 
    print("Testing: buscar tema específico dentro de textos de noticias")
    print("=" * 70)
    
    orchestrator = ChatbotOrchestrator()
    
    # Test cases covering all user requirements
    test_cases = [
        {
            "category": "🔍 Búsqueda de palabras específicas",
            "queries": [
                "buscar cursos en las noticias",
                "buscar idiomas en las noticias", 
                "buscar teología en las noticias",
                "buscar graduación en las noticias"
            ]
        },
        {
            "category": "📰 Últimas noticias",
            "queries": [
                "¿cuáles son las últimas noticias?",
                "muéstrame las noticias más recientes",
                "¿qué hay de nuevo?",
                "últimas noticias del centro"
            ]
        },
        {
            "category": "🎯 Búsqueda por tema específico",
            "queries": [
                "¿hay alguna noticia que hable sobre eventos?",
                "noticia sobre actividades",
                "¿qué noticias hablan de becas?",
                "noticias sobre instalaciones"
            ]
        },
        {
            "category": "📖 Consultas generales de noticias",
            "queries": [
                "¿qué noticias tienen?",
                "información del blog",
                "ver todas las noticias",
                "mostrar noticias disponibles"
            ]
        }
    ]
    
    for test_category in test_cases:
        print(f"\n{test_category['category']}")
        print("-" * 60)
        
        for i, query in enumerate(test_category['queries'], 1):
            print(f"\n{i}. Query: {query}")
            
            try:
                result = orchestrator.process_question(query, f"test_{i}")
                
                if result.get('success', False):
                    intent = result.get('intencion', 'N/A')
                    confidence = result.get('confianza', 0)
                    docs_count = len(result.get('documentos_recuperados', []))
                    response = result.get('respuesta', '')
                    
                    print(f"   ✅ Intent: {intent} (confidence: {confidence:.2f})")
                    print(f"   ✅ Documents found: {docs_count}")
                    
                    # Check if response contains news content
                    if any(keyword in response.lower() for keyword in ['noticias', 'título:', 'fecha:', 'blog']):
                        print(f"   ✅ Contains news content: YES")
                    else:
                        print(f"   ⚠️  Contains news content: NO")
                    
                    # Show first 150 characters of response
                    preview = response[:150].replace('\n', ' ')
                    print(f"   📝 Response preview: {preview}...")
                    
                else:
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   💥 Exception: {e}")
        
        print("\n" + "="*70)
    
    print("\n🎯 Testing Complete!")

def test_specific_search_within_news():
    """Test the ability to search for specific words within news content"""
    
    print("\n🔍 Testing Specific Word Search Within News")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    # Test searching for specific terms that should be in the news content
    search_tests = [
        {
            "query": "buscar 'graduación' en las noticias",
            "expected_terms": ["graduación", "promoción", "celebrando"]
        },
        {
            "query": "buscar 'teología' en las noticias", 
            "expected_terms": ["teología", "fe", "contemporánea"]
        },
        {
            "query": "buscar 'idiomas' en las noticias",
            "expected_terms": ["idiomas", "laboratorio", "renovado"]
        },
        {
            "query": "buscar 'becas' en las noticias",
            "expected_terms": ["becas", "programa", "oportunidades"]
        }
    ]
    
    for test in search_tests:
        query = test["query"]
        expected_terms = test["expected_terms"]
        
        print(f"\n🔍 Testing: {query}")
        print(f"   Expected terms: {', '.join(expected_terms)}")
        
        try:
            result = orchestrator.process_question(query, "search_test")
            
            if result.get('success', False):
                response = result.get('respuesta', '').lower()
                
                # Check if expected terms are found in response
                found_terms = []
                for term in expected_terms:
                    if term.lower() in response:
                        found_terms.append(term)
                
                print(f"   ✅ Found terms: {', '.join(found_terms) if found_terms else 'None'}")
                print(f"   ✅ Search success: {len(found_terms) > 0}")
                
                # Check if it's showing search results format
                if "noticias encontradas" in response or "resultados de búsqueda" in response:
                    print(f"   ✅ Using search format: YES")
                else:
                    print(f"   ⚠️  Using search format: NO")
                    
            else:
                print(f"   ❌ Query failed: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")

def test_latest_news_functionality():
    """Test the latest news functionality specifically"""
    
    print("\n📰 Testing Latest News Functionality")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    latest_news_queries = [
        "últimas noticias",
        "noticias recientes", 
        "¿qué hay de nuevo?",
        "mostrar las noticias más nuevas"
    ]
    
    for query in latest_news_queries:
        print(f"\n📰 Testing: {query}")
        
        try:
            result = orchestrator.process_question(query, "latest_test")
            
            if result.get('success', False):
                response = result.get('respuesta', '')
                
                # Check if it's using the latest news format
                if "últimas noticias del centro" in response.lower():
                    print(f"   ✅ Using latest news format: YES")
                else:
                    print(f"   ⚠️  Using latest news format: NO")
                
                # Check if it shows multiple news items
                if response.count("**") >= 4:  # At least 2 news items (2 titles = 4 **)
                    print(f"   ✅ Shows multiple news: YES")
                else:
                    print(f"   ⚠️  Shows multiple news: NO")
                
                # Check if it includes dates
                if "📅" in response:
                    print(f"   ✅ Includes dates: YES")
                else:
                    print(f"   ⚠️  Includes dates: NO")
                    
            else:
                print(f"   ❌ Query failed: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")

if __name__ == "__main__":
    test_news_search_requirements()
    test_specific_search_within_news()
    test_latest_news_functionality()