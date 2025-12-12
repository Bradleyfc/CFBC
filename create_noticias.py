#!/usr/bin/env python3
"""
Crear noticias para el blog
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from blog.models import Noticia, Categoria
from django.contrib.auth.models import User

def create_noticias():
    """
    Crear 10 noticias para el blog
    """
    print("📰 Creando Noticias para el Blog")
    print("=" * 40)
    
    # Obtener un usuario para asignar como autor
    try:
        autor = User.objects.filter(is_staff=True).first()
        if not autor:
            autor = User.objects.first()
        
        if not autor:
            print("❌ No hay usuarios disponibles para asignar como autor")
            return
    except Exception as e:
        print(f"❌ Error obteniendo usuario: {e}")
        return
    
    # Crear o obtener categoría
    try:
        categoria, created = Categoria.objects.get_or_create(
            nombre='Noticias Generales',
            defaults={
                'descripcion': 'Noticias generales del Centro Fray Bartolomé de las Casas'
            }
        )
        if created:
            print(f"✅ Categoría creada: {categoria.nombre}")
    except Exception as e:
        print(f"❌ Error creando categoría: {e}")
        return
    
    noticias_data = [
        {
            'titulo': 'Inicio de Inscripciones para Cursos de Idiomas 2025',
            'resumen': 'Ya están abiertas las inscripciones para los cursos de inglés, alemán e italiano. Plazas limitadas.',
            'contenido': 'El Centro Fray Bartolomé de las Casas anuncia el inicio del período de inscripciones para los cursos de idiomas del año 2025. Ofrecemos cursos de inglés básico y avanzado, alemán básico e italiano básico y diplomado. Las clases comenzarán en febrero y las plazas son limitadas. Para inscribirse, los interesados deben registrarse en nuestro sitio web y completar el formulario de aplicación correspondiente.'
        },
        {
            'titulo': 'Nuevo Curso de Diseño Gráfico Disponible',
            'resumen': 'Lanzamos nuestro programa de diseño gráfico con herramientas modernas y metodología práctica.',
            'contenido': 'Nos complace anunciar el lanzamiento de nuestros cursos de diseño gráfico, tanto básico como avanzado. Los estudiantes aprenderán a utilizar herramientas profesionales de diseño y desarrollarán proyectos reales. El curso incluye teoría del color, composición, tipografía y diseño digital. Las inscripciones están abiertas y las clases se impartirán en modalidad presencial con acceso a laboratorios especializados.'
        },
        {
            'titulo': 'Taller de Teología: Explorando la Fe Contemporánea',
            'resumen': 'Un espacio de reflexión y diálogo sobre temas teológicos actuales dirigido a toda la comunidad.',
            'contenido': 'El Centro invita a participar en nuestro taller de teología, un espacio de encuentro y reflexión sobre la fe en el mundo contemporáneo. El taller abordará temas como la espiritualidad moderna, la ética cristiana y el diálogo interreligioso. Está dirigido a personas de todas las edades que deseen profundizar en su comprensión de la fe y participar en discusiones enriquecedoras con otros miembros de la comunidad.'
        },
        {
            'titulo': 'Programa Especial para Adolescentes: Arte y Creatividad',
            'resumen': 'Taller de apreciación artística diseñado especialmente para jóvenes de 13 a 17 años.',
            'contenido': 'Hemos desarrollado un programa especial dirigido a adolescentes que combina apreciación artística, creatividad y desarrollo personal. El taller incluye actividades de pintura, música, teatro y escritura creativa. Los participantes trabajarán en proyectos individuales y grupales, fomentando la expresión personal y el trabajo en equipo. El programa está diseñado para ser dinámico y atractivo para jóvenes de 13 a 17 años.'
        },
        {
            'titulo': 'Celebración del Día Internacional de la Educación',
            'resumen': 'El Centro se une a la celebración mundial reconociendo la importancia de la educación de calidad.',
            'contenido': 'En conmemoración del Día Internacional de la Educación, el Centro Fray Bartolomé de las Casas reafirma su compromiso con la formación integral y la educación de calidad. Durante esta semana especial, realizaremos actividades que destacan la importancia del aprendizaje continuo y el desarrollo personal. Invitamos a toda la comunidad a reflexionar sobre el valor transformador de la educación en nuestras vidas.'
        },
        {
            'titulo': 'Nuevas Instalaciones: Laboratorio de Idiomas Renovado',
            'resumen': 'Hemos renovado completamente nuestro laboratorio de idiomas con tecnología de última generación.',
            'contenido': 'Nos enorgullece presentar nuestro laboratorio de idiomas completamente renovado, equipado con tecnología de última generación para mejorar la experiencia de aprendizaje. Las nuevas instalaciones incluyen sistemas de audio individuales, software interactivo y recursos multimedia que permiten una inmersión completa en el idioma. Esta mejora beneficiará a todos los estudiantes de nuestros cursos de inglés, alemán e italiano.'
        },
        {
            'titulo': 'Conferencia: "El Futuro del Diseño Digital"',
            'resumen': 'Expertos en diseño compartirán las últimas tendencias y herramientas del diseño digital moderno.',
            'contenido': 'El próximo mes realizaremos una conferencia especial sobre "El Futuro del Diseño Digital", donde expertos de la industria compartirán las últimas tendencias, herramientas y oportunidades profesionales en el campo del diseño. La conferencia está dirigida a estudiantes actuales, egresados y profesionales interesados en mantenerse actualizados. Habrá sesiones sobre diseño UX/UI, branding digital y nuevas tecnologías creativas.'
        },
        {
            'titulo': 'Programa de Becas 2025: Oportunidades de Estudio',
            'resumen': 'Anunciamos nuestro programa de becas para estudiantes con excelencia académica y necesidad económica.',
            'contenido': 'El Centro Fray Bartolomé de las Casas se complace en anunciar su programa de becas para el año 2025. Ofrecemos becas parciales y completas para estudiantes que demuestren excelencia académica y necesidad económica. Las becas cubren matrícula y materiales de estudio para cualquiera de nuestros cursos disponibles. Los interesados pueden solicitar información detallada y formularios de aplicación en nuestra secretaría académica.'
        },
        {
            'titulo': 'Graduación de la Promoción 2024: Celebrando Logros',
            'resumen': 'Celebramos los logros de nuestros graduados de 2024 en una ceremonia especial.',
            'contenido': 'Con gran alegría celebramos la graduación de la promoción 2024 del Centro Fray Bartolomé de las Casas. Durante la ceremonia, reconocimos los logros de estudiantes que completaron exitosamente sus cursos en las diferentes áreas de estudio. La ceremonia incluyó la entrega de diplomas, reconocimientos especiales y palabras inspiradoras sobre la importancia del aprendizaje continuo. Felicitamos a todos nuestros graduados por su dedicación y esfuerzo.'
        },
        {
            'titulo': 'Alianza Estratégica con Instituciones Educativas Internacionales',
            'resumen': 'Establecemos nuevas alianzas que ampliarán las oportunidades educativas para nuestros estudiantes.',
            'contenido': 'El Centro ha establecido alianzas estratégicas con instituciones educativas internacionales que permitirán ampliar las oportunidades de estudio y certificación para nuestros estudiantes. Estas alianzas incluyen programas de intercambio, certificaciones internacionales y acceso a recursos educativos globales. Los estudiantes de idiomas podrán obtener certificaciones reconocidas internacionalmente, y los de diseño tendrán acceso a software y herramientas profesionales de última generación.'
        }
    ]
    
    # Crear las noticias
    noticias_creadas = 0
    fecha_base = datetime.now()
    
    for i, noticia_data in enumerate(noticias_data):
        try:
            # Crear fecha escalonada (una noticia cada 3 días hacia atrás)
            fecha_publicacion = fecha_base - timedelta(days=i*3)
            
            noticia, created = Noticia.objects.get_or_create(
                titulo=noticia_data['titulo'],
                defaults={
                    'resumen': noticia_data['resumen'],
                    'contenido': noticia_data['contenido'],
                    'autor': autor,
                    'categoria': categoria,
                    'fecha_publicacion': fecha_publicacion,
                    'estado': 'publicado'
                }
            )
            
            if created:
                noticias_creadas += 1
                print(f"✅ Creada: {noticia.titulo}")
            else:
                print(f"⚠️  Ya existe: {noticia.titulo}")
                
        except Exception as e:
            print(f"❌ Error creando noticia '{noticia_data['titulo']}': {e}")
    
    print(f"\n📊 Resumen:")
    print(f"   Noticias creadas: {noticias_creadas}")
    print(f"   Total de noticias en el blog: {Noticia.objects.count()}")

if __name__ == '__main__':
    try:
        create_noticias()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()