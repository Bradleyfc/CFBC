"""
Tests de propiedades para el Panel de Blog Autor (blog-autor-panel).
Cubre las 17 propiedades de corrección definidas en design.md.

Convenciones:
- HypothesisTestCase: tests con @given que necesitan rollback de BD por ejemplo.
- TestCase: tests sin Hypothesis o que no necesitan rollback por ejemplo.
- Todos los @given llevan @settings(deadline=None, max_examples=50).
- Estrategias de texto excluyen caracteres que PostgreSQL rechaza (NUL, surrogates).
- Para leer contexto de respuesta se usa self.client (no RequestFactory).
- Para tests que solo verifican cambios en BD se puede usar RequestFactory.
"""
import uuid
from unittest.mock import MagicMock

from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from django.utils import timezone

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from blog.forms import (
    AutorNoticiaForm, EditorRevisionForm,
    validar_imagen_autor,
    EXTENSIONES_VALIDAS, MIMES_VALIDOS, LIMITE_BYTES,
)
from blog.models import Categoria, Comentario, Noticia
from blog.views import (
    es_autor,
    panel_autores,
    mis_noticias_autor,
    crear_noticia_autor,
    editar_noticia_autor,
    eliminar_noticia_autor,
    enviar_revision,
    bandeja_revision,
    revisar_noticia,
    panel_editores,
)

# Configuración Hypothesis: sin deadline (BD lenta en tests), sin health check de too_slow.
_pbt_settings = dict(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)

# ── Estrategias de texto seguro para PostgreSQL ───────────────────────────
# Excluye surrogados (Cs) y el carácter NUL (\x00) que PostgreSQL rechaza.
_safe_alphabet = st.characters(
    blacklist_categories=('Cs',),
    blacklist_characters='\x00',
)
safe_text = st.text(alphabet=_safe_alphabet, min_size=0, max_size=500)
safe_text_min10 = st.text(alphabet=_safe_alphabet, min_size=10, max_size=500).filter(
    lambda t: len(t.strip()) >= 10
)
safe_text_short = st.text(alphabet=_safe_alphabet, max_size=9).filter(
    lambda t: len(t.strip()) < 10
)

# ── Helpers / Factories ────────────────────────────────────────────────────

def make_grupo_autor():
    grupo, _ = Group.objects.get_or_create(name='Blog Autor')
    return grupo


def make_grupo_editor():
    grupo, _ = Group.objects.get_or_create(name='Editor')
    return grupo


def make_user(grupo=None, is_staff=False, is_superuser=False):
    username = 'u_' + uuid.uuid4().hex[:20]
    user = User.objects.create_user(username=username, password='pass')
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.save()
    if grupo:
        user.groups.add(grupo)
    return user


def make_categoria():
    return Categoria.objects.create(nombre='Cat_' + uuid.uuid4().hex[:8])


def make_noticia(autor, estado='borrador', categoria=None):
    cat = categoria or make_categoria()
    return Noticia.objects.create(
        titulo='Noticia_' + uuid.uuid4().hex[:8],
        resumen='Resumen de prueba',
        contenido='Contenido de prueba',
        categoria=cat,
        autor=autor,
        estado=estado,
    )


def make_fake_image(name='img.jpg', content_type='image/jpeg', size=1024):
    """Crea un objeto similar a InMemoryUploadedFile para tests de validación."""
    img = MagicMock()
    img.name = name
    img.content_type = content_type
    img.size = size
    return img


def _make_request(factory, method, path, user, data=None):
    """Crea una request con sesión y mensajes configurados (para RequestFactory)."""
    if method == 'POST':
        request = factory.post(path, data or {})
    else:
        request = factory.get(path)
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


# ── Property 1: Control de acceso — función es_autor ──────────────────────

class TestEsAutorProperty(HypothesisTestCase):
    """
    Property 1 — es_autor retorna True ↔ autenticado AND (en_grupo OR staff OR superuser).
    Validates: Requirements 1.1
    """

    @given(st.booleans(), st.booleans(), st.booleans())
    @settings(**_pbt_settings)
    def test_es_autor_retorna_true_para_grupo_autor(self, en_grupo, is_staff, is_superuser):
        """Property 1: es_autor(user) == en_grupo OR is_staff OR is_superuser."""
        grupo = make_grupo_autor() if en_grupo else None
        user = make_user(grupo=grupo, is_staff=is_staff, is_superuser=is_superuser)
        expected = en_grupo or is_staff or is_superuser
        self.assertEqual(es_autor(user), expected)

    def test_es_autor_false_sin_privilegios(self):
        user = make_user()
        self.assertFalse(es_autor(user))

    def test_es_autor_true_solo_grupo(self):
        user = make_user(grupo=make_grupo_autor())
        self.assertTrue(es_autor(user))

    def test_es_autor_true_solo_staff(self):
        user = make_user(is_staff=True)
        self.assertTrue(es_autor(user))

    def test_es_autor_true_solo_superuser(self):
        user = make_user(is_superuser=True)
        self.assertTrue(es_autor(user))


# ── Property 2: Aislamiento de noticias por autor ─────────────────────────

class TestAislamientoNoticias(HypothesisTestCase):
    """
    Property 2 — mis_noticias_autor solo retorna noticias del usuario autenticado.
    Validates: Requirements 2.1, 7.5
    """

    @given(
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5),
    )
    @settings(**_pbt_settings)
    def test_mis_noticias_solo_retorna_propias(self, n_propias, n_ajenas):
        """Para cualquier (n_propias, n_ajenas), page_obj solo contiene noticias propias."""
        grupo = make_grupo_autor()
        autor_a = make_user(grupo=grupo)
        autor_b = make_user(grupo=grupo)

        for _ in range(n_propias):
            make_noticia(autor_a)
        for _ in range(n_ajenas):
            make_noticia(autor_b)

        self.client.force_login(autor_a)
        response = self.client.get('/noticias/autores/mis-noticias/')
        self.assertEqual(response.status_code, 200)

        ids_propios = set(
            Noticia.objects.filter(autor=autor_a).values_list('id', flat=True)
        )
        for noticia in response.context['page_obj']:
            self.assertIn(noticia.id, ids_propios,
                          "page_obj contiene una noticia de otro autor")


# ── Property 3: Creación siempre genera borrador del autor ────────────────

class TestCreacionSiempreBorrador(HypothesisTestCase):
    """
    Property 3 — POST a crear_noticia_autor siempre crea noticia con
    estado='borrador' y autor=request.user.
    Validates: Requirements 2.2
    """

    @given(st.sampled_from(['borrador', 'publicado', 'pendiente_revision', 'archivado']))
    @settings(**_pbt_settings)
    def test_creacion_fuerza_estado_borrador_y_autor(self, estado_en_post):
        """POST con cualquier estado → noticia guardada con estado='borrador'."""
        grupo = make_grupo_autor()
        autor = make_user(grupo=grupo)
        cat = make_categoria()

        self.client.force_login(autor)
        data = {
            'titulo': 'Titulo_' + uuid.uuid4().hex[:8],
            'resumen': 'Resumen de prueba para creacion',
            'contenido': 'Contenido suficiente de prueba',
            'categoria': cat.pk,
            'estado': estado_en_post,
            'fecha_publicacion': '2025-01-01T12:00',
        }
        response = self.client.post('/noticias/autores/crear/', data)
        # Redirect exitoso (302) indica que el form fue válido y la noticia creada
        self.assertEqual(response.status_code, 302,
                         f"El form no fue válido (status {response.status_code})")

        noticia = Noticia.objects.filter(autor=autor).order_by('-fecha_creacion').first()
        self.assertIsNotNone(noticia, "No se creó ninguna noticia")
        self.assertEqual(noticia.estado, 'borrador',
                         f"Esperaba estado='borrador', se guardó: '{noticia.estado}'")
        self.assertEqual(noticia.autor, autor)


# ── Property 4: Ownership — protección de edición y eliminación ───────────

class TestOwnershipProteccion(TestCase):
    """
    Property 4 — Editar o eliminar noticia ajena es rechazado sin modificar BD.
    Validates: Requirements 2.3, 2.4
    """

    def test_editar_noticia_ajena_es_rechazado(self):
        """Autor A no puede editar noticia de Autor B."""
        factory = RequestFactory()
        grupo = make_grupo_autor()
        autor_a = make_user(grupo=grupo)
        autor_b = make_user(grupo=grupo)
        noticia = make_noticia(autor_b, estado='borrador')
        titulo_original = noticia.titulo

        data = {
            'titulo': 'Titulo modificado',
            'resumen': 'Nuevo resumen modificado',
            'contenido': 'Nuevo contenido modificado',
            'categoria': noticia.categoria.pk,
            'fecha_publicacion': '2025-01-01T12:00',
        }
        request = _make_request(factory, 'POST', f'/noticias/autores/editar/{noticia.pk}/',
                                 autor_a, data)
        editar_noticia_autor(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertEqual(noticia.titulo, titulo_original,
                         "La noticia fue modificada por un autor no propietario")

    def test_eliminar_noticia_ajena_es_rechazado(self):
        """Autor A no puede eliminar noticia de Autor B."""
        factory = RequestFactory()
        grupo = make_grupo_autor()
        autor_a = make_user(grupo=grupo)
        autor_b = make_user(grupo=grupo)
        noticia = make_noticia(autor_b, estado='borrador')
        pk = noticia.pk

        request = _make_request(factory, 'POST', f'/noticias/autores/eliminar/{pk}/',
                                 autor_a, {})
        eliminar_noticia_autor(request, pk=pk)

        self.assertTrue(Noticia.objects.filter(pk=pk).exists(),
                        "La noticia fue eliminada por un autor no propietario")


# ── Property 5: Inmutabilidad de noticias en estados no-borrador ──────────

class TestInmutabilidadEstadosNoBorrador(HypothesisTestCase):
    """
    Property 5 — POST de edición rechazado cuando noticia NO está en borrador.
    Validates: Requirements 2.5, 2.6, 3.6
    """

    @given(st.sampled_from(['pendiente_revision', 'publicado']))
    @settings(**_pbt_settings)
    def test_post_edicion_rechazado_en_estado_no_borrador(self, estado):
        """Noticia en pendiente/publicado → POST de edición no modifica el contenido."""
        factory = RequestFactory()
        grupo = make_grupo_autor()
        autor = make_user(grupo=grupo)
        noticia = make_noticia(autor, estado=estado)
        contenido_original = noticia.contenido
        titulo_original = noticia.titulo

        data = {
            'titulo': 'Nuevo titulo modificado',
            'resumen': 'Nuevo resumen modificado',
            'contenido': 'Nuevo contenido modificado',
            'categoria': noticia.categoria.pk,
            'fecha_publicacion': '2025-01-01T12:00',
        }
        request = _make_request(factory, 'POST', f'/noticias/autores/editar/{noticia.pk}/',
                                 autor, data)
        editar_noticia_autor(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertEqual(noticia.contenido, contenido_original,
                         f"El contenido fue modificado en estado {estado}")
        self.assertEqual(noticia.titulo, titulo_original,
                         f"El título fue modificado en estado {estado}")


# ── Property 6: Edición de borrador preserva estado borrador ─────────────

class TestEdicionPreservaBorrador(TestCase):
    """
    Property 6 — POST de edición válido sobre borrador propio → estado sigue 'borrador'.
    Validates: Requirements 2.7
    """

    def test_edicion_mantiene_estado_borrador(self):
        """Editar un borrador propio no cambia el estado."""
        factory = RequestFactory()
        grupo = make_grupo_autor()
        autor = make_user(grupo=grupo)
        noticia = make_noticia(autor, estado='borrador')

        data = {
            'titulo': 'Titulo actualizado ok',
            'resumen': 'Resumen actualizado ok',
            'contenido': 'Contenido actualizado ok',
            'categoria': noticia.categoria.pk,
            'fecha_publicacion': '2025-01-01T12:00',
        }
        request = _make_request(factory, 'POST', f'/noticias/autores/editar/{noticia.pk}/',
                                 autor, data)
        editar_noticia_autor(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertEqual(noticia.estado, 'borrador',
                         f"El estado cambió de borrador a {noticia.estado}")


# ── Property 7: Validación de imagen (example-based) ─────────────────────

class TestValidacionImagen(TestCase):
    """
    Property 7 — validar_imagen_autor rechaza extensión/MIME/tamaño inválidos.
    Validates: Requirements 3.1, 3.2
    """

    def test_extension_invalida_lanza_error(self):
        img = make_fake_image(name='archivo.exe', content_type='image/jpeg', size=1024)
        with self.assertRaises(ValidationError):
            validar_imagen_autor(img)

    def test_mime_invalido_lanza_error(self):
        img = make_fake_image(name='foto.jpg', content_type='application/octet-stream', size=1024)
        with self.assertRaises(ValidationError):
            validar_imagen_autor(img)

    def test_tamano_excesivo_lanza_error(self):
        img = make_fake_image(name='grande.jpg', content_type='image/jpeg',
                              size=LIMITE_BYTES + 1)
        with self.assertRaises(ValidationError):
            validar_imagen_autor(img)

    def test_imagen_valida_no_lanza_error(self):
        img = make_fake_image(name='foto.png', content_type='image/png', size=LIMITE_BYTES - 1)
        try:
            validar_imagen_autor(img)
        except ValidationError:
            self.fail("validar_imagen_autor lanzó ValidationError con imagen válida")

    def test_gif_valido(self):
        validar_imagen_autor(make_fake_image(name='a.gif', content_type='image/gif', size=512))

    def test_webp_valido(self):
        validar_imagen_autor(make_fake_image(name='a.webp', content_type='image/webp', size=512))

    def test_tamano_exactamente_limite_es_valido(self):
        validar_imagen_autor(make_fake_image(name='a.jpg', content_type='image/jpeg',
                                             size=LIMITE_BYTES))


# ── Property 7 (PBT): extensiones inválidas siempre fallan ───────────────

class TestValidacionImagenHypothesis(HypothesisTestCase):
    """
    Property 7 (PBT) — Cualquier extensión fuera del conjunto válido es rechazada.
    Validates: Requirements 3.1, 3.2
    """

    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=('Ll', 'Lu', 'Nd'),
                blacklist_characters='\x00',
            ),
            min_size=1,
            max_size=10,
        ).filter(lambda x: x.lower() not in EXTENSIONES_VALIDAS)
    )
    @settings(**_pbt_settings)
    def test_extension_invalida_siempre_falla(self, ext):
        """Cualquier extensión no en el conjunto válido → ValidationError."""
        img = make_fake_image(name=f'archivo.{ext}', content_type='image/jpeg', size=1024)
        with self.assertRaises(ValidationError):
            validar_imagen_autor(img)


# ── Properties 9 & 10: Transición de estados ─────────────────────────────

class TestTransicionEstados(TestCase):
    """
    Property 9 — enviar_revision cambia estado borrador → pendiente_revision.
    Property 10 — Re-envío de noticia ya en pendiente_revision no cambia estado.
    Validates: Requirements 4.1, 4.5
    """

    def test_enviar_revision_cambia_estado(self):
        """Property 9: borrador → enviar_revision → estado=pendiente_revision en BD."""
        factory = RequestFactory()
        grupo = make_grupo_autor()
        autor = make_user(grupo=grupo)
        noticia = make_noticia(autor, estado='borrador')

        request = _make_request(factory, 'POST',
                                 f'/noticias/autores/enviar-revision/{noticia.pk}/',
                                 autor, {})
        enviar_revision(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertEqual(noticia.estado, 'pendiente_revision')

    def test_enviar_revision_idempotencia(self):
        """Property 10: noticia ya en pendiente_revision → re-envío no cambia estado."""
        factory = RequestFactory()
        grupo = make_grupo_autor()
        autor = make_user(grupo=grupo)
        noticia = make_noticia(autor, estado='pendiente_revision')

        request = _make_request(factory, 'POST',
                                 f'/noticias/autores/enviar-revision/{noticia.pk}/',
                                 autor, {})
        enviar_revision(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertEqual(noticia.estado, 'pendiente_revision',
                         "El estado cambió al re-enviar una noticia ya pendiente")


# ── Property 11: Contador pendientes en contexto del editor ──────────────

class TestContadorPendientes(HypothesisTestCase):
    """
    Property 11 — pendientes_count en contexto de panel_editores == N pendientes.
    Validates: Requirements 4.4, 5.7
    """

    @given(st.integers(min_value=0, max_value=10))
    @settings(**_pbt_settings)
    def test_pendientes_count_en_contexto_editor(self, n_pendientes):
        """pendientes_count refleja exactamente las noticias en pendiente_revision."""
        grupo_editor = make_grupo_editor()
        editor = make_user(grupo=grupo_editor)
        autor = make_user(grupo=make_grupo_autor())

        for _ in range(n_pendientes):
            make_noticia(autor, estado='pendiente_revision')
        # Noticias en otros estados (no deben sumarse)
        make_noticia(autor, estado='borrador')
        make_noticia(autor, estado='publicado')

        self.client.force_login(editor)
        response = self.client.get('/noticias/editores/')
        self.assertEqual(response.status_code, 200)

        count_en_contexto = response.context['pendientes_count']
        count_en_bd = Noticia.objects.filter(estado='pendiente_revision').count()
        self.assertEqual(count_en_contexto, count_en_bd,
                         "pendientes_count en contexto difiere del conteo en BD")


# ── Property 12: Validación de notas del editor ───────────────────────────

class TestValidacionNotasEditor(HypothesisTestCase):
    """
    Property 12 — notas_editor con strip() < 10 chars → devolución rechazada;
                  notas_editor con strip() >= 10 → devolución aceptada.
    Validates: Requirements 4.6, 5.6
    """

    @given(safe_text_short)
    @settings(**_pbt_settings)
    def test_devolver_rechaza_notas_cortas(self, notas_cortas):
        """Notas con < 10 chars (strip) → noticia permanece en pendiente_revision."""
        factory = RequestFactory()
        editor = make_user(grupo=make_grupo_editor())
        autor = make_user(grupo=make_grupo_autor())
        noticia = make_noticia(autor, estado='pendiente_revision')

        data = {'accion': 'devolver', 'notas_editor': notas_cortas}
        request = _make_request(factory, 'POST',
                                 f'/noticias/editores/revisar/{noticia.pk}/', editor, data)
        revisar_noticia(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertNotEqual(noticia.estado, 'borrador',
                            f"Notas cortas ({repr(notas_cortas)!r}) cambiaron estado a borrador")

    @given(safe_text_min10)
    @settings(**_pbt_settings)
    def test_devolver_acepta_notas_suficientes(self, notas_suficientes):
        """Notas con >= 10 chars (strip) → noticia cambia a borrador."""
        factory = RequestFactory()
        editor = make_user(grupo=make_grupo_editor())
        autor = make_user(grupo=make_grupo_autor())
        noticia = make_noticia(autor, estado='pendiente_revision')

        data = {'accion': 'devolver', 'notas_editor': notas_suficientes}
        request = _make_request(factory, 'POST',
                                 f'/noticias/editores/revisar/{noticia.pk}/', editor, data)
        revisar_noticia(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertEqual(noticia.estado, 'borrador',
                         "Notas suficientes no cambiaron el estado a borrador")


# ── Property 13: Bandeja filtra solo pendientes ───────────────────────────

class TestBandejaFiltraPendientes(HypothesisTestCase):
    """
    Property 13 — bandeja_revision contiene exclusivamente noticias en
    estado='pendiente_revision'.
    Validates: Requirements 5.1
    """

    @given(
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5),
    )
    @settings(**_pbt_settings)
    def test_bandeja_solo_muestra_pendientes(self, n_borrador, n_pendiente, n_publicado):
        """page_obj de bandeja_revision solo contiene noticias pendiente_revision."""
        editor = make_user(grupo=make_grupo_editor())
        autor = make_user(grupo=make_grupo_autor())

        for _ in range(n_borrador):
            make_noticia(autor, estado='borrador')
        for _ in range(n_pendiente):
            make_noticia(autor, estado='pendiente_revision')
        for _ in range(n_publicado):
            make_noticia(autor, estado='publicado')

        self.client.force_login(editor)
        response = self.client.get('/noticias/editores/bandeja-revision/')
        self.assertEqual(response.status_code, 200)

        for noticia in response.context['page_obj']:
            self.assertEqual(noticia.estado, 'pendiente_revision',
                             f"La bandeja contiene noticia en estado '{noticia.estado}'")


# ── Properties 14 & 15: Publicación y devolución ─────────────────────────

class TestPublicacionYDevolucion(HypothesisTestCase):
    """
    Property 14 — publicar() → estado='publicado', notas_editor='', fecha_publicacion≈now.
    Property 15 — devolver() con notas≥10 → estado='borrador', notas guardadas exactas.
    Validates: Requirements 5.4, 5.5
    """

    def test_publicar_resetea_notas_y_fecha(self):
        """Property 14: publicar → estado publicado, notas vacías, fecha reciente (≤5s)."""
        factory = RequestFactory()
        editor = make_user(grupo=make_grupo_editor())
        autor = make_user(grupo=make_grupo_autor())
        noticia = make_noticia(autor, estado='pendiente_revision')
        noticia.notas_editor = 'alguna nota previa que debe borrarse'
        noticia.save(update_fields=['notas_editor'])

        antes = timezone.now()
        request = _make_request(factory, 'POST',
                                  f'/noticias/editores/revisar/{noticia.pk}/',
                                  editor, {'accion': 'publicar'})
        revisar_noticia(request, pk=noticia.pk)
        despues = timezone.now()

        noticia.refresh_from_db()
        self.assertEqual(noticia.estado, 'publicado')
        self.assertEqual(noticia.notas_editor, '', "notas_editor no fue reseteado al publicar")
        self.assertIsNotNone(noticia.fecha_publicacion)
        self.assertGreaterEqual(noticia.fecha_publicacion, antes)
        self.assertLessEqual(noticia.fecha_publicacion, despues)

    @given(safe_text_min10)
    @settings(**_pbt_settings)
    def test_devolver_guarda_notas_y_cambia_borrador(self, notas):
        """Property 15: devolver con notas≥10 → borrador y notas guardadas exactas."""
        factory = RequestFactory()
        editor = make_user(grupo=make_grupo_editor())
        autor = make_user(grupo=make_grupo_autor())
        noticia = make_noticia(autor, estado='pendiente_revision')

        data = {'accion': 'devolver', 'notas_editor': notas}
        request = _make_request(factory, 'POST',
                                  f'/noticias/editores/revisar/{noticia.pk}/',
                                  editor, data)
        revisar_noticia(request, pk=noticia.pk)

        noticia.refresh_from_db()
        self.assertEqual(noticia.estado, 'borrador', "El estado no cambió a borrador")
        self.assertEqual(noticia.notas_editor, notas.strip(),
                         "Las notas guardadas no coinciden con las enviadas")


# ── Property 16: Estadísticas filtradas por autor ─────────────────────────

class TestEstadisticasFiltradas(HypothesisTestCase):
    """
    Property 16 — Contadores del dashboard coinciden con conteos filtrados por autor.
    Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
    """

    @given(
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5),
    )
    @settings(**_pbt_settings)
    def test_dashboard_solo_cuenta_noticias_propias(self, n_propias, n_ajenas):
        """Contadores del dashboard == conteos filtrados por autor=request.user."""
        grupo = make_grupo_autor()
        autor_a = make_user(grupo=grupo)
        autor_b = make_user(grupo=grupo)

        estados_ciclo = ['borrador', 'publicado', 'pendiente_revision', 'borrador', 'publicado']
        for i in range(n_propias):
            make_noticia(autor_a, estado=estados_ciclo[i % len(estados_ciclo)])
        for _ in range(n_ajenas):
            make_noticia(autor_b, estado='publicado')

        self.client.force_login(autor_a)
        response = self.client.get('/noticias/autores/')
        self.assertEqual(response.status_code, 200)
        ctx = response.context

        esperado_total = Noticia.objects.filter(autor=autor_a).count()
        esperado_publicadas = Noticia.objects.filter(autor=autor_a, estado='publicado').count()
        esperado_borradores = Noticia.objects.filter(autor=autor_a, estado='borrador').count()
        esperado_revision = Noticia.objects.filter(
            autor=autor_a, estado='pendiente_revision').count()

        self.assertEqual(ctx['mis_total'], esperado_total,
                         "mis_total incluye noticias de otros autores")
        self.assertEqual(ctx['mis_publicadas'], esperado_publicadas,
                         "mis_publicadas incluye noticias de otros autores")
        self.assertEqual(ctx['mis_borradores'], esperado_borradores,
                         "mis_borradores incluye noticias de otros autores")
        self.assertEqual(ctx['mis_en_revision'], esperado_revision,
                         "mis_en_revision incluye noticias de otros autores")


# ── Property 17: Migración preserva estados existentes ───────────────────

class TestMigracionPreservaEstados(TestCase):
    """
    Property 17 — Estados previos se conservan; 'pendiente_revision' en ESTADO_CHOICES;
    campo notas_editor existe con blank=True y default=''.
    Validates: Requirements 8.4
    """

    def test_estados_existentes_no_modificados(self):
        """Noticias en borrador/publicado/archivado conservan su estado en BD."""
        autor = make_user(grupo=make_grupo_autor())
        n_b = make_noticia(autor, estado='borrador')
        n_p = make_noticia(autor, estado='publicado')
        n_a = make_noticia(autor, estado='archivado')
        n_b.refresh_from_db(); n_p.refresh_from_db(); n_a.refresh_from_db()
        self.assertEqual(n_b.estado, 'borrador')
        self.assertEqual(n_p.estado, 'publicado')
        self.assertEqual(n_a.estado, 'archivado')

    def test_pendiente_revision_en_estado_choices(self):
        valores = [v for v, _ in Noticia.ESTADO_CHOICES]
        self.assertIn('pendiente_revision', valores)

    def test_notas_editor_campo_existe_blank_default(self):
        campo = Noticia._meta.get_field('notas_editor')
        self.assertTrue(campo.blank)
        self.assertEqual(campo.default, '')

    def test_creacion_noticia_notas_editor_vacio_por_defecto(self):
        autor = make_user(grupo=make_grupo_autor())
        noticia = make_noticia(autor)
        self.assertEqual(noticia.notas_editor, '')

    def test_orden_pendiente_revision_en_choices(self):
        """pendiente_revision debe estar entre 'borrador' y 'publicado'."""
        valores = [v for v, _ in Noticia.ESTADO_CHOICES]
        self.assertGreater(valores.index('pendiente_revision'), valores.index('borrador'))
        self.assertLess(valores.index('pendiente_revision'), valores.index('publicado'))


# ── TODO: Property 8 (eliminación imagen previa) ─────────────────────────
# Requiere setup de storage mock con archivo real.
# Testear con mock de noticia.imagen_principal.delete (ver design.md Property 8).
