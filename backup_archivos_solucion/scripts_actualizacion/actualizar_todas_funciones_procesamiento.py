#!/usr/bin/env python
"""
Script para actualizar TODAS las funciones de procesamiento para usar mapeos de campos.
"""

# Leer el archivo
with open('datos_archivados/historical_data_saver.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Lista de reemplazos a realizar
# Formato: (buscar, reemplazar, nombre_tabla)
reemplazos = [
    # _procesar_categorias
    (
        '''def _procesar_categorias(datos_tabla, ModeloHistorico, mapeo_categorias, logger):
    """Procesa y guarda categorías en HistoricalCourseCategory."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva categoría histórica
                categoria = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_coursecategory',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(categoria, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_categorias(datos_tabla, ModeloHistorico, mapeo_categorias, logger):
    """Procesa y guarda categorías en HistoricalCourseCategory."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_coursecategory')
                
                # Crear nueva categoría histórica
                categoria = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_coursecategory',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(categoria, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_cursos
    (
        '''def _procesar_cursos(datos_tabla, ModeloHistorico, mapeo_areas, mapeo_categorias, mapeo_cursos, logger):
    """Procesa y guarda cursos en HistoricalCourseInformation."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nuevo curso histórico
                curso = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_courseinformation',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(curso, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_cursos(datos_tabla, ModeloHistorico, mapeo_areas, mapeo_categorias, mapeo_cursos, logger):
    """Procesa y guarda cursos en HistoricalCourseInformation."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_courseinformation')
                
                # Crear nuevo curso histórico
                curso = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_courseinformation',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(curso, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_admin_teachers
    (
        '''def _procesar_admin_teachers(datos_tabla, ModeloHistorico, mapeo_cursos, logger):
    """Procesa y guarda relaciones admin-teachers en HistoricalCourseInformationAdminTeachers."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva relación histórica
                admin_teacher = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_courseinformation_adminteachers',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(admin_teacher, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_admin_teachers(datos_tabla, ModeloHistorico, mapeo_cursos, logger):
    """Procesa y guarda relaciones admin-teachers en HistoricalCourseInformationAdminTeachers."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_courseinformation_adminteachers')
                
                # Crear nueva relación histórica
                admin_teacher = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_courseinformation_adminteachers',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(admin_teacher, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_asignaturas
    (
        '''def _procesar_asignaturas(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_asignaturas, logger):
    """Procesa y guarda asignaturas en HistoricalSubjectInformation."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva asignatura histórica
                asignatura = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_subjectinformation',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(asignatura, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_asignaturas(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_asignaturas, logger):
    """Procesa y guarda asignaturas en HistoricalSubjectInformation."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_subjectinformation')
                
                # Crear nueva asignatura histórica
                asignatura = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_subjectinformation',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(asignatura, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_ediciones
    (
        '''def _procesar_ediciones(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_ediciones, logger):
    """Procesa y guarda ediciones en HistoricalEdition."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva edición histórica
                edicion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_edition',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(edicion, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_ediciones(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_ediciones, logger):
    """Procesa y guarda ediciones en HistoricalEdition."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_edition')
                
                # Crear nueva edición histórica
                edicion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_edition',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(edicion, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_solicitudes
    (
        '''def _procesar_solicitudes(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_solicitudes, logger):
    """Procesa y guarda solicitudes en HistoricalEnrollmentApplication."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva solicitud histórica
                solicitud = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollmentapplication',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(solicitud, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_solicitudes(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_solicitudes, logger):
    """Procesa y guarda solicitudes en HistoricalEnrollmentApplication."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_enrollmentapplication')
                
                # Crear nueva solicitud histórica
                solicitud = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollmentapplication',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(solicitud, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_cuentas
    (
        '''def _procesar_cuentas(datos_tabla, ModeloHistorico, mapeo_cuentas, logger):
    """Procesa y guarda cuentas en HistoricalAccountNumber."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva cuenta histórica
                cuenta = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_accountnumber',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(cuenta, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_cuentas(datos_tabla, ModeloHistorico, mapeo_cuentas, logger):
    """Procesa y guarda cuentas en HistoricalAccountNumber."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_accountnumber')
                
                # Crear nueva cuenta histórica
                cuenta = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_accountnumber',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(cuenta, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_pagos
    (
        '''def _procesar_pagos(datos_tabla, ModeloHistorico, mapeo_solicitudes, mapeo_cuentas, logger):
    """Procesa y guarda pagos en HistoricalEnrollmentPay."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nuevo pago histórico
                pago = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollmentpay',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(pago, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_pagos(datos_tabla, ModeloHistorico, mapeo_solicitudes, mapeo_cuentas, logger):
    """Procesa y guarda pagos en HistoricalEnrollmentPay."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_enrollmentpay')
                
                # Crear nuevo pago histórico
                pago = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollmentpay',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(pago, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_inscripciones
    (
        '''def _procesar_inscripciones(datos_tabla, ModeloHistorico, mapeo_asignaturas, mapeo_ediciones, logger):
    """Procesa y guarda inscripciones en HistoricalEnrollment."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva inscripción histórica
                inscripcion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollment',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(inscripcion, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_inscripciones(datos_tabla, ModeloHistorico, mapeo_asignaturas, mapeo_ediciones, logger):
    """Procesa y guarda inscripciones en HistoricalEnrollment."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_enrollment')
                
                # Crear nueva inscripción histórica
                inscripcion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollment',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(inscripcion, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
    
    # _procesar_aplicaciones
    (
        '''def _procesar_aplicaciones(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_ediciones, logger):
    """Procesa y guarda aplicaciones en HistoricalApplication."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Crear nueva aplicación histórica
                aplicacion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_application',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(aplicacion, datos, campos_excluir=['id', 'pk'], logger=logger)''',
        '''def _procesar_aplicaciones(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_ediciones, logger):
    """Procesa y guarda aplicaciones en HistoricalApplication."""
    registros_guardados = 0
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_application')
                
                # Crear nueva aplicación histórica
                aplicacion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_application',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(aplicacion, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
    ),
]

# Aplicar todos los reemplazos
funciones_actualizadas = 0
for buscar, reemplazar in reemplazos:
    if buscar in contenido:
        contenido = contenido.replace(buscar, reemplazar)
        funciones_actualizadas += 1
        print(f"✓ Función actualizada ({funciones_actualizadas}/10)")
    else:
        print(f"⚠ No se encontró el patrón para actualizar")

# Guardar el archivo
with open('datos_archivados/historical_data_saver.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print(f"\n✓ Archivo actualizado. {funciones_actualizadas} funciones modificadas.")
