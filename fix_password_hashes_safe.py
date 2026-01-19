#!/usr/bin/env python
"""
Script seguro para corregir hashes de contraseñas malformados.
Evita usar funciones de Django que validen los hashes durante la corrección.
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction, connection
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analizar_hash_seguro(password_hash):
    """Analiza el formato de un hash de contraseña sin usar validadores de Django"""
    if not password_hash:
        return "vacío", 0, []
    
    if not isinstance(password_hash, str):
        return "no_string", 0, []
    
    # Verificar si parece un hash
    algoritmos_conocidos = ['pbkdf2_sha256', 'pbkdf2_sha1', 'bcrypt', 'argon2', 'sha1', 'md5']
    
    es_hash = False
    algoritmo = "desconocido"
    
    for alg in algoritmos_conocidos:
        if password_hash.startswith(alg + '$'):
            es_hash = True
            algoritmo = alg
            break
    
    if not es_hash:
        # Podría ser texto plano o hash sin prefijo conocido
        if len(password_hash) < 20:
            return "posible_texto_plano", 0, []
        else:
            return "hash_desconocido", 0, []
    
    # Dividir por $ para contar partes
    partes = password_hash.split('$')
    return algoritmo, len(partes), partes

def generar_hash_pbkdf2_sha256(password):
    """Genera un hash PBKDF2-SHA256 manualmente sin usar Django"""
    import hashlib
    import base64
    import secrets
    
    # Parámetros por defecto de Django
    algorithm = 'pbkdf2_sha256'
    iterations = 260000
    salt = base64.b64encode(secrets.token_bytes(12)).decode('ascii')
    
    # Generar hash
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('ascii'), iterations)
    hash_b64 = base64.b64encode(hash_bytes).decode('ascii')
    
    return f"{algorithm}${iterations}${salt}${hash_b64}"

def corregir_hash_malformado_seguro(user_id, password_hash):
    """Corrige un hash de contraseña malformado de forma segura"""
    try:
        algoritmo, num_partes, partes = analizar_hash_seguro(password_hash)
        
        logger.info(f"Usuario {user_id}: Algoritmo={algoritmo}, Partes={num_partes}")
        
        if algoritmo == 'pbkdf2_sha256' and num_partes == 3:
            # Hash malformado: pbkdf2_sha256$salt$hash (falta iterations)
            # Agregar iterations por defecto
            iterations = '260000'
            hash_corregido = f"{partes[0]}${iterations}${partes[1]}${partes[2]}"
            logger.info(f"Usuario {user_id}: Hash PBKDF2-SHA256 corregido (agregadas iterations)")
            return hash_corregido
        
        elif algoritmo == 'pbkdf2_sha1' and num_partes == 3:
            # Hash malformado: pbkdf2_sha1$salt$hash (falta iterations)
            iterations = '150000'
            hash_corregido = f"{partes[0]}${iterations}${partes[1]}${partes[2]}"
            logger.info(f"Usuario {user_id}: Hash PBKDF2-SHA1 corregido (agregadas iterations)")
            return hash_corregido
        
        elif num_partes < 3 or algoritmo in ['posible_texto_plano', 'hash_desconocido', 'desconocido']:
            # Hash muy malformado o texto plano, generar nuevo hash
            password_temporal = f"temporal_{user_id}_2025"
            hash_nuevo = generar_hash_pbkdf2_sha256(password_temporal)
            logger.warning(f"Usuario {user_id}: Generando contraseña temporal: {password_temporal}")
            return hash_nuevo
        
        else:
            # Hash parece estar bien formado
            logger.info(f"Usuario {user_id}: Hash parece correcto")
            return password_hash
            
    except Exception as e:
        logger.error(f"Error corrigiendo hash para usuario {user_id}: {e}")
        # En caso de error, generar contraseña temporal
        password_temporal = f"temporal_{user_id}_2025"
        return generar_hash_pbkdf2_sha256(password_temporal)

def main():
    """Función principal para corregir hashes de contraseñas"""
    print("🔍 CORRECCIÓN SEGURA DE HASHES DE CONTRASEÑAS")
    print("=" * 60)
    
    # Usar consulta SQL directa para evitar validaciones de Django
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username, password FROM auth_user ORDER BY id")
        usuarios_raw = cursor.fetchall()
    
    print(f"📊 Usuarios encontrados: {len(usuarios_raw)}")
    
    usuarios_problematicos = []
    usuarios_analizados = 0
    
    # Analizar todos los usuarios
    for user_id, username, password_hash in usuarios_raw:
        usuarios_analizados += 1
        
        try:
            algoritmo, num_partes, partes = analizar_hash_seguro(password_hash)
            
            # Considerar problemático si:
            # 1. Es PBKDF2 pero tiene menos de 4 partes
            # 2. Es texto plano
            # 3. Es hash desconocido
            es_problematico = False
            
            if algoritmo in ['pbkdf2_sha256', 'pbkdf2_sha1'] and num_partes != 4:
                es_problematico = True
                razon = f"PBKDF2 con {num_partes} partes (necesita 4)"
            elif algoritmo == 'posible_texto_plano':
                es_problematico = True
                razon = "Posible texto plano"
            elif algoritmo in ['hash_desconocido', 'desconocido']:
                es_problematico = True
                razon = "Hash con formato desconocido"
            elif algoritmo == 'vacío':
                es_problematico = True
                razon = "Contraseña vacía"
            
            if es_problematico:
                usuarios_problematicos.append({
                    'id': user_id,
                    'username': username,
                    'algoritmo': algoritmo,
                    'num_partes': num_partes,
                    'razon': razon,
                    'hash_preview': password_hash[:50] + "..." if len(password_hash) > 50 else password_hash
                })
                
        except Exception as e:
            logger.error(f"Error analizando usuario {user_id} ({username}): {e}")
            usuarios_problematicos.append({
                'id': user_id,
                'username': username,
                'algoritmo': 'error',
                'num_partes': 0,
                'razon': f"Error de análisis: {str(e)}",
                'hash_preview': 'N/A'
            })
    
    print(f"\n📊 RESUMEN DEL ANÁLISIS:")
    print(f"   Usuarios analizados: {usuarios_analizados}")
    print(f"   Usuarios problemáticos: {len(usuarios_problematicos)}")
    
    if not usuarios_problematicos:
        print("✅ No se encontraron problemas en los hashes de contraseñas.")
        return
    
    print(f"\n⚠️  USUARIOS CON HASHES PROBLEMÁTICOS:")
    for i, usuario in enumerate(usuarios_problematicos[:10], 1):  # Mostrar solo los primeros 10
        print(f"   {i}. ID {usuario['id']}: {usuario['username']}")
        print(f"      Problema: {usuario['razon']}")
        print(f"      Hash: {usuario['hash_preview']}")
        print()
    
    if len(usuarios_problematicos) > 10:
        print(f"   ... y {len(usuarios_problematicos) - 10} usuarios más")
    
    print(f"\n🔧 PROCEDIENDO A CORREGIR {len(usuarios_problematicos)} USUARIOS...")
    print("=" * 60)
    
    usuarios_corregidos = 0
    usuarios_con_errores = 0
    contraseñas_temporales = []
    
    # Corregir usuarios problemáticos usando SQL directo
    with transaction.atomic():
        for usuario_info in usuarios_problematicos:
            try:
                user_id = usuario_info['id']
                username = usuario_info['username']
                
                # Obtener hash actual
                with connection.cursor() as cursor:
                    cursor.execute("SELECT password FROM auth_user WHERE id = %s", [user_id])
                    result = cursor.fetchone()
                    if not result:
                        continue
                    
                    hash_original = result[0]
                
                # Corregir el hash
                hash_corregido = corregir_hash_malformado_seguro(user_id, hash_original)
                
                # Actualizar usando SQL directo
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE auth_user SET password = %s WHERE id = %s",
                        [hash_corregido, user_id]
                    )
                
                usuarios_corregidos += 1
                
                # Si se generó contraseña temporal, guardar info
                if f"temporal_{user_id}_2025" in str(hash_original) or "temporal_" in str(hash_corregido):
                    contraseñas_temporales.append({
                        'id': user_id,
                        'username': username,
                        'password': f"temporal_{user_id}_2025"
                    })
                
                print(f"✅ Usuario {user_id} ({username}) corregido")
                
            except Exception as e:
                logger.error(f"Error corrigiendo usuario {usuario_info['id']}: {e}")
                print(f"❌ Error corrigiendo usuario {usuario_info['id']}: {e}")
                usuarios_con_errores += 1
    
    print(f"\n🎉 CORRECCIÓN COMPLETADA:")
    print("=" * 30)
    print(f"   ✅ Usuarios corregidos: {usuarios_corregidos}")
    print(f"   ❌ Usuarios con errores: {usuarios_con_errores}")
    print(f"   🔑 Contraseñas temporales generadas: {len(contraseñas_temporales)}")
    
    if contraseñas_temporales:
        print(f"\n🔑 CONTRASEÑAS TEMPORALES GENERADAS:")
        print("-" * 40)
        for info in contraseñas_temporales[:5]:  # Mostrar solo las primeras 5
            print(f"   Usuario: {info['username']} (ID: {info['id']})")
            print(f"   Contraseña temporal: {info['password']}")
            print()
        
        if len(contraseñas_temporales) > 5:
            print(f"   ... y {len(contraseñas_temporales) - 5} más")
        
        print(f"\n📝 IMPORTANTE:")
        print(f"   - Los usuarios con contraseñas temporales deben cambiarlas")
        print(f"   - Formato: 'temporal_[ID_USUARIO]_2025'")
        print(f"   - Notifica a los usuarios afectados")
    
    if usuarios_corregidos > 0:
        print(f"\n✅ Los usuarios ahora deberían ser accesibles en el admin de Django")

if __name__ == "__main__":
    main()