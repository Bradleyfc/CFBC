# Generated by Django 5.2.1 on 2025-07-12 14:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0008_remove_calificaciones_nota_1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='curso_academico',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='principal.cursoacademico', verbose_name='Curso Académico'),
        ),
    ]
