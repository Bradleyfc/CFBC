# Design Document - Sistema de Gestión de Documentos para Cursos

## Overview

El sistema de gestión de documentos para cursos se integrará como una nueva funcionalidad dentro de la aplicación Django existente. Permitirá a los profesores organizar y compartir materiales educativos con sus estudiantes de manera estructurada, con notificaciones automáticas por email y control de acceso basado en roles y inscripciones.

La solución se implementará como una nueva aplicación Django llamada `course_documents` que se integrará con los modelos existentes de `Curso`, `Matriculas` y el sistema de usuarios.

## Architecture

### Componentes Principales

1. **Modelos de Datos**: Nuevos modelos para carpetas y documentos
2. **Vistas y URLs**: Dashboards específicos para profesores y estudiantes
3. **Sistema de Notificaciones**: Envío automático de emails
4. **Control de Acceso**: Middleware y decoradores para verificar permisos
5. **Interfaz de Usuario**: Templates integrados con el diseño existente

### Integración con Sistema Existente

- **Modelo Curso**: Relación directa con carpetas de documentos
- **Modelo Matriculas**: Control de acceso para estudiantes
- **Sistema de Usuarios**: Verificación de roles (profesor/estudiante)
- **ProfileView**: Extensión para mostrar botones de acceso a dashboards

## Components and Interfaces

### 1. Modelos de Datos

```python
# course_documents/models.py

class DocumentFolder(models.Model):
    """Carpeta para organizar documentos por curso"""
    curso = models.ForeignKey('principal.Curso', on_delete=models.CASCADE, related_name='document_folders')
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CourseDocument(models.Model):
    """Documento subido por el profesor"""
    folder = models.ForeignKey(DocumentFolder, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='course_documents/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField()

class DocumentAccess(models.Model):
    """Registro de acceso a documentos por estudiantes"""
    document = models.ForeignKey(CourseDocument, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)

class NewContentNotification(models.Model):
    """Seguimiento de contenido nuevo para mostrar indicadores"""
    curso = models.ForeignKey('principal.Curso', on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    has_new_content = models.BooleanField(default=False)
    last_checked = models.DateTimeField(auto_now=True)
```

### 2. Vistas y Controladores

```python
# course_documents/views.py

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Dashboard del profesor para gestionar documentos de un curso"""
    
class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Dashboard del estudiante para acceder a documentos de un curso"""
    
class CreateFolderView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vista para crear nuevas carpetas"""
    
class UploadDocumentView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vista para subir documentos"""
    
class DownloadDocumentView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vista para descargar documentos con control de acceso"""
```

### 3. Sistema de Notificaciones

```python
# course_documents/services.py

class NotificationService:
    """Servicio para envío de notificaciones por email"""
    
    @staticmethod
    def notify_new_document(document: CourseDocument):
        """Envía notificación a estudiantes inscritos cuando se sube un documento"""
        
    @staticmethod
    def update_content_indicators(curso: Curso):
        """Actualiza indicadores de contenido nuevo para estudiantes"""
```

### 4. Control de Acceso

```python
# course_documents/permissions.py

class TeacherPermissionMixin:
    """Mixin para verificar que el usuario es profesor del curso"""
    
class StudentPermissionMixin:
    """Mixin para verificar que el usuario está inscrito en el curso"""
```

## Data Models

### Relaciones entre Modelos

```
Curso (existente)
├── DocumentFolder (1:N)
│   └── CourseDocument (1:N)
│       └── DocumentAccess (1:N)
└── NewContentNotification (1:N)

User (existente)
├── DocumentFolder.created_by (1:N)
├── CourseDocument.uploaded_by (1:N)
├── DocumentAccess.student (1:N)
└── NewContentNotification.student (1:N)

Matriculas (existente)
└── [Usado para verificar inscripciones]
```

### Validaciones de Datos

- **DocumentFolder.name**: No vacío, máximo 255 caracteres, sin caracteres especiales peligrosos
- **CourseDocument.file**: Tipos de archivo permitidos (PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT, ZIP)
- **CourseDocument.file_size**: Máximo 50MB por archivo
- **Permisos**: Verificación de roles y inscripciones en cada operación

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Basándome en el análisis de prework, he identificado las siguientes propiedades de corrección consolidadas:

**Property 1: Dashboard access buttons match user courses**
*For any* user (profesor or estudiante), the number of dashboard access buttons displayed should equal the number of courses they are assigned to or enrolled in respectively
**Validates: Requirements 1.1, 4.1**

**Property 2: Dashboard navigation shows correct course content**
*For any* course dashboard access, clicking a course button should navigate to the dashboard showing content specific to that exact course
**Validates: Requirements 1.2, 4.2, 1.3, 4.3**

**Property 3: Multiple course buttons are uniquely identified**
*For any* user with multiple courses, each dashboard button should contain the unique name of its corresponding course
**Validates: Requirements 1.5, 4.5**

**Property 4: Folder name validation rejects invalid input**
*For any* folder creation attempt with empty names or only whitespace characters, the system should reject the creation and maintain the current state
**Validates: Requirements 2.3**

**Property 5: Folder creation with valid names succeeds**
*For any* valid folder name (non-empty, allowed characters), creating a folder should result in the folder appearing immediately in the dashboard
**Validates: Requirements 2.2, 2.4**

**Property 6: Character validation for folder names**
*For any* folder name containing disallowed special characters, the system should reject the creation
**Validates: Requirements 2.5**

**Property 7: Document-folder association integrity**
*For any* document upload to a selected folder, the document should be stored and associated with exactly that folder
**Validates: Requirements 3.2**

**Property 8: File type validation**
*For any* file upload with a disallowed file extension, the system should reject the upload and display an error message
**Validates: Requirements 3.4**

**Property 9: Folder content display completeness**
*For any* folder with documents, selecting the folder should display all documents contained within that folder
**Validates: Requirements 5.1**

**Property 10: Download access logging**
*For any* successful document download by a student, the system should create a corresponding access log entry
**Validates: Requirements 5.3**

**Property 11: Access control enforcement**
*For any* user attempting to access course documents, the system should verify appropriate role (profesor/estudiante) and course relationship (assigned/enrolled) before granting access
**Validates: Requirements 5.4, 8.1, 8.2, 8.3**

**Property 12: Email notification distribution**
*For any* new document upload, the system should send individual email notifications to all students enrolled in that course
**Validates: Requirements 6.1, 6.5**

**Property 13: Email content completeness**
*For any* notification email sent, the message should contain the course name, folder name, document name, and direct link to the course dashboard
**Validates: Requirements 6.2, 6.3**

**Property 14: New content indicator activation**
*For any* new document upload, the system should immediately activate the new content indicator for all enrolled students of that course
**Validates: Requirements 7.4**

**Property 15: New content indicator removal**
*For any* student accessing a course dashboard with new content, the new content indicator for that course should be removed for that student
**Validates: Requirements 7.2**

**Property 16: Default indicator state**
*For any* course without new content, the dashboard button should not display a new content indicator
**Validates: Requirements 7.3**

**Property 17: Unauthorized access logging**
*For any* unauthorized access attempt, the system should deny access and create an audit log entry of the attempt
**Validates: Requirements 8.4**

**Property 18: Comprehensive operation logging**
*For any* document-related operation (upload, download, folder creation), the system should create corresponding audit log entries
**Validates: Requirements 8.5**

## Error Handling

### File Upload Errors
- **File size limits**: Maximum 50MB per file with clear error messages
- **File type restrictions**: Only allow educational file formats (PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT, ZIP)
- **Storage failures**: Graceful handling with retry mechanisms and user notification

### Access Control Errors
- **Unauthorized access**: Clear error messages without revealing system information
- **Session timeouts**: Automatic redirect to login with context preservation
- **Permission changes**: Real-time validation of user permissions

### Email Notification Errors
- **SMTP failures**: Queue system for retry attempts with exponential backoff
- **Invalid email addresses**: Skip invalid addresses and log errors
- **Bulk email limits**: Batch processing to avoid rate limiting

### Database Errors
- **Connection failures**: Graceful degradation with user notification
- **Constraint violations**: Clear validation messages
- **Transaction rollbacks**: Ensure data consistency

## Testing Strategy

### Dual Testing Approach

The system will implement both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Testing**:
- Specific examples demonstrating correct behavior
- Integration points between components  
- Edge cases and error conditions
- File upload/download functionality
- Email notification system
- User interface interactions

**Property-Based Testing**:
- Universal properties that should hold across all inputs
- Access control verification across different user/course combinations
- File validation across various file types and sizes
- Email notification distribution patterns
- Indicator state management across multiple scenarios

**Property-Based Testing Configuration**:
- **Library**: Django Hypothesis for Python/Django integration
- **Iterations**: Minimum 100 iterations per property test
- **Test Tagging**: Each property-based test will include a comment with the format: `**Feature: gestion-documentos-cursos, Property {number}: {property_text}**`
- **Property Implementation**: Each correctness property will be implemented by a single property-based test

**Testing Requirements**:
- Each correctness property must be implemented by exactly one property-based test
- Property-based tests must run a minimum of 100 iterations
- All property-based tests must be tagged with explicit references to design document properties
- Unit tests and property tests are complementary - both must be included for comprehensive coverage

### Integration Testing
- End-to-end workflows for professor document management
- Student access and download processes
- Email notification delivery verification
- Cross-browser compatibility for file operations

### Performance Testing
- File upload performance with various file sizes
- Dashboard loading times with large numbers of documents
- Email notification system scalability
- Database query optimization verification