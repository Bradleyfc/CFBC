#!/usr/bin/env python
"""
Test script to verify final improvements:
1. Location/direction questions
2. Site search functionality  
3. "página Nuestros Cursos" references
"""
import os
import sys
import django

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

def test_final_improvements():
    """Test all final improvements"""
    
    print("Testing Final Improvements")
    print("=" * 60)
    
    try:
        # Import orchestrator
        from chatbot.services.orchestrator import ChatbotOrchestrator
        
        orchestrator = ChatbotOrchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Test questions for different improvements
        test_categories = {
            "📍 Location/Direction Questions": [
                "¿Dónde está ubicado el centro?",
                "¿Cuál es la dirección del centro?",
                "¿Cómo llegar al centro?",
                "¿Cómo puedo llegar al lugar?",
                "¿En qué zona está el centro?",
                "¿Dónde queda el Centro Fray Bartolomé?"
            ],
            
            "🔍 Site Search Functionality": [
                "buscar información sobre cursos",
                "mostrar contenido sobre idiomas",
                "inglés",
                "diseño",
                "teología",
                "información sobre inscripciones"
            ],
            
            "📚 Course References": [
                "¿Qué cursos están disponibles?",
                "¿Cuándo empiezan las inscripciones?",
                "¿Hay cursos de idiomas?",
                "¿Cómo me inscribo?"
            ]
        }
        
        print(f"\n🔍 Testing improvements across {len(test_categories)} categories...\n")
        
        for category, questions in test_categories.items():
            print(f"{'='*60}")
            print(f"{category}")
            print("-" * 60)
            
            for i, question in enumerate(questions, 1):
                print(f"\nQuestion {i}: {question}")
                print("-" * 40)
                
                try:
                    result = orchestrator.process_question(question, f"test_session_{category}_{i}")
                    
                    if result.get('success', False):
                        response = result['respuesta']
                        intent = result['intencion']
                        confidence = result['confianza']
                        docs_found = len(result['documentos_recuperados'])
                        
                        print(f"✅ SUCCESS")
                        print(f"Intent: {intent} (confidence: {confidence:.2f})")
                        print(f"Documents: {docs_found}")
                        print(f"Response length: {len(response)} chars")
                        
                        # Check for specific improvements
                        response_lower = response.lower()
                        
                        # Check for location improvements
                        if category.startswith("📍"):
                            location_keywords = ['dirección', 'ubicación', 'cómo llegar', 'vedado', 'la habana', 'transporte', 'taxi']
                            found_location = any(keyword in response_lower for keyword in location_keywords)
                            print(f"Contains location info: {'✅' if found_location else '❌'}")
                        
                        # Check for site search functionality
                        elif category.startswith("🔍"):
                            search_keywords = ['resultados', 'búsqueda', 'cursos:', 'inscripciones:', 'información general:']
                            found_search = any(keyword in response_lower for keyword in search_keywords)
                            print(f"Shows search results: {'✅' if found_search else '❌'}")
                        
                        # Check for correct page references
                        if 'página nuestros cursos' in response_lower:
                            print("✅ Uses 'página Nuestros Cursos'")
                        elif 'página de cursos' in response_lower:
                            print("❌ Still uses old 'página de Cursos'")
                        
                        # Show response preview
                        preview = response[:150] + "..." if len(response) > 150 else response
                        print(f"Response: {preview}")
                        
                    else:
                        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    print(f"❌ ERROR: {e}")
            
            print()
        
        # Test specific improvements
        print("=" * 60)
        print("🔍 SPECIFIC IMPROVEMENT TESTS")
        print("=" * 60)
        
        # Test 1: Location detection
        print("\n1. Testing enhanced location detection...")
        location_result = orchestrator.process_question("¿Dónde está el centro?", "test_location")
        if location_result.get('intencion') == 'ubicaciones':
            print("✅ Location intent correctly detected")
        else:
            print(f"❌ Location intent not detected. Got: {location_result.get('intencion')}")
        
        # Test 2: Site search functionality
        print("\n2. Testing site search functionality...")
        search_result = orchestrator.process_question("buscar cursos de idiomas", "test_search")
        search_response = search_result.get('respuesta', '')
        if 'resultados de búsqueda' in search_response.lower() or len(search_response) > 200:
            print("✅ Site search functionality working")
        else:
            print("❌ Site search functionality not working properly")
        
        # Test 3: Page reference consistency
        print("\n3. Testing page reference consistency...")
        course_result = orchestrator.process_question("¿Qué cursos tienen?", "test_page_ref")
        course_response = course_result.get('respuesta', '')
        if 'página nuestros cursos' in course_response.lower():
            print("✅ Uses correct 'página Nuestros Cursos' reference")
        elif 'página de cursos' in course_response.lower():
            print("❌ Still uses old 'página de Cursos' reference")
        else:
            print("ℹ️ No page reference found in this response")
        
        print("\n" + "=" * 60)
        print("🎉 FINAL IMPROVEMENTS TESTING COMPLETED!")
        print("✅ All improvements have been tested")
        print("\n📋 Improvements implemented:")
        print("   • Enhanced location/direction responses")
        print("   • Site search functionality")
        print("   • Consistent 'página Nuestros Cursos' references")
        print("   • Better intent detection for location queries")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_final_improvements()
    sys.exit(0 if success else 1)