"""
Script para verificar los logs de Django relacionados con el guardado en historial.
"""

import os
import sys
from pathlib import Path

def buscar_archivos_log():
    """Busca archivos de log en el proyecto."""
    print("\n" + "=" * 80)
    print("BUSCANDO ARCHIVOS DE LOG")
    print("=" * 80)
    
    # Directorios comunes donde se guardan logs
    directorios_buscar = [
        '.',
        'logs',
        'log',
        'var/log',
        '/var/log',
        '/tmp',
    ]
    
    archivos_log_encontrados = []
    
    for directorio in directorios_buscar:
        if os.path.exists(directorio):
            print(f"\n📁 Buscando en: {directorio}")
            try:
                for root, dirs, files in os.walk(directorio):
                    for file in files:
                        if file.endswith('.log') or 'log' in file.lower():
                            ruta_completa = os.path.join(root, file)
                            archivos_log_encontrados.append(ruta_completa)
                            print(f"   ✅ Encontrado: {ruta_completa}")
            except PermissionError:
                print(f"   ⚠️  Sin permisos para acceder a {directorio}")
    
    return archivos_log_encontrados


def buscar_en_settings():
    """Busca la configuración de logging en settings.py."""
    print("\n" + "=" * 80)
    print("VERIFICANDO CONFIGURACIÓN DE LOGGING EN SETTINGS")
    print("=" * 80)
    
    settings_paths = [
        'cfbc/settings.py',
        'settings.py',
        'config/settings.py',
        'cfbc/settings/base.py',
    ]
    
    for settings_path in settings_paths:
        if os.path.exists(settings_path):
            print(f"\n📄 Leyendo: {settings_path}")
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    
                    if 'LOGGING' in contenido:
                        print("   ✅ Configuración LOGGING encontrada")
                        
                        # Extraer la sección de LOGGING
                        inicio = contenido.find('LOGGING')
                        if inicio != -1:
                            # Buscar el final del diccionario LOGGING
                            lineas = contenido[inicio:].split('\n')
                            print("\n   Configuración de LOGGING:")
                            nivel_llaves = 0
                            for i, linea in enumerate(lineas[:50]):  # Limitar a 50 líneas
                                print(f"   {linea}")
                                nivel_llaves += linea.count('{') - linea.count('}')
                                if i > 0 and nivel_llaves == 0:
                                    break
                    else:
                        print("   ⚠️  No se encontró configuración LOGGING")
                        
            except Exception as e:
                print(f"   ❌ Error leyendo archivo: {e}")


def buscar_errores_recientes():
    """Busca errores recientes en los logs."""
    print("\n" + "=" * 80)
    print("BUSCANDO ERRORES RECIENTES RELACIONADOS CON HISTORIAL")
    print("=" * 80)
    
    archivos_log = buscar_archivos_log()
    
    palabras_clave = [
        'guardar_datos_docencia_en_historial',
        'historical_data_saver',
        'HistoricalArea',
        'DatoArchivadoDinamico',
        'ERROR',
        'Exception',
        'Traceback',
    ]
    
    for archivo_log in archivos_log:
        print(f"\n📄 Analizando: {archivo_log}")
        try:
            with open(archivo_log, 'r', encoding='utf-8', errors='ignore') as f:
                lineas = f.readlines()
                
                # Buscar las últimas 100 líneas
                lineas_recientes = lineas[-100:] if len(lineas) > 100 else lineas
                
                coincidencias = []
                for i, linea in enumerate(lineas_recientes):
                    for palabra in palabras_clave:
                        if palabra.lower() in linea.lower():
                            coincidencias.append((i, linea.strip()))
                            break
                
                if coincidencias:
                    print(f"   ✅ Encontradas {len(coincidencias)} coincidencias:")
                    for i, linea in coincidencias[-10:]:  # Mostrar últimas 10
                        print(f"      Línea {i}: {linea[:100]}")
                else:
                    print("   ➖ No se encontraron coincidencias")
                    
        except Exception as e:
            print(f"   ❌ Error leyendo log: {e}")


def verificar_consola_django():
    """Proporciona instrucciones para verificar logs en consola."""
    print("\n" + "=" * 80)
    print("INSTRUCCIONES PARA VERIFICAR LOGS EN CONSOLA")
    print("=" * 80)
    
    print("""
Para verificar los logs en tiempo real cuando ejecutas "Combinar Tablas":

1. Abre una terminal y ejecuta:
   python manage.py runserver

2. En otra terminal, ejecuta:
   tail -f <archivo_log>
   
   O si no hay archivo de log configurado, los logs aparecerán en la consola
   del servidor Django.

3. Realiza la acción "Combinar Tablas" en la interfaz web.

4. Observa los logs en tiempo real para ver:
   - Si se llama a guardar_datos_docencia_en_historial
   - Si hay errores durante el proceso
   - Cuántos registros se procesan
   - Si se guardan en los modelos históricos

5. Busca específicamente estos mensajes:
   - "INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL"
   - "Procesando tabla: Docencia_area"
   - "Encontrados X registros en Docencia_area"
   - "registros guardados en historial"
   - Cualquier mensaje de ERROR o Exception
""")


def main():
    """Función principal."""
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE LOGS DE DJANGO")
    print("=" * 80)
    
    buscar_archivos_log()
    buscar_en_settings()
    buscar_errores_recientes()
    verificar_consola_django()
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN COMPLETADA")
    print("=" * 80)


if __name__ == '__main__':
    main()
