#!/usr/bin/env python3
"""
Test script to verify professor mention fixes and inscription time response
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_professor_filtering():
    """Test the improved professor filtering methods"""
    orchestrator = ChatbotOrchestrator()
    
    # Test data that contains professor mentions (similar to the problematic response)
    test_data = [
        "Curso de Italiano | Profesor: Mateo vi | Fecha de inicio: 2025-12-17 | Fecha límite de inscripción: 2025-12-16",
        "Estado: En etapa de inscripción | Profesor: Mateo vi | Fecha de inicio: 2025-12-12 | Fecha límite de inscripción:",
        "Diplomado de Italiano | Estado: En etapa de inscripción | Profesor: Mateo vi | Fecha de inicio: 2025-12-12 | Fecha límite de inscripción: 2025-12-11"
    ]
    
    print("=== Testing Professor Filtering Methods ===\n")
    
    for i, data in enumerate(test_data, 1):
        print(f"Test {i}:")
        print(f"Original: {data}")
        
        # Test improved method
        improved_result = orchestrator._remove_professor_mentions_improved(data)
        print(f"Improved: {improved_result}")
        
        # Test selective method
        selective_result = orchestrator._remove_professor_mentions_selective(data)
        print(f"Selective: {selective_result}")
        
        print()

def test_inscription_time_query():
    """Test the specific problematic query"""
    orchestrator = ChatbotOrchestrator()
    
    # The exact query that was problematic
    query = "cuanto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripcion"
    
    print("=== Testing Inscription Time Query ===\n")
    print(f"Query: {query}")
    
    try:
        result = orchestrator.process_question(query, "test_session")
        
        print(f"Success: {result.get('success', False)}")
        print(f"Intent: {result.get('intencion', 'unknown')}")
        print(f"Confidence: {result.get('confianza', 0)}")
        print(f"Response time: {result.get('tiempo', 0):.2f}s")
        print(f"Documents found: {len(result.get('documentos_recuperados', []))}")
        
        response = result.get('respuesta', '')
        print(f"\nResponse:\n{response}")
        
        # Check for professor mentions in response
        if any(prof in response.lower() for prof in ['profesor', 'mateo', 'docente', 'instructor']):
            print("\n❌ ERROR: Professor mentions found in response!")
        else:
            print("\n✅ SUCCESS: No professor mentions found in response!")
        
        # Check if response is complete (not cut off)
        if response.endswith(':') or response.endswith('|') or len(response) < 50:
            print("❌ ERROR: Response appears to be incomplete!")
        else:
            print("✅ SUCCESS: Response appears to be complete!")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_course_response_filtering():
    """Test course response generation with professor filtering"""
    orchestrator = ChatbotOrchestrator()
    
    # Test queries that might trigger course responses
    test_queries = [
        "información sobre el curso de italiano",
        "fechas de inscripción para italiano",
        "cuando empieza el curso de italiano"
    ]
    
    print("=== Testing Course Response Filtering ===\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        
        try:
            result = orchestrator.process_question(query, "test_session")
            response = result.get('respuesta', '')
            
            # Check for professor mentions
            if any(prof in response.lower() for prof in ['profesor', 'mateo', 'docente', 'instructor']):
                print(f"❌ ERROR: Professor mentions found!")
                print(f"Response: {response[:200]}...")
            else:
                print(f"✅ SUCCESS: No professor mentions!")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print()

if __name__ == "__main__":
    print("Testing Professor Mention Fixes and Inscription Time Response\n")
    
    # Test 1: Professor filtering methods
    test_professor_filtering()
    
    # Test 2: Specific problematic query
    test_inscription_time_query()
    
    # Test 3: Course response filtering
    test_course_response_filtering()
    
    print("Testing completed!")