#!/usr/bin/env python3
"""
Test script to debug the inscription time response method
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_inscription_time_method():
    """Test the inscription time response method directly"""
    orchestrator = ChatbotOrchestrator()
    
    # Get the actual course documents for the query
    query = "cuanto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripcion"
    
    documents = orchestrator.semantic_search.search(
        query=query,
        top_k=5,
        categoria=None
    )
    
    # Filter for course documents
    course_docs = [doc for doc in documents if doc.get('content_type') == 'principal.curso']
    
    print("=== Testing Inscription Time Method ===\n")
    print(f"Found {len(course_docs)} course documents")
    
    for i, doc in enumerate(course_docs[:3], 1):
        print(f"\nCourse Document {i}:")
        print(f"Text: {doc.get('text', '')}")
        print(f"Category: {doc.get('categoria', 'unknown')}")
        print(f"Score: {doc.get('score', 0):.3f}")
    
    if course_docs:
        print(f"\n=== Testing _create_inscription_time_response ===")
        response = orchestrator._create_inscription_time_response(course_docs, query)
        print(f"Response:\n{response}")
        
        # Check for professor mentions
        if any(prof in response.lower() for prof in ['profesor', 'mateo', 'docente', 'instructor']):
            print("\n❌ ERROR: Professor mentions found!")
        else:
            print("\n✅ SUCCESS: No professor mentions!")
    else:
        print("\n❌ No course documents found!")

if __name__ == "__main__":
    test_inscription_time_method()