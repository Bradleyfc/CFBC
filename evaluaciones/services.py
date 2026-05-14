from decimal import Decimal
from typing import Optional

from .models import RespuestaIntento


class CalificacionService:

    @staticmethod
    def es_respuesta_correcta(respuesta: RespuestaIntento) -> Optional[bool]:
        """
        Determina si una respuesta individual es correcta.

        - seleccion_unica / verdadero_falso: True si la unica opcion
          seleccionada tiene es_correcta=True; False en cualquier otro caso.
        - opcion_multiple: True si el conjunto de opciones seleccionadas
          es exactamente igual al conjunto de opciones con es_correcta=True.
        - escritura_libre: None (no aplica calificacion automatica).
        """
        tipo = respuesta.pregunta.tipo

        if tipo == "escritura_libre":
            return None

        if tipo in ("seleccion_unica", "verdadero_falso"):
            opciones = respuesta.opciones_seleccionadas.all()
            if opciones.count() != 1:
                return False
            return opciones.first().es_correcta

        if tipo == "opcion_multiple":
            ids_seleccionados = set(
                respuesta.opciones_seleccionadas.values_list("id", flat=True)
            )
            ids_correctos = set(
                respuesta.pregunta.opciones
                .filter(es_correcta=True)
                .values_list("id", flat=True)
            )
            return ids_seleccionados == ids_correctos

        # Tipo desconocido: no se puede calificar automaticamente
        return None

    @staticmethod
    def calcular_calificacion_momentanea(intento):
        """
        Calcula el porcentaje de respuestas correctas.
        Para seleccion_unica y verdadero_falso: la opcion seleccionada
        debe ser correcta.
        Para opcion_multiple: todas las opciones correctas deben estar
        seleccionadas y ninguna incorrecta.
        Retorna un Decimal entre 0 y 10.
        """
        from .models import CalificacionEvaluacion

        respuestas = intento.respuestas.select_related("pregunta").all()
        total = respuestas.count()

        if total == 0:
            puntaje = Decimal("0.00")
        else:
            correctas = sum(
                1
                for r in respuestas
                if CalificacionService.es_respuesta_correcta(r) is True
            )
            puntaje = Decimal(str(round((correctas / total) * 10, 2)))

        calificacion, _ = CalificacionEvaluacion.objects.update_or_create(
            intento=intento,
            defaults={
                "puntaje": puntaje,
                "es_automatica": True,
            },
        )
        return calificacion
