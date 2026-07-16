#!/usr/bin/env python3
"""
Script para limpiar grupos duplicados creados por el sistema anterior
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.contrib.auth.models import Group, User
from django.db import transaction

def limpiar_grupos_duplicados():
    """Limpia los grupos duplicados y migra usuarios a los grupos correctos"""
    
    print("=== LIMPIEZA DE GRUPOS DUPLICADOS ===")
    print()
    
    # Mapeo de grupos numéricos a nombres correctos
    mapeo_grupos = {
        'Grupo_422': 'Administración',
        'Grupo_423': 'Blog Autor',  # Nota: en MariaDB era "Blog Author"
        'Grupo_424': 'Blog Moderador', 
        'Grupo_425': 'Editor',
        'Grupo_426': 'Estudiantes',
        'Grupo_427': 'Profesores',
        'Grupo_428': 'Secretaría'
    }
    
    with transaction.atomic():
        usuarios_migrados = 0
        grupos_eliminados = 0
        
        for grupo_numerico, nombre_correcto in mapeo_grupos.items():
            try:
                # Buscar el grupo numérico
                grupo_duplicado = Group.objects.filter(name=grupo_numerico).first()
                if not grupo_duplicado:
                    print(f"✓ Grupo {grupo_numerico} no existe (ya limpiado)")
                    continue
                
                # Buscar o crear el grupo correcto
                grupo_correcto, created = Group.objects.get_or_create(name=nombre_correcto)
                
                if created:
                    print(f"✓ Grupo '{nombre_correcto}' creado")
                else:
                    print(f"○ Grupo '{nombre_correcto}' ya existe")
                
                # Migrar usuarios del grupo duplicado al correcto
                usuarios_en_duplicado = grupo_duplicado.user_set.all()
                usuarios_migrados_grupo = 0
                
                for usuario in usuarios_en_duplicado:
                    # Remover del grupo duplicado y agregar al correcto
                    usuario.groups.remove(grupo_duplicado)
                    usuario.groups.add(grupo_correcto)
                    usuarios_migrados_grupo += 1
                    usuarios_migrados += 1
                
                print(f"  → {usuarios_migrados_grupo} usuarios migrados de '{grupo_numerico}' a '{nombre_correcto}'")
                
                # Eliminar el grupo duplicado
                grupo_duplicado.delete()
                grupos_eliminados += 1
                print(f"  → Grupo duplicado '{grupo_numerico}' eliminado")
                
            except Exception as e:
                print(f"❌ Error procesando {grupo_numerico}: {e}")
        
        print()
        print("=== RESUMEN ===")
        print(f"✓ Grupos eliminados: {grupos_eliminados}")
        print(f"✓ Usuarios migrados: {usuarios_migrados}")
        
        # Mostrar estado final
        print()
        print("=== GRUPOS FINALES ===")
        grupos_finales = Group.objects.all().order_by('name')
        for grupo in grupos_finales:
            usuarios_count = grupo.user_set.count()
            print(f"  {grupo.name}: {usuarios_count} usuarios")
        
        print()
        print("🎉 ¡Limpieza completada exitosamente!")

if __name__ == "__main__":
    limpiar_grupos_duplicados()