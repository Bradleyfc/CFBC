#!/usr/bin/env python
"""
Script para probar la API del chatbot
"""

import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.test import Client

def test_chatbot_api():
    """Probar la API del chatbot"""
    
    client = Client()
    
    # Datos de prueba
    test_data = {
        'pregunta': '¿Cuándo empiezan las inscripciones?',
        'session_id': 'test_session_123'
    }
    
    print("🌐 Probando API del chatbot...")
    
    # Probar endpoint /chatbot/ask/
    response = client.post(
        '/chatbot/ask/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API funcionando correctamente")
        print(f"Respuesta: {data.get('respuesta', '')[:150]}...")
        print(f"Fuentes: {len(data.get('fuentes', []))}")
        print(f"Confianza: {data.get('confianza', 0)}")
    else:
        print(f"❌ Error en API: {response.status_code}")
        print(f"Contenido: {response.content.decode()}")
    
    # Probar endpoint /chatbot/status/
    response = client.get('/chatbot/status/')
    print(f"\nStatus endpoint: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Status endpoint funcionando")
        print(f"Estado: {data}")

if __name__ == "__main__":
    test_chatbot_api()