#!/usr/bin/env python
"""
Script para pre-descargar los modelos de Hugging Face del chatbot
Ejecutar: python chatbot/download_models.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

def download_models():
    """Descarga todos los modelos necesarios para el chatbot"""
    
    print("🤖 Descargando modelos del Chatbot Semántico CFBC...")
    print("=" * 60)
    
    try:
        # 1. Descargar modelo de embeddings semánticos
        print("\n📥 Descargando modelo de embeddings semánticos...")
        print("   Modelo: paraphrase-multilingual-MiniLM-L12-v2")
        print("   Tamaño aproximado: ~470 MB")
        
        from chatbot.services.semantic_search import SemanticSearchService
        search_service = SemanticSearchService()
        print("   ✅ Modelo de embeddings descargado correctamente")
        
        # 2. Descargar modelo LLM para generación de texto
        print("\n📥 Descargando modelo LLM para generación...")
        print("   Modelo: google/flan-t5-small")
        print("   Tamaño aproximado: ~308 MB")
        
        from chatbot.services.llm_generator import LLMGeneratorService
        llm_service = LLMGeneratorService()
        print("   ✅ Modelo LLM descargado correctamente")
        
        # 3. Verificar que todo funcione
        print("\n🔍 Verificando funcionamiento...")
        
        # Probar embeddings
        test_embedding = search_service.generate_embedding("prueba")
        print(f"   ✅ Embeddings funcionando (dimensión: {len(test_embedding)})")
        
        # Probar LLM (si está habilitado)
        if llm_service.is_available():
            print("   ✅ LLM funcionando correctamente")
        else:
            print("   ⚠️  LLM no disponible (puede estar deshabilitado)")
        
        print("\n🎉 ¡Todos los modelos descargados y verificados!")
        print("\n📍 Ubicación de los modelos:")
        print("   - Cache de Hugging Face: ~/.cache/huggingface/")
        print("   - En Windows: C:\\Users\\[usuario\\.cache\\huggingface\\")
        
        # Mostrar tamaño total aproximado
        print("\n💾 Espacio utilizado aproximado: ~800 MB")
        
    except Exception as e:
        print(f"\n❌ Error descargando modelos: {e}")
        print("\n🔧 Soluciones posibles:")
        print("   1. Verificar conexión a internet")
        print("   2. Verificar que las dependencias estén instaladas:")
        print("      pip install sentence-transformers transformers torch")
        print("   3. Verificar espacio en disco disponible")
        return False
    
    return True

if __name__ == "__main__":
    success = download_models()
    if success:
        print("\n✅ Descarga completada. El chatbot está listo para usar.")
    else:
        print("\n❌ Descarga fallida. Revisa los errores anteriores.")
        sys.exit(1)