#!/usr/bin/env python3
"""
Test improved course response generation
"""
import re

def remove_professor_mentions_selective(text: str) -> str:
    """
    More selective professor removal that preserves course information
    """
    if not text:
        return text
    
    # Split by common separators to work with chunks
    chunks = []
    
    # Split by pipes first
    if '|' in text:
        parts = text.split('|')
    else:
        # Split by common patterns if no pipes
        parts = re.split(r'(?=Curso|Estado|Fecha|Diplomado)', text)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Skip parts that are primarily about professors
        part_lower = part.lower()
        if any(prof_word in part_lower for prof_word in ['profesor:', 'profesora:', 'docente:', 'instructor:']):
            # Skip this entire part
            continue
        
        # Remove isolated professor names
        part = re.sub(r'\bmateo\s+vi\b', '', part, flags=re.IGNORECASE)
        part = re.sub(r'\bmateo\b', '', part, flags=re.IGNORECASE)
        
        # Clean up and add if it has useful content
        part = part.strip()
        if part and len(part) > 3:
            chunks.append(part)
    
    # Reconstruct the text
    if chunks:
        result = ' | '.join(chunks)
        # Final cleanup
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\|\s*\|', '|', result)
        return result.strip()
    
    return text

def create_proper_course_response(course_info: str, query: str) -> str:
    """
    Create a proper course response for inscription queries
    """
    # Clean the course info first
    cleaned_info = remove_professor_mentions_selective(course_info)
    
    # Extract key information
    course_name = ""
    state = ""
    deadline = ""
    start_date = ""
    
    # Extract course name
    if 'curso de italiano' in cleaned_info.lower():
        course_name = "Curso de Italiano"
    elif 'diplomado de italiano' in cleaned_info.lower():
        course_name = "Diplomado de Italiano"
    elif 'italiano' in cleaned_info.lower():
        course_name = "Curso de Italiano"
    
    # Extract state
    if 'en etapa de inscripción' in cleaned_info.lower():
        state = "En etapa de inscripción"
    elif 'disponible' in cleaned_info.lower():
        state = "Disponible"
    
    # Extract dates
    dates = re.findall(r'(\d{4}-\d{2}-\d{2})', cleaned_info)
    if dates:
        if len(dates) >= 2:
            # Usually first date is deadline, second is start
            deadline = dates[0]
            start_date = dates[1]
        else:
            deadline = dates[0]
    
    # Build response based on query type
    query_lower = query.lower()
    
    if 'cuánto tiempo' in query_lower and 'inscrib' in query_lower:
        # Time remaining query
        response = f"⏰ **Información de Inscripción - {course_name}:**\n\n"
        
        if state:
            response += f"📊 **Estado actual:** {state}\n"
        
        if deadline:
            response += f"📅 **Fecha límite de inscripción:** {deadline}\n"
            
            # Calculate time remaining (simplified)
            try:
                from datetime import datetime
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
                today = datetime.now()
                days_remaining = (deadline_date - today).days
                
                if days_remaining > 0:
                    response += f"⏳ **Tiempo restante:** {days_remaining} días\n"
                elif days_remaining == 0:
                    response += f"⚠️ **¡Último día para inscribirse!**\n"
                else:
                    response += f"❌ **Fecha límite vencida** (hace {abs(days_remaining)} días)\n"
            except:
                response += f"⏳ **Revisa la fecha límite:** {deadline}\n"
        
        if start_date:
            response += f"🚀 **Fecha de inicio del curso:** {start_date}\n"
        
        response += f"\n📝 **Para inscribirte:**\n"
        response += f"1. Regístrate en el sitio web del centro\n"
        response += f"2. Inicia sesión con tus credenciales\n"
        response += f"3. Ve a la página Nuestros Cursos\n"
        response += f"4. Busca el {course_name} y completa tu inscripción\n"
        response += f"\n💡 **Importante:** Sin registro no podrás inscribirte."
        
    else:
        # General course info
        response = f"📚 **{course_name}:**\n\n"
        
        if state:
            response += f"📊 **Estado:** {state}\n"
        if deadline:
            response += f"📅 **Fecha límite de inscripción:** {deadline}\n"
        if start_date:
            response += f"🚀 **Fecha de inicio:** {start_date}\n"
        
        response += f"\n📝 **Para más información, visita la página Nuestros Cursos.**"
    
    return response

def test_improved_response():
    """Test the improved response generation"""
    
    print("🧪 Testing Improved Course Response Generation")
    print("=" * 60)
    
    # Sample problematic data
    problematic_data = "de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-17 Fecha límite de inscripción: 2025-12-16 Curso de Italiano Diplomado de Italiano Estado: En etapa de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-12 Fecha límite de inscripción:"
    
    # Sample query
    query = "¿cuánto tiempo me queda para inscribirme en el curso de italiano antes que cierre la etapa de inscripción?"
    
    print(f"Query: {query}")
    print(f"\nOriginal data: {problematic_data}")
    
    # Test selective cleaning
    cleaned = remove_professor_mentions_selective(problematic_data)
    print(f"\nCleaned data: {cleaned}")
    
    # Generate proper response
    proper_response = create_proper_course_response(problematic_data, query)
    print(f"\nProper response:")
    print(proper_response)
    
    # Check for professor mentions
    professor_words = ['profesor', 'profesora', 'docente', 'instructor', 'mateo']
    found_professors = [word for word in professor_words if word.lower() in proper_response.lower()]
    
    print(f"\n🔍 Analysis:")
    if found_professors:
        print(f"❌ Professor mentions found: {', '.join(found_professors)}")
    else:
        print("✅ No professor mentions")
    
    print(f"✅ Response length: {len(proper_response)} characters")
    print(f"✅ Contains useful info: {'Yes' if any(word in proper_response.lower() for word in ['fecha', 'inscripción', 'italiano']) else 'No'}")

if __name__ == "__main__":
    test_improved_response()