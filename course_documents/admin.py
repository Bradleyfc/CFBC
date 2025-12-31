from django.contrib import admin
from .models import DocumentFolder, CourseDocument, DocumentAccess, FolderAccess, NewContentNotification, AuditLog


@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'curso', 'created_by', 'created_at', 'document_count']
    list_filter = ['created_at', 'curso']
    search_fields = ['name', 'curso__name', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']

    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documentos'


@admin.register(CourseDocument)
class CourseDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'folder', 'uploaded_by', 'uploaded_at', 'file_size_display']
    list_filter = ['uploaded_at', 'folder__curso']
    search_fields = ['name', 'folder__name', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'file_size']

    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'Tamaño'


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ['document', 'student', 'accessed_at', 'ip_address']
    list_filter = ['accessed_at', 'document__folder__curso']
    search_fields = ['document__name', 'student__username']
    readonly_fields = ['accessed_at']


@admin.register(FolderAccess)
class FolderAccessAdmin(admin.ModelAdmin):
    list_display = ['student', 'folder', 'folder_curso', 'last_accessed', 'created_at']
    list_filter = ['last_accessed', 'created_at', 'folder__curso']
    search_fields = ['student__username', 'folder__name', 'folder__curso__name']
    readonly_fields = ['created_at', 'last_accessed']

    def folder_curso(self, obj):
        return obj.folder.curso.name
    folder_curso.short_description = 'Curso'


@admin.register(NewContentNotification)
class NewContentNotificationAdmin(admin.ModelAdmin):
    list_display = ['curso', 'student', 'has_new_content', 'last_checked']
    list_filter = ['has_new_content', 'last_checked', 'curso']
    search_fields = ['curso__name', 'student__username']
    readonly_fields = ['last_checked']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'curso', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp', 'curso']
    search_fields = ['user__username', 'details']
    readonly_fields = ['timestamp']