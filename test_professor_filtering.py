#!/usr/bin/env python3
"""
Test script to identify and fix professor mention filtering issues
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
    """Test the professor filtering with the problematic query"""
    
    print("🧪 Testing Professor Filtering Issues")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # The problematic query mentioned by the user
    test_query = "¿cuánto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripción?"
    
    print(f"🔍 Testing query: {test_query}")
    print("-" * 60)
    
    try:
        result = orchestrator.process_question(test_query, "professor_test")
        
        if result.get('success', False):
            response = result.get('respuesta', '')
            
            print("📝 RESPONSE RECEIVED:")
            print(response)
            print("\n" + "="*60)
            
            # Check for professor mentions
            professor_indicators = [
                'profesor', 'profesora', 'docente', 'instructor', 
                'mateo', 'mateo vi', 'maestro', 'maestra'
            ]
            
            found_professors = []
            response_lower = response.lower()
            
            for indicator in professor_indicators:
                if indicator in response_lower:
                    found_professors.append(indicator)
            
            print("🔍 ANALYSIS:")
            if found_professors:
                print(f"❌ PROFESSOR MENTIONS FOUND: {', '.join(found_professors)}")
                print("   This violates the no-professor-mention rule!")
            else:
                print("✅ NO PROFESSOR MENTIONS FOUND")
            
            # Check if response is complete
            if response.endswith('...') or len(response) < 50:
                print("❌ RESPONSE APPEARS INCOMPLETE")
            else:
                print("✅ RESPONSE APPEARS COMPLETE")
            
            # Check for useful course information
            useful_info = ['fecha', 'inscripción', 'curso', 'italiano', 'tiempo', 'límite']
            found_info = [info for info in useful_info if info in response_lower]
            
            print(f"📊 USEFUL INFO FOUND: {', '.join(found_info) if found_info else 'None'}")
            
        else:
            print(f"❌ QUERY FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

def test_professor_removal_method():
    """Test the professor removal method directly"""
    
    print("\n🔧 Testing Professor Removal Method Directly")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    
    # Test cases with professor mentions
    test_cases = [
        "Curso de Italiano | Profesor: Mateo vi | Fecha de inicio: 2025-12-17",
        "Diplomado de Italiano | Estado: En etapa de inscripción | Profesor: Mateo vi | Fecha límite: 2025-12-16",
        "Curso: Italiano | Área: Idiomas | Docente: Juan Pérez | Horario: Lunes 9am",
        "Instructor: María García | Curso de Diseño | Modalidad: Presencial"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}:")
        print(f"Original: {test_case}")
        
        try:
            cleaned = orchestrator._remove_all_professor_mentions(test_case)
            print(f"Cleaned:  {cleaned}")
            
            # Check if professor mentions were removed
            professor_indicators = ['profesor', 'profesora', 'docente', 'instructor', 'mateo', 'juan', 'maría']
            remaining_professors = [p for p in professor_indicators if p in cleaned.lower()]
            
            if remaining_professors:
                print(f"❌ STILL CONTAINS: {', '.join(remaining_professors)}")
            else:
                print("✅ PROFESSOR MENTIONS REMOVED")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

def create_improved_professor_filter():
    """Create an improved professor filtering function"""
    
    print("\n🛠️ Creating Improved Professor Filter")
    print("=" * 60)
    
    def improved_remove_professors(text: str) -> str:
        """Improved professor removal function"""
        if not text:
            return text
        
        import re
        
        # More comprehensive patterns
        remove_patterns = [
            # Direct professor mentions
            r'profesor:\s*[^|]*\|?',
            r'profesora:\s*[^|]*\|?',
            r'docente:\s*[^|]*\|?',
            r'instructor:\s*[^|]*\|?',
            r'maestro:\s*[^|]*\|?',
            r'maestra:\s*[^|]*\|?',
            
            # Specific names
            r'mateo\s+vi[^|]*\|?',
            r'mateo[^|]*\|?',
            
            # Pipe-separated professor info
            r'\|\s*profesor:\s*[^|]*',
            r'\|\s*profesora:\s*[^|]*',
            r'\|\s*docente:\s*[^|]*',
            r'\|\s*instructor:\s*[^|]*',
            
            # Any field that might contain professor names
            r'\|\s*[^|]*mateo[^|]*',
            r'profesor[^|]*',
            r'profesora[^|]*',
            r'docente[^|]*',
            r'instructor[^|]*'
        ]
        
        cleaned_text = text
        
        # Apply all patterns
        for pattern in remove_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up formatting
        cleaned_text = re.sub(r'\|\s*\|', '|', cleaned_text)  # Remove double pipes
        cleaned_text = re.sub(r'^\s*\|\s*', '', cleaned_text)  # Remove leading pipes
        cleaned_text = re.sub(r'\s*\|\s*$', '', cleaned_text)  # Remove trailing pipes
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize spaces
        
        return cleaned_text.strip()
    
    # Test the improved function
    test_cases = [
        "Curso de Italiano | Profesor: Mateo vi | Fecha de inicio: 2025-12-17",
        "Diplomado de Italiano Estado: En etapa de inscripción Profesor: Mateo vi Fecha límite: 2025-12-16",
        "Curso: Italiano | Área: Idiomas | Docente: Juan Pérez | Horario: Lunes 9am"
    ]
    
    print("Testing improved filter:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Original: {test_case}")
        cleaned = improved_remove_professors(test_case)
        print(f"   Cleaned:  {cleaned}")
        
        # Check for remaining professor mentions
        professor_words = ['profesor', 'profesora', 'docente', 'instructor', 'mateo', 'juan', 'maría']
        remaining = [word for word in professor_words if word in cleaned.lower()]
        
        if remaining:
            print(f"   ❌ Still contains: {', '.join(remaining)}")
        else:
            print(f"   ✅ Clean")

if __name__ == "__main__":
    test_professor_filtering()
    test_professor_removal_method()
    create_improved_professor_filter()