from django.contrib import admin
from .models import DocumentFolder, CourseDocument, AuditLog, DocumentAccess

@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'curso', 'get_curso_academico', 'created_at')
    list_filter = ('curso__curso_academico',)
    search_fields = ('name', 'curso__name')

    def get_curso_academico(self, obj):
        return obj.curso.curso_academico if obj.curso.curso_academico else '— sin asignar —'
    get_curso_academico.short_description = 'Curso Académico'

@admin.register(CourseDocument)
class CourseDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_folder', 'get_curso', 'get_curso_academico', 'uploaded_at', 'file_size')
    list_filter = ('folder__curso__curso_academico',)
    search_fields = ('name', 'folder__name', 'folder__curso__name')

    def get_folder(self, obj):
        return obj.folder.name
    get_folder.short_description = 'Carpeta'

    def get_curso(self, obj):
        return obj.folder.curso.name
    get_curso.short_description = 'Curso'

    def get_curso_academico(self, obj):
        ca = obj.folder.curso.curso_academico
        return ca.nombre if ca else '— sin asignar —'
    get_curso_academico.short_description = 'Curso Académico'
