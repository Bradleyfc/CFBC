#!/usr/bin/env python3
"""
Script para reconstruir el índice FAISS con chunking mejorado
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.services.semantic_search import SemanticSearchService
from chatbot.services.text_chunker import TextChunker
from chatbot.models import FAQ, DocumentEmbedding
from chatbot.config import CHUNK_SIZE, CHUNK_OVERLAP, USE_MMR, SIMILARITY_THRESHOLD
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rebuild_index_with_improved_chunking():
    """
    Reconstruir el índice con chunking mejorado
    """
    print("🔄 Reconstruyendo índice con chunking mejorado...")
    print(f"   Configuración:")
    print(f"   - Tamaño de chunk: {CHUNK_SIZE} caracteres")
    print(f"   - Solapamiento: {CHUNK_OVERLAP} caracteres")
    print(f"   - MMR habilitado: {USE_MMR}")
    print(f"   - Umbral de similitud: {SIMILARITY_THRESHOLD}")
    
    # Inicializar servicios
    semantic_search = SemanticSearchService()
    text_chunker = TextChunker()
    
    # Limpiar índice existente
    semantic_search.clear_index()
    semantic_search.initialize_index()
    
    # Limpiar embeddings existentes en la base de datos
    print("\n🗑️  Limpiando embeddings existentes...")
    DocumentEmbedding.objects.all().delete()
    
    # Procesar FAQs
    print("\n📚 Procesando FAQs...")
    faqs = FAQ.objects.filter(activa=True)
    faq_chunks_created = 0
    
    for faq in faqs:
        try:
            # Crear chunks optimizados para FAQ
            chunks = text_chunker.chunk_faq(
                faq.pregunta,
                faq.respuesta,
                {
                    'content_type': 'chatbot.faq',
                    'object_id': faq.id,
                    'categoria': faq.categoria.nombre if faq.categoria else 'general',
                    'destacada': faq.destacada,
                    'prioridad': faq.prioridad
                }
            )
            
            # Indexar cada chunk
            for chunk in chunks:
                try:
                    # Generar embedding
                    embedding_vector = semantic_search.generate_embedding(chunk['text'])
                    
                    # Crear embedding en la base de datos
                    embedding_obj = DocumentEmbedding.objects.create(
                        content_type=faq.get_content_type(),
                        object_id=faq.id,
                        texto_indexado=chunk['text'],
                        categoria=chunk.get('categoria', 'general'),
                        chunk_index=chunk.get('chunk_index', 0),
                        chunk_type=chunk.get('chunk_type', 'combined')
                    )
                    
                    # Guardar embedding
                    embedding_obj.save_embedding(embedding_vector)
                    
                    # Indexar en FAISS
                    semantic_search.index_document(
                        embedding_obj.id,
                        chunk['text'],
                        {
                            'content_type': 'chatbot.faq',
                            'object_id': faq.id,
                            'categoria': chunk.get('categoria', 'general'),
                            'chunk_type': chunk.get('chunk_type', 'combined'),
                            'destacada': chunk.get('destacada', False),
                            'prioridad': chunk.get('prioridad', 0)
                        }
                    )
                    
                    faq_chunks_created += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando chunk de FAQ {faq.id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error procesando FAQ {faq.id}: {e}")
            continue
    
    print(f"   ✅ {faq_chunks_created} chunks de FAQs creados")
    
    total_faq_chunks = faq_chunks_created
    
    # Procesar otros contenidos (cursos, blog, footer)
    print("\n📖 Procesando otros contenidos...")
    
    from chatbot.services.content_indexer import ContentIndexerService
    content_indexer = ContentIndexerService()
    
    # Indexar cursos
    print("   📚 Indexando cursos...")
    course_chunks = content_indexer.index_courses()
    print(f"   ✅ {course_chunks} chunks de cursos creados")
    
    # Indexar blog
    print("   📰 Indexando blog...")
    blog_chunks = content_indexer.index_blog_posts()
    print(f"   ✅ {blog_chunks} chunks de blog creados")
    
    # Indexar footer
    print("   📞 Indexando información de contacto...")
    footer_chunks = content_indexer.index_footer_content()
    print(f"   ✅ {footer_chunks} chunks de contacto creados")
    
    # Indexar proceso de registro y login
    print("   🔐 Indexando proceso de registro y login...")
    auth_chunks = content_indexer.index_auth_process()
    print(f"   ✅ {auth_chunks} chunks de autenticación creados")
    
    # Indexar páginas de registro y login detalladas
    print("   📝 Indexando páginas de registro y login...")
    reg_login_chunks = content_indexer.index_registration_and_login_pages()
    print(f"   ✅ {reg_login_chunks} chunks de registro/login creados")
    
    total_content_chunks = course_chunks + blog_chunks + footer_chunks + auth_chunks + reg_login_chunks
    
    # Guardar índice
    print("\n💾 Guardando índice...")
    semantic_search.save_index()
    
    # Mostrar estadísticas
    stats = semantic_search.get_index_stats()
    print(f"\n📊 Estadísticas del nuevo índice:")
    print(f"   - Total de vectores: {stats['total_vectors']}")
    print(f"   - Dimensión: {stats['dimension']}")
    print(f"   - Metadatos: {stats['metadata_count']}")
    print(f"   - FAQs: {total_faq_chunks} chunks")
    print(f"   - Contenido web: {total_content_chunks} chunks")
    print(f"     • Cursos: {course_chunks}")
    print(f"     • Blog: {blog_chunks}")
    print(f"     • Contacto: {footer_chunks}")
    print(f"     • Autenticación: {auth_chunks}")
    print(f"     • Registro/Login: {reg_login_chunks}")
    
    print("\n🎉 Índice reconstruido exitosamente!")
    print("\n📋 Mejoras implementadas:")
    print("   • Chunking optimizado (150-300 caracteres)")
    print("   • Deduplicación automática")
    print("   • Max Marginal Relevance (MMR) para diversidad")
    print("   • Indexación completa del sitio web")
    print("   • Respuestas basadas en contenido real")
    print("   • Información detallada de registro y login")
    print("   • Guías paso a paso para inscripciones")
    
    return True

def test_improved_search():
    """
    Probar las mejoras de búsqueda
    """
    print("\n🔍 Probando búsquedas mejoradas...")
    
    semantic_search = SemanticSearchService()
    
    test_queries = [
        "¿Qué cursos están disponibles?",
        "¿Cuándo empiezan las inscripciones?",
        "¿Cómo me registro en el sitio?",
        "¿Cómo hago login?",
        "¿Hay cursos de idiomas?",
        "¿Dónde está ubicado el centro?",
        "¿Qué necesito para inscribirme?"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Consulta: {query}")
        
        try:
            results = semantic_search.search(query, top_k=3)
            
            print(f"   📊 Resultados: {len(results)}")
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                text = result.get('text', '')[:100]
                chunk_type = result.get('chunk_type', 'unknown')
                print(f"   {i}. Score: {score:.3f} | Tipo: {chunk_type} | Texto: {text}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Pruebas completadas!")

if __name__ == '__main__':
    try:
        success = rebuild_index_with_improved_chunking()
        if success:
            test_improved_search()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)