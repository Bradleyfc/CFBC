#!/usr/bin/env python3
"""
Check contact text format
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.models import DocumentEmbedding

def check_contact_text():
    """
    Check contact text format
    """
    print("🔍 Contact Text Format")
    print("=" * 40)
    
    # Get contact documents
    contact_docs = DocumentEmbedding.objects.filter(categoria='contacto')
    
    for i, doc in enumerate(contact_docs, 1):
        print(f"\n{i}. Contact Document:")
        print(f"   Text: {repr(doc.texto_indexado)}")
        print(f"   Lines:")
        for j, line in enumerate(doc.texto_indexado.split('\n'), 1):
            print(f"     {j}: {repr(line.strip())}")

if __name__ == '__main__':
    try:
        check_contact_text()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()