"""
Management command: generar_metricas
=====================================
Genera (o actualiza) el registro diario de MetricaComunidad para una fecha dada.

Uso:
    # Genera métricas de HOY (uso normal en cron)
    python manage.py generar_metricas

    # Genera métricas de una fecha específica (backfill)
    python manage.py generar_metricas --fecha 2026-07-01

    # Rellena todos los días desde una fecha hasta hoy
    python manage.py generar_metricas --desde 2026-06-01

    # Fuerza regenerar aunque ya exista el registro del día
    python manage.py generar_metricas --forzar
"""

from datetime import date, timedelta, timezone as dt_timezone

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.utils import timezone

from blog.models import (
    Comentario,
    MetricaComunidad,
    ReporteComentario,
    SancionUsuario,
)


class Command(BaseCommand):
    help = "Genera el snapshot diario de métricas de comunidad del blog."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fecha",
            type=str,
            default=None,
            help="Fecha ISO (YYYY-MM-DD) para la que generar métricas. Por defecto: hoy.",
        )
        parser.add_argument(
            "--desde",
            type=str,
            default=None,
            help="Rellena métricas desde esta fecha ISO hasta hoy (backfill).",
        )
        parser.add_argument(
            "--forzar",
            action="store_true",
            default=False,
            help="Sobreescribe el registro si ya existe para esa fecha.",
        )

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_fecha(valor: str) -> date:
        try:
            return date.fromisoformat(valor)
        except ValueError:
            raise CommandError(f"Fecha inválida: '{valor}'. Usa formato YYYY-MM-DD.")

    @staticmethod
    def _rango_fechas(inicio: date, fin: date):
        """Genera todos los días entre inicio y fin (inclusive)."""
        actual = inicio
        while actual <= fin:
            yield actual
            actual += timedelta(days=1)

    # ── lógica principal ─────────────────────────────────────────────────

    def _generar_para_fecha(self, target: date, forzar: bool) -> bool:
        """
        Calcula y guarda las métricas para `target`.
        Retorna True si se creó/actualizó, False si se saltó.
        """
        if not forzar and MetricaComunidad.objects.filter(fecha=target).exists():
            self.stdout.write(
                self.style.WARNING(f"  [{target}] Ya existe. Usa --forzar para sobreescribir.")
            )
            return False

        # ── inicio y fin del día en UTC ──────────────────────────────────
        from datetime import datetime as _dt
        inicio_dia = timezone.make_aware(
            _dt(target.year, target.month, target.day, 0, 0, 0),
            timezone=dt_timezone.utc,
        )
        fin_dia = inicio_dia + timedelta(days=1)

        # ── métricas ─────────────────────────────────────────────────────

        # 1. Total de reportes de comentarios creados ese día
        total_reportes = ReporteComentario.objects.filter(
            fecha_reporte__gte=inicio_dia,
            fecha_reporte__lt=fin_dia,
        ).count()

        # 2. Total de comentarios activos creados ese día
        total_comentarios = Comentario.objects.filter(
            fecha_creacion__gte=inicio_dia,
            fecha_creacion__lt=fin_dia,
        ).count()

        # 3. Total de sanciones aplicadas ese día
        total_sanciones = SancionUsuario.objects.filter(
            fecha_inicio__gte=inicio_dia,
            fecha_inicio__lt=fin_dia,
        ).count()

        # 4. Usuario más activo: el que más comentarios publicó ese día
        usuario_mas_activo = None
        top = (
            Comentario.objects.filter(
                fecha_creacion__gte=inicio_dia,
                fecha_creacion__lt=fin_dia,
            )
            .values("autor")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )
        if top:
            try:
                usuario_mas_activo = User.objects.get(pk=top["autor"])
            except User.DoesNotExist:
                pass

        # 5. Pico de toxicidad: ratio reportes/comentarios escalado a 0.0–10.0
        #    Fórmula: (reportes / comentarios) * 10, capped en 10.0
        #    None si no hubo comentarios ese día.
        pico_toxicidad = None
        if total_comentarios > 0:
            pico_toxicidad = round(
                min((total_reportes / total_comentarios) * 10, 10.0), 2
            )

        # ── guardar ──────────────────────────────────────────────────────
        MetricaComunidad.objects.update_or_create(
            fecha=target,
            defaults={
                "total_reportes": total_reportes,
                "total_comentarios": total_comentarios,
                "total_sanciones": total_sanciones,
                "usuario_mas_activo": usuario_mas_activo,
                "pico_toxicidad": pico_toxicidad,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  [{target}] Generado — reportes: {total_reportes}, "
                f"comentarios: {total_comentarios}, sanciones: {total_sanciones}, "
                f"toxicidad: {pico_toxicidad if pico_toxicidad is not None else '—'}"
            )
        )
        return True

    # ── handle ───────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        forzar = options["forzar"]
        hoy = date.today()

        # Backfill: --desde FECHA hasta hoy
        if options["desde"]:
            inicio = self._parse_fecha(options["desde"])
            if inicio > hoy:
                raise CommandError("--desde no puede ser una fecha futura.")
            self.stdout.write(f"Backfill desde {inicio} hasta {hoy}...")
            creados = 0
            for d in self._rango_fechas(inicio, hoy):
                if self._generar_para_fecha(d, forzar):
                    creados += 1
            self.stdout.write(self.style.SUCCESS(f"\nTotal procesados: {creados}"))
            return

        # Fecha específica o hoy
        target = self._parse_fecha(options["fecha"]) if options["fecha"] else hoy
        self.stdout.write(f"Generando métricas para {target}...")
        self._generar_para_fecha(target, forzar)
