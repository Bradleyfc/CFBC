#!/usr/bin/env python3
"""
Check course details available
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from principal.models import Curso

def check_course_details():
    """
    Check detailed course information
    """
    print("🔍 Course Details Available")
    print("=" * 40)
    
    cursos = Curso.objects.all()
    
    for curso in cursos:
        print(f"\n📚 {curso.name}")
        print(f"   Área: {curso.get_area_display()}")
        print(f"   Tipo: {curso.get_tipo_display()}")
        print(f"   Estado: {curso.get_status_display()}")
        print(f"   Estado dinámico: {curso.get_dynamic_status_display()}")
        print(f"   Fecha límite inscripción: {curso.enrollment_deadline}")
        print(f"   Fecha inicio: {curso.start_date}")
        print(f"   Cantidad de clases: {curso.class_quantity}")
        print(f"   Descripción: {curso.description[:100] if curso.description else 'Sin descripción'}...")
        
        if curso.teacher:
            print(f"   Profesor: {curso.teacher.get_full_name() or curso.teacher.username}")

if __name__ == '__main__':
    try:
        check_course_details()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()