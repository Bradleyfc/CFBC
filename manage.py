#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import warnings


def main():
    """Run administrative tasks."""
    # Silenciar warnings de Hugging Face y PyTorch
    warnings.filterwarnings("ignore", message=".*resume_download.*deprecated.*")
    warnings.filterwarnings("ignore", message=".*torch_dtype.*deprecated.*")
    warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub.*")
    
    # Configurar variables de entorno para reducir logs
    os.environ.setdefault('TRANSFORMERS_VERBOSITY', 'error')
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
