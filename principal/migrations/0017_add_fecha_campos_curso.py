# Generated manually

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0016_alter_notaindividual_valor'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='curso',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AlterModelOptions(
            name='curso',
            options={'ordering': ['-fecha_actualizacion', '-fecha_creacion'], 'verbose_name': 'Curso', 'verbose_name_plural': 'Cursos'},
        ),
    ]
