#!/usr/bin/env python3
"""
Test categories in database
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.models import DocumentEmbedding

def test_categories():
    """
    Check categories in database
    """
    print("🔍 Categories in Database")
    print("=" * 40)
    
    # Get all unique categories
    categories = set(DocumentEmbedding.objects.values_list('categoria', flat=True))
    
    print("Unique categories:")
    for cat in sorted(categories):
        count = DocumentEmbedding.objects.filter(categoria=cat).count()
        print(f'  "{cat}": {count} documents')
    
    print("\nSample documents with 'contacto' category:")
    contacto_docs = DocumentEmbedding.objects.filter(categoria='contacto')[:3]
    for doc in contacto_docs:
        print(f"  - {doc.texto_indexado[:80]}...")

if __name__ == '__main__':
    try:
        test_categories()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()