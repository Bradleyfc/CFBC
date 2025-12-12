#!/usr/bin/env python3
"""
Comprehensive test for all the professor mention and inscription time fixes
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_comprehensive_fixes():
    """Test various queries to ensure all fixes work"""
    orchestrator = ChatbotOrchestrator()
    
    # Test queries that should trigger different response methods
    test_queries = [
        # Time-remaining queries (should use _create_inscription_time_response)
        "cuanto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripcion",
        "cuántos días quedan para inscribirse en italiano",
        "tiempo restante para inscripción italiano",
        
        # General inscription queries (should use course response with professor filtering)
        "fechas de inscripción para el curso de italiano",
        "cuando empieza el curso de italiano",
        "información sobre inscripciones italiano",
        
        # Course queries (should use course response)
        "qué cursos hay disponibles",
        "información sobre cursos de idiomas",
        
        # Registration queries
        "como me registro en el sitio",
        "proceso de inscripción"
    ]
    
    print("=== Comprehensive Testing of Fixes ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")
        
        try:
            result = orchestrator.process_question(query, f"test_session_{i}")
            response = result.get('respuesta', '')
            
            # Check for professor mentions
            has_professor = any(prof in response.lower() for prof in ['profesor', 'mateo', 'docente', 'instructor'])
            
            # Check if response is complete
            is_complete = not (response.endswith(':') or response.endswith('|') or len(response.strip()) < 20)
            
            # Check success
            is_success = result.get('success', False)
            
            print(f"  ✅ Success: {is_success}")
            print(f"  ✅ No professor mentions: {not has_professor}")
            print(f"  ✅ Complete response: {is_complete}")
            print(f"  Intent: {result.get('intencion', 'unknown')}")
            print(f"  Response length: {len(response)} chars")
            
            if has_professor:
                print(f"  ❌ ERROR: Professor mentions found!")
                print(f"  Response preview: {response[:200]}...")
            
            if not is_complete:
                print(f"  ❌ ERROR: Incomplete response!")
                print(f"  Response: {response}")
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
        
        print()

if __name__ == "__main__":
    test_comprehensive_fixes()