#!/usr/bin/env python3
"""
Script para diagnosticar qué tablas están siendo omitidas en la migración
"""
import os
import sys
import django
import mysql.connector
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

def conectar_mariadb(host, database, user, password, port=3306):
    """Conectar a MariaDB"""
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error conectando a MariaDB: {e}")
        return None

def obtener_todas_las_tablas(connection):
    """Obtener todas las tablas de la base de datos"""
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tablas = [tabla[0] for tabla in cursor.fetchall()]
    cursor.close()
    return sorted(tablas)

def aplicar_filtro_actual(tablas):
    """Aplicar el filtro actual que usa el sistema"""
    # Este es el filtro actual en services.py línea 217-220
    tablas_interes = [t for t in tablas if not t.startswith('django_') 
                     and not t.startswith('auth_permission')
                     and t not in ['django_migrations', 'django_session', 'django_content_type']]
    return sorted(tablas_interes)

def main():
    if len(sys.argv) != 5:
        print("Uso: python diagnosticar_tablas_omitidas.py <host> <database> <user> <password>")
        print("Ejemplo: python diagnosticar_tablas_omitidas.py localhost mi_db usuario contraseña")
        sys.exit(1)
    
    host = sys.argv[1]
    database = sys.argv[2]
    user = sys.argv[3]
    password = sys.argv[4]
    
    print(f"Conectando a MariaDB: {host}/{database}")
    connection = conectar_mariadb(host, database, user, password)
    
    if not connection:
        print("No se pudo conectar a la base de datos")
        sys.exit(1)
    
    try:
        # Obtener todas las tablas
        todas_las_tablas = obtener_todas_las_tablas(connection)
        print(f"\n=== DIAGNÓSTICO DE TABLAS ===")
        print(f"Total de tablas en la base de datos: {len(todas_las_tablas)}")
        
        # Aplicar filtro actual
        tablas_filtradas = aplicar_filtro_actual(todas_las_tablas)
        print(f"Tablas después del filtro actual: {len(tablas_filtradas)}")
        print(f"Tablas omitidas por el filtro: {len(todas_las_tablas) - len(tablas_filtradas)}")
        
        # Mostrar tablas omitidas
        tablas_omitidas = [t for t in todas_las_tablas if t not in tablas_filtradas]
        
        print(f"\n=== TABLAS OMITIDAS ({len(tablas_omitidas)}) ===")
        for tabla in tablas_omitidas:
            print(f"  - {tabla}")
        
        print(f"\n=== TABLAS QUE SE MIGRARÍAN ({len(tablas_filtradas)}) ===")
        for tabla in tablas_filtradas:
            print(f"  - {tabla}")
        
        # Análisis por categorías
        print(f"\n=== ANÁLISIS POR CATEGORÍAS ===")
        
        # Tablas Django
        django_tables = [t for t in todas_las_tablas if t.startswith('django_')]
        print(f"Tablas Django (django_*): {len(django_tables)}")
        for tabla in django_tables:
            print(f"  - {tabla}")
        
        # Tablas auth_permission
        auth_perm_tables = [t for t in todas_las_tablas if t.startswith('auth_permission')]
        print(f"\nTablas auth_permission: {len(auth_perm_tables)}")
        for tabla in auth_perm_tables:
            print(f"  - {tabla}")
        
        # Tablas específicamente excluidas
        excluidas_especificas = [t for t in todas_las_tablas if t in ['django_migrations', 'django_session', 'django_content_type']]
        print(f"\nTablas específicamente excluidas: {len(excluidas_especificas)}")
        for tabla in excluidas_especificas:
            print(f"  - {tabla}")
        
        # Tablas auth_ que SÍ se incluyen
        auth_incluidas = [t for t in tablas_filtradas if t.startswith('auth_')]
        print(f"\nTablas auth_ que SÍ se migran: {len(auth_incluidas)}")
        for tabla in auth_incluidas:
            print(f"  - {tabla}")
        
        # Tablas principales del sistema
        principales = [t for t in tablas_filtradas if t.startswith('principal_')]
        print(f"\nTablas principales: {len(principales)}")
        for tabla in principales:
            print(f"  - {tabla}")
        
        # Otras tablas del sistema
        otras_sistema = [t for t in tablas_filtradas if not t.startswith('auth_') and not t.startswith('principal_')]
        print(f"\nOtras tablas del sistema: {len(otras_sistema)}")
        for tabla in otras_sistema:
            print(f"  - {tabla}")
        
        print(f"\n=== RESUMEN ===")
        print(f"Total en BD: {len(todas_las_tablas)}")
        print(f"Se migrarían: {len(tablas_filtradas)}")
        print(f"Se omiten: {len(tablas_omitidas)}")
        print(f"Diferencia reportada por usuario: {85 - 79} = 6 tablas")
        print(f"Diferencia real encontrada: {len(todas_las_tablas) - len(tablas_filtradas)} tablas")
        
        if len(todas_las_tablas) - len(tablas_filtradas) == 6:
            print("✓ La diferencia coincide con lo reportado por el usuario")
        else:
            print("⚠ La diferencia NO coincide con lo reportado")
        
    finally:
        connection.close()

if __name__ == "__main__":
    main()