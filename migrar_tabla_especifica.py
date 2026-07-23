#!/usr/bin/env python3
"""
Script para migrar una tabla específica que no fue incluida en la migración automática
"""
import os
import sys
import django
import mysql.connector
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.services import MigracionService, InspectorBaseDatos
from datos_archivados.models import DatoArchivadoDinamico
from django.contrib.auth.models import User

def migrar_tabla_especifica(host, database, user, password, tabla_nombre, port=3306):
    """Migra una tabla específica"""
    
    print(f"Iniciando migración de tabla específica: {tabla_nombre}")
    
    # Verificar si ya existe
    registros_existentes = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla_nombre).count()
    if registros_existentes > 0:
        print(f"⚠ La tabla {tabla_nombre} ya tiene {registros_existentes} registros migrados")
        respuesta = input("¿Desea continuar y migrar registros nuevos? (s/n): ")
        if respuesta.lower() != 's':
            print("Migración cancelada")
            return
    
    # Crear servicio de migración
    servicio = MigracionService(host, database, user, password, port)
    
    try:
        # Conectar a MariaDB
        if not servicio.conectar_mariadb():
            print("❌ Error: No se pudo conectar a MariaDB")
            return False
        
        # Crear inspector
        inspector = InspectorBaseDatos(servicio.connection)
        
        # Verificar que la tabla existe
        tablas_disponibles = inspector.obtener_tablas()
        if tabla_nombre not in tablas_disponibles:
            print(f"❌ Error: La tabla '{tabla_nombre}' no existe en la base de datos")
            print(f"Tablas disponibles que contienen 'account':")
            for tabla in tablas_disponibles:
                if 'account' in tabla.lower():
                    print(f"  - {tabla}")
            return False
        
        print(f"✓ Tabla encontrada: {tabla_nombre}")
        
        # Inspeccionar la tabla específica
        estructura = inspector.inspeccionar_tabla(tabla_nombre)
        modelo_dinamico = inspector.crear_modelo_dinamico(estructura)
        
        print(f"✓ Estructura inspeccionada: {len(estructura['columnas'])} columnas")
        
        # Obtener usuario para el log
        usuario = User.objects.filter(is_superuser=True).first()
        if not usuario:
            print("❌ Error: No hay superusuarios disponibles")
            return False
        
        # Iniciar log de migración
        servicio.iniciar_migracion(usuario)
        servicio.migration_log.estado = 'en_progreso'
        servicio.migration_log.save()
        
        # Configurar inspector en el servicio
        servicio.inspector = inspector
        servicio.inspector.tablas_inspeccionadas = {tabla_nombre: estructura}
        
        # Migrar la tabla
        print(f"Migrando registros de {tabla_nombre}...")
        registros_origen = servicio.migrar_tabla_dinamica(tabla_nombre, modelo_dinamico)
        
        # Contar registros realmente migrados
        registros_nuevos = DatoArchivadoDinamico.objects.filter(
            tabla_origen=tabla_nombre,
            fecha_migracion__gte=servicio.migration_log.fecha_inicio
        ).count()
        
        # Finalizar migración
        servicio.migration_log.usuarios_migrados = registros_nuevos
        servicio.finalizar_migracion('completada')
        
        print(f"✅ Migración completada:")
        print(f"   - Registros en origen: {registros_origen}")
        print(f"   - Registros nuevos migrados: {registros_nuevos}")
        print(f"   - Total registros en destino: {DatoArchivadoDinamico.objects.filter(tabla_origen=tabla_nombre).count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        if servicio.migration_log:
            servicio.finalizar_migracion('error', str(e))
        return False
    finally:
        servicio.desconectar_mariadb()

def main():
    if len(sys.argv) != 6:
        print("Uso: python migrar_tabla_especifica.py <host> <database> <user> <password> <tabla_nombre>")
        print("Ejemplo: python migrar_tabla_especifica.py localhost mi_db usuario contraseña accounts_registro")
        sys.exit(1)
    
    host = sys.argv[1]
    database = sys.argv[2]
    user = sys.argv[3]
    password = sys.argv[4]
    tabla_nombre = sys.argv[5]
    
    success = migrar_tabla_especifica(host, database, user, password, tabla_nombre)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()