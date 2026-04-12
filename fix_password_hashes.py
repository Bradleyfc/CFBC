#!/usr/bin/env python
"""
Script para corregir hashes de contraseñas malformados después de la combinación de datos.

El error "not enough values to unpack (expected 4, got 3)" indica que hay hashes
de contraseñas con formato incorrecto en la base de datos.

Django espera hashes con formato: algorithm$iterations$salt$hash
Pero algunos pueden tener solo: algorithm$salt$hash (3 partes en lugar de 4)
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analizar_hash_password(password_hash):
    """Analiza el formato de un hash de contraseña"""
    if not password_hash:
        return "vacío", 0, None
    
    if not password_hash.startswith(('pbkdf2_sha256', 'pbkdf2_sha1', 'bcrypt', 'argon2', 'sha1', 'md5')):
        return "texto_plano", 0, password_hash
    
    partes = password_hash.split('$')
    return partes[0], len(partes), partes

def corregir_hash_malformado(user_id, password_hash):
    """Corrige un hash de contraseña malformado"""
    try:
        algoritmo, num_partes, partes = analizar_hash_password(password_hash)
        
        if num_partes == 3 and algoritmo in ['pbkdf2_sha256', 'pbkdf2_sha1']:
            # Hash malformado: algorithm$salt$hash (falta iterations)
            # Agregar iterations por defecto
            if algoritmo == 'pbkdf2_sha256':
                iterations = '260000'  # Valor por defecto de Django 3.2+
            else:
                iterations = '150000'  # Valor por defecto para SHA1
            
            # Reconstruir hash: algorithm$iterations$salt$hash
            hash_corregido = f"{partes[0]}${iterations}${partes[1]}${partes[2]}"
            logger.info(f"Usuario {user_id}: Hash corregido de {num_partes} a 4 partes")
            return hash_corregido
        
        elif num_partes < 3:
            # Hash muy malformado, generar contraseña temporal
            password_temporal = f"temporal_{user_id}_2025"
            hash_nuevo = make_password(password_temporal)
            logger.warning(f"Usuario {user_id}: Hash muy malformado, generando contraseña temporal: {password_temporal}")
            return hash_nuevo
        
        else:
            # Hash parece estar bien formado
            return password_hash
            
    except Exception as e:
        logger.error(f"Error corrigiendo hash para usuario {user_id}: {e}")
        # En caso de error, generar contraseña temporal
        password_temporal = f"temporal_{user_id}_2025"
        return make_password(password_temporal)

def main():
    """Función principal para corregir hashes de contraseñas"""
    print("🔍 Analizando hashes de contraseñas en la base de datos...")
    
    usuarios_problematicos = []
    usuarios_analizados = 0
    usuarios_corregidos = 0
    
    # Analizar todos los usuarios
    for user in User.objects.all():
        usuarios_analizados += 1
        
        try:
            # Intentar analizar el hash
            algoritmo, num_partes, partes = analizar_hash_password(user.password)
            
            if num_partes != 4 and algoritmo != "texto_plano" and algoritmo != "vacío":
                usuarios_problematicos.append({
                    'id': user.id,
                    'username': user.username,
                    'algoritmo': algoritmo,
                    'num_partes': num_partes,
                    'hash_original': user.password[:50] + "..." if len(user.password) > 50 else user.password
                })
                logger.warning(f"Usuario problemático encontrado: {user.id} ({user.username}) - {num_partes} partes")
        
        except Exception as e:
            logger.error(f"Error analizando usuario {user.id} ({user.username}): {e}")
            usuarios_problematicos.append({
                'id': user.id,
                'username': user.username,
                'algoritmo': 'error',
                'num_partes': 0,
                'hash_original': str(e)
            })
    
    print(f"\n📊 Resumen del análisis:")
    print(f"   Usuarios analizados: {usuarios_analizados}")
    print(f"   Usuarios con problemas: {len(usuarios_problematicos)}")
    
    if not usuarios_problematicos:
        print("✅ No se encontraron problemas en los hashes de contraseñas.")
        return
    
    print(f"\n⚠️  Usuarios con hashes problemáticos:")
    for usuario in usuarios_problematicos:
        print(f"   ID {usuario['id']}: {usuario['username']} - {usuario['algoritmo']} ({usuario['num_partes']} partes)")
    
    # Auto-confirmar corrección para resolver el problema
    print(f"\n🔧 Procediendo automáticamente a corregir {len(usuarios_problematicos)} usuarios...")
    
    print("\n🔧 Corrigiendo hashes de contraseñas...")
    
    # Corregir usuarios problemáticos
    with transaction.atomic():
        for usuario_info in usuarios_problematicos:
            try:
                user = User.objects.get(id=usuario_info['id'])
                hash_original = user.password
                
                # Corregir el hash
                hash_corregido = corregir_hash_malformado(user.id, hash_original)
                
                # Actualizar usuario
                user.password = hash_corregido
                user.save()
                
                usuarios_corregidos += 1
                print(f"✅ Usuario {user.id} ({user.username}) corregido")
                
            except Exception as e:
                logger.error(f"Error corrigiendo usuario {usuario_info['id']}: {e}")
                print(f"❌ Error corrigiendo usuario {usuario_info['id']}: {e}")
    
    print(f"\n🎉 Corrección completada:")
    print(f"   Usuarios corregidos: {usuarios_corregidos}")
    print(f"   Usuarios con errores: {len(usuarios_problematicos) - usuarios_corregidos}")
    
    if usuarios_corregidos > 0:
        print(f"\n📝 IMPORTANTE:")
        print(f"   - Los usuarios corregidos pueden necesitar restablecer sus contraseñas")
        print(f"   - Los usuarios con contraseñas temporales deben cambiarlas")
        print(f"   - Formato de contraseñas temporales: 'temporal_[ID]_2025'")

if __name__ == "__main__":
    main()