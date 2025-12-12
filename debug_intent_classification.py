#!/usr/bin/env python3
"""
Debug script to check intent classification for the problematic query
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.intent_classifier import IntentClassifier

def debug_intent_classification():
    """Debug the intent classification for the problematic query"""
    
    query = "cuanto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripcion"
    
    print(f"Query: {query}")
    print(f"Query lower: {query.lower()}")
    
    # Test intent classifier
    intent_classifier = IntentClassifier()
    
    should_filter, intent = intent_classifier.should_filter_by_intent(query)
    primary_intent, confidence = intent_classifier.get_primary_intent(query)
    
    print(f"\nIntent Classification:")
    print(f"Should filter: {should_filter}")
    print(f"Intent: {intent}")
    print(f"Primary intent: {primary_intent}")
    print(f"Confidence: {confidence}")
    
    # Test enhanced detection patterns
    query_lower = query.lower()
    
    print(f"\nEnhanced Detection Tests:")
    
    # Time-remaining patterns
    time_patterns = ['cuánto tiempo me queda', 'cuanto tiempo me queda', 'cuánto tiempo queda', 'cuanto tiempo queda', 'tiempo restante', 'tiempo que queda', 'cuántos días quedan', 'cuantos dias quedan']
    time_match = any(pattern in query_lower for pattern in time_patterns)
    print(f"Time-remaining patterns match: {time_match}")
    if time_match:
        for pattern in time_patterns:
            if pattern in query_lower:
                print(f"  - Matched pattern: '{pattern}'")
    
    # Registration patterns
    reg_patterns = ['registr', 'crear cuenta', 'login', 'iniciar sesión', 'entrar', 'acceder', 'usuario', 'contraseña', 'olvidé']
    reg_match = any(word in query_lower for word in reg_patterns)
    print(f"Registration patterns match: {reg_match}")
    
    # Location patterns
    loc_patterns = ['dónde se menciona', 'donde se menciona', 'en qué lugar se menciona', 'en que lugar se menciona', 'dónde aparece', 'donde aparece']
    loc_match = any(pattern in query_lower for pattern in loc_patterns)
    print(f"Location patterns match: {loc_match}")
    
    # General inscription patterns
    insc_patterns = ['inscripción', 'inscribir', 'matrícula', 'fecha', 'cuándo', 'hasta cuándo', 'límite', 'disponible', 'abierta', 'empieza', 'inicia', 'comienza', 'termina']
    insc_match = any(word in query_lower for word in insc_patterns)
    print(f"General inscription patterns match: {insc_match}")
    if insc_match:
        for pattern in insc_patterns:
            if pattern in query_lower:
                print(f"  - Matched pattern: '{pattern}'")

def debug_orchestrator_flow():
    """Debug the orchestrator flow for the problematic query"""
    
    orchestrator = ChatbotOrchestrator()
    query = "cuanto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripcion"
    
    print(f"\n=== Debugging Orchestrator Flow ===")
    print(f"Query: {query}")
    
    # Test semantic search
    documents = orchestrator.semantic_search.search(
        query=query,
        top_k=5,
        categoria=None
    )
    
    print(f"\nSemantic Search Results:")
    print(f"Found {len(documents)} documents")
    
    for i, doc in enumerate(documents[:3], 1):
        print(f"\nDocument {i}:")
        print(f"  Content type: {doc.get('content_type', 'unknown')}")
        print(f"  Category: {doc.get('categoria', 'unknown')}")
        print(f"  Score: {doc.get('score', 0):.3f}")
        print(f"  Text: {doc.get('text', '')[:200]}...")
    
    # Test document categorization
    faq_docs = [doc for doc in documents if doc.get('content_type') == 'chatbot.faq']
    course_docs = [doc for doc in documents if doc.get('content_type') == 'principal.curso']
    blog_docs = [doc for doc in documents if doc.get('content_type') == 'blog.noticia']
    
    print(f"\nDocument Categorization:")
    print(f"FAQ docs: {len(faq_docs)}")
    print(f"Course docs: {len(course_docs)}")
    print(f"Blog docs: {len(blog_docs)}")
    
    # Check which response method would be called
    if faq_docs:
        print(f"\nWould call: _generate_faq_response")
        # Test FAQ response
        faq_doc = faq_docs[0]
        print(f"FAQ doc text: {faq_doc.get('text', '')[:300]}...")
    elif course_docs:
        print(f"\nWould call: _generate_course_response")
        # Test course response detection
        query_lower = query.lower()
        if any(pattern in query_lower for pattern in ['cuánto tiempo me queda', 'cuanto tiempo me queda']):
            print(f"Should trigger: _create_inscription_time_response")
        else:
            print(f"Would use general course response")
    else:
        print(f"\nWould call: _handle_no_results or _generate_generic_response")

if __name__ == "__main__":
    print("Debugging Intent Classification and Orchestrator Flow\n")
    
    debug_intent_classification()
    debug_orchestrator_flow()
    
    print("\nDebugging completed!")