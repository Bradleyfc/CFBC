# Migración correctiva: agrega físicamente las columnas combinado, fecha_combinacion
# y registros_procesados a la tabla datos_archivados_datoarchivadodinamico.
#
# La migración 0005 usó SeparateDatabaseAndState con database_operations=[]
# por lo que las columnas se registraron en el estado de Django pero nunca
# se crearon en la base de datos real. Esta migración las crea físicamente
# usando SeparateDatabaseAndState en sentido inverso: sólo ejecuta en la BD,
# sin tocar el estado (que ya está correcto desde la migración 0005).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datos_archivados", "0011_asistenciaarchivada_semestre_archivado_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Estas operaciones se ejecutan en la base de datos real
            database_operations=[
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
            # Sin cambios en el estado (ya está correcto desde 0005)
            state_operations=[],
        ),
    ]
