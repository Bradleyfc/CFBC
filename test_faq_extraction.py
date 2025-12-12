#!/usr/bin/env python3
"""
Test script to debug FAQ extraction and professor filtering
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
sys.path.append('.')
django.setup()

from chatbot.services.orchestrator import ChatbotOrchestrator

def test_faq_extraction():
    """Test FAQ extraction with the problematic text"""
    orchestrator = ChatbotOrchestrator()
    
    # The exact problematic FAQ text
    faq_text = "de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-17 Fecha límite de inscripción: 2025-12-16 Curso de Italiano Diplomado de Italiano Estado: En etapa de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-12 Fecha límite de inscripción:"
    
    print("=== Testing FAQ Extraction ===\n")
    print(f"Original FAQ text: {faq_text}")
    
    # Test _extract_answer_from_faq
    extracted = orchestrator._extract_answer_from_faq(faq_text)
    print(f"\nExtracted answer: {extracted}")
    
    # Test professor filtering on extracted text
    filtered = orchestrator._remove_professor_mentions_improved(extracted)
    print(f"\nFiltered answer: {filtered}")
    
    # Test the complete FAQ response generation
    faq_doc = {'text': faq_text}
    complete_response = orchestrator._generate_faq_response(faq_doc)
    print(f"\nComplete FAQ response: {complete_response}")
    
    # Check for professor mentions
    if any(prof in complete_response.lower() for prof in ['profesor', 'mateo', 'docente', 'instructor']):
        print("\n❌ ERROR: Professor mentions still found in final response!")
    else:
        print("\n✅ SUCCESS: No professor mentions in final response!")

if __name__ == "__main__":
    test_faq_extraction()