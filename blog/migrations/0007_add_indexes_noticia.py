from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_update_tipo_sancion_choices'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='noticia',
            index=models.Index(fields=['estado', 'visibilidad'], name='idx_noticia_estado_visibilidad'),
        ),
        migrations.AddIndex(
            model_name='noticia',
            index=models.Index(fields=['-fecha_publicacion'], name='idx_noticia_fecha_publicacion_desc'),
        ),
        migrations.AddIndex(
            model_name='noticia',
            index=models.Index(fields=['categoria'], name='idx_noticia_categoria'),
        ),
        migrations.AddIndex(
            model_name='noticia',
            index=models.Index(fields=['autor'], name='idx_noticia_autor'),
        ),
        migrations.AddIndex(
            model_name='noticia',
            index=models.Index(fields=['destacada'], name='idx_noticia_destacada', condition=models.Q(destacada=True)),
        ),
        migrations.AddIndex(
            model_name='noticia',
            index=models.Index(fields=['estado', '-fecha_publicacion'], name='idx_noticia_estado_fecha_pub_desc'),
        ),
    ]