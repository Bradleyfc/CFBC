# Migracion corregida: las columnas ya existen en la BD (creadas manualmente).
# Solo actualizamos el estado interno de Django para que el modelo las reconozca.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datos_archivados", "0004_codigoverificacionreclamacion"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="datoarchivadodinamico",
                    name="combinado",
                    field=models.BooleanField(default=False, verbose_name="Combinado"),
                ),
                migrations.AddField(
                    model_name="datoarchivadodinamico",
                    name="fecha_combinacion",
                    field=models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Combinacion"),
                ),
                migrations.AddField(
                    model_name="datoarchivadodinamico",
                    name="registros_procesados",
                    field=models.IntegerField(default=0, verbose_name="Registros Procesados"),
                ),
            ],
        ),
    ]
