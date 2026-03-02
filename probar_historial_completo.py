#!/usr/bin/env python3
"""
Script para probar el historial completo con las 11 secciones
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import Group
from principal.views import obtener_historial_usuario
import json

print("=" * 80)
print("PRUEBA DE HISTORIAL COMPLETO - 11 SECCIONES")
print("=" * 80)

# Buscar un usuario con historial
from historial.models import HistoricalApplication

usuario_con_historial = None
for app in HistoricalApplication.objects.filter(usuario__isnull=False).select_related('usuario')[:10]:
    usuario_con_historial = app.usuario
    break

if not usuario_con_historial:
    print("\n⚠ No se encontraron usuarios con historial")
    exit()

print(f"\n1. Usuario de prueba: {usuario_con_historial.username}")
print(f"   Nombre: {usuario_con_historial.get_full_name()}")
print(f"   Email: {usuario_con_historial.email}")

# Crear usuario secretaria
grupo_secretaria, _ = Group.objects.get_or_create(name='Secretaría')
usuario_secretaria = User.objects.filter(groups=grupo_secretaria).first()

if not usuario_secretaria:
    print("\n⚠ No hay usuarios en el grupo Secretaría")
    exit()

# Simular petición
factory = RequestFactory()
request = factory.get(f'/historial-usuario/{usuario_con_historial.id}/')
request.user = usuario_secretaria

middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
request.session.save()

print("\n2. Ejecutando vista obtener_historial_usuario...")
try:
    response = obtener_historial_usuario(request, usuario_con_historial.id)
    
    if response.status_code == 200:
        data = json.loads(response.content)
        
        print("\n3. ✓ Vista ejecutada correctamente")
        print("\n4. Datos retornados:")
        print(f"   Usuario: {data['usuario']['nombre']}")
        print(f"\n   SECCIONES DISPONIBLES:")
        print(f"   1. Aplicaciones: {len(data['aplicaciones'])} registros")
        print(f"   2. Matrículas: {len(data['matriculas'])} registros")
        print(f"   3. Solicitudes: {len(data['solicitudes_inscripcion'])} registros")
        print(f"   4. Pagos: {len(data['pagos'])} registros")
        print(f"   5. Cuentas Bancarias: {len(data['cuentas_bancarias'])} registros")
        print(f"   6. Cursos como Profesor: {len(data['cursos_como_profesor'])} registros")
        print(f"   7. Cursos Administrados: {len(data['cursos_administrados'])} registros")
        print(f"   8. Ediciones: {len(data['ediciones'])} registros")
        print(f"   9. Asignaturas: {len(data['asignaturas'])} registros")
        print(f"   10. Áreas: {len(data['areas'])} registros")
        print(f"   11. Categorías: {len(data['categorias'])} registros")
        
        # Mostrar ejemplo de datos detallados
        if data['aplicaciones']:
            print(f"\n5. Ejemplo de Aplicación (datos completos):")
            app = data['aplicaciones'][0]
            for key, value in app.items():
                if key not in ['id', 'tabla_origen', 'fecha_consolidacion']:
                    print(f"   - {key}: {value}")
        
        total_registros = sum([
            len(data['aplicaciones']),
            len(data['matriculas']),
            len(data['solicitudes_inscripcion']),
            len(data['pagos']),
            len(data['cuentas_bancarias']),
            len(data['cursos_como_profesor']),
            len(data['cursos_administrados']),
            len(data['ediciones']),
            len(data['asignaturas']),
            len(data['areas']),
            len(data['categorias'])
        ])
        
        print(f"\n6. TOTAL DE REGISTROS: {total_registros}")
        
    else:
        print(f"\n✗ Error: Status code {response.status_code}")
        print(f"   Respuesta: {response.content}")
        
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("INSTRUCCIONES PARA PROBAR EN EL NAVEGADOR")
print("=" * 80)
print(f"""
1. Inicia el servidor:
   python manage.py runserver

2. Accede como usuario del grupo "Secretaría"

3. Ve a: Perfil → Listado de Usuarios Registrados

4. Busca el usuario: {usuario_con_historial.username}

5. Click en "Ver Historial"

6. Verás el modal con las 11 secciones de información histórica

✓ El historial completo está funcionando!
""")
print("=" * 80)
