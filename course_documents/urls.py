from django.urls import path
from . import views

app_name = 'course_documents'

urlpatterns = [
    # Teacher dashboard URLs
    path('teacher/<int:curso_id>/', 
         views.TeacherDashboardView.as_view(), 
         name='teacher_dashboard'),
    
    path('teacher/<int:curso_id>/create-folder/', 
         views.CreateFolderView.as_view(), 
         name='create_folder'),
    
    path('teacher/<int:curso_id>/folder/<int:folder_id>/', 
         views.FolderDetailView.as_view(), 
         name='folder_detail'),
    
    path('teacher/<int:curso_id>/folder/<int:folder_id>/upload/', 
         views.UploadDocumentView.as_view(), 
         name='upload_document'),
    
    path('teacher/<int:curso_id>/folder/<int:folder_id>/delete/', 
         views.DeleteFolderView.as_view(), 
         name='delete_folder'),
    
    path('teacher/<int:curso_id>/document/<int:document_id>/delete/', 
         views.DeleteDocumentView.as_view(), 
         name='delete_document'),
    
    # Student dashboard URLs
    path('student/<int:curso_id>/', 
         views.StudentDashboardView.as_view(), 
         name='student_dashboard'),
    
    path('student/<int:curso_id>/folder/<int:folder_id>/', 
         views.StudentFolderDetailView.as_view(), 
         name='student_folder_detail'),
    
    path('student/<int:curso_id>/download/<int:document_id>/', 
         views.DownloadDocumentView.as_view(), 
         name='download_document'),
    
    path('student/<int:curso_id>/history/', 
         views.StudentDocumentHistoryView.as_view(), 
         name='student_history'),
]