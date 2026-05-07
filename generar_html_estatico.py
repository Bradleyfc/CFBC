"""
Genera HTMLs estáticos offline de la página de inicio y cursos.
Usa Django directamente (sin servidor ni login).
Todo queda en UN SOLO archivo .html con fuentes en base64.

Uso:
    source venv/bin/activate
    python3 generar_html_estatico.py
"""

import os
import sys
import base64
import re
from pathlib import Path

# ── Configurar Django ──────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cfbc.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.template.loader import render_to_string
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

# Importar modelos necesarios
try:
    from principal.models import Curso as Course
except ImportError:
    Course = None
try:
    from blog.models import Noticia, Categoria
except ImportError:
    Noticia = None
    Categoria = None

# ── Rutas de fuentes locales ───────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
FONT_WOFF2 = STATIC_DIR / "fonts" / "material-icons" / "MaterialIcons-Regular.woff2"
FONT_WOFF  = STATIC_DIR / "fonts" / "material-icons" / "MaterialIcons-Regular.woff"
CSS_TAILWIND      = STATIC_DIR / "css" / "tailwind.css"
CSS_ICONS         = STATIC_DIR / "css" / "icons.css"
CSS_DOC_ICONS     = STATIC_DIR / "css" / "document-icons.css"


def leer_base64(path: Path, mime: str) -> str:
    if not path.exists():
        print(f"  ⚠ No encontrado: {path}")
        return ""
    data = path.read_bytes()
    b64  = base64.b64encode(data).decode("ascii")
    print(f"  ✓ {path.name} ({len(data)//1024} KB)")
    return f"data:{mime};base64,{b64}"


def leer_css(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def css_fuente_embebida() -> str:
    """@font-face con la fuente Material Icons en base64."""
    w2 = leer_base64(FONT_WOFF2, "font/woff2")
    w  = leer_base64(FONT_WOFF,  "font/woff")
    srcs = []
    if w2: srcs.append(f"url('{w2}') format('woff2')")
    if w:  srcs.append(f"url('{w}') format('woff')")
    if not srcs:
        return ""
    return f"""@font-face {{
  font-family: 'Material Icons';
  font-style: normal;
  font-weight: 400;
  font-display: block;
  src: {', '.join(srcs)};
}}
.material-icons {{
  font-family: 'Material Icons' !important;
  font-weight: normal; font-style: normal; font-size: 24px;
  line-height: 1; letter-spacing: normal; text-transform: none;
  display: inline-block; white-space: nowrap; word-wrap: normal;
  direction: ltr; -webkit-font-feature-settings: 'liga';
  font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased;
  vertical-align: middle;
}}"""


def construir_html_completo(titulo: str, cuerpo_html: str, css_font: str) -> str:
    """
    Construye un HTML autocontenido con todo embebido:
    fuente Material Icons (base64) + Tailwind CSS + iconos CSS.
    """
    tailwind_css  = leer_css(CSS_TAILWIND)
    icons_css     = leer_css(CSS_ICONS)
    doc_icons_css = leer_css(CSS_DOC_ICONS)

    # Eliminar tags Django que puedan haber quedado sin renderizar
    cuerpo_limpio = re.sub(r'\{%[^%]*%\}', '', cuerpo_html)
    cuerpo_limpio = re.sub(r'\{\{[^}]*\}\}', '', cuerpo_limpio)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo}</title>
  <style>
    /* ── Material Icons (fuente embebida en base64) ── */
    {css_font}
  </style>
  <style>
    /* ── Tailwind CSS ── */
    {tailwind_css}
  </style>
  <style>
    /* ── Icons CSS ── */
    {icons_css}
  </style>
  <style>
    /* ── Document Icons CSS ── */
    {doc_icons_css}
  </style>
  <style>
    /* ── Estilos base ── */
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f1f5f9; }}
    img {{ max-width: 100%; }}
    /* Footer: forzar colores correctos en versión estática */
    .glass-footer {{ color: #e5e7eb !important; }}
    .glass-footer a {{ color: #e5e7eb !important; text-decoration: none; }}
    .glass-footer a:hover {{ color: #ffffff !important; }}
    .glass-footer h5, .glass-footer h6 {{ color: #ffffff !important; }}
    .glass-footer p {{ color: #e5e7eb !important; }}
    .glass-footer strong {{ color: #ffffff !important; }}
    .glass-footer .text-gray-200 {{ color: #e5e7eb !important; }}
    .glass-footer .text-white {{ color: #ffffff !important; }}
    .glass-footer .text-xs {{ color: #e5e7eb !important; }}
    /* Preservar colores de iconos de contacto */
    .glass-footer .text-blue-400 {{ color: #60a5fa !important; }}
    .glass-footer .text-green-400 {{ color: #4ade80 !important; }}
    .glass-footer .text-red-400 {{ color: #f87171 !important; }}
  </style>
</head>
<body>
{cuerpo_limpio}
</body>
</html>"""


def obtener_contexto_home():
    """Obtiene datos reales de la base de datos para la home."""
    ctx = {
        "request": None,
        "cursos_grupos_3": [],
        "noticias_grupos_3": [],
        "categorias_con_noticias": [],
    }

    if Course:
        try:
            cursos = list(Course.objects.filter(status__in=["I", "P"]).order_by("-start_date")[:12])
            # Agrupar de 3 en 3
            ctx["cursos_grupos_3"] = [cursos[i:i+3] for i in range(0, len(cursos), 3)]
            print(f"  ✓ {len(cursos)} cursos cargados")
        except Exception as e:
            print(f"  ⚠ Error cargando cursos: {e}")
    if Noticia:
        try:
            noticias = list(Noticia.objects.filter(estado="publicado").order_by("-fecha_publicacion")[:9])
            ctx["noticias_grupos_3"] = [noticias[i:i+3] for i in range(0, len(noticias), 3)]
            print(f"  ✓ {len(noticias)} noticias cargadas")
        except Exception as e:
            print(f"  ⚠ Error cargando noticias: {e}")

    if Categoria:
        try:
            cats = list(Categoria.objects.all()[:10])
            ctx["categorias_con_noticias"] = cats
        except Exception as e:
            pass

    return ctx


def obtener_contexto_cursos():
    """Obtiene datos reales para la página de cursos."""
    from django.core.paginator import Paginator
    from principal.models import CursoAcademico

    ctx = {
        "user": type("User", (), {"first_name": "", "username": "Visitante", "is_authenticated": False})(),
        "group_name": "",
        "courses": [],
        "page_obj": None,
        "is_paginated": False,
        "area_seleccionada": "",
        "tipo_seleccionado": "",
        "filtro_servidor": True,
    }

    if Course:
        try:
            # Usar el curso académico activo igual que CoursesView
            curso_academico_activo = CursoAcademico.objects.filter(activo=True).first()
            if curso_academico_activo:
                cursos = list(Course.objects.filter(
                    curso_academico=curso_academico_activo
                ).order_by("name"))
            else:
                cursos = list(Course.objects.all().order_by("name"))

            # Añadir atributos que el template espera en cada curso
            for curso in cursos:
                curso.is_enrolled = False
                curso.tiene_solicitud_pendiente = False
                curso.tiene_solicitud_rechazada = False
                curso.enrollment_count = 0
                curso.formulario_aplicacion = None

            # Paginación: 8 por página igual que CoursesView
            paginator = Paginator(cursos, 8)
            page_obj = paginator.get_page(1)

            ctx["courses"] = page_obj
            ctx["page_obj"] = page_obj
            ctx["is_paginated"] = paginator.num_pages > 1
            print(f"  ✓ {len(cursos)} cursos cargados ({paginator.num_pages} página(s))")
        except Exception as e:
            print(f"  ⚠ Error cargando cursos: {e}")

    return ctx


def obtener_contexto_noticias():
    """Obtiene datos reales de la base de datos para la página de noticias."""
    from django.core.paginator import Paginator

    ctx = {
        "page_obj": None,
        "noticias_destacadas": [],
        "categorias": [],
        "busqueda": "",
        "categoria_actual": None,
    }

    if Noticia:
        try:
            noticias_qs = list(
                Noticia.objects.filter(estado="publicado")
                .select_related("categoria", "autor")
                .order_by("-fecha_actualizacion", "-fecha_creacion")
            )
            paginator = Paginator(noticias_qs, 6)
            ctx["page_obj"] = paginator.get_page(1)
            print(f"  ✓ {len(noticias_qs)} noticias cargadas")
        except Exception as e:
            print(f"  ⚠ Error cargando noticias: {e}")

        try:
            destacadas = list(
                Noticia.objects.filter(estado="publicado", destacada=True)
                .order_by("-fecha_actualizacion")[:10]
            )
            ctx["noticias_destacadas"] = destacadas
            print(f"  ✓ {len(destacadas)} noticias destacadas")
        except Exception as e:
            print(f"  ⚠ Error cargando destacadas: {e}")

    if Categoria:
        try:
            cats = list(Categoria.objects.all()[:10])
            ctx["categorias"] = cats
            print(f"  ✓ {len(cats)} categorías cargadas")
        except Exception as e:
            print(f"  ⚠ Error cargando categorías: {e}")

    return ctx


def obtener_contexto_reglamento():
    """Obtiene el contexto para la página del reglamento general."""
    from django.utils import timezone
    
    ctx = {
        "ano_anterior": timezone.now().year - 1,
        "ano_actual": timezone.now().year,
    }
    
    print(f"  ✓ Contexto del reglamento preparado (año: {ctx['ano_actual']})")
    return ctx


def renderizar_template_seguro(template_name: str, context: dict) -> str:
    """
    Renderiza un template Django con manejo de errores.
    Usa RequestFactory para simular un request sin servidor.
    """
    factory = RequestFactory()
    request = factory.get("/")
    request.user = AnonymousUser()

    context["request"] = request

    try:
        html = render_to_string(template_name, context, request=request)
        return html
    except Exception as e:
        print(f"  ⚠ Error renderizando {template_name}: {e}")
        # Intentar renderizar solo el bloque content
        return f"<p>Error al renderizar: {e}</p>"


def embeber_imagenes_media(html: str) -> str:
    """
    Convierte URLs de imágenes /media/... a base64 si los archivos existen.
    """
    media_root = BASE_DIR / "media"

    def reemplazar(m):
        src = m.group(1)
        if src.startswith("/media/"):
            ruta = media_root / src[7:]  # quitar /media/
            if ruta.exists():
                ext = ruta.suffix.lower()
                mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                            ".png": "image/png", ".gif": "image/gif",
                            ".webp": "image/webp", ".svg": "image/svg+xml"}
                mime = mime_map.get(ext, "image/jpeg")
                data = ruta.read_bytes()
                b64  = base64.b64encode(data).decode("ascii")
                return f'src="data:{mime};base64,{b64}"'
        return m.group(0)

    return re.sub(r'src="(/media/[^"]+)"', reemplazar, html)


def inyectar_assets_en_html_completo(html: str, css_font: str) -> str:
    """
    Para templates que ya generan un HTML completo (con su propio <head>),
    inyecta las fuentes y CSS directamente antes de </head> en lugar de
    envolver el HTML en otro documento.
    """
    tailwind_css  = leer_css(CSS_TAILWIND)
    icons_css     = leer_css(CSS_ICONS)
    doc_icons_css = leer_css(CSS_DOC_ICONS)

    # Limpiar tags Django residuales
    html = re.sub(r'\{%[^%]*%\}', '', html)
    html = re.sub(r'\{\{[^}]*\}\}', '', html)

    bloque_css = f"""
  <style>/* Material Icons (base64) */
    {css_font}
  </style>
  <style>/* Tailwind CSS */
    {tailwind_css}
  </style>
  <style>/* Icons CSS */
    {icons_css}
  </style>
  <style>/* Document Icons CSS */
    {doc_icons_css}
  </style>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f1f5f9; }}
    img {{ max-width: 100%; }}
    /* Footer: forzar colores correctos en versión estática */
    .glass-footer {{ color: #e5e7eb !important; }}
    .glass-footer a {{ color: #e5e7eb !important; text-decoration: none; }}
    .glass-footer a:hover {{ color: #ffffff !important; }}
    .glass-footer h5, .glass-footer h6 {{ color: #ffffff !important; }}
    .glass-footer p {{ color: #e5e7eb !important; }}
    .glass-footer strong {{ color: #ffffff !important; }}
    .glass-footer .text-gray-200 {{ color: #e5e7eb !important; }}
    .glass-footer .text-white {{ color: #ffffff !important; }}
    .glass-footer .text-xs {{ color: #e5e7eb !important; }}
    /* Preservar colores de iconos de contacto */
    .glass-footer .text-blue-400 {{ color: #60a5fa !important; }}
    .glass-footer .text-green-400 {{ color: #4ade80 !important; }}
    .glass-footer .text-red-400 {{ color: #f87171 !important; }}
  </style>"""

    # Inyectar justo antes de </head>
    if '</head>' in html:
        html = html.replace('</head>', bloque_css + '\n</head>', 1)
    else:
        # Fallback: insertar al inicio
        html = bloque_css + html

    # Eliminar links a CSS externos que no funcionarán offline
    html = re.sub(r'<link[^>]+href="[^"]*cdn[^"]*"[^>]*>', '', html)
    html = re.sub(r'<link[^>]+href="[^"]*static[^"]*\.css[^"]*"[^>]*>', '', html)
    html = re.sub(r'<script[^>]+src="[^"]*cdn[^"]*"[^>]*></script>', '', html)

    return html



    """
    Convierte URLs de imágenes /media/... a base64 si los archivos existen.
    """
    media_root = BASE_DIR / "media"

    def reemplazar(m):
        src = m.group(1)
        if src.startswith("/media/"):
            ruta = media_root / src[7:]  # quitar /media/
            if ruta.exists():
                ext = ruta.suffix.lower()
                mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                            ".png": "image/png", ".gif": "image/gif",
                            ".webp": "image/webp", ".svg": "image/svg+xml"}
                mime = mime_map.get(ext, "image/jpeg")
                data = ruta.read_bytes()
                b64  = base64.b64encode(data).decode("ascii")
                return f'src="data:{mime};base64,{b64}"'
        return m.group(0)

    return re.sub(r'src="(/media/[^"]+)"', reemplazar, html)


def generar_pagina(titulo: str, template: str, contexto: dict,
                   salida: str, css_font: str):
    print(f"\n{'─'*55}")
    print(f"  Generando: {salida}")
    print(f"{'─'*55}")

    print("  [1] Renderizando template…")
    html_renderizado = renderizar_template_seguro(template, contexto)

    print("  [2] Embebiendo imágenes de media…")
    html_renderizado = embeber_imagenes_media(html_renderizado)

    # Detectar si el template ya genera un HTML completo (tiene su propio DOCTYPE)
    es_html_completo = '<!DOCTYPE' in html_renderizado[:500] or '<html' in html_renderizado[:500]

    if es_html_completo:
        print("  [3] Inyectando assets en HTML existente…")
        html_final = inyectar_assets_en_html_completo(html_renderizado, css_font)
    else:
        print("  [3] Construyendo HTML autocontenido…")
        html_final = construir_html_completo(titulo, html_renderizado, css_font)

    with open(salida, "w", encoding="utf-8") as f:
        f.write(html_final)

    kb = os.path.getsize(salida) // 1024
    print(f"  ✅ Guardado: {salida} ({kb} KB)")


def main():
    print("=" * 55)
    print("  Generador HTML Offline — CFBC")
    print("=" * 55)

    # Preparar fuente embebida
    print("\n[*] Embebiendo fuente Material Icons…")
    css_font = css_fuente_embebida()
    if not css_font:
        print("\n  ✗ Fuentes no encontradas. Ejecuta primero:")
        print("    python3 descargar_iconos_offline.py")
        sys.exit(1)

    # Página de inicio
    print("\n[1/4] Página de Inicio")
    ctx_home = obtener_contexto_home()
    generar_pagina(
        titulo   = "Centro Fray Bartolomé de las Casas — Inicio",
        template = "home.html",
        contexto = ctx_home,
        salida   = "pagina_inicio_offline.html",
        css_font = css_font,
    )

    # Página de cursos
    print("\n[2/4] Página de Cursos")
    ctx_cursos = obtener_contexto_cursos()
    generar_pagina(
        titulo   = "Centro Fray Bartolomé de las Casas — Cursos",
        template = "cursos.html",
        contexto = ctx_cursos,
        salida   = "pagina_cursos_offline.html",
        css_font = css_font,
    )

    # Página de noticias
    print("\n[3/4] Página de Noticias")
    ctx_noticias = obtener_contexto_noticias()
    generar_pagina(
        titulo   = "Centro Fray Bartolomé de las Casas — Noticias",
        template = "blog/lista_noticias.html",
        contexto = ctx_noticias,
        salida   = "pagina_noticias_offline.html",
        css_font = css_font,
    )

    # Página de reglamento general
    print("\n[4/4] Página de Reglamento General")
    ctx_reglamento = obtener_contexto_reglamento()
    generar_pagina(
        titulo   = "Centro Fray Bartolomé de las Casas — Reglamento General",
        template = "registration/reglamento_general.html",
        contexto = ctx_reglamento,
        salida   = "pagina_reglamento_general_offline.html",
        css_font = css_font,
    )

    print("\n" + "=" * 55)
    print("  Archivos generados:")
    for f in [
        "pagina_inicio_offline.html",
        "pagina_cursos_offline.html",
        "pagina_noticias_offline.html",
        "pagina_reglamento_general_offline.html",
    ]:
        if os.path.exists(f):
            print(f"    • {f}  ({os.path.getsize(f)//1024} KB)")
    print("=" * 55)
    print("\nAbre los archivos con doble clic — sin internet, sin servidor.\n")


if __name__ == "__main__":
    main()
