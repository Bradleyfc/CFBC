# Iconos de Documentos Mejorados

## Resumen de Cambios

Se han implementado iconos específicos por tipo de archivo en la página de Documentos del Curso, reemplazando el icono genérico `description` que se usaba para todos los documentos.

## Nuevas Funcionalidades

### 1. Métodos Agregados al Modelo `CourseDocument`

#### `get_file_icon()`
Retorna el icono de Material Icons apropiado según la extensión del archivo:
- **PDF**: `picture_as_pdf`
- **Word (.doc, .docx)**: `description`
- **PowerPoint (.ppt, .pptx)**: `slideshow`
- **Excel (.xls, .xlsx)**: `table_chart`
- **Texto (.txt)**: `text_snippet`
- **Archivos comprimidos (.zip, .rar, .7z)**: `folder_zip`
- **Imágenes (.jpg, .jpeg, .png, .gif, .bmp)**: `image`
- **Por defecto**: `insert_drive_file`

#### `get_file_icon_color()`
Retorna la clase de color Tailwind CSS apropiada:
- **PDF**: `text-red-600`
- **Word**: `text-blue-600`
- **PowerPoint**: `text-orange-600`
- **Excel**: `text-green-600`
- **Texto**: `text-gray-600`
- **Archivos comprimidos**: `text-purple-600`
- **Imágenes**: `text-pink-600`
- **Por defecto**: `text-gray-600`

#### `get_file_icon_class()`
Retorna la clase CSS para el contenedor del icono con efectos glassmorphism:
- **PDF**: `document-icon-pdf`
- **Word**: `document-icon-word`
- **PowerPoint**: `document-icon-powerpoint`
- **Excel**: `document-icon-excel`
- **Texto**: `document-icon-text`
- **Archivos comprimidos**: `document-icon-archive`
- **Imágenes**: `document-icon-image`
- **Por defecto**: `document-icon-default`

#### `get_file_type_name()`
Retorna el nombre descriptivo del tipo de archivo para tooltips:
- **PDF**: "Documento PDF"
- **Word**: "Documento Word"
- **PowerPoint**: "Presentación PowerPoint"
- **Excel**: "Hoja de cálculo Excel"
- **Texto**: "Archivo de texto"
- **ZIP**: "Archivo comprimido ZIP"
- **Imágenes**: "Imagen JPEG/PNG/GIF/BMP"
- **Por defecto**: "Archivo"

### 2. Nuevo Archivo CSS: `static/css/document-icons.css`

Contiene estilos glassmorphism específicos para cada tipo de documento:

#### Características principales:
- **Efectos glassmorphism** con blur y transparencias
- **Colores específicos** por tipo de archivo
- **Animaciones suaves** de hover y entrada
- **Tooltips informativos** que muestran el tipo de archivo
- **Responsive design** que se adapta a dispositivos móviles
- **Accesibilidad** con soporte para focus y reduced motion

#### Clases CSS principales:
- `.document-icon-container`: Contenedor base con efectos glassmorphism
- `.document-icon-pdf`, `.document-icon-word`, etc.: Variantes por tipo
- `.document-icon-tooltip`: Tooltips informativos
- `.document-icon-new`: Efecto de pulso para documentos nuevos

### 3. Templates Actualizados

#### Templates modificados:
- `templates/course_documents/folder_detail.html`
- `templates/course_documents/student_dashboard.html`
- `templates/course_documents/student_folder_detail.html`
- `templates/course_documents/student_history.html`
- `templates/base.html` (agregado el nuevo CSS)

#### Cambios realizados:
- Reemplazado el icono genérico `description` por iconos específicos
- Agregados contenedores con efectos glassmorphism
- Implementados tooltips informativos
- Mejorada la presentación visual con colores específicos

## Beneficios de los Cambios

### 1. Mejor Experiencia de Usuario
- **Identificación rápida** del tipo de archivo
- **Interfaz más intuitiva** y profesional
- **Tooltips informativos** al pasar el mouse

### 2. Diseño Mejorado
- **Efectos glassmorphism** modernos y elegantes
- **Colores específicos** que facilitan la identificación
- **Animaciones suaves** que mejoran la interacción

### 3. Accesibilidad
- **Soporte para focus** con teclado
- **Respeto por preferencias** de reduced motion
- **Contraste adecuado** en todos los colores

### 4. Mantenibilidad
- **Código modular** y bien organizado
- **Fácil extensión** para nuevos tipos de archivo
- **Documentación clara** de todos los métodos

## Tipos de Archivo Soportados

| Extensión | Icono | Color | Descripción |
|-----------|-------|-------|-------------|
| .pdf | picture_as_pdf | Rojo | Documentos PDF |
| .doc, .docx | description | Azul | Documentos Word |
| .ppt, .pptx | slideshow | Naranja | Presentaciones PowerPoint |
| .xls, .xlsx | table_chart | Verde | Hojas de cálculo Excel |
| .txt | text_snippet | Gris | Archivos de texto |
| .zip, .rar, .7z | folder_zip | Púrpura | Archivos comprimidos |
| .jpg, .jpeg, .png, .gif, .bmp | image | Rosa | Imágenes |
| Otros | insert_drive_file | Gris | Archivos genéricos |

## Implementación Técnica

### Sin Cambios en Base de Datos
Los nuevos métodos son solo funciones de presentación que no requieren migraciones.

### Compatibilidad
- Compatible con todos los navegadores modernos
- Funciona con y sin JavaScript habilitado
- Responsive en todos los dispositivos

### Rendimiento
- CSS optimizado con efectos de hardware acceleration
- Iconos vectoriales de Material Icons (escalables)
- Animaciones suaves sin impacto en rendimiento

## Uso en Templates

```html
<!-- Icono con contenedor glassmorphism y tooltip -->
<div class="document-icon-container {{ document.get_file_icon_class }} document-icon-tooltip" 
     data-tooltip="{{ document.get_file_type_name }}">
    <span class="material-icons {{ document.get_file_icon_color }}">{{ document.get_file_icon }}</span>
</div>

<!-- Icono simple con color -->
<span class="material-icons {{ document.get_file_icon_color }}">{{ document.get_file_icon }}</span>
```

## Extensibilidad

Para agregar soporte a nuevos tipos de archivo, simplemente:

1. Agregar la extensión a los mapeos en los métodos del modelo
2. Agregar la clase CSS correspondiente en `document-icons.css`
3. Los templates se actualizarán automáticamente

## Conclusión

Esta implementación mejora significativamente la experiencia visual y funcional de la página de Documentos del Curso, proporcionando una interfaz más moderna, intuitiva y profesional para profesores y estudiantes.