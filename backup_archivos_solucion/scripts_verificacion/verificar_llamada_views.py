"""
Script para verificar que la función guardar_datos_docencia_en_historial
se está llamando correctamente desde views.py
"""

import os
import re

def analizar_views():
    """Analiza el archivo views.py para verificar la llamada a la función."""
    print("\n" + "=" * 80)
    print("ANALIZANDO LLAMADAS EN VIEWS.PY")
    print("=" * 80)
    
    archivo_views = 'datos_archivados/views.py'
    
    if not os.path.exists(archivo_views):
        print(f"❌ No se encontró el archivo: {archivo_views}")
        return
    
    with open(archivo_views, 'r', encoding='utf-8') as f:
        contenido = f.read()
        lineas = contenido.split('\n')
    
    # Buscar imports
    print("\n📦 VERIFICANDO IMPORTS")
    print("-" * 80)
    
    import_encontrado = False
    for i, linea in enumerate(lineas, 1):
        if 'guardar_datos_docencia_en_historial' in linea and 'import' in linea:
            print(f"✅ Línea {i}: {linea.strip()}")
            import_encontrado = True
    
    if not import_encontrado:
        print("❌ No se encontró el import de guardar_datos_docencia_en_historial")
        print("   Debe agregarse:")
        print("   from .historical_data_saver import guardar_datos_docencia_en_historial")
    
    # Buscar llamadas a la función
    print("\n📞 VERIFICANDO LLAMADAS A LA FUNCIÓN")
    print("-" * 80)
    
    llamadas = []
    for i, linea in enumerate(lineas, 1):
        if 'guardar_datos_docencia_en_historial(' in linea and 'import' not in linea:
            llamadas.append((i, linea))
    
    if llamadas:
        print(f"✅ Encontradas {len(llamadas)} llamadas a la función:")
        for num_linea, linea in llamadas:
            print(f"\n   Línea {num_linea}:")
            print(f"   {linea.strip()}")
            
            # Mostrar contexto (5 líneas antes y después)
            print(f"\n   Contexto:")
            inicio = max(0, num_linea - 6)
            fin = min(len(lineas), num_linea + 5)
            for j in range(inicio, fin):
                marcador = ">>>" if j == num_linea - 1 else "   "
                print(f"   {marcador} {j+1:4d}: {lineas[j]}")
    else:
        print("❌ No se encontraron llamadas a guardar_datos_docencia_en_historial")
        print("   La función no se está ejecutando")
    
    # Buscar la lógica de separación de tablas
    print("\n🔍 VERIFICANDO LÓGICA DE SEPARACIÓN DE TABLAS")
    print("-" * 80)
    
    separacion_encontrada = False
    for i, linea in enumerate(lineas, 1):
        if 'tablas_docencia' in linea and '=' in linea and 'es_tabla_docencia' in linea:
            print(f"✅ Línea {i}: Lógica de separación encontrada")
            print(f"   {linea.strip()}")
            separacion_encontrada = True
            
            # Mostrar contexto
            print(f"\n   Contexto:")
            inicio = max(0, i - 3)
            fin = min(len(lineas), i + 10)
            for j in range(inicio, fin):
                marcador = ">>>" if j == i - 1 else "   "
                print(f"   {marcador} {j+1:4d}: {lineas[j]}")
            break
    
    if not separacion_encontrada:
        print("❌ No se encontró la lógica de separación de tablas")
    
    # Buscar condiciones que verifican tablas_docencia
    print("\n🎯 VERIFICANDO CONDICIONES PARA TABLAS DE DOCENCIA")
    print("-" * 80)
    
    condiciones = []
    for i, linea in enumerate(lineas, 1):
        if re.search(r'if\s+tablas_docencia', linea):
            condiciones.append((i, linea))
    
    if condiciones:
        print(f"✅ Encontradas {len(condiciones)} condiciones:")
        for num_linea, linea in condiciones:
            print(f"\n   Línea {num_linea}:")
            print(f"   {linea.strip()}")
    else:
        print("⚠️  No se encontraron condiciones que verifiquen tablas_docencia")
    
    # Buscar manejo de errores
    print("\n🛡️  VERIFICANDO MANEJO DE ERRORES")
    print("-" * 80)
    
    try_catch_encontrado = False
    for i, linea in enumerate(lineas, 1):
        if 'guardar_datos_docencia_en_historial' in lineas[min(i, len(lineas)-1)]:
            # Buscar try/except cercano
            for j in range(max(0, i-10), min(len(lineas), i+10)):
                if 'try:' in lineas[j]:
                    try_catch_encontrado = True
                    print(f"✅ Try/except encontrado cerca de la línea {i}")
                    
                    # Buscar el except correspondiente
                    for k in range(j, min(len(lineas), j+50)):
                        if 'except' in lineas[k]:
                            print(f"   Línea {k+1}: {lineas[k].strip()}")
                            # Mostrar qué hace con el error
                            for m in range(k, min(len(lineas), k+5)):
                                if lineas[m].strip():
                                    print(f"      {lineas[m].strip()}")
                            break
                    break
    
    if not try_catch_encontrado:
        print("⚠️  No se encontró manejo de errores alrededor de la llamada")
        print("   Recomendación: Agregar try/except para capturar errores")


def verificar_es_tabla_docencia():
    """Verifica la función es_tabla_docencia."""
    print("\n" + "=" * 80)
    print("VERIFICANDO FUNCIÓN es_tabla_docencia")
    print("=" * 80)
    
    archivo = 'datos_archivados/historical_data_saver.py'
    
    if not os.path.exists(archivo):
        print(f"❌ No se encontró el archivo: {archivo}")
        return
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar la función
    if 'def es_tabla_docencia' in contenido:
        print("✅ Función es_tabla_docencia encontrada")
        
        # Extraer la función
        inicio = contenido.find('def es_tabla_docencia')
        fin = contenido.find('\ndef ', inicio + 1)
        funcion = contenido[inicio:fin]
        
        print("\nCódigo de la función:")
        print("-" * 80)
        print(funcion)
        print("-" * 80)
        
        # Verificar el mapeo
        if 'DOCENCIA_TABLES_MAPPING' in contenido:
            print("\n✅ DOCENCIA_TABLES_MAPPING encontrado")
            
            inicio_map = contenido.find('DOCENCIA_TABLES_MAPPING = {')
            fin_map = contenido.find('}', inicio_map) + 1
            mapeo = contenido[inicio_map:fin_map]
            
            print("\nMapeo de tablas:")
            print("-" * 80)
            print(mapeo)
            print("-" * 80)
            
            # Contar tablas en el mapeo
            tablas = re.findall(r"'(Docencia_\w+)':", mapeo)
            print(f"\n📊 Total de tablas en el mapeo: {len(tablas)}")
            print("Tablas:")
            for tabla in tablas:
                print(f"   • {tabla}")
    else:
        print("❌ No se encontró la función es_tabla_docencia")


def generar_codigo_test():
    """Genera código de prueba para verificar la detección de tablas."""
    print("\n" + "=" * 80)
    print("CÓDIGO DE PRUEBA PARA DJANGO SHELL")
    print("=" * 80)
    
    codigo = """
# Ejecutar en Django shell: python manage.py shell

from datos_archivados.historical_data_saver import (
    es_tabla_docencia,
    son_todas_tablas_docencia,
    DOCENCIA_TABLES_MAPPING
)

# Probar con tablas de ejemplo
tablas_prueba = [
    'Docencia_area',
    'Docencia_coursecategory',
    'Docencia_courseinformation',
    'Usuario_user',  # Esta NO es de docencia
]

print("\\nProbando es_tabla_docencia:")
print("-" * 50)
for tabla in tablas_prueba:
    resultado = es_tabla_docencia(tabla)
    print(f"{tabla}: {resultado}")

print("\\nProbando son_todas_tablas_docencia:")
print("-" * 50)
solo_docencia = ['Docencia_area', 'Docencia_coursecategory']
mixtas = ['Docencia_area', 'Usuario_user']

print(f"Solo docencia {solo_docencia}: {son_todas_tablas_docencia(solo_docencia)}")
print(f"Mixtas {mixtas}: {son_todas_tablas_docencia(mixtas)}")

print("\\nMapeo completo:")
print("-" * 50)
for tabla, modelo in DOCENCIA_TABLES_MAPPING.items():
    print(f"{tabla} -> {modelo}")
"""
    
    print(codigo)
    
    # Guardar en archivo
    with open('test_deteccion_tablas.py', 'w', encoding='utf-8') as f:
        f.write(codigo)
    
    print("\n✅ Código guardado en: test_deteccion_tablas.py")


def main():
    """Función principal."""
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE LLAMADA A guardar_datos_docencia_en_historial")
    print("=" * 80)
    
    analizar_views()
    verificar_es_tabla_docencia()
    generar_codigo_test()
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN COMPLETADA")
    print("=" * 80)
    
    print("\n📋 RESUMEN DE VERIFICACIONES:")
    print("1. ✅ Imports verificados")
    print("2. ✅ Llamadas a la función verificadas")
    print("3. ✅ Lógica de separación de tablas verificada")
    print("4. ✅ Condiciones verificadas")
    print("5. ✅ Manejo de errores verificado")
    print("6. ✅ Función es_tabla_docencia verificada")
    print("7. ✅ Código de prueba generado")
    
    print("\n📝 PRÓXIMOS PASOS:")
    print("1. Revisar la salida anterior para identificar problemas")
    print("2. Ejecutar: python test_deteccion_tablas.py")
    print("3. Ejecutar: python test_guardado_historial_debug.py")
    print("4. Revisar logs de Django cuando se ejecuta 'Combinar Tablas'")


if __name__ == '__main__':
    main()
