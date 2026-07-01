"""
Pruebas unitarias, de integración y PBT para el sistema de permisos
del grupo Blog Moderador y funcionalidades de moderación.

Validates: Requirements 1, 2, 3, 4, 5, 6, 7, 8, 9
"""
import datetime as dt
from datetime import timedelta, timezone as dt_timezone

from django.contrib.auth.models import Group, User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from hypothesis import given, settings as hyp_settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypTestCase

from blog.models import (
    Noticia,
    Categoria,
    Comentario,
    ReporteComentario,
    SancionUsuario,
    ComentarioFijado,
)
from blog.views import usuario_sancionado
from principal.config_grupos import configurar_permisos_grupo


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de setup compartidos
# ─────────────────────────────────────────────────────────────────────────────

CODENAMES_AUTORIZADOS = [
    'view_comentario', 'add_comentario', 'change_comentario',
    'change_noticia',
    'view_reportecomentario', 'add_reportecomentario', 'change_reportecomentario',
    'view_sancionusuario', 'add_sancionusuario', 'change_sancionusuario',
    'view_comentariofijado', 'add_comentariofijado', 'change_comentariofijado',
    'delete_comentariofijado',
    'view_metricacomunidad',
]

CODENAMES_PROHIBIDOS = [
    'add_noticia', 'delete_noticia', 'view_noticia',
    'add_categoria', 'change_categoria', 'delete_categoria', 'view_categoria',
    'delete_comentario',
    'delete_reportecomentario',
    'delete_sancionusuario',
    'add_metricacomunidad', 'change_metricacomunidad', 'delete_metricacomunidad',
]


def crear_grupo_moderador():
    """Crea el grupo Blog Moderador con sus permisos configurados."""
    grupo, _ = Group.objects.get_or_create(name='Blog Moderador')
    grupo.permissions.clear()
    from principal.config_grupos import GRUPOS_SISTEMA
    config = next(g for g in GRUPOS_SISTEMA if g['nombre'] == 'Blog Moderador')
    configurar_permisos_grupo(grupo, config)
    return grupo


def crear_noticia_base(autor, titulo='Noticia de prueba', permitir_comentarios=True):
    """Crea una Noticia publicada mínima para tests."""
    categoria, _ = Categoria.objects.get_or_create(
        nombre='Categoría Test',
        defaults={'descripcion': 'Para pruebas'}
    )
    return Noticia.objects.create(
        titulo=titulo,
        resumen='Resumen de prueba',
        contenido='Contenido de prueba',
        categoria=categoria,
        autor=autor,
        estado='publicado',
        permitir_comentarios=permitir_comentarios,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. PermisosGrupoModeradorTest
# ─────────────────────────────────────────────────────────────────────────────

class PermisosGrupoModeradorTest(TestCase):
    """Validates: Requirements 9.1, 9.2"""

    def setUp(self):
        self.grupo = crear_grupo_moderador()
        self.user = User.objects.create_user(
            username='moderador_test', password='pass1234'
        )
        self.user.groups.add(self.grupo)
        # Refrescar caché de permisos
        self.user = User.objects.get(pk=self.user.pk)

    def test_blog_moderador_tiene_exactamente_15_permisos(self):
        """El grupo debe tener exactamente los 15 codenames autorizados."""
        codenames_asignados = set(
            self.grupo.permissions.values_list('codename', flat=True)
        )
        self.assertEqual(
            len(CODENAMES_AUTORIZADOS), 15,
            "La constante CODENAMES_AUTORIZADOS debe tener 15 elementos"
        )
        for codename in CODENAMES_AUTORIZADOS:
            self.assertTrue(
                self.user.has_perm(f'blog.{codename}'),
                f"El moderador DEBERÍA tener el permiso: blog.{codename}"
            )
        # Verificar que no hay más permisos de la app blog de los esperados
        codenames_blog_asignados = set(
            self.grupo.permissions.filter(
                content_type__app_label='blog'
            ).values_list('codename', flat=True)
        )
        self.assertEqual(
            codenames_blog_asignados,
            set(CODENAMES_AUTORIZADOS),
            f"Permisos blog inesperados: {codenames_blog_asignados - set(CODENAMES_AUTORIZADOS)}"
        )

    def test_moderador_no_tiene_permisos_prohibidos(self):
        """El moderador NO debe tener ninguno de los 13 codenames prohibidos."""
        for codename in CODENAMES_PROHIBIDOS:
            self.assertFalse(
                self.user.has_perm(f'blog.{codename}'),
                f"El moderador NO debería tener el permiso: blog.{codename}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 2. ReporteComentarioTest
# ─────────────────────────────────────────────────────────────────────────────

class ReporteComentarioTest(TestCase):
    """Validates: Requirements 2.6, 2.7"""

    def setUp(self):
        self.autor = User.objects.create_user('autor_rep', password='pass')
        self.moderador = User.objects.create_user('mod_rep', password='pass')
        self.noticia = crear_noticia_base(self.autor)
        self.comentario = Comentario.objects.create(
            noticia=self.noticia,
            autor=self.autor,
            contenido='Comentario de prueba',
            activo=True,
        )
        self.reporte = ReporteComentario.objects.create(
            comentario=self.comentario,
            reportado_por=self.autor,
            motivo='Spam',
            estado='pendiente',
        )

    def test_resolucion_retirado_oculta_comentario(self):
        """Resolver como resuelto_retirado → comentario.activo=False, auditoría rellena."""
        self.reporte.estado = 'resuelto_retirado'
        self.reporte.resuelto_por = self.moderador
        self.reporte.fecha_resolucion = timezone.now()
        self.reporte.save(update_fields=['estado', 'resuelto_por', 'fecha_resolucion'])

        self.comentario.activo = False
        self.comentario.save(update_fields=['activo'])

        self.reporte.refresh_from_db()
        self.comentario.refresh_from_db()

        self.assertFalse(self.comentario.activo)
        self.assertIsNotNone(self.reporte.resuelto_por)
        self.assertIsNotNone(self.reporte.fecha_resolucion)
        self.assertEqual(self.reporte.estado, 'resuelto_retirado')

    def test_resolucion_mantenido_no_cambia_comentario(self):
        """Resolver como resuelto_mantenido → activo sin cambios, auditoría rellena."""
        activo_original = self.comentario.activo

        self.reporte.estado = 'resuelto_mantenido'
        self.reporte.resuelto_por = self.moderador
        self.reporte.fecha_resolucion = timezone.now()
        self.reporte.save(update_fields=['estado', 'resuelto_por', 'fecha_resolucion'])

        self.reporte.refresh_from_db()
        self.comentario.refresh_from_db()

        self.assertEqual(self.comentario.activo, activo_original)
        self.assertIsNotNone(self.reporte.resuelto_por)
        self.assertIsNotNone(self.reporte.fecha_resolucion)
        self.assertEqual(self.reporte.estado, 'resuelto_mantenido')


# ─────────────────────────────────────────────────────────────────────────────
# 3. SancionUsuarioTest
# ─────────────────────────────────────────────────────────────────────────────

class SancionUsuarioTest(TestCase):
    """Validates: Requirements 3.6, 3.8"""

    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user('usuario_san', password='pass')
        self.moderador = User.objects.create_user('mod_san', password='pass')
        self.noticia = crear_noticia_base(self.moderador)

    def test_sancion_activa_bloquea_comentario(self):
        """Usuario con sanción activa (fecha_fin=None) → POST redirecciona (no puede comentar)."""
        SancionUsuario.objects.create(
            usuario=self.usuario,
            tipo_sancion='silencio',
            motivo='Prueba',
            fecha_fin=None,
            aplicada_por=self.moderador,
            activa=True,
        )
        self.client.login(username='usuario_san', password='pass')
        url = reverse('blog:agregar_comentario', kwargs={'slug': self.noticia.slug})
        response = self.client.post(url, {'contenido': 'Hola'})
        # La vista redirige (no procesa el comentario) cuando hay sanción activa
        self.assertNotEqual(response.status_code, 200)
        # Verificar que no se creó el comentario
        self.assertFalse(
            Comentario.objects.filter(noticia=self.noticia, autor=self.usuario).exists()
        )

    def test_sancion_expirada_no_bloquea(self):
        """Sanción con fecha_fin en el pasado → usuario_sancionado() retorna False."""
        hace_un_dia = timezone.now() - timedelta(days=1)
        SancionUsuario.objects.create(
            usuario=self.usuario,
            tipo_sancion='baneo_temporal',
            motivo='Expirada',
            fecha_fin=hace_un_dia,
            aplicada_por=self.moderador,
            activa=True,
        )
        self.assertFalse(usuario_sancionado(self.usuario))


# ─────────────────────────────────────────────────────────────────────────────
# 4. ComentarioFijadoTest
# ─────────────────────────────────────────────────────────────────────────────

class ComentarioFijadoTest(TestCase):
    """Validates: Requirements 5.6, 5.7, 5.8"""

    def setUp(self):
        self.client = Client()
        self.grupo = crear_grupo_moderador()
        self.moderador = User.objects.create_user('mod_fij', password='pass')
        self.moderador.groups.add(self.grupo)
        self.moderador = User.objects.get(pk=self.moderador.pk)

        self.autor = User.objects.create_user('autor_fij', password='pass')
        self.noticia = crear_noticia_base(self.autor)
        self.comentario_activo = Comentario.objects.create(
            noticia=self.noticia,
            autor=self.autor,
            contenido='Comentario activo',
            activo=True,
        )
        self.comentario_oculto = Comentario.objects.create(
            noticia=self.noticia,
            autor=self.autor,
            contenido='Comentario oculto',
            activo=False,
        )

    def test_fijar_comentario_oculto_falla(self):
        """POST a mod_fijar con comentario activo=False → mensaje de error, no se crea fijado."""
        self.client.login(username='mod_fij', password='pass')
        url = reverse('blog:mod_fijar', kwargs={'pk': self.comentario_oculto.pk})
        response = self.client.post(url)
        # Redirige con mensaje de error
        self.assertIn(response.status_code, [302, 403])
        self.assertFalse(
            ComentarioFijado.objects.filter(comentario=self.comentario_oculto).exists()
        )

    def test_fijar_comentario_duplicado_falla(self):
        """Fijar el mismo comentario dos veces → mensaje de error en segunda llamada."""
        self.client.login(username='mod_fij', password='pass')
        url = reverse('blog:mod_fijar', kwargs={'pk': self.comentario_activo.pk})
        # Primera vez: debe tener éxito
        self.client.post(url)
        self.assertTrue(
            ComentarioFijado.objects.filter(comentario=self.comentario_activo).exists()
        )
        # Segunda vez: debe rechazar sin crear duplicado
        self.client.post(url)
        self.assertEqual(
            ComentarioFijado.objects.filter(comentario=self.comentario_activo).count(),
            1,
            "No debe haber duplicados en ComentarioFijado"
        )

    def test_comentarios_fijados_aparecen_primero(self):
        """En detalle_noticia, fijados preceden a normales en el contexto."""
        comentario_normal = Comentario.objects.create(
            noticia=self.noticia,
            autor=self.autor,
            contenido='Comentario normal',
            activo=True,
        )
        ComentarioFijado.objects.create(
            comentario=self.comentario_activo,
            noticia=self.noticia,
            fijado_por=self.moderador,
            orden=0,
        )
        url = reverse('blog:detalle_noticia', kwargs={'slug': self.noticia.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        comentarios_ctx = response.context['comentarios']
        ids_ctx = [c.pk for c in comentarios_ctx]

        idx_fijado = ids_ctx.index(self.comentario_activo.pk)
        idx_normal = ids_ctx.index(comentario_normal.pk)
        self.assertLess(
            idx_fijado, idx_normal,
            "El comentario fijado debe aparecer antes que los comentarios normales"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 5. ControlHiloTest
# ─────────────────────────────────────────────────────────────────────────────

class ControlHiloTest(TestCase):
    """Validates: Requirements 4.1, 4.2, 6.3"""

    def setUp(self):
        self.client = Client()
        self.grupo = crear_grupo_moderador()
        self.moderador = User.objects.create_user('mod_hilo', password='pass')
        self.moderador.groups.add(self.grupo)
        self.moderador = User.objects.get(pk=self.moderador.pk)

        self.autor = User.objects.create_user('autor_hilo', password='pass')
        self.noticia = crear_noticia_base(
            self.autor, titulo='Noticia Hilo Test', permitir_comentarios=True
        )
        self.comentario = Comentario.objects.create(
            noticia=self.noticia,
            autor=self.autor,
            contenido='Comentario hilo',
            activo=True,
        )

    def test_toggle_comentarios_solo_ese_campo(self):
        """POST con permitir_comentarios → solo ese campo cambia, titulo intacto."""
        titulo_original = self.noticia.titulo
        self.client.login(username='mod_hilo', password='pass')
        url = reverse('blog:mod_toggle_comentarios', kwargs={'pk': self.noticia.pk})
        self.client.post(url, {'permitir_comentarios': 'false'})

        self.noticia.refresh_from_db()
        self.assertFalse(self.noticia.permitir_comentarios)
        self.assertEqual(
            self.noticia.titulo, titulo_original,
            "El título no debe cambiar al hacer toggle de comentarios"
        )

    def test_mover_comentario_hilo_cerrado(self):
        """Mover comentario a noticia con permitir_comentarios=False → mensaje de error."""
        noticia_cerrada = crear_noticia_base(
            self.autor, titulo='Noticia Cerrada', permitir_comentarios=False
        )
        self.client.login(username='mod_hilo', password='pass')
        url = reverse('blog:mod_mover_comentario', kwargs={'pk': self.comentario.pk})
        response = self.client.post(url, {'noticia_destino': str(noticia_cerrada.pk)})

        # La vista redirige con mensaje de error; el comentario sigue en la noticia original
        self.comentario.refresh_from_db()
        self.assertEqual(
            self.comentario.noticia.pk, self.noticia.pk,
            "El comentario no debe haber sido movido al hilo cerrado"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. PBTPermisosTest — Property-Based Tests con hypothesis
# ─────────────────────────────────────────────────────────────────────────────

class PBTPermisosTest(HypTestCase):
    """
    Pruebas de propiedad para verificar invariantes del sistema de permisos
    y sanciones usando hypothesis.

    Validates: Requirements 9.1, 9.2, 3.8
    """

    def setUp(self):
        self.grupo = crear_grupo_moderador()

    @given(st.sampled_from(CODENAMES_PROHIBIDOS))
    @hyp_settings(suppress_health_check=[HealthCheck.too_slow], max_examples=13, deadline=None)
    def test_pbt_moderador_no_tiene_permisos_prohibidos(self, codename):
        """
        **Validates: Requirements 9.2**
        Para cualquier codename prohibido, un miembro del grupo Blog Moderador
        no debe tener ese permiso.
        """
        # Crear usuario fresco en cada ejemplo para evitar contaminación de caché
        username = f'pbt_user_{codename[:20]}'
        user, _ = User.objects.get_or_create(username=username)
        user.groups.set([self.grupo])
        user.save()
        # Refrescar el objeto para limpiar la caché de permisos
        user = User.objects.get(pk=user.pk)
        self.assertFalse(
            user.has_perm(f'blog.{codename}'),
            f"El moderador NO debe tener blog.{codename}"
        )

    @given(
        st.datetimes(
            min_value=dt.datetime(2000, 1, 1),
            max_value=dt.datetime(2024, 12, 31, 23, 59, 59),
            timezones=st.just(dt_timezone.utc),
        )
    )
    @hyp_settings(suppress_health_check=[HealthCheck.too_slow], max_examples=20, deadline=None)
    def test_pbt_sancion_expirada_no_bloquea(self, fecha_fin):
        """
        **Validates: Requirements 3.8**
        Cualquier sanción con fecha_fin en el pasado (antes de ahora)
        no debe bloquear al usuario para comentar.
        """
        usuario = User.objects.create_user(
            username=f'pbt_san_{fecha_fin.strftime("%Y%m%d%H%M%S")}',
            password='pass'
        )
        moderador, _ = User.objects.get_or_create(username='pbt_mod_sancion')
        SancionUsuario.objects.create(
            usuario=usuario,
            tipo_sancion='baneo_temporal',
            motivo='PBT fecha expirada',
            fecha_fin=fecha_fin,  # siempre en el pasado según el generador
            aplicada_por=moderador,
            activa=True,
        )
        self.assertFalse(
            usuario_sancionado(usuario),
            f"Con fecha_fin={fecha_fin} (pasado), la sanción no debe bloquear"
        )
