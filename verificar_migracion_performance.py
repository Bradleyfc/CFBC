#!/usr/bin/env python3
"""
Script para verificar y diagnosticar problemas de rendimiento en la migración
y el modal de resumen que no muestra las tablas migradas.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.models import MigracionLog, DatoArchivadoDinamico
from django.utils import timezone
from datetime import timedelta

def diagnosticar_migracion():
    """Diagnostica problemas comunes en la migración"""
    print("🔍 DIAGNÓSTICO DE MIGRACIÓN")
    print("=" * 50)
    
    # 1. Verificar última migración
    ultima_migracion = MigracionLog.objects.first()
    if ultima_migracion:
        print(f"📅 Última migración: {ultima_migracion.fecha_inicio}")
        print(f"📊 Estado: {ultima_migracion.estado}")
        print(f"🗂️  Tablas inspeccionadas: {ultima_migracion.tablas_inspeccionadas}")
        print(f"✅ Tablas con datos: {ultima_migracion.tablas_con_datos}")
        print(f"⭕ Tablas vacías: {ultima_migracion.tablas_vacias}")
        print(f"📝 Registros migrados: {ultima_migracion.usuarios_migrados}")
        
        # Verificar consistencia
        total_tablas_procesadas = (ultima_migracion.tablas_con_datos or 0) + (ultima_migracion.tablas_vacias or 0)
        print(f"\n🔍 VERIFICACIÓN DE CONSISTENCIA:")
        print(f"   Tablas procesadas calculadas: {total_tablas_procesadas}")
        print(f"   Tablas inspeccionadas reportadas: {ultima_migracion.tablas_inspeccionadas}")
        
        if total_tablas_procesadas != ultima_migracion.tablas_inspeccionadas:
            print("⚠️  PROBLEMA: Las tablas procesadas no coinciden con las inspeccionadas")
        else:
            print("✅ Consistencia OK")
            
        # Verificar datos reales
        datos_reales = DatoArchivadoDinamico.objects.count()
        tablas_reales = DatoArchivadoDinamico.objects.values('tabla_origen').distinct().count()
        
        print(f"\n📊 DATOS REALES EN BASE DE DATOS:")
        print(f"   Registros totales: {datos_reales}")
        print(f"   Tablas con datos: {tablas_reales}")
        
        if datos_reales != ultima_migracion.usuarios_migrados:
            print(f"⚠️  PROBLEMA: Registros reportados ({ultima_migracion.usuarios_migrados}) != Registros reales ({datos_reales})")
        else:
            print("✅ Conteo de registros OK")
            
        if tablas_reales != ultima_migracion.tablas_con_datos:
            print(f"⚠️  PROBLEMA: Tablas reportadas ({ultima_migracion.tablas_con_datos}) != Tablas reales ({tablas_reales})")
        else:
            print("✅ Conteo de tablas OK")
            
    else:
        print("❌ No se encontraron migraciones registradas")
    
    # 2. Verificar migraciones recientes con problemas
    hace_24_horas = timezone.now() - timedelta(hours=24)
    migraciones_recientes = MigracionLog.objects.filter(
        fecha_inicio__gte=hace_24_horas
    ).order_by('-fecha_inicio')
    
    print(f"\n📈 MIGRACIONES ÚLTIMAS 24 HORAS: {migraciones_recientes.count()}")
    for mig in migraciones_recientes[:5]:
        duracion = "N/A"
        if mig.fecha_fin and mig.fecha_inicio:
            duracion_seg = (mig.fecha_fin - mig.fecha_inicio).total_seconds()
            duracion = f"{int(duracion_seg/60)}m {int(duracion_seg%60)}s"
        
        print(f"   {mig.fecha_inicio.strftime('%H:%M:%S')} - {mig.estado} - {duracion} - {mig.usuarios_migrados} registros")
        
        if mig.estado == 'error':
            print(f"      ❌ Error: {mig.errores[:100]}...")
    
    # 3. Verificar distribución de datos por tabla
    print(f"\n📋 TOP 10 TABLAS CON MÁS DATOS:")
    tablas_stats = DatoArchivadoDinamico.objects.values('tabla_origen').annotate(
        total=django.db.models.Count('id')
    ).order_by('-total')[:10]
    
    for tabla in tablas_stats:
        print(f"   {tabla['tabla_origen']}: {tabla['total']} registros")
    
    return ultima_migracion

def verificar_modal_resumen():
    """Verifica problemas específicos del modal de resumen"""
    print(f"\n🖥️  VERIFICACIÓN DEL MODAL DE RESUMEN")
    print("=" * 50)
    
    # Verificar si hay migraciones completadas sin mostrar
    migraciones_completadas = MigracionLog.objects.filter(
        estado='completada',
        fecha_inicio__gte=timezone.now() - timedelta(hours=2)
    ).order_by('-fecha_inicio')
    
    print(f"✅ Migraciones completadas (últimas 2h): {migraciones_completadas.count()}")
    
    for mig in migraciones_completadas:
        print(f"\n📊 Migración {mig.id}:")
        print(f"   Inicio: {mig.fecha_inicio}")
        print(f"   Fin: {mig.fecha_fin}")
        print(f"   Tablas inspeccionadas: {mig.tablas_inspeccionadas}")
        print(f"   Tablas con datos: {mig.tablas_con_datos}")
        print(f"   Tablas vacías: {mig.tablas_vacias}")
        print(f"   Registros: {mig.usuarios_migrados}")
        
        # Verificar si los datos están correctos para el modal
        if mig.tablas_con_datos == 0 and mig.usuarios_migrados > 0:
            print("   ⚠️  PROBLEMA: Hay registros pero tablas_con_datos = 0")
            print("   🔧 SOLUCIÓN: Actualizar tablas_con_datos basado en datos reales")
            
            # Calcular tablas con datos reales para esta migración
            tablas_reales = DatoArchivadoDinamico.objects.filter(
                fecha_migracion__gte=mig.fecha_inicio,
                fecha_migracion__lte=mig.fecha_fin or timezone.now()
            ).values('tabla_origen').distinct().count()
            
            print(f"   📊 Tablas reales con datos: {tablas_reales}")
            
            # Corregir automáticamente
            if tablas_reales > 0:
                mig.tablas_con_datos = tablas_reales
                mig.tablas_vacias = max(0, mig.tablas_inspeccionadas - tablas_reales)
                mig.save()
                print(f"   ✅ CORREGIDO: tablas_con_datos = {tablas_reales}")

def generar_reporte_performance():
    """Genera un reporte de rendimiento"""
    print(f"\n⚡ REPORTE DE RENDIMIENTO")
    print("=" * 50)
    
    # Analizar migraciones por duración
    migraciones_con_duracion = []
    for mig in MigracionLog.objects.filter(
        estado='completada',
        fecha_fin__isnull=False
    ).order_by('-fecha_inicio')[:10]:
        duracion = (mig.fecha_fin - mig.fecha_inicio).total_seconds()
        registros_por_segundo = mig.usuarios_migrados / duracion if duracion > 0 else 0
        
        migraciones_con_duracion.append({
            'id': mig.id,
            'duracion': duracion,
            'registros': mig.usuarios_migrados,
            'rps': registros_por_segundo,
            'tablas': mig.tablas_inspeccionadas
        })
    
    if migraciones_con_duracion:
        print("📈 RENDIMIENTO DE MIGRACIONES RECIENTES:")
        print("   ID | Duración | Registros | Reg/seg | Tablas")
        print("   ---|----------|-----------|---------|-------")
        
        for mig in migraciones_con_duracion:
            duracion_min = int(mig['duracion'] / 60)
            duracion_seg = int(mig['duracion'] % 60)
            print(f"   {mig['id']:2d} | {duracion_min:2d}m {duracion_seg:2d}s | {mig['registros']:8d} | {mig['rps']:6.1f} | {mig['tablas']:5d}")
        
        # Calcular promedios
        avg_rps = sum(m['rps'] for m in migraciones_con_duracion) / len(migraciones_con_duracion)
        print(f"\n📊 Promedio: {avg_rps:.1f} registros/segundo")
        
        # Detectar migraciones lentas
        migraciones_lentas = [m for m in migraciones_con_duracion if m['rps'] < 10]
        if migraciones_lentas:
            print(f"⚠️  Migraciones lentas detectadas: {len(migraciones_lentas)}")
            print("   Posibles causas:")
            print("   - Base de datos con muchos registros (>40,000)")
            print("   - Conexión lenta a la base de datos")
            print("   - Actualizaciones de progreso muy frecuentes")
            print("   - Conteo de registros en cada tabla")

def main():
    """Función principal"""
    print("🚀 DIAGNÓSTICO DE MIGRACIÓN Y MODAL DE RESUMEN")
    print("=" * 60)
    
    try:
        # Ejecutar diagnósticos
        ultima_migracion = diagnosticar_migracion()
        verificar_modal_resumen()
        generar_reporte_performance()
        
        print(f"\n✅ DIAGNÓSTICO COMPLETADO")
        print("=" * 60)
        
        # Recomendaciones
        print("🔧 RECOMENDACIONES:")
        print("1. Si el modal no muestra tablas migradas, ejecutar este script corrige automáticamente")
        print("2. Para mejorar rendimiento con >40k registros:")
        print("   - Usar configuración optimizada en config_migracion.py")
        print("   - Reducir frecuencia de actualizaciones de progreso")
        print("   - Considerar migración en lotes más pequeños")
        print("3. Verificar conexión de red si la migración es muy lenta")
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()