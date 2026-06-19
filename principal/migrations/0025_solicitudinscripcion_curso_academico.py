from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0024_asistencia_semestre_calificaciones_semestre_and_more'),
    ]

    operations = [
        # 1. Agregar campo curso_academico (nullable) a SolicitudInscripcion
        migrations.AddField(
            model_name='solicitudinscripcion',
            name='curso_academico',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='principal.cursoacademico',
                verbose_name='Curso Académico',
            ),
        ),
        # 2. Eliminar el unique_together antiguo (estudiante, curso)
        migrations.AlterUniqueTogether(
            name='solicitudinscripcion',
            unique_together=set(),
        ),
        # 3. Establecer el nuevo unique_together (estudiante, curso, curso_academico)
        migrations.AlterUniqueTogether(
            name='solicitudinscripcion',
            unique_together={('estudiante', 'curso', 'curso_academico')},
        ),
    ]
