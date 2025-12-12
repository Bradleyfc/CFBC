#!/usr/bin/env python3
"""
Simple test for professor filtering without Django dependencies
"""
import re

def remove_professor_mentions_improved(text: str) -> str:
    """
    Improved method to remove all mentions of professors and personal information
    """
    if not text:
        return text
    
    # More comprehensive patterns to remove professor information
    remove_patterns = [
        # Direct professor mentions with colons
        r'profesor:\s*[^|]*\|?',
        r'profesora:\s*[^|]*\|?',
        r'docente:\s*[^|]*\|?',
        r'instructor:\s*[^|]*\|?',
        r'maestro:\s*[^|]*\|?',
        r'maestra:\s*[^|]*\|?',
        
        # Specific names that are professors
        r'mateo\s+vi[^|]*\|?',
        r'mateo[^|]*\|?',
        
        # Professor mentions without colons
        r'profesor[^|]*\|?',
        r'profesora[^|]*\|?',
        r'docente[^|]*\|?',
        r'instructor[^|]*\|?',
        
        # Pipe-separated professor information
        r'\|\s*profesor:\s*[^|]*',
        r'\|\s*profesora:\s*[^|]*',
        r'\|\s*docente:\s*[^|]*',
        r'\|\s*instructor:\s*[^|]*',
        r'\|\s*maestro:\s*[^|]*',
        r'\|\s*maestra:\s*[^|]*',
        
        # Any pipe section containing professor names
        r'\|\s*[^|]*mateo[^|]*',
        r'\|\s*[^|]*profesor[^|]*',
        r'\|\s*[^|]*profesora[^|]*',
        r'\|\s*[^|]*docente[^|]*',
        r'\|\s*[^|]*instructor[^|]*',
        
        # Lines or sections starting with professor info
        r'^profesor[^|]*\|?',
        r'^profesora[^|]*\|?',
        r'^docente[^|]*\|?',
        r'^instructor[^|]*\|?',
        
        # General professor-related phrases
        r'nombre del profesor[^|]*\|?',
        r'impartido por[^|]*\|?',
        r'a cargo de[^|]*\|?'
    ]
    
    cleaned_text = text
    
    # Apply all removal patterns
    for pattern in remove_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up formatting issues
    cleaned_text = re.sub(r'\|\s*\|', '|', cleaned_text)  # Remove double pipes
    cleaned_text = re.sub(r'^\s*\|\s*', '', cleaned_text)  # Remove leading pipes
    cleaned_text = re.sub(r'\s*\|\s*$', '', cleaned_text)  # Remove trailing pipes
    cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)  # Remove empty lines
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize spaces
    
    # Final cleanup: remove any remaining isolated professor names
    isolated_names = ['mateo', 'mateo vi']
    for name in isolated_names:
        cleaned_text = re.sub(rf'\b{re.escape(name)}\b', '', cleaned_text, flags=re.IGNORECASE)
    
    # Final space cleanup
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    return cleaned_text.strip()

def test_professor_filtering():
    """Test the professor filtering function"""
    
    print("🧪 Testing Professor Filtering")
    print("=" * 50)
    
    # Test cases based on the user's reported issue
    test_cases = [
        # The exact format from the user's issue
        "de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-17 Fecha límite de inscripción: 2025-12-16 Curso de Italiano Diplomado de Italiano Estado: En etapa de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-12 Fecha límite de inscripción:",
        
        # Other variations
        "Curso de Italiano | Profesor: Mateo vi | Fecha de inicio: 2025-12-17",
        "Diplomado de Italiano | Estado: En etapa de inscripción | Profesor: Mateo vi | Fecha límite: 2025-12-16",
        "Curso: Italiano | Área: Idiomas | Docente: Juan Pérez | Horario: Lunes 9am",
        "Instructor: María García | Curso de Diseño | Modalidad: Presencial",
        
        # Edge cases
        "Profesor: Mateo vi | Curso de Italiano | Estado: Disponible",
        "Curso de Italiano Profesor: Mateo vi Estado: En etapa de inscripción",
        "Estado: En etapa de inscripción | Profesor: Mateo vi | Fecha límite de inscripción: 2025-12-16"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}:")
        print(f"Original: {test_case}")
        
        cleaned = remove_professor_mentions_improved(test_case)
        print(f"Cleaned:  {cleaned}")
        
        # Check if professor mentions were removed
        professor_words = ['profesor', 'profesora', 'docente', 'instructor', 'mateo', 'juan', 'maría']
        remaining_professors = [word for word in professor_words if word.lower() in cleaned.lower()]
        
        if remaining_professors:
            print(f"❌ STILL CONTAINS: {', '.join(remaining_professors)}")
        else:
            print("✅ PROFESSOR MENTIONS REMOVED")
        
        # Check if useful information is preserved
        useful_info = ['curso', 'italiano', 'fecha', 'límite', 'inscripción', 'estado', 'etapa']
        preserved_info = [info for info in useful_info if info.lower() in cleaned.lower()]
        print(f"📊 PRESERVED INFO: {', '.join(preserved_info) if preserved_info else 'None'}")

def create_clean_course_response():
    """Create a clean course response without professor mentions"""
    
    print("\n🛠️ Creating Clean Course Response")
    print("=" * 50)
    
    # Sample problematic response
    problematic_response = """de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-17 Fecha límite de inscripción: 2025-12-16 Curso de Italiano Diplomado de Italiano Estado: En etapa de inscripción Profesor: Mateo vi Fecha de inicio: 2025-12-12 Fecha límite de inscripción:"""
    
    print("Original problematic response:")
    print(problematic_response)
    
    # Clean it
    cleaned = remove_professor_mentions_improved(problematic_response)
    print(f"\nCleaned response:")
    print(cleaned)
    
    # Create a proper formatted response
    if cleaned:
        # Extract useful information
        info_parts = []
        
        if 'curso de italiano' in cleaned.lower():
            info_parts.append("📚 **Curso de Italiano**")
        
        if 'diplomado de italiano' in cleaned.lower():
            info_parts.append("🎓 **Diplomado de Italiano**")
        
        if 'en etapa de inscripción' in cleaned.lower():
            info_parts.append("✅ **Estado:** En etapa de inscripción")
        
        # Extract dates
        import re
        dates = re.findall(r'(\d{4}-\d{2}-\d{2})', cleaned)
        if dates:
            if len(dates) >= 2:
                info_parts.append(f"📅 **Fecha límite de inscripción:** {dates[0]}")
                info_parts.append(f"🚀 **Fecha de inicio:** {dates[1]}")
            else:
                info_parts.append(f"📅 **Fecha:** {dates[0]}")
        
        if info_parts:
            formatted_response = "\n".join(info_parts)
            formatted_response += "\n\n📝 **Para inscribirte, visita la página Nuestros Cursos en nuestro sitio web.**"
            
            print(f"\nFormatted clean response:")
            print(formatted_response)

if __name__ == "__main__":
    test_professor_filtering()
    create_clean_course_response()