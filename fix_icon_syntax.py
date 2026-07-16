#!/usr/bin/env python3
"""
Script para corregir la sintaxis incorrecta de los iconos Material Icons
Corrige casos como: <span class="fa material-icons">icono</span></i>
A: <span class="material-icons">icono</span>
"""

import os
import re
import glob

def fix_icon_syntax_in_file(file_path):
    """Corrige la sintaxis de iconos Material Icons en un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Patrón 1: <span class="fa material-icons ...">icono</span></i>
        pattern1 = r'<span class="fa material-icons([^"]*)"[^>]*>([^<]+)</span></i>'
        def fix_fa_material_icons(match):
            nonlocal changes_made
            extra_classes = match.group(1).strip()
            icon_name = match.group(2).strip()
            changes_made += 1
            if extra_classes:
                return f'<span class="material-icons{extra_classes}">{icon_name}</span>'
            else:
                return f'<span class="material-icons">{icon_name}</span>'
        
        content = re.sub(pattern1, fix_fa_material_icons, content)
        
        # Patrón 2: <span class="bi material-icons ...">icono</span></i>
        pattern2 = r'<span class="bi material-icons([^"]*)"[^>]*>([^<]+)</span></i>'
        def fix_bi_material_icons(match):
            nonlocal changes_made
            extra_classes = match.group(1).strip()
            icon_name = match.group(2).strip()
            changes_made += 1
            if extra_classes:
                return f'<span class="material-icons{extra_classes}">{icon_name}</span>'
            else:
                return f'<span class="material-icons">{icon_name}</span>'
        
        content = re.sub(pattern2, fix_bi_material_icons, content)
        
        # Patrón 3: <span class="icon material-icons ...">icono</span></i>
        pattern3 = r'<span class="icon material-icons([^"]*)"[^>]*>([^<]+)</span></i>'
        def fix_icon_material_icons(match):
            nonlocal changes_made
            extra_classes = match.group(1).strip()
            icon_name = match.group(2).strip()
            changes_made += 1
            if extra_classes:
                return f'<span class="material-icons{extra_classes}">{icon_name}</span>'
            else:
                return f'<span class="material-icons">{icon_name}</span>'
        
        content = re.sub(pattern3, fix_icon_material_icons, content)
        
        # Patrón 4: Limpiar clases duplicadas como "material-icons material-icons"
        pattern4 = r'class="([^"]*?)material-icons\s+material-icons([^"]*?)"'
        def fix_duplicate_material_icons(match):
            nonlocal changes_made
            before = match.group(1).strip()
            after = match.group(2).strip()
            classes = []
            if before:
                classes.append(before)
            classes.append('material-icons')
            if after:
                classes.append(after)
            changes_made += 1
            return f'class="{" ".join(classes)}"'
        
        content = re.sub(pattern4, fix_duplicate_material_icons, content)
        
        # Solo escribir si hubo cambios
        if changes_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path}: {changes_made} problemas corregidos")
            return changes_made
        else:
            print(f"⚪ {file_path}: Sin problemas")
            return 0
            
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return 0

def main():
    """Función principal"""
    print("🔧 Corrigiendo sintaxis incorrecta de Material Icons")
    print("=" * 60)
    
    # Buscar todos los archivos HTML en templates
    template_files = []
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                template_files.append(os.path.join(root, file))
    
    if not template_files:
        print("❌ No se encontraron archivos de template")
        return
    
    print(f"📁 Encontrados {len(template_files)} archivos de template")
    print()
    
    total_changes = 0
    files_changed = 0
    
    # Procesar cada archivo
    for file_path in sorted(template_files):
        changes = fix_icon_syntax_in_file(file_path)
        total_changes += changes
        if changes > 0:
            files_changed += 1
    
    print()
    print("=" * 60)
    print(f"🎉 ¡Correcciones completadas!")
    print(f"📊 Resumen:")
    print(f"   • Archivos procesados: {len(template_files)}")
    print(f"   • Archivos corregidos: {files_changed}")
    print(f"   • Total de problemas corregidos: {total_changes}")
    print()
    print("🔍 Problemas corregidos:")
    print("   • <span class=\"fa material-icons\">icono</span></i> → <span class=\"material-icons\">icono</span>")
    print("   • <span class=\"bi material-icons\">icono</span></i> → <span class=\"material-icons\">icono</span>")
    print("   • <span class=\"icon material-icons\">icono</span></i> → <span class=\"material-icons\">icono</span>")
    print("   • Clases duplicadas: material-icons material-icons → material-icons")

if __name__ == "__main__":
    main()