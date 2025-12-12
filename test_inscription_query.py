#!/usr/bin/env python3
"""
Test script to debug the specific inscription query issue
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')

django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_inscription_query():
    """Test the specific inscription query that's causing problems"""
    
    print("🧪 Testing Inscription Query Issue")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # The exact query that's causing problems
    test_query = "¿cuánto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripción?"
    
    print(f"🔍 Query: {test_query}")
    print("-" * 60)
    
    try:
        # Get the raw documents first to see what data we're working with
        documents = orchestrator.semantic_search.search(
            query=test_query,
            top_k=5,
            categoria='cursos'
        )
        
        print(f"📊 Found {len(documents)} documents")
        print("\n📄 Raw document content:")
        
        for i, doc in enumerate(documents[:3], 1):
            text = doc.get('text', '').strip()
            print(f"\n{i}. Document (score: {doc.get('score', 0):.3f}):")
            print(f"   Content: {text[:200]}...")
            
            # Check if it contains professor mentions
            if 'mateo' in text.lower() or 'profesor' in text.lower():
                print(f"   ⚠️  Contains professor mentions!")
        
        print("\n" + "="*60)
        
        # Now test the full orchestrator response
        result = orchestrator.process_question(test_query, "inscription_test")
        
        if result.get('success', False):
            response = result.get('respuesta', '')
            
            print("📝 ORCHESTRATOR RESPONSE:")
            print(response)
            print("\n" + "="*60)
            
            # Analyze the response
            print("🔍 RESPONSE ANALYSIS:")
            
            # Check for professor mentions
            professor_words = ['profesor', 'profesora', 'docente', 'instructor', 'mateo']
            found_professors = [word for word in professor_words if word.lower() in response.lower()]
            
            if found_professors:
                print(f"❌ PROFESSOR MENTIONS FOUND: {', '.join(found_professors)}")
            else:
                print("✅ NO PROFESSOR MENTIONS")
            
            # Check if response is complete
            if response.endswith('...') or len(response) < 50:
                print("❌ RESPONSE APPEARS INCOMPLETE")
                print(f"   Length: {len(response)} characters")
            else:
                print("✅ RESPONSE APPEARS COMPLETE")
                print(f"   Length: {len(response)} characters")
            
            # Check for useful information
            useful_keywords = ['fecha', 'límite', 'inscripción', 'italiano', 'tiempo', 'días']
            found_keywords = [kw for kw in useful_keywords if kw in response.lower()]
            print(f"📊 USEFUL KEYWORDS FOUND: {', '.join(found_keywords) if found_keywords else 'None'}")
            
        else:
            print(f"❌ ORCHESTRATOR FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

def test_professor_filtering_directly():
    """Test the professor filtering method directly on sample course data"""
    
    print("\n🔧 Testing Professor Filtering on Course Data")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Sample course data that might contain professor mentions
    sample_data = [
        "Curso de Italiano | Profesor: Mateo vi | Fecha de inicio: 2025-12-17 | Fecha límite de inscripción: 2025-12-16",
        "Diplomado de Italiano | Estado: En etapa de inscripción | Profesor: Mateo vi | Fecha límite de inscripción: 2025-12-16",
        "Curso: Italiano | Área: Idiomas | Profesor: Juan Pérez | Horario: Lunes 9am | Estado: Disponible",
        "Inscripciones para Curso de Italiano: Estado actual: Abierta | Fecha límite de inscripción: 2025-12-16 | Fecha de inicio: 2025-12-17"
    ]
    
    print("Testing both old and new professor filtering methods:")
    
    for i, data in enumerate(sample_data, 1):
        print(f"\n🧪 Test {i}:")
        print(f"Original: {data}")
        
        try:
            # Test old method
            old_cleaned = orchestrator._remove_all_professor_mentions(data)
            print(f"Old method: {old_cleaned}")
            
            # Test new method
            new_cleaned = orchestrator._remove_professor_mentions_improved(data)
            print(f"New method: {new_cleaned}")
            
            # Check which one is better
            old_has_prof = any(word in old_cleaned.lower() for word in ['profesor', 'mateo', 'juan'])
            new_has_prof = any(word in new_cleaned.lower() for word in ['profesor', 'mateo', 'juan'])
            
            print(f"Old method clean: {'❌' if old_has_prof else '✅'}")
            print(f"New method clean: {'❌' if new_has_prof else '✅'}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_inscription_query()
    test_professor_filtering_directly()