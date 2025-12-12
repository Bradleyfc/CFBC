#!/usr/bin/env python3
"""
Test script for enhanced news search functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_news_search():
    """Test the enhanced news search functionality"""
    
    print("🧪 Testing Enhanced News Search Functionality")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = ChatbotOrchestrator()
    
    # Test queries for news functionality
    test_queries = [
        # Latest news queries
        "¿Cuáles son las últimas noticias?",
        "Muéstrame las noticias más recientes",
        "¿Qué hay de nuevo en el centro?",
        
        # Topic-specific searches
        "Buscar noticias sobre cursos",
        "¿Hay alguna noticia que hable sobre eventos?",
        "Mostrar noticias sobre actividades",
        
        # General news queries
        "¿Qué noticias tienen?",
        "Información sobre el blog",
        "Ver noticias del centro"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 50)
        
        try:
            # Process the question
            result = orchestrator.process_question(query, f"test_session_{i}")
            
            if result.get('success', False):
                print(f"✅ Intent: {result.get('intencion', 'N/A')}")
                print(f"✅ Confidence: {result.get('confianza', 0):.2f}")
                print(f"✅ Documents found: {len(result.get('documentos_recuperados', []))}")
                print(f"✅ Response time: {result.get('tiempo', 0):.2f}s")
                print(f"\n📝 Response:\n{result.get('respuesta', 'No response')}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                print(f"📝 Response: {result.get('respuesta', 'No response')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("\n" + "="*60)
    
    print("\n🎯 Testing Complete!")

def test_blog_response_methods():
    """Test individual blog response methods"""
    
    print("\n🧪 Testing Individual Blog Response Methods")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Mock blog documents for testing
    mock_blog_docs = [
        {
            'text': '''Título: Nuevos Cursos de Idiomas 2024
Categoría: Educación
Resumen: El centro anuncia la apertura de nuevos cursos de idiomas para el año 2024
Contenido: Este año ofrecemos una amplia variedad de cursos de idiomas incluyendo inglés, alemán e italiano
Autor: Centro Fray Bartolomé
Fecha: 2024-01-15''',
            'content_type': 'blog.noticia',
            'categoria': 'blog'
        },
        {
            'text': '''Título: Evento Cultural de Fin de Año
Categoría: Eventos
Resumen: Gran evento cultural para celebrar el fin de año académico
Contenido: Invitamos a toda la comunidad a participar en nuestro evento cultural de fin de año
Autor: Centro Fray Bartolomé
Fecha: 2024-12-10''',
            'content_type': 'blog.noticia',
            'categoria': 'blog'
        }
    ]
    
    # Test latest news response
    print("\n📰 Testing Latest News Response:")
    print("-" * 40)
    latest_response = orchestrator._generate_latest_news_response(mock_blog_docs)
    print(latest_response)
    
    # Test news search response
    print("\n🔍 Testing News Search Response:")
    print("-" * 40)
    search_response = orchestrator._generate_news_search_response(mock_blog_docs, "buscar noticias sobre cursos")
    print(search_response)
    
    # Test single news response
    print("\n📄 Testing Single News Response:")
    print("-" * 40)
    single_response = orchestrator._generate_single_news_response(mock_blog_docs[0])
    print(single_response)
    
    # Test blog info extraction
    print("\n🔧 Testing Blog Info Extraction:")
    print("-" * 40)
    title, summary, date = orchestrator._extract_blog_info(mock_blog_docs[0]['text'])
    print(f"Title: {title}")
    print(f"Summary: {summary}")
    print(f"Date: {date}")
    
    # Test search terms extraction
    print("\n🔍 Testing Search Terms Extraction:")
    print("-" * 40)
    search_terms = orchestrator._extract_search_terms("buscar noticias sobre cursos de idiomas")
    print(f"Search terms: {search_terms}")

if __name__ == "__main__":
    test_news_search()
    test_blog_response_methods()