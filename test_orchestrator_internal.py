#!/usr/bin/env python3
"""
Test orchestrator internal methods
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator
from chatbot.services.semantic_search import SemanticSearchService
from chatbot.services.intent_classifier import IntentClassifier

def test_orchestrator_internal():
    """
    Test orchestrator internal methods step by step
    """
    print("🔍 Orchestrator Internal Debug")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    intent_classifier = IntentClassifier()
    
    query = "¿Dónde está ubicado el centro?"
    
    print(f"Consulta: {query}")
    print("-" * 40)
    
    # Step 1: Intent classification
    should_filter, intent = intent_classifier.should_filter_by_intent(query)
    primary_intent, confidence = intent_classifier.get_primary_intent(query)
    
    print(f"1. Intent classification:")
    print(f"   Should filter: {should_filter}")
    print(f"   Intent: {intent}")
    print(f"   Primary intent: {primary_intent}")
    print(f"   Confidence: {confidence}")
    
    # Step 2: Category mapping
    categoria = orchestrator._map_intent_to_category(intent) if should_filter else None
    print(f"2. Category mapping:")
    print(f"   Mapped category: {categoria}")
    
    # Step 3: Semantic search
    print(f"3. Semantic search:")
    documents = semantic_search.search(
        query=query,
        top_k=3,
        categoria=categoria
    )
    print(f"   Documents found: {len(documents)}")
    
    for i, doc in enumerate(documents, 1):
        print(f"   {i}. Score: {doc.get('score', 0):.3f} | Cat: {doc.get('categoria', 'unknown')}")
        print(f"      Text: {doc.get('text', '')[:80]}...")
    
    # Step 4: Test Spanish filtering
    if documents:
        print(f"4. Spanish filtering:")
        spanish_docs = orchestrator._filter_spanish_documents(documents)
        print(f"   Spanish documents: {len(spanish_docs)}")
        
        for i, doc in enumerate(spanish_docs, 1):
            print(f"   {i}. Text: {doc.get('text', '')[:80]}...")
    
    # Step 5: Test structured response generation
    if documents:
        print(f"5. Response generation:")
        try:
            response = orchestrator._generate_structured_response(documents, query)
            print(f"   Response: {response[:100]}...")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == '__main__':
    try:
        test_orchestrator_internal()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()