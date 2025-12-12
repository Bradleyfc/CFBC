#!/usr/bin/env python
"""
Setup script para el proyecto CFBC con descarga automática de modelos
"""

from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys
import os

class PostInstallCommand(install):
    """Comando personalizado para ejecutar después de la instalación"""
    
    def run(self):
        # Ejecutar instalación normal
        install.run(self)
        
        # Ejecutar hooks de post-instalación
        try:
            from chatbot.install_hooks import post_install_setup
            post_install_setup()
        except Exception as e:
            print(f"⚠️  Error en configuración post-instalación: {e}")
            print("💡 Puedes ejecutar manualmente: python chatbot/install_hooks.py")

# Leer requirements.txt
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='cfbc-chatbot',
    version='1.0.0',
    description='Centro de Formación Bíblica Católica - Sistema con Chatbot Semántico',
    packages=find_packages(),
    install_requires=read_requirements(),
    cmdclass={
        'install': PostInstallCommand,
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)