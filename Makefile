# Makefile para el proyecto CFBC con Chatbot Semántico

.PHONY: install setup models migrate data index static test clean help

# Instalación completa
install: setup models data index static
	@echo "🎉 Instalación completa terminada"

# Configuración básica
setup:
	@echo "🔧 Instalando dependencias..."
	pip install -r requirements.txt
	@echo "✅ Dependencias instaladas"

# Descargar modelos de IA
models:
	@echo "🤖 Descargando modelos de IA (~800 MB)..."
	python manage.py download_models --verbose
	@echo "✅ Modelos descargados"

# Migraciones de base de datos
migrate:
	@echo "🗄️  Aplicando migraciones..."
	python manage.py migrate
	@echo "✅ Migraciones aplicadas"

# Cargar datos iniciales
data: migrate
	@echo "📊 Cargando datos iniciales..."
	python manage.py loaddata chatbot/fixtures/categorias_faq.json
	python manage.py loaddata chatbot/fixtures/faqs_iniciales.json
	python manage.py loaddata chatbot/fixtures/faq_variaciones.json
	@echo "✅ Datos iniciales cargados"

# Construir índice semántico
index:
	@echo "🔍 Construyendo índice semántico..."
	python manage.py rebuild_index
	@echo "✅ Índice construido"

# Recopilar archivos estáticos
static:
	@echo "📁 Recopilando archivos estáticos..."
	python manage.py collectstatic --noinput
	@echo "✅ Archivos estáticos listos"

# Ejecutar servidor de desarrollo
run:
	@echo "🚀 Iniciando servidor de desarrollo..."
	python manage.py runserver

# Ejecutar tests
test:
	@echo "🧪 Ejecutando tests..."
	python manage.py test chatbot

# Limpiar archivos temporales
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf chatbot_data/faiss_index/*
	@echo "✅ Limpieza completada"

# Reinstalar modelos
reinstall-models:
	@echo "🔄 Reinstalando modelos..."
	rm -rf ~/.cache/huggingface/transformers/
	python manage.py download_models --verbose --force
	@echo "✅ Modelos reinstalados"

# Mostrar ayuda
help:
	@echo "📖 Comandos disponibles:"
	@echo "  make install       - Instalación completa del sistema"
	@echo "  make setup         - Instalar solo dependencias Python"
	@echo "  make models        - Descargar solo modelos de IA"
	@echo "  make migrate       - Aplicar migraciones de BD"
	@echo "  make data          - Cargar datos iniciales"
	@echo "  make index         - Construir índice semántico"
	@echo "  make static        - Recopilar archivos estáticos"
	@echo "  make run           - Ejecutar servidor de desarrollo"
	@echo "  make test          - Ejecutar tests"
	@echo "  make clean         - Limpiar archivos temporales"
	@echo "  make reinstall-models - Reinstalar modelos de IA"
	@echo "  make help          - Mostrar esta ayuda"