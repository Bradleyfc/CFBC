from django.db import migrations, models


def migrar_tipos_sancion(apps, schema_editor):
    """
    Convierte baneo_temporal y baneo_permanente → silencio_permanente.
    El tipo 'silencio' (temporal) se mantiene igual.
    """
    SancionUsuario = apps.get_model('blog', 'SancionUsuario')
    SancionUsuario.objects.filter(
        tipo_sancion__in=['baneo_temporal', 'baneo_permanente']
    ).update(tipo_sancion='silencio_permanente')


def revertir_tipos_sancion(apps, schema_editor):
    """Reversión: convierte silencio_permanente → baneo_permanente."""
    SancionUsuario = apps.get_model('blog', 'SancionUsuario')
    SancionUsuario.objects.filter(
        tipo_sancion='silencio_permanente'
    ).update(tipo_sancion='baneo_permanente')


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_noticia_notas_editor_alter_noticia_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sancionusuario',
            name='tipo_sancion',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('silencio', 'Silencio temporal'),
                    ('silencio_permanente', 'Silencio permanente'),
                ],
            ),
        ),
        migrations.RunPython(migrar_tipos_sancion, revertir_tipos_sancion),
    ]
