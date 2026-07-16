from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_documents', '0008_documentfolder_curso_id_original'),
    ]

    operations = [
        # CourseDocument indexes
        migrations.AddIndex(
            model_name='coursedocument',
            index=models.Index(fields=['folder'], name='idx_course_document_folder'),
        ),
        migrations.AddIndex(
            model_name='coursedocument',
            index=models.Index(fields=['-uploaded_at'], name='idx_course_document_uploaded_at_desc'),
        ),
        migrations.AddIndex(
            model_name='coursedocument',
            index=models.Index(fields=['uploaded_by'], name='idx_course_document_uploaded_by'),
        ),
        # DocumentAccess indexes
        migrations.AddIndex(
            model_name='documentaccess',
            index=models.Index(fields=['document'], name='idx_document_access_document'),
        ),
        migrations.AddIndex(
            model_name='documentaccess',
            index=models.Index(fields=['student'], name='idx_document_access_student'),
        ),
        migrations.AddIndex(
            model_name='documentaccess',
            index=models.Index(fields=['-accessed_at'], name='idx_document_access_accessed_at_desc'),
        ),
    ]