#!/usr/bin/env python3
"""
Test de debug completo
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

def test_debug_completo():
    """
    Debug completo del proceso
    """
    print("🔍 Debug Completo")
    print("=" * 40)
    
    orchestrator = ChatbotOrchestrator()
    semantic_search = SemanticSearchService()
    intent_classifier = IntentClassifier()
    
    query = "¿Dónde está ubicado el centro?"
    
    print(f"Consulta: {query}")
    print("-" * 40)
    
    # 1. Clasificación de intención
    print("1. Clasificación de intención:")
    should_filter, intent = intent_classifier.should_filter_by_intent(query)
    primary_intent, confidence = intent_classifier.get_primary_intent(query)
    
    print(f"   Should filter: {should_filter}")
    print(f"   Intent: {intent}")
    print(f"   Primary intent: {primary_intent}")
    print(f"   Confidence: {confidence}")
    
    # 2. Búsqueda semántica sin filtro
    print("\n2. Búsqueda semántica sin filtro:")
    results_no_filter = semantic_search.search(query, top_k=3)
    print(f"   Resultados: {len(results_no_filter)}")
    
    for i, result in enumerate(results_no_filter, 1):
        print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: {result.get('categoria', 'unknown')}")
        print(f"      Texto: {result.get('text', '')[:80]}...")
    
    # 3. Búsqueda semántica con filtro (si aplica)
    if should_filter and intent:
        print(f"\n3. Búsqueda semántica con filtro '{intent}':")
        results_filtered = semantic_search.search(query, top_k=3, categoria=intent)
        print(f"   Resultados: {len(results_filtered)}")
        
        for i, result in enumerate(results_filtered, 1):
            print(f"   {i}. Score: {result.get('score', 0):.3f} | Cat: {result.get('categoria', 'unknown')}")
            print(f"      Texto: {result.get('text', '')[:80]}...")
    else:
        print("\n3. No se aplica filtro por categoría")
    
    # 4. Respuesta del orchestrator
    print("\n4. Respuesta del orchestrator:")
    response = orchestrator.process_question(query, session_id="debug_completo")
    
    print(f"   Respuesta: {response.get('respuesta', 'N/A')[:100]}...")
    print(f"   Documentos: {len(response.get('documentos_recuperados', []))}")
    print(f"   Éxito: {response.get('success', False)}")

if __name__ == '__main__':
    try:
        test_debug_completo()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()