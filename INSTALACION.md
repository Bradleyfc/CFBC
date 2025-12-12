# 🚀 Guía de Instalación - Chatbot Semántico CFBC

## 🎯 Instalación Automática con Descarga de Modelos

### Opción 1: Instalación Inteligente (Recomendado)
```bash
python install_with_models.py
```
**Detecta automáticamente las dependencias y descarga los modelos**

### Opción 2: Monitor Automático
```bash
# Terminal 1: Iniciar monitor
python auto_install_models.py

# Terminal 2: Instalar dependencias
pip install -r requirements.txt
```
**El monitor detecta la instalación y descarga modelos automáticamente**

### Opción 3: Script Completo
```bash
python install_chatbot.py
```

### Opción 4: Usando Make
```bash
make install
```

### Opción 5: Usando setup.py
```bash
pip install -e .
```

## ¿Qué se instala automáticamente?

✅ **Dependencias Python** (requirements.txt)
✅ **Modelos de IA** (~800 MB) - **SE DESCARGAN AUTOMÁTICAMENTE**
- `paraphrase-multilingual-MiniLM-L12-v2` (~470 MB)
- `google/flan-t5-small` (~308 MB)
✅ **Migraciones de base de datos**
✅ **Datos iniciales** (6 categorías, 8 FAQs, 16 variaciones)
✅ **Índice semántico FAISS**
✅ **Archivos estáticos**

## 🤖 Descarga Automática de Modelos

Los modelos se descargan automáticamente en estos casos:

1. **Al instalar con scripts automáticos** (install_with_models.py)
2. **Al usar el monitor** (auto_install_models.py)
3. **Al iniciar Django** (primera vez que se usa el chatbot)
4. **Con setup.py** (pip install -e .)

**No necesitas hacer nada extra** - los modelos se descargan solos después de instalar las dependencias.

## Instalación Manual (Paso a Paso)

Si prefieres control total sobre el proceso:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Migraciones
python manage.py migrate

# 3. Datos iniciales
python manage.py loaddata chatbot/fixtures/categorias_faq.json
python manage.py loaddata chatbot/fixtures/faqs_iniciales.json
python manage.py loaddata chatbot/fixtures/faq_variaciones.json

# 4. Descargar modelos (esto toma tiempo)
python manage.py download_models --verbose

# 5. Construir índice
python manage.py rebuild_index

# 6. Archivos estáticos
python manage.py collectstatic --noinput
```

## Verificación de la Instalación

```bash
# Ejecutar servidor
python manage.py runserver

# Abrir en navegador
http://127.0.0.1:8000
```

El widget del chatbot debe aparecer automáticamente en la esquina inferior derecha.

## Comandos Útiles

```bash
# Ver estado del sistema
python manage.py shell -c "
from chatbot.services.semantic_search import SemanticSearchService
search = SemanticSearchService()
print('✅ Chatbot funcionando')
"

# Reconstruir índice si hay problemas
python manage.py rebuild_index --verbose

# Ver métricas
python manage.py export_metrics
```

## Solución de Problemas

### Error: "No module named 'sentence_transformers'"
```bash
pip install sentence-transformers transformers torch
```

### Error: "FAISS index not found"
```bash
python manage.py rebuild_index
```

### Modelos no se descargan
```bash
# Verificar conexión y espacio en disco
python manage.py download_models --verbose --force
```

### Limpiar instalación
```bash
make clean
# o manualmente:
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## Requisitos del Sistema

- **Python**: 3.8+
- **RAM**: 4GB mínimo (8GB recomendado)
- **Almacenamiento**: 2GB libres
- **Internet**: Para descargar modelos (solo primera vez)

## Ubicación de los Modelos

Los modelos se almacenan en:
- **Linux/Mac**: `~/.cache/huggingface/`
- **Windows**: `C:\Users\[usuario]\.cache\huggingface\`

## Próximos Pasos

1. ✅ Ejecutar `python manage.py runserver`
2. ✅ Abrir http://127.0.0.1:8000
3. ✅ Probar el chatbot en la esquina inferior derecha
4. ✅ Acceder al admin en `/admin/` para gestionar FAQs

---

**¿Problemas?** Consulta `chatbot/CONFIGURACION.md` para configuración avanzada.