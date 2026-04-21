"""
Migración de datos: pobla curso_academico en DocumentFolder existentes
tomándolo del curso asociado.
"""
from django.db import migrations


def poblar_curso_academico(apps, schema_editor):
    DocumentFolder = apps.get_model('course_documents', 'DocumentFolder')
    for folder in DocumentFolder.objects.select_related('curso__curso_academico').filter(
        curso__isnull=False, curso_academico__isnull=True
    ):
        if folder.curso and folder.curso.curso_academico_id:
            folder.curso_academico_id = folder.curso.curso_academico_id
            folder.save(update_fields=['curso_academico'])


class Migration(migrations.Migration):

    dependencies = [
        ('course_documents', '0006_documentfolder_curso_academico_nullable_curso'),
    ]

    operations = [
        migrations.RunPython(poblar_curso_academico, migrations.RunPython.noop),
    ]
