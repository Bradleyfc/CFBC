from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datos_archivados', '0006_alter_notaindividualarchivada_valor_decimal'),
    ]

    operations = [
        migrations.AddField(
            model_name='cursoarchivado',
            name='image',
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name='Ruta de imagen',
            ),
        ),
    ]
