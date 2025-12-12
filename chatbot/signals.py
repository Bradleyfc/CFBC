"""
Django signals for automatic content indexing
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import FAQ, FAQVariation, DocumentEmbedding
from .services.content_indexer import ContentIndexerService

logger = logging.getLogger(__name__)


# FAQ Signals

@receiver(post_save, sender=FAQ)
def index_faq_on_save(sender, instance, created, **kwargs):
    """
    Automatically index FAQ when it's created or updated
    """
    if not instance.activa:
        # If FAQ is inactive, remove from index
        remove_faq_from_index(instance)
        return
    
    try:
        indexer = ContentIndexerService()
        
        # Remove old embeddings for this FAQ
        content_type = ContentType.objects.get_for_model(FAQ)
        DocumentEmbedding.objects.filter(
            content_type=content_type,
            object_id=instance.id
        ).delete()
        
        # Extract and index texts
        texts = indexer.extract_text_from_faq(instance)
        categoria = indexer._determine_categoria('faq', instance)
        
        import pickle
        for text in texts:
            embedding = indexer.search_service.generate_embedding(text)
            DocumentEmbedding.objects.create(
                content_type=content_type,
                object_id=instance.id,
                texto_indexado=text,
                embedding_vector=pickle.dumps(embedding),
                categoria=categoria
            )
        
        # Rebuild FAISS index
        indexer.search_service.rebuild_index()
        
        action = "created" if created else "updated"
        logger.info(f"FAQ {instance.id} {action} and indexed")
    except Exception as e:
        logger.error(f"Error indexing FAQ {instance.id}: {e}")


@receiver(post_delete, sender=FAQ)
def remove_faq_on_delete(sender, instance, **kwargs):
    """
    Remove FAQ from index when deleted
    """
    remove_faq_from_index(instance)


def remove_faq_from_index(faq):
    """Helper function to remove FAQ from index"""
    try:
        content_type = ContentType.objects.get_for_model(FAQ)
        DocumentEmbedding.objects.filter(
            content_type=content_type,
            object_id=faq.id
        ).delete()
        
        # Rebuild FAISS index
        indexer = ContentIndexer()
        indexer.search_service.rebuild_index()
        
        logger.info(f"FAQ {faq.id} removed from index")
    except Exception as e:
        logger.error(f"Error removing FAQ {faq.id} from index: {e}")


# FAQVariation Signals

@receiver(post_save, sender=FAQVariation)
def index_faq_variation_on_save(sender, instance, created, **kwargs):
    """
    Re-index parent FAQ when variation is created or updated
    """
    try:
        # Trigger re-indexing of parent FAQ
        index_faq_on_save(FAQ, instance.faq, created=False)
        
        action = "created" if created else "updated"
        logger.info(f"FAQVariation {instance.id} {action}, parent FAQ re-indexed")
    except Exception as e:
        logger.error(f"Error indexing FAQVariation {instance.id}: {e}")


@receiver(post_delete, sender=FAQVariation)
def index_faq_variation_on_delete(sender, instance, **kwargs):
    """
    Re-index parent FAQ when variation is deleted
    """
    try:
        # Trigger re-indexing of parent FAQ
        index_faq_on_save(FAQ, instance.faq, created=False)
        
        logger.info(f"FAQVariation {instance.id} deleted, parent FAQ re-indexed")
    except Exception as e:
        logger.error(f"Error re-indexing after FAQVariation {instance.id} deletion: {e}")


# Curso Signals

@receiver(post_save, sender='principal.Curso')
def index_curso_on_save(sender, instance, created, **kwargs):
    """
    Automatically index Curso when it's created or updated
    """
    # Only index if status is relevant
    if instance.status not in ['I', 'IT', 'P']:
        # Remove from index if status changed to irrelevant
        remove_curso_from_index(instance)
        return
    
    try:
        indexer = ContentIndexer()
        
        # Extract text
        text = indexer.extract_text_from_curso(instance)
        categoria = indexer._determine_categoria('curso', instance)
        
        # Generate embedding
        import pickle
        embedding = indexer.search_service.generate_embedding(text)
        
        # Save to database
        content_type = ContentType.objects.get_for_model(sender)
        DocumentEmbedding.objects.update_or_create(
            content_type=content_type,
            object_id=instance.id,
            defaults={
                'texto_indexado': text,
                'embedding_vector': pickle.dumps(embedding),
                'categoria': categoria
            }
        )
        
        # Rebuild FAISS index
        indexer.search_service.rebuild_index()
        
        action = "created" if created else "updated"
        logger.info(f"Curso {instance.id} {action} and indexed")
    except Exception as e:
        logger.error(f"Error indexing Curso {instance.id}: {e}")


@receiver(post_delete, sender='principal.Curso')
def remove_curso_on_delete(sender, instance, **kwargs):
    """
    Remove Curso from index when deleted
    """
    remove_curso_from_index(instance)


def remove_curso_from_index(curso):
    """Helper function to remove Curso from index"""
    try:
        from principal.models import Curso
        content_type = ContentType.objects.get_for_model(Curso)
        DocumentEmbedding.objects.filter(
            content_type=content_type,
            object_id=curso.id
        ).delete()
        
        # Rebuild FAISS index
        indexer = ContentIndexer()
        indexer.search_service.rebuild_index()
        
        logger.info(f"Curso {curso.id} removed from index")
    except Exception as e:
        logger.error(f"Error removing Curso {curso.id} from index: {e}")


# Noticia Signals

@receiver(post_save, sender='blog.Noticia')
def index_noticia_on_save(sender, instance, created, **kwargs):
    """
    Automatically index Noticia when it's created or updated
    """
    # Only index if published
    if instance.estado != 'publicado':
        # Remove from index if not published
        remove_noticia_from_index(instance)
        return
    
    try:
        indexer = ContentIndexer()
        
        # Extract text
        text = indexer.extract_text_from_noticia(instance)
        categoria = indexer._determine_categoria('noticia', instance)
        
        # Generate embedding
        import pickle
        embedding = indexer.search_service.generate_embedding(text)
        
        # Save to database
        content_type = ContentType.objects.get_for_model(sender)
        DocumentEmbedding.objects.update_or_create(
            content_type=content_type,
            object_id=instance.id,
            defaults={
                'texto_indexado': text,
                'embedding_vector': pickle.dumps(embedding),
                'categoria': categoria
            }
        )
        
        # Rebuild FAISS index
        indexer.search_service.rebuild_index()
        
        action = "created" if created else "updated"
        logger.info(f"Noticia {instance.id} {action} and indexed")
    except Exception as e:
        logger.error(f"Error indexing Noticia {instance.id}: {e}")


@receiver(post_delete, sender='blog.Noticia')
def remove_noticia_on_delete(sender, instance, **kwargs):
    """
    Remove Noticia from index when deleted
    """
    remove_noticia_from_index(instance)


def remove_noticia_from_index(noticia):
    """Helper function to remove Noticia from index"""
    try:
        from blog.models import Noticia
        content_type = ContentType.objects.get_for_model(Noticia)
        DocumentEmbedding.objects.filter(
            content_type=content_type,
            object_id=noticia.id
        ).delete()
        
        # Rebuild FAISS index
        indexer = ContentIndexer()
        indexer.search_service.rebuild_index()
        
        logger.info(f"Noticia {noticia.id} removed from index")
    except Exception as e:
        logger.error(f"Error removing Noticia {noticia.id} from index: {e}")
