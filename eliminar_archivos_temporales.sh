#!/bin/bash

echo "🗑️  Eliminando archivos temporales..."
echo ""
echo "⚠️  IMPORTANTE: Se ha creado un backup en backup_archivos_solucion/"
echo ""

# Contador de archivos eliminados
eliminados=0

# Archivos de Prueba
echo "Eliminando archivos de prueba..."
rm -f test_modal_completo.py && ((eliminados++))
rm -f test_final_simple.py && ((eliminados++))
rm -f test_modal_real.py && ((eliminados++))
rm -f test_guardado_historial_debug.py && ((eliminados++))
rm -f test_historial_saver.py && ((eliminados++))
rm -f test_separacion_tablas.py && ((eliminados++))
rm -f test_tablas_mixtas_completo.py && ((eliminados++))
rm -f debug_datos_categoria.py && ((eliminados++))
rm -f diagnostico_modal_combinar.py && ((eliminados++))
rm -f diagnostico_rapido.py && ((eliminados++))

# Archivos de Documentación
echo "Eliminando archivos de documentación..."
rm -f RESUMEN_SOLUCION_FINAL.md && ((eliminados++))
rm -f INSTRUCCIONES_USO_TABLAS_MIXTAS.md && ((eliminados++))
rm -f GUARDADO_HISTORIAL_DOCENCIA.md && ((eliminados++))
rm -f SOLUCION_PROBLEMA_MODAL.md && ((eliminados++))
rm -f INSTRUCCIONES_COMPLETAR_ACTUALIZACION.md && ((eliminados++))
rm -f INSTRUCCIONES_USO_HISTORIAL.md && ((eliminados++))
rm -f RESUMEN_IMPLEMENTACION_TABLAS_MIXTAS.md && ((eliminados++))
rm -f IMPLEMENTACION_TABLAS_MIXTAS.md && ((eliminados++))
rm -f DIAGRAMA_FLUJO_TABLAS_MIXTAS.md && ((eliminados++))
rm -f RESUMEN_CAMBIOS_HISTORIAL.md && ((eliminados++))
rm -f CHECKLIST_VERIFICACION.md && ((eliminados++))
rm -f VERIFICACION_TABLAS_MIXTAS.md && ((eliminados++))
rm -f INSTRUCCIONES_DIAGNOSTICO.md && ((eliminados++))
rm -f README_DIAGNOSTICO.md && ((eliminados++))
rm -f DIAGNOSTICO_PROBLEMA_GUARDADO_HISTORIAL.md && ((eliminados++))
rm -f SOLUCION_RAPIDA.md && ((eliminados++))
rm -f RESUMEN_VERIFICACION_FINAL.md && ((eliminados++))
rm -f COMO_USAR_VERIFICACION.md && ((eliminados++))
rm -f SOLUCION_COMPLETADA.md && ((eliminados++))
rm -f SOLUCION_FINAL_MODAL.md && ((eliminados++))

# Scripts de Actualización
echo "Eliminando scripts de actualización..."
rm -f actualizar_funcion_categorias.py && ((eliminados++))
rm -f actualizar_funciones_procesamiento.py && ((eliminados++))
rm -f actualizar_funciones_simple.py && ((eliminados++))
rm -f actualizar_modelos_historicos.py && ((eliminados++))
rm -f actualizar_todas_funciones_final.py && ((eliminados++))
rm -f actualizar_todas_funciones_procesamiento.py && ((eliminados++))
rm -f agregar_campos_auditoria_modelos.py && ((eliminados++))
rm -f completar_campos_auditoria.py && ((eliminados++))
rm -f modify_views_final.py && ((eliminados++))
rm -f modify_views_mixto.py && ((eliminados++))
rm -f patch_logging_historial.py && ((eliminados++))
rm -f agregar_completar_campos.py && ((eliminados++))
rm -f agregar_completar_todas.py && ((eliminados++))
rm -f fix_scope_views.py && ((eliminados++))

# Scripts de Verificación
echo "Eliminando scripts de verificación..."
rm -f verificar_logs_django.py && ((eliminados++))
rm -f verificar_estructura_tabla.py && ((eliminados++))
rm -f verificar_campos_todas_tablas.py && ((eliminados++))
rm -f verificar_llamada_views.py && ((eliminados++))
rm -f verificar_implementacion.sh && ((eliminados++))

# Archivos de Salida
echo "Eliminando archivos de salida..."
rm -f test_output.txt && ((eliminados++))
rm -f test_final_output.txt && ((eliminados++))
rm -f test_final2.txt && ((eliminados++))
rm -f test_final3.txt && ((eliminados++))
rm -f test_modal_output.txt && ((eliminados++))
rm -f test_modal2.txt && ((eliminados++))

# Eliminar los scripts de backup y eliminación
echo "Eliminando scripts de mantenimiento..."
rm -f crear_backup.sh && ((eliminados++))

echo ""
echo "✅ Limpieza completada!"
echo ""
echo "📊 Resumen:"
echo "   - Archivos eliminados: $eliminados"
echo ""
echo "💾 Backup disponible en: backup_archivos_solucion/"
echo ""
echo "📝 Archivos IMPORTANTES que se mantuvieron:"
echo "   ✅ datos_archivados/historical_data_saver.py"
echo "   ✅ mapeos_campos_docencia.py"
echo "   ✅ datos_archivados/views.py"
echo "   ✅ historial/models.py"
echo ""
echo "Para eliminar este script ejecuta: rm eliminar_archivos_temporales.sh"
echo ""
