from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_add_indexes_noticia'),
    ]

    operations = [
        # Comentario indexes
        migrations.AddIndex(
            model_name='comentario',
            index=models.Index(fields=['noticia'], name='idx_comentario_noticia'),
        ),
        migrations.AddIndex(
            model_name='comentario',
            index=models.Index(fields=['autor'], name='idx_comentario_autor'),
        ),
        migrations.AddIndex(
            model_name='comentario',
            index=models.Index(fields=['-fecha_creacion'], name='idx_comentario_fecha_creacion_desc'),
        ),
        # Composite index for common query pattern
        migrations.AddIndex(
            model_name='comentario',
            index=models.Index(fields=['noticia', 'activo'], name='idx_comentario_noticia_activo'),
        ),
    ]