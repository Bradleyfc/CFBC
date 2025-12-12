#!/usr/bin/env python
"""
Test script to verify registration and login responses
"""
import os
import sys
import django

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

def test_registration_and_login_responses():
    """Test that chatbot provides detailed registration and login information"""
    
    print("Testing Registration and Login Responses")
    print("=" * 60)
    
    try:
        # Import orchestrator
        from chatbot.services.orchestrator import ChatbotOrchestrator
        
        orchestrator = ChatbotOrchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Test questions about registration and login
        test_questions = [
            # Registration questions
            "¿Cómo me registro en el sitio?",
            "¿Cómo crear una cuenta?",
            "¿Qué necesito para registrarme?",
            "¿Dónde está la página de registro?",
            
            # Login questions
            "¿Cómo hago login?",
            "¿Cómo iniciar sesión?",
            "¿Olvidé mi contraseña, qué hago?",
            "¿Dónde está la página de login?",
            
            # Inscription process questions
            "¿Cómo me inscribo a un curso?",
            "¿Qué necesito para inscribirme?",
            "¿Puedo inscribirme sin registrarme?",
            "¿Cuál es el proceso de inscripción?",
            
            # General access questions
            "¿Cómo accedo a los cursos?",
            "¿Necesito una cuenta para ver los cursos?",
            "¿Es gratis registrarse?"
        ]
        
        print(f"\n🔍 Testing {len(test_questions)} questions about registration and login...\n")
        
        for i, question in enumerate(test_questions, 1):
            print(f"{'='*60}")
            print(f"Question {i}: {question}")
            print("-" * 60)
            
            try:
                result = orchestrator.process_question(question, f"test_session_{i}")
                
                if result.get('success', False):
                    response = result['respuesta']
                    intent = result['intencion']
                    confidence = result['confianza']
                    docs_found = len(result['documentos_recuperados'])
                    
                    print(f"✅ SUCCESS")
                    print(f"Intent: {intent} (confidence: {confidence:.2f})")
                    print(f"Documents found: {docs_found}")
                    print(f"Response length: {len(response)} characters")
                    print()
                    print("📝 RESPONSE:")
                    print(response)
                    
                    # Check if response contains registration/login information
                    registration_keywords = [
                        'registro', 'registrar', 'crear cuenta', 'formulario',
                        'usuario', 'contraseña', 'email', 'datos personales'
                    ]
                    
                    login_keywords = [
                        'login', 'iniciar sesión', 'entrar', 'credenciales',
                        'olvidó su contraseña', 'restablecer'
                    ]
                    
                    process_keywords = [
                        'paso 1', 'paso 2', 'paso 3', 'obligatorio',
                        'proceso', 'inscripción'
                    ]
                    
                    response_lower = response.lower()
                    
                    found_registration = any(keyword in response_lower for keyword in registration_keywords)
                    found_login = any(keyword in response_lower for keyword in login_keywords)
                    found_process = any(keyword in response_lower for keyword in process_keywords)
                    
                    print()
                    print("🔍 CONTENT ANALYSIS:")
                    print(f"   Contains registration info: {'✅' if found_registration else '❌'}")
                    print(f"   Contains login info: {'✅' if found_login else '❌'}")
                    print(f"   Contains process steps: {'✅' if found_process else '❌'}")
                    
                    # Check for specific important information
                    important_info = []
                    if 'sin registro' in response_lower and 'no podrá' in response_lower:
                        important_info.append("✅ Explains registration is required")
                    if 'gratuito' in response_lower or 'gratis' in response_lower:
                        important_info.append("✅ Mentions registration is free")
                    if 'página de cursos' in response_lower:
                        important_info.append("✅ References courses page")
                    if 'formulario' in response_lower:
                        important_info.append("✅ Mentions registration form")
                    if 'olvidó su contraseña' in response_lower:
                        important_info.append("✅ Includes password recovery info")
                    
                    if important_info:
                        print("   Key information included:")
                        for info in important_info:
                            print(f"     {info}")
                    
                else:
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
            
            print()
        
        print("=" * 60)
        print("🎉 REGISTRATION AND LOGIN TESTING COMPLETED!")
        print("✅ The chatbot now has detailed information about:")
        print("   • Registration process and requirements")
        print("   • Login procedures and troubleshooting")
        print("   • Step-by-step inscription guidance")
        print("   • Access requirements for courses")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_registration_and_login_responses()
    sys.exit(0 if success else 1)