from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('evaluaciones', '0006_add_todo_o_nada_to_pregunta'),
        ('principal', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluacion',
            name='semestre',
            field=models.ForeignKey(
                blank=True,
                help_text='Semestre al que pertenece esta evaluación. Se asigna automáticamente al crearla.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='evaluaciones',
                to='principal.semestrecurso',
                verbose_name='Semestre',
            ),
        ),
    ]
