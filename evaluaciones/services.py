import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from .models import RespuestaIntento


class CalificacionService:

    @staticmethod
    def es_respuesta_correcta(respuesta: RespuestaIntento) -> Optional[bool]:
        """
        Determina si una respuesta individual es totalmente correcta.
        Para VF y opcion_multiple usa puntaje_parcial internamente,
        pero este método sigue devolviendo True/False para compatibilidad
        con el template de resultado.
        """
        tipo = respuesta.pregunta.tipo

        if tipo == "escritura_libre":
            return None

        if tipo == "seleccion_unica":
            opciones = respuesta.opciones_seleccionadas.all()
            if opciones.count() != 1:
                return False
            return opciones.first().es_correcta

        if tipo == "verdadero_falso":
            # Correcta solo si TODAS las afirmaciones están bien
            if not respuesta.texto_respuesta:
                return False
            try:
                vf_data = json.loads(respuesta.texto_respuesta)
            except (ValueError, TypeError):
                return False
            for opcion in respuesta.pregunta.opciones.all():
                respondio = vf_data.get(str(opcion.id), '')
                esperado = 'V' if opcion.es_correcta else 'F'
                if respondio != esperado:
                    return False
            return True

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

        return None

    @staticmethod
    def puntaje_parcial(respuesta: RespuestaIntento) -> Decimal:
        """
        Calcula el puntaje obtenido para una respuesta, permitiendo
        puntaje parcial en VF y opcion_multiple.

        - seleccion_unica: todo o nada (valor de la pregunta o 0).
        - verdadero_falso: valor_pregunta / num_afirmaciones por cada
          afirmación respondida correctamente.
        - opcion_multiple: valor_pregunta / num_opciones_correctas por
          cada opción correcta seleccionada (sin penalización por incorrectas
          adicionales, pero tampoco se suma por ellas).
        - escritura_libre: 0 (calificación manual).
        """
        tipo = respuesta.pregunta.tipo
        valor = Decimal(str(respuesta.pregunta.valor))

        if tipo == "escritura_libre" or valor == 0:
            return Decimal('0.00')

        if tipo == "seleccion_unica":
            opciones = respuesta.opciones_seleccionadas.all()
            if opciones.count() == 1 and opciones.first().es_correcta:
                return valor
            return Decimal('0.00')

        if tipo == "verdadero_falso":
            if not respuesta.texto_respuesta:
                return Decimal('0.00')
            try:
                vf_data = json.loads(respuesta.texto_respuesta)
            except (ValueError, TypeError):
                return Decimal('0.00')
            afirmaciones = list(respuesta.pregunta.opciones.all())
            num = len(afirmaciones)
            if num == 0:
                return Decimal('0.00')
            valor_por_afirmacion = (valor / Decimal(num)).quantize(
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            )
            correctas = sum(
                1 for op in afirmaciones
                if vf_data.get(str(op.id), '') == ('V' if op.es_correcta else 'F')
            )
            return (valor_por_afirmacion * correctas).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

        if tipo == "opcion_multiple":
            todas_opciones = list(respuesta.pregunta.opciones.all())
            num_total = len(todas_opciones)
            ids_correctos = {op.id for op in todas_opciones if op.es_correcta}
            num_correctas = len(ids_correctos)
            if num_correctas == 0:
                return Decimal('0.00')
            # Premio por cada correcta marcada: valor / num_correctas
            valor_por_correcta = (valor / Decimal(num_correctas)).quantize(
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            )
            # Penalización por cada incorrecta marcada: valor / total_opciones
            valor_por_incorrecta = (valor / Decimal(num_total)).quantize(
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            ) if num_total > 0 else Decimal('0.00')
            ids_seleccionados = set(
                respuesta.opciones_seleccionadas.values_list("id", flat=True)
            )
            acertadas = len(ids_correctos & ids_seleccionados)
            incorrectas = len(ids_seleccionados - ids_correctos)
            puntaje = (valor_por_correcta * acertadas) - (valor_por_incorrecta * incorrectas)
            return max(puntaje, Decimal('0.00')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

        return Decimal('0.00')

    @staticmethod
    def calcular_calificacion_momentanea(intento):
        """
        Suma el puntaje parcial de cada pregunta.
        VF y opción múltiple otorgan puntos proporcionales a las
        afirmaciones/opciones respondidas correctamente.
        """
        from .models import CalificacionEvaluacion

        respuestas = (
            intento.respuestas
            .select_related('pregunta')
            .prefetch_related('opciones_seleccionadas', 'pregunta__opciones')
            .all()
        )

        total_valor = sum(Decimal(str(r.pregunta.valor)) for r in respuestas)

        if total_valor > 0:
            puntaje = sum(
                CalificacionService.puntaje_parcial(r) for r in respuestas
            )
            puntaje = min(
                Decimal(str(puntaje)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                Decimal('10.00')
            )
        else:
            # Fallback: porcentaje igualitario si ninguna pregunta tiene valor
            total = respuestas.count()
            if total == 0:
                puntaje = Decimal('0.00')
            else:
                correctas = sum(
                    1 for r in respuestas
                    if CalificacionService.es_respuesta_correcta(r) is True
                )
                puntaje = Decimal(str(round((correctas / total) * 10, 2)))

        calificacion, _ = CalificacionEvaluacion.objects.update_or_create(
            intento=intento,
            defaults={
                'puntaje': puntaje,
                'es_automatica': True,
            },
        )
        return calificacion
