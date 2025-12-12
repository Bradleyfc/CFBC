#!/usr/bin/env python3
"""
Revisar cursos disponibles
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from principal.models import Curso

def check_cursos():
    """
    Revisar cursos disponibles
    """
    print("📚 Cursos Disponibles")
    print("=" * 40)
    
    # Ver todos los cursos disponibles
    cursos = Curso.objects.all()
    print(f'Total de cursos en la base de datos: {cursos.count()}')
    print('\nCursos disponibles:')
    for curso in cursos:
        area_nombre = curso.get_area_display()
        print(f'- {curso.name} (Área: {area_nombre})')
        print(f'  Estado: {curso.get_status_display()}')
        print(f'  Descripción: {curso.description[:100] if curso.description else "Sin descripción"}...')
        print()

if __name__ == '__main__':
    try:
        check_cursos()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()