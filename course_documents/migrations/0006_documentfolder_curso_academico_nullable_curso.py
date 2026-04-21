from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('course_documents', '0005_auditlog_curso_set_null'),
        ('principal', '0001_initial'),
    ]

    operations = [
        # 1. Hacer curso nullable (para que no se pierda la carpeta al eliminar el Curso)
        migrations.AlterField(
            model_name='documentfolder',
            name='curso',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='document_folders',
                to='principal.curso',
                verbose_name='Curso',
            ),
        ),
        # 2. Agregar FK a CursoAcademico
        migrations.AddField(
            model_name='documentfolder',
            name='curso_academico',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='document_folders',
                to='principal.cursoacademico',
                verbose_name='Curso Académico',
            ),
        ),
        # 3. Eliminar unique_together que ya no aplica con campos nullable
        migrations.AlterUniqueTogether(
            name='documentfolder',
            unique_together=set(),
        ),
    ]
