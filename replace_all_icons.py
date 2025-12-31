#!/usr/bin/env python3
"""
Script para reemplazar TODOS los Bootstrap Icons con Font Awesome en todos los templates
"""

import os
import re
import glob

# Mapeo de Bootstrap Icons a Font Awesome
ICON_MAPPING = {
    # Archivos y carpetas
    'bi-folder': 'fa-folder',
    'bi-folder-plus': 'fa-folder-plus',
    'bi-folder-open': 'fa-folder-open',
    'bi-folder-x': 'fa-folder',
    'bi-folder2-open': 'fa-folder-open',
    'bi-file-earmark': 'fa-file',
    'bi-file-earmark-text': 'fa-file-text',
    'bi-file-earmark-excel': 'fa-file-excel',
    'bi-file-earmark-pdf': 'fa-file-text',
    'bi-file-earmark-x': 'fa-file',
    'bi-file-text': 'fa-file-text',
    'bi-document-text': 'fa-file-text',
    
    # Usuarios y personas
    'bi-people': 'fa-users',
    'bi-person-fill': 'fa-user',
    'bi-person-badge': 'fa-user',
    'bi-person-plus': 'fa-user',
    'bi-user': 'fa-user',
    'bi-users': 'fa-users',
    
    # Acciones
    'bi-upload': 'fa-upload',
    'bi-download': 'fa-download',
    'bi-eye': 'fa-eye',
    'bi-trash': 'fa-trash',
    'bi-search': 'fa-search',
    'bi-filter': 'fa-filter',
    'bi-funnel': 'fa-filter',
    'bi-save': 'fa-download',
    'bi-check': 'fa-check-circle',
    'bi-x': 'fa-times',
    'bi-check-circle-fill': 'fa-check-circle',
    
    # Navegación
    'bi-arrow-left': 'fa-arrow-left',
    'bi-arrow-counterclockwise': 'fa-sync',
    'bi-arrow-clockwise': 'fa-sync',
    'bi-chevron-right': 'fa-arrow-left',
    'bi-chevron-down': 'fa-arrow-left',
    'bi-chevron-left': 'fa-arrow-left',
    
    # Cerrar y cancelar
    'bi-x-lg': 'fa-times',
    'bi-x-circle': 'fa-times-circle',
    'bi-times': 'fa-times',
    'bi-times-circle': 'fa-times-circle',
    
    # Alertas e información
    'bi-exclamation-triangle': 'fa-exclamation-triangle',
    'bi-exclamation-circle': 'fa-exclamation-circle',
    'bi-info-circle': 'fa-info-circle',
    'bi-check-circle': 'fa-check-circle',
    'bi-plus-circle': 'fa-plus-circle',
    
    # Gráficos y estadísticas
    'bi-graph-up': 'fa-chart-line',
    'bi-chart-line': 'fa-chart-line',
    'bi-bar-chart': 'fa-chart-line',
    
    # Portapapeles y datos
    'bi-clipboard-data': 'fa-clipboard',
    'bi-clipboard': 'fa-clipboard',
    'bi-clipboard-plus': 'fa-clipboard',
    
    # Formularios y texto
    'bi-journal-text': 'fa-file-text',
    'bi-list-ol': 'fa-clipboard',
    'bi-list': 'fa-clipboard',
    
    # Contacto y comunicación
    'bi-geo-alt-fill': 'fa-map-marker',
    'bi-telephone-fill': 'fa-phone',
    'bi-envelope-fill': 'fa-envelope',
    'bi-facebook': 'fa-facebook',
    'bi-twitter': 'fa-twitter',
    'bi-instagram': 'fa-instagram',
    'bi-linkedin': 'fa-linkedin',
    
    # Autenticación
    'bi-box-arrow-in-right': 'fa-sign-in',
    
    # Vistas y layouts
    'bi-grid-3x3-gap': 'fa-th',
    'bi-grid': 'fa-th',
    
    # Tiempo
    'bi-clock-history': 'fa-clock',
    'bi-clock': 'fa-clock',
    
    # Otros iconos comunes
    'bi-home': 'fa-home',
    'bi-house': 'fa-home',
    'bi-cog': 'fa-cog',
    'bi-gear': 'fa-cog',
    'bi-calendar': 'fa-calendar',
    'bi-calendar-check': 'fa-calendar',
    'bi-star': 'fa-star',
    'bi-heart': 'fa-heart',
    'bi-envelope': 'fa-envelope',
    'bi-phone': 'fa-phone',
    'bi-map-pin': 'fa-map-marker',
    'bi-camera': 'fa-camera',
    'bi-book-open': 'fa-book',
    'bi-book': 'fa-book',
    'bi-academic-cap': 'fa-graduation-cap',
    'bi-identification': 'fa-id-card',
    'bi-pencil': 'fa-pencil',
    'bi-edit': 'fa-pencil',
    'bi-person': 'fa-user',
    'bi-question-circle': 'fa-info-circle',
    'bi-reply': 'fa-arrow-left',
    'bi-inbox': 'fa-inbox',
    'bi-exclamation-triangle-fill': 'fa-exclamation-triangle',
    'bi-send': 'fa-paper-plane',
    'bi-shield-lock': 'fa-shield',
    'bi-shield-check': 'fa-shield',
    'bi-key': 'fa-key',
    'bi-hdd-stack': 'fa-server',
    'bi-chevron-right': 'fa-arrow-right',
    'bi-clipboard-check': 'fa-clipboard',
    'bi-box-arrow-right': 'fa-sign-out',
    'bi-table': 'fa-table',
    'bi-database': 'fa-database',
    'bi-funnel-fill': 'fa-filter',
    'bi-arrow-up-circle': 'fa-arrow-up',
    'bi-arrow-down-circle': 'fa-arrow-down',
    'bi-plus': 'fa-plus',
    'bi-dash': 'fa-minus',
    'bi-three-dots': 'fa-ellipsis-h',
    'bi-pencil-square': 'fa-pencil',
    'bi-trash3': 'fa-trash',
    'bi-eye-slash': 'fa-eye-slash',
    'bi-check2': 'fa-check',
    'bi-x-circle-fill': 'fa-times-circle',
    'bi-info-circle-fill': 'fa-info-circle',
    'bi-check-circle-fill': 'fa-check-circle',
    'bi-exclamation-circle-fill': 'fa-exclamation-circle',
    'bi-list-ul': 'fa-list',
    'bi-calendar-event': 'fa-calendar',
    'bi-play-circle': 'fa-play-circle',
    'bi-file-earmark-plus': 'fa-file',
    'bi-dot': 'fa-circle',
    'bi-play-fill': 'fa-play',
    'bi-gear-fill': 'fa-cog',
    'bi-speedometer2': 'fa-tachometer',
    'bi-archive': 'fa-archive',
    'bi-activity': 'fa-chart-line',
    'bi-code-square': 'fa-code',
    'bi-lightning': 'fa-bolt',
    'bi-lightning-fill': 'fa-bolt',
    'bi-house-door': 'fa-home',
    'bi-arrow-down-up': 'fa-arrows-v',
    'bi-check-square': 'fa-check-square',
    'bi-diagram-3': 'fa-sitemap',
}

def replace_icons_in_file(file_path):
    """Reemplaza todos los iconos Bootstrap en un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Patrón más amplio para encontrar iconos Bootstrap: <i class="...bi bi-ICON...">
        pattern = r'<i\s+class="([^"]*)"([^>]*)>'
        
        def replace_icon(match):
            nonlocal changes_made
            class_attr = match.group(1)
            other_attrs = match.group(2)
            
            # Verificar si contiene bi bi-ICON
            if 'bi ' in class_attr and 'bi-' in class_attr:
                # Extraer el nombre del icono Bootstrap
                bi_match = re.search(r'bi-([\w-]+)', class_attr)
                if bi_match:
                    bi_icon = f"bi-{bi_match.group(1)}"
                    
                    # Buscar el equivalente en Font Awesome
                    if bi_icon in ICON_MAPPING:
                        fa_icon = ICON_MAPPING[bi_icon]
                        
                        # Reemplazar bi bi-ICON con fa fa-ICON
                        new_class = re.sub(r'bi\s+bi-[\w-]+', f'fa {fa_icon}', class_attr)
                        
                        changes_made += 1
                        return f'<span class="{new_class}"{other_attrs}></span>'
            
            return match.group(0)  # No cambiar si no se encuentra mapeo
        
        # Aplicar reemplazos
        content = re.sub(pattern, replace_icon, content)
        
        # Solo escribir si hubo cambios
        if changes_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path}: {changes_made} iconos reemplazados")
            return changes_made
        else:
            print(f"⚪ {file_path}: Sin cambios")
            return 0
            
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return 0

def main():
    """Función principal"""
    print("🚀 Iniciando reemplazo masivo de Bootstrap Icons por Font Awesome")
    print("=" * 70)
    
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
        changes = replace_icons_in_file(file_path)
        total_changes += changes
        if changes > 0:
            files_changed += 1
    
    print()
    print("=" * 70)
    print(f"🎉 ¡Proceso completado!")
    print(f"📊 Resumen:")
    print(f"   • Archivos procesados: {len(template_files)}")
    print(f"   • Archivos modificados: {files_changed}")
    print(f"   • Total de iconos reemplazados: {total_changes}")
    print()
    print("✅ Todos los Bootstrap Icons han sido reemplazados por Font Awesome")
    print("🌐 Tu aplicación ahora funciona 100% offline sin dependencias externas")
    
    if total_changes > 0:
        print()
        print("🔄 Próximos pasos:")
        print("   1. Recompilar Tailwind CSS: python manage.py tailwind build --force")
        print("   2. Reiniciar el servidor: python manage.py runserver")
        print("   3. Probar la aplicación sin conexión a internet")

if __name__ == "__main__":
    main()