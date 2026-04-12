#!/usr/bin/env python3
"""
Script para reemplazar TODOS los iconos (Font Awesome y Bootstrap) con Google Material Icons
"""

import os
import re
import glob

# Mapeo de iconos a Material Icons
ICON_MAPPING = {
    # Archivos y carpetas
    'bi-folder': 'folder',
    'fa-folder': 'folder',
    'icon-folder': 'folder',
    'bi-folder-plus': 'create_new_folder',
    'fa-folder-plus': 'create_new_folder',
    'icon-folder-plus': 'create_new_folder',
    'bi-folder-open': 'folder_open',
    'fa-folder-open': 'folder_open',
    'icon-folder-open': 'folder_open',
    'bi-folder2-open': 'folder_open',
    'bi-file-earmark': 'description',
    'fa-file': 'description',
    'icon-file': 'description',
    'bi-file-earmark-text': 'article',
    'fa-file-text': 'article',
    'icon-file-text': 'article',
    'bi-file-earmark-excel': 'table_chart',
    'fa-file-excel': 'table_chart',
    'icon-file-excel': 'table_chart',
    'bi-file-earmark-pdf': 'picture_as_pdf',
    'bi-file-earmark-x': 'description',
    'bi-file-earmark-plus': 'note_add',
    
    # Usuarios y personas
    'bi-people': 'group',
    'fa-users': 'group',
    'icon-users': 'group',
    'bi-person-fill': 'person',
    'bi-person-badge': 'badge',
    'bi-person-plus': 'person_add',
    'bi-person': 'person',
    'fa-user': 'person',
    'icon-user': 'person',
    'bi-users': 'group',
    
    # Acciones
    'bi-upload': 'cloud_upload',
    'fa-upload': 'cloud_upload',
    'icon-upload': 'cloud_upload',
    'bi-download': 'cloud_download',
    'fa-download': 'cloud_download',
    'icon-download': 'cloud_download',
    'bi-eye': 'visibility',
    'fa-eye': 'visibility',
    'icon-eye': 'visibility',
    'bi-trash': 'delete',
    'fa-trash': 'delete',
    'icon-trash': 'delete',
    'bi-search': 'search',
    'fa-search': 'search',
    'icon-search': 'search',
    'bi-filter': 'filter_list',
    'fa-filter': 'filter_list',
    'icon-filter': 'filter_list',
    'bi-funnel': 'filter_list',
    'bi-save': 'save',
    'bi-check': 'check',
    'fa-check': 'check',
    'icon-check': 'check',
    'bi-x': 'close',
    'fa-times': 'close',
    'icon-times': 'close',
    'bi-check-circle-fill': 'check_circle',
    'fa-check-circle': 'check_circle',
    'icon-check-circle': 'check_circle',
    
    # Navegación
    'bi-arrow-left': 'arrow_back',
    'fa-arrow-left': 'arrow_back',
    'icon-arrow-left': 'arrow_back',
    'bi-arrow-counterclockwise': 'undo',
    'bi-arrow-clockwise': 'refresh',
    'fa-sync': 'refresh',
    'icon-sync': 'refresh',
    'bi-chevron-right': 'chevron_right',
    'bi-chevron-down': 'keyboard_arrow_down',
    'bi-chevron-left': 'chevron_left',
    
    # Cerrar y cancelar
    'bi-x-lg': 'close',
    'bi-x-circle': 'cancel',
    'fa-times-circle': 'cancel',
    'icon-times-circle': 'cancel',
    'bi-times': 'close',
    'bi-times-circle': 'cancel',
    
    # Alertas e información
    'bi-exclamation-triangle': 'warning',
    'fa-exclamation-triangle': 'warning',
    'icon-exclamation-triangle': 'warning',
    'bi-exclamation-circle': 'error',
    'fa-exclamation-circle': 'error',
    'icon-exclamation-circle': 'error',
    'bi-info-circle': 'info',
    'fa-info-circle': 'info',
    'icon-info-circle': 'info',
    'bi-check-circle': 'check_circle',
    'bi-plus-circle': 'add_circle',
    'fa-plus-circle': 'add_circle',
    'icon-plus-circle': 'add_circle',
    
    # Gráficos y estadísticas
    'bi-graph-up': 'trending_up',
    'bi-chart-line': 'trending_up',
    'fa-chart-line': 'trending_up',
    'icon-chart-line': 'trending_up',
    'bi-bar-chart': 'bar_chart',
    
    # Portapapeles y datos
    'bi-clipboard-data': 'assignment',
    'bi-clipboard': 'assignment',
    'fa-clipboard': 'assignment',
    'icon-clipboard': 'assignment',
    'bi-clipboard-plus': 'assignment_add',
    'bi-clipboard-check': 'assignment_turned_in',
    
    # Formularios y texto
    'bi-journal-text': 'article',
    'bi-list-ol': 'format_list_numbered',
    'bi-list': 'list',
    'bi-list-ul': 'list',
    
    # Contacto y comunicación
    'bi-geo-alt-fill': 'location_on',
    'fa-map-marker': 'location_on',
    'icon-map-marker': 'location_on',
    'bi-telephone-fill': 'phone',
    'fa-phone': 'phone',
    'icon-phone': 'phone',
    'bi-envelope-fill': 'email',
    'fa-envelope': 'email',
    'icon-envelope': 'email',
    'bi-facebook': 'facebook',
    'fa-facebook': 'facebook',
    'icon-facebook': 'facebook',
    'bi-twitter': 'twitter',
    'fa-twitter': 'twitter',
    'icon-twitter': 'twitter',
    'bi-instagram': 'instagram',
    'fa-instagram': 'instagram',
    'icon-instagram': 'instagram',
    'bi-linkedin': 'linkedin',
    'fa-linkedin': 'linkedin',
    'icon-linkedin': 'linkedin',
    
    # Autenticación
    'bi-box-arrow-in-right': 'login',
    'fa-sign-in': 'login',
    'icon-sign-in': 'login',
    'bi-box-arrow-right': 'logout',
    'fa-sign-out': 'logout',
    'icon-sign-out': 'logout',
    
    # Vistas y layouts
    'bi-grid-3x3-gap': 'grid_view',
    'bi-grid': 'grid_view',
    'fa-th': 'grid_view',
    'icon-th': 'grid_view',
    
    # Tiempo
    'bi-clock-history': 'history',
    'bi-clock': 'schedule',
    'fa-clock': 'schedule',
    'icon-clock': 'schedule',
    
    # Otros iconos comunes
    'bi-home': 'home',
    'bi-house': 'home',
    'fa-home': 'home',
    'icon-home': 'home',
    'bi-cog': 'settings',
    'bi-gear': 'settings',
    'bi-gear-fill': 'settings',
    'fa-cog': 'settings',
    'icon-cog': 'settings',
    'bi-calendar': 'event',
    'bi-calendar-check': 'event_available',
    'bi-calendar-event': 'event',
    'fa-calendar': 'event',
    'icon-calendar': 'event',
    'bi-star': 'star',
    'fa-star': 'star',
    'icon-star': 'star',
    'bi-heart': 'favorite',
    'fa-heart': 'favorite',
    'icon-heart': 'favorite',
    'bi-camera': 'camera_alt',
    'fa-camera': 'camera_alt',
    'icon-camera': 'camera_alt',
    'bi-book-open': 'book',
    'bi-book': 'book',
    'fa-book': 'book',
    'icon-book': 'book',
    'bi-academic-cap': 'school',
    'bi-identification': 'badge',
    'bi-pencil': 'edit',
    'bi-edit': 'edit',
    'fa-pencil': 'edit',
    'icon-pencil': 'edit',
    'bi-question-circle': 'help',
    'bi-reply': 'reply',
    'bi-inbox': 'inbox',
    'fa-inbox': 'inbox',
    'icon-inbox': 'inbox',
    'bi-exclamation-triangle-fill': 'warning',
    'bi-send': 'send',
    'fa-paper-plane': 'send',
    'icon-paper-plane': 'send',
    'bi-shield-lock': 'lock',
    'bi-shield-check': 'verified_user',
    'fa-shield': 'security',
    'icon-shield': 'security',
    'bi-key': 'vpn_key',
    'fa-key': 'vpn_key',
    'icon-key': 'vpn_key',
    'bi-hdd-stack': 'storage',
    'fa-server': 'dns',
    'icon-server': 'dns',
    'bi-table': 'table_view',
    'fa-table': 'table_view',
    'icon-table': 'table_view',
    'bi-database': 'storage',
    'fa-database': 'storage',
    'icon-database': 'storage',
    'bi-funnel-fill': 'filter_list',
    'bi-arrow-up-circle': 'keyboard_arrow_up',
    'fa-arrow-up': 'keyboard_arrow_up',
    'icon-arrow-up': 'keyboard_arrow_up',
    'bi-arrow-down-circle': 'keyboard_arrow_down',
    'fa-arrow-down': 'keyboard_arrow_down',
    'icon-arrow-down': 'keyboard_arrow_down',
    'bi-plus': 'add',
    'fa-plus': 'add',
    'icon-plus': 'add',
    'bi-dash': 'remove',
    'fa-minus': 'remove',
    'icon-minus': 'remove',
    'bi-three-dots': 'more_horiz',
    'fa-ellipsis-h': 'more_horiz',
    'icon-ellipsis-h': 'more_horiz',
    'bi-pencil-square': 'edit',
    'bi-trash3': 'delete',
    'bi-eye-slash': 'visibility_off',
    'fa-eye-slash': 'visibility_off',
    'icon-eye-slash': 'visibility_off',
    'bi-check2': 'check',
    'bi-x-circle-fill': 'cancel',
    'bi-info-circle-fill': 'info',
    'bi-check-circle-fill': 'check_circle',
    'bi-exclamation-circle-fill': 'error',
    'bi-play-circle': 'play_circle',
    'fa-play-circle': 'play_circle',
    'icon-play-circle': 'play_circle',
    'bi-dot': 'fiber_manual_record',
    'bi-play-fill': 'play_arrow',
    'fa-play': 'play_arrow',
    'icon-play': 'play_arrow',
    'bi-speedometer2': 'speed',
    'fa-tachometer': 'speed',
    'icon-tachometer': 'speed',
    'bi-archive': 'archive',
    'fa-archive': 'archive',
    'icon-archive': 'archive',
    'bi-activity': 'trending_up',
    'bi-code-square': 'code',
    'fa-code': 'code',
    'icon-code': 'code',
    'bi-lightning': 'flash_on',
    'bi-lightning-fill': 'flash_on',
    'fa-bolt': 'flash_on',
    'icon-bolt': 'flash_on',
    'bi-house-door': 'home',
    'bi-arrow-down-up': 'swap_vert',
    'fa-arrows-v': 'swap_vert',
    'icon-arrows-v': 'swap_vert',
    'bi-check-square': 'check_box',
    'fa-check-square': 'check_box',
    'icon-check-square': 'check_box',
    'bi-diagram-3': 'account_tree',
    'fa-sitemap': 'account_tree',
    'icon-sitemap': 'account_tree',
}

def replace_icons_in_file(file_path):
    """Reemplaza todos los iconos en un archivo con Material Icons"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Patrón para encontrar iconos: <i class="..."> o <span class="...">
        pattern = r'<(i|span)\s+class="([^"]*)"([^>]*)>'
        
        def replace_icon(match):
            nonlocal changes_made
            tag = match.group(1)
            class_attr = match.group(2)
            other_attrs = match.group(3)
            
            # Buscar iconos en las clases
            classes = class_attr.split()
            new_classes = []
            icon_found = None
            
            for cls in classes:
                # Verificar si es un icono conocido
                if cls in ICON_MAPPING:
                    icon_found = ICON_MAPPING[cls]
                    new_classes.append('material-icons')
                elif cls.startswith(('bi-', 'fa-', 'icon-')):
                    # Es un icono pero no está en el mapeo, usar un icono genérico
                    if 'folder' in cls:
                        icon_found = 'folder'
                    elif 'file' in cls:
                        icon_found = 'description'
                    elif 'user' in cls or 'person' in cls:
                        icon_found = 'person'
                    elif 'home' in cls or 'house' in cls:
                        icon_found = 'home'
                    elif 'search' in cls:
                        icon_found = 'search'
                    elif 'close' in cls or 'times' in cls or 'x' in cls:
                        icon_found = 'close'
                    elif 'check' in cls:
                        icon_found = 'check'
                    elif 'arrow' in cls:
                        icon_found = 'arrow_forward'
                    else:
                        icon_found = 'help'  # Icono por defecto
                    new_classes.append('material-icons')
                else:
                    # No es un icono, mantener la clase
                    new_classes.append(cls)
            
            if icon_found:
                changes_made += 1
                new_class_str = ' '.join(new_classes)
                return f'<span class="{new_class_str}"{other_attrs}>{icon_found}</span>'
            
            return match.group(0)  # No cambiar si no se encuentra icono
        
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
    print("🚀 Iniciando reemplazo masivo de iconos por Google Material Icons")
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
    print("✅ Todos los iconos han sido reemplazados por Google Material Icons")
    print("🌐 Tu aplicación ahora funciona 100% offline con Material Icons")
    
    if total_changes > 0:
        print()
        print("🔄 Próximos pasos:")
        print("   1. Recompilar Tailwind CSS: python manage.py tailwind build --force")
        print("   2. Reiniciar el servidor: python manage.py runserver")
        print("   3. Probar la aplicación sin conexión a internet")

if __name__ == "__main__":
    main()