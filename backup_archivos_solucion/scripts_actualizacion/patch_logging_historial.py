"""
Script para agregar logging adicional al archivo historical_data_saver.py
Este script agrega prints y logging detallado para debug.
"""

import os

def agregar_logging_detallado():
    """Agrega logging adicional al archivo historical_data_saver.py"""
    
    archivo = 'datos_archivados/historical_data_saver.py'
    
    if not os.path.exists(archivo):
        print(f"❌ No se encontró el archivo: {archivo}")
        return
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar la línea donde se obtienen los datos
    linea_buscar = "datos_tabla = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla)"
    
    if linea_buscar in contenido:
        # Agregar logging después de esta línea
        logging_adicional = """
            # DEBUG: Verificar que el query funciona
            logger.info(f"🔍 DEBUG: Ejecutando query para tabla: {tabla}")
            logger.info(f"🔍 DEBUG: Query: DatoArchivadoDinamico.objects.filter(tabla_origen='{tabla}')")
            logger.info(f"🔍 DEBUG: Tipo de datos_tabla: {type(datos_tabla)}")
            
            # Verificar si el queryset está vacío
            if not datos_tabla.exists():
                logger.warning(f"⚠️  DEBUG: El queryset está vacío para {tabla}")
                logger.info(f"🔍 DEBUG: Verificando todas las tablas disponibles...")
                todas_tablas = DatoArchivadoDinamico.objects.values_list('tabla_origen', flat=True).distinct()
                logger.info(f"🔍 DEBUG: Tablas disponibles: {list(todas_tablas)}")
"""
        
        contenido = contenido.replace(
            linea_buscar,
            linea_buscar + logging_adicional
        )
        
        print("✅ Logging adicional agregado después del query")
    
    # Agregar logging al inicio de cada función _procesar_*
    funciones_procesar = [
        '_procesar_areas',
        '_procesar_categorias',
        '_procesar_cursos',
        '_procesar_admin_teachers',
        '_procesar_asignaturas',
        '_procesar_ediciones',
        '_procesar_solicitudes',
        '_procesar_cuentas',
        '_procesar_pagos',
        '_procesar_inscripciones',
        '_procesar_aplicaciones',
    ]
    
    for funcion in funciones_procesar:
        patron = f'def {funcion}(datos_tabla,'
        if patron in contenido:
            # Buscar el inicio del with transaction.atomic():
            inicio_funcion = contenido.find(patron)
            inicio_transaction = contenido.find('with transaction.atomic():', inicio_funcion)
            
            if inicio_transaction != -1:
                logging_funcion = f"""
    logger.info(f"🔧 DEBUG: Iniciando {funcion}")
    logger.info(f"🔧 DEBUG: Cantidad de registros a procesar: {{datos_tabla.count()}}")
    
    """
                # Insertar antes del with transaction.atomic()
                contenido = contenido[:inicio_transaction] + logging_funcion + contenido[inicio_transaction:]
                print(f"✅ Logging agregado a {funcion}")
    
    # Guardar el archivo modificado
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print(f"\n✅ Archivo modificado guardado: {archivo}")
    print("   Se agregó logging detallado para debug")


def main():
    print("\n" + "=" * 80)
    print("AGREGANDO LOGGING ADICIONAL PARA DEBUG")
    print("=" * 80)
    
    agregar_logging_detallado()
    
    print("\n" + "=" * 80)
    print("COMPLETADO")
    print("=" * 80)
    print("\nAhora puedes:")
    print("1. Ejecutar el servidor Django")
    print("2. Hacer clic en 'Combinar Tablas'")
    print("3. Observar los logs detallados en la consola")


if __name__ == '__main__':
    main()
