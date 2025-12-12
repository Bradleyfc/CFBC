#!/usr/bin/env python3
"""
Test script for specific topic news functionality
Testing queries like "¿qué noticia habla sobre [tema]?"
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_specific_topic_queries():
    """Test the new specific topic news functionality"""
    
    print("🎯 Testing Specific Topic News Queries")
    print("Testing: '¿qué noticia habla sobre [tema]?' functionality")
    print("=" * 70)
    
    orchestrator = ChatbotOrchestrator()
    
    # Test cases for specific topic queries
    test_queries = [
        # Direct topic questions
        "¿Qué noticia habla sobre cursos?",
        "¿Cuál noticia habla sobre idiomas?",
        "¿Qué noticias hablan sobre eventos?",
        "¿Cuál noticia habla sobre graduación?",
        "¿Qué noticia habla sobre teología?",
        "¿Cuáles noticias hablan sobre becas?",
        "¿Qué noticia habla sobre instalaciones?",
        "¿Cuál noticia habla sobre actividades?",
        
        # Variations
        "¿Qué noticia habla de diseño?",
        "¿Cuáles noticias hablan de educación?",
        "¿Qué noticia habla sobre laboratorio?",
        "¿Cuál noticia habla sobre renovación?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 50)
        
        try:
            # Process the question
            result = orchestrator.process_question(query, f"topic_test_{i}")
            
            if result.get('success', False):
                intent = result.get('intencion', 'N/A')
                confidence = result.get('confianza', 0)
                docs_count = len(result.get('documentos_recuperados', []))
                response = result.get('respuesta', '')
                
                print(f"✅ Intent: {intent} (confidence: {confidence:.2f})")
                print(f"✅ Documents found: {docs_count}")
                
                # Check if it's using the specific topic format
                if "noticias que hablan sobre" in response.lower():
                    print(f"✅ Using specific topic format: YES")
                else:
                    print(f"⚠️  Using specific topic format: NO")
                
                # Check if it shows only titles (no summaries)
                if "📅" in response and "resumen:" not in response.lower():
                    print(f"✅ Shows titles only: YES")
                else:
                    print(f"⚠️  Shows titles only: NO")
                
                # Show response
                print(f"\n📝 Response:\n{response}")
                
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                print(f"📝 Response: {result.get('respuesta', 'No response')}")
                
        except Exception as e:
            print(f"💥 Exception: {e}")
        
        print("\n" + "="*70)
    
    print("\n🎯 Testing Complete!")

def test_topic_extraction():
    """Test the topic extraction functionality"""
    
    print("\n🔧 Testing Topic Extraction")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    test_cases = [
        "¿Qué noticia habla sobre cursos?",
        "¿Cuál noticia habla sobre idiomas del centro?",
        "¿Qué noticias hablan sobre eventos?",
        "¿Cuál noticia habla de graduación?",
        "¿Qué noticia habla sobre teología en el blog?",
        "¿Cuáles noticias hablan sobre becas?"
    ]
    
    for query in test_cases:
        topic = orchestrator._extract_topic_from_question(query)
        print(f"Query: {query}")
        print(f"  → Extracted topic: '{topic}'")
        print()

def test_topic_matching():
    """Test the topic matching functionality"""
    
    print("\n🎯 Testing Topic Matching")
    print("=" * 50)
    
    orchestrator = ChatbotOrchestrator()
    
    # Mock content examples
    test_content = [
        {
            'content': 'título: nuevos cursos de idiomas categoría: educación resumen: el centro anuncia nuevos programas de inglés y alemán',
            'topics': ['cursos', 'idiomas', 'educación']
        },
        {
            'content': 'título: graduación de la promoción 2024 categoría: eventos resumen: celebramos los logros de nuestros egresados',
            'topics': ['graduación', 'eventos']
        },
        {
            'content': 'título: taller de teología categoría: actividades resumen: espacio de reflexión sobre fe contemporánea',
            'topics': ['teología', 'actividades']
        }
    ]
    
    for content_data in test_content:
        content = content_data['content']
        expected_topics = content_data['topics']
        
        print(f"Content: {content[:60]}...")
        print(f"Expected topics: {expected_topics}")
        
        for topic in expected_topics:
            matches = orchestrator._topic_matches_content(topic, content)
            relevance = orchestrator._calculate_topic_relevance(topic, content)
            print(f"  → Topic '{topic}': matches={matches}, relevance={relevance:.1f}")
        
        print()

if __name__ == "__main__":
    test_specific_topic_queries()
    test_topic_extraction()
    test_topic_matching()