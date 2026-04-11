#!/usr/bin/env python3
"""
Script para limpiar y arreglar los Material Icons después del reemplazo
"""

import os
import re
import glob

def fix_icons_in_file(file_path):
    """Arregla los iconos Material Icons en un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Arreglar clases duplicadas como "fa material-icons material-icons"
        pattern1 = r'class="([^"]*?)\s*(?:fa|bi|icon)\s+material-icons\s+material-icons([^"]*?)"'
        def fix_duplicate_classes(match):
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
        
        content = re.sub(pattern1, fix_duplicate_classes, content)
        
        # Arreglar spans anidados como <span class="...">icon</span></span>
        pattern2 = r'<span class="([^"]*material-icons[^"]*)"[^>]*>([^<]+)</span></span>'
        def fix_nested_spans(match):
            nonlocal changes_made
            class_attr = match.group(1)
            icon_name = match.group(2)
            changes_made += 1
            return f'<span class="{class_attr}">{icon_name}</span>'
        
        content = re.sub(pattern2, fix_nested_spans, content)
        
        # Arreglar iconos que no tienen el nombre correcto
        pattern3 = r'<span class="([^"]*material-icons[^"]*)"[^>]*>(close|group|person|trending_up|cloud_upload|cloud_download|visibility|delete|warning|error|info|check_circle|add_circle|assignment|search|filter_list|arrow_back|refresh|home|event|schedule|location_on|phone|email|facebook|twitter|instagram|linkedin|login|grid_view|inbox|send|security|vpn_key|dns|arrow_forward|logout|table_view|storage|keyboard_arrow_up|keyboard_arrow_down|add|remove|more_horiz|visibility_off|book|play_circle|play_arrow|circle|speed|archive|code|flash_on|swap_vert|check_box|account_tree|check|article|badge|assignment_add|format_list_numbered|save|undo|bar_chart|picture_as_pdf|history|description|chevron_left|list|check_circle|person_add|help|reply|verified_user|lock|assignment_turned_in|event_available|folder_open|filter_list|edit|cancel|settings|star|favorite|camera_alt|school|fiber_manual_record|note_add|folder|create_new_folder|table_chart)</span>'
        
        # Solo escribir si hubo cambios
        if changes_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path}: {changes_made} problemas arreglados")
            return changes_made
        else:
            print(f"⚪ {file_path}: Sin problemas")
            return 0
            
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return 0

def main():
    """Función principal"""
    print("🔧 Arreglando problemas con Material Icons")
    print("=" * 50)
    
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
        changes = fix_icons_in_file(file_path)
        total_changes += changes
        if changes > 0:
            files_changed += 1
    
    print()
    print("=" * 50)
    print(f"🎉 ¡Arreglos completados!")
    print(f"📊 Resumen:")
    print(f"   • Archivos procesados: {len(template_files)}")
    print(f"   • Archivos arreglados: {files_changed}")
    print(f"   • Total de problemas arreglados: {total_changes}")

if __name__ == "__main__":
    main()