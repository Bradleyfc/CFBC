from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_documents', '0007_populate_curso_academico_en_carpetas'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentfolder',
            name='curso_id_original',
            field=models.IntegerField(
                blank=True,
                editable=False,
                null=True,
                verbose_name='ID original del curso (para restauración)',
            ),
        ),
        # Poblar curso_id_original con el valor actual de curso_id en las carpetas
        # que ya tienen curso asignado
        migrations.RunSQL(
            sql="""
                UPDATE course_documents_documentfolder
                SET curso_id_original = curso_id
                WHERE curso_id IS NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
