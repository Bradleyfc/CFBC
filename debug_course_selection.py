#!/usr/bin/env python3
"""
Debug course selection logic
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def debug_course_selection():
    """Debug why the wrong course is being selected"""
    orchestrator = ChatbotOrchestrator()
    
    # Get the actual course documents
    query = "cuanto tiempo me queda para inscribirme en el curso de italiano"
    documents = orchestrator.semantic_search.search(query=query, top_k=5, categoria=None)
    course_docs = [doc for doc in documents if doc.get('content_type') == 'principal.curso']
    
    print("=== Debugging Course Selection ===\n")
    
    for i, doc in enumerate(course_docs[:3], 1):
        text = doc.get('text', '').strip()
        print(f"Document {i}:")
        print(f"Text: {text}")
        print(f"Has 'italiano': {'italiano' in text.lower()}")
        print(f"Has 'fecha': {'fecha' in text.lower()}")
        print(f"Has 'inscripción': {'inscripción' in text.lower()}")
        print(f"Has 'en etapa de inscripción': {'en etapa de inscripción' in text.lower()}")
        print(f"Has 'inscripciones abiertas': {'inscripciones abiertas' in text.lower()}")
        print()

if __name__ == "__main__":
    debug_course_selection()