# Generated by Django 5.2.1 on 2025-07-24 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0011_formularioaplicacion_preguntaformulario_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opcionrespuesta',
            name='texto',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Texto de la opción'),
        ),
        migrations.AlterField(
            model_name='preguntaformulario',
            name='tipo',
            field=models.CharField(choices=[('seleccion_multiple', 'Selección Múltiple'), ('escritura_libre', 'Escritura Libre')], default='seleccion_multiple', max_length=20, verbose_name='Tipo de pregunta'),
        ),
    ]
