#!/usr/bin/env python
"""
Optimized model downloader with progress tracking and resume capability
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Callable
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


class OptimizedModelDownloader:
    """Downloader optimizado para modelos de Hugging Face"""
    
    def __init__(self):
        self.session = requests.Session()
        # Configurar headers para mejor rendimiento
        self.session.headers.update({
            'User-Agent': 'CFBC-Chatbot/1.0',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
    
    def download_with_progress(
        self, 
        model_name: str, 
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """
        Descarga un modelo con barra de progreso y capacidad de reanudar
        
        Args:
            model_name: Nombre del modelo (ej: 'google/flan-t5-small')
            progress_callback: Función callback para progreso
            
        Returns:
            True si la descarga fue exitosa
        """
        
        try:
            logger.info(f"🚀 Iniciando descarga optimizada de {model_name}")
            
            # Usar huggingface_hub para descarga optimizada
            from huggingface_hub import snapshot_download
            from huggingface_hub.utils import disable_progress_bars, enable_progress_bars
            
            # Habilitar barras de progreso
            enable_progress_bars()
            
            start_time = time.time()
            
            # Descargar con opciones optimizadas
            cache_dir = snapshot_download(
                repo_id=model_name,
                cache_dir=None,  # Usar cache por defecto
                resume_download=True,  # Reanudar si se interrumpe
                local_files_only=False,
                use_auth_token=False,
                revision="main",
                allow_patterns=None,  # Descargar todos los archivos
                ignore_patterns=["*.msgpack", "*.h5"],  # Ignorar formatos no necesarios
                max_workers=4,  # Descargas paralelas
            )
            
            download_time = time.time() - start_time
            logger.info(f"✅ Modelo {model_name} descargado en {download_time:.1f}s")
            logger.info(f"📁 Ubicación: {cache_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error descargando {model_name}: {e}")
            return False
    
    def check_model_cached(self, model_name: str) -> bool:
        """
        Verifica si un modelo ya está en cache
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            True si el modelo está en cache
        """
        try:
            from huggingface_hub import try_to_load_from_cache
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            
            # Verificar tokenizer
            try:
                AutoTokenizer.from_pretrained(model_name, local_files_only=True)
                tokenizer_cached = True
            except:
                tokenizer_cached = False
            
            # Verificar modelo
            try:
                AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=True)
                model_cached = True
            except:
                model_cached = False
            
            return tokenizer_cached and model_cached
            
        except Exception as e:
            logger.debug(f"Error verificando cache para {model_name}: {e}")
            return False
    
    def get_model_size(self, model_name: str) -> Optional[int]:
        """
        Obtiene el tamaño aproximado de un modelo
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            Tamaño en bytes, o None si no se puede determinar
        """
        
        # Tamaños conocidos (aproximados)
        known_sizes = {
            'google/flan-t5-small': 308 * 1024 * 1024,  # ~308 MB
            'google/flan-t5-base': 990 * 1024 * 1024,   # ~990 MB
            't5-small': 242 * 1024 * 1024,              # ~242 MB
            'paraphrase-multilingual-MiniLM-L12-v2': 470 * 1024 * 1024,  # ~470 MB
        }
        
        return known_sizes.get(model_name)
    
    def download_model_smart(self, model_name: str) -> bool:
        """
        Descarga inteligente que verifica cache primero
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            True si el modelo está disponible (cached o descargado)
        """
        
        # Verificar si ya está en cache
        if self.check_model_cached(model_name):
            logger.info(f"✅ Modelo {model_name} ya está en cache")
            return True
        
        # Mostrar información de descarga
        size = self.get_model_size(model_name)
        if size:
            size_mb = size / (1024 * 1024)
            logger.info(f"📦 Descargando {model_name} (~{size_mb:.0f} MB)")
        
        # Descargar
        return self.download_with_progress(model_name)
    
    def cleanup_old_models(self, keep_models: list = None) -> None:
        """
        Limpia modelos antiguos del cache para liberar espacio
        
        Args:
            keep_models: Lista de modelos a mantener
        """
        try:
            from huggingface_hub import scan_cache_dir
            
            if keep_models is None:
                keep_models = [
                    'google/flan-t5-small',
                    'paraphrase-multilingual-MiniLM-L12-v2'
                ]
            
            cache_info = scan_cache_dir()
            
            for repo in cache_info.repos:
                if repo.repo_id not in keep_models:
                    logger.info(f"🗑️  Limpiando modelo antiguo: {repo.repo_id}")
                    # Aquí podrías implementar la limpieza si es necesario
            
        except Exception as e:
            logger.debug(f"Error en limpieza de cache: {e}")


# Instancia global del descargador
model_downloader = OptimizedModelDownloader()


def download_model_optimized(model_name: str) -> bool:
    """
    Función de conveniencia para descargar un modelo de forma optimizada
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        True si la descarga fue exitosa
    """
    return model_downloader.download_model_smart(model_name)


def is_model_cached(model_name: str) -> bool:
    """
    Función de conveniencia para verificar si un modelo está en cache
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        True si el modelo está en cache
    """
    return model_downloader.check_model_cached(model_name)