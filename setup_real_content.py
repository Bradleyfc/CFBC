#!/usr/bin/env python
"""
Script para configurar el contenido real del chatbot basado en el sitio web CFBC
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from chatbot.models import CategoriaFAQ, FAQ, FAQVariation
from principal.models import Curso
from blog.models import Noticia

def crear_categorias_reales():
    """Crear categorías basadas en el contenido real del sitio"""
    
    print("📂 Creando categorías reales...")
    
    categorias_data = [
        {
            'nombre': 'Cursos',
            'descripcion': 'Información sobre los cursos disponibles en el Centro Fray Bartolomé de las Casas',
            'slug': 'cursos'
        },
        {
            'nombre': 'Inscripciones',
            'descripcion': 'Proceso de inscripción, requisitos y fechas importantes',
            'slug': 'inscripciones'
        },
        {
            'nombre': 'Información General',
            'descripcion': 'Información general sobre el centro, ubicación, contacto y servicios',
            'slug': 'general'
        },
        {
            'nombre': 'Áreas de Estudio',
            'descripcion': 'Información sobre las diferentes áreas de estudio disponibles',
            'slug': 'areas'
        }
    ]
    
    for cat_data in categorias_data:
        categoria, created = CategoriaFAQ.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"   ✅ Categoría creada: {categoria.nombre}")
        else:
            print(f"   ℹ️  Categoría existente: {categoria.nombre}")
    
    return CategoriaFAQ.objects.all()

def crear_faqs_cursos():
    """Crear FAQs basadas en los cursos reales"""
    
    print("\n📚 Creando FAQs de cursos...")
    
    categoria_cursos = CategoriaFAQ.objects.get(slug='cursos')
    categoria_areas = CategoriaFAQ.objects.get(slug='areas')
    
    # FAQ general sobre cursos disponibles
    cursos = Curso.objects.all()
    cursos_por_area = {}
    
    for curso in cursos:
        area = curso.get_area_display()
        if area not in cursos_por_area:
            cursos_por_area[area] = []
        cursos_por_area[area].append(curso)
    
    # FAQ: ¿Qué cursos están disponibles?
    cursos_texto = "En el Centro Fray Bartolomé de las Casas ofrecemos los siguientes cursos:\n\n"
    
    for area, cursos_area in cursos_por_area.items():
        cursos_texto += f"**{area}:**\n"
        for curso in cursos_area:
            estado = curso.get_dynamic_status_display()
            cursos_texto += f"• {curso.name} - {estado}\n"
            if curso.description:
                cursos_texto += f"  {curso.description[:100]}...\n"
        cursos_texto += "\n"
    
    cursos_texto += "Para más información sobre inscripciones, consulta nuestros requisitos y fechas disponibles."
    
    faq_cursos, created = FAQ.objects.get_or_create(
        pregunta="¿Qué cursos están disponibles?",
        defaults={
            'respuesta': cursos_texto,
            'categoria': categoria_cursos,
            'destacada': True,
            'prioridad': 10
        }
    )
    
    if created:
        print(f"   ✅ FAQ creada: {faq_cursos.pregunta}")
        
        # Crear variaciones
        variaciones = [
            "¿Cuáles son los cursos que ofrecen?",
            "¿Qué materias tienen disponibles?",
            "¿Qué puedo estudiar aquí?",
            "Muéstrame los cursos disponibles",
            "¿Qué opciones de estudio hay?"
        ]
        
        for variacion in variaciones:
            FAQVariation.objects.create(
                faq=faq_cursos,
                texto_texto_variacion=variacion
            )
    
    # FAQ por cada área
    for area, cursos_area in cursos_por_area.items():
        area_texto = f"En el área de {area} ofrecemos:\n\n"
        
        for curso in cursos_area:
            area_texto += f"**{curso.name}**\n"
            if curso.description:
                area_texto += f"{curso.description}\n"
            area_texto += f"Estado: {curso.get_dynamic_status_display()}\n"
            if curso.teacher:
                area_texto += f"Profesor: {curso.teacher.get_full_name() or curso.teacher.username}\n"
            if curso.start_date:
                area_texto += f"Fecha de inicio: {curso.start_date}\n"
            if curso.enrollment_deadline:
                area_texto += f"Fecha límite de inscripción: {curso.enrollment_deadline}\n"
            area_texto += "\n"
        
        faq_area, created = FAQ.objects.get_or_create(
            pregunta=f"¿Qué cursos hay en {area}?",
            defaults={
                'respuesta': area_texto,
                'categoria': categoria_areas,
                'destacada': False,
                'prioridad': 5
            }
        )
        
        if created:
            print(f"   ✅ FAQ de área creada: {faq_area.pregunta}")

def crear_faqs_inscripciones():
    """Crear FAQs sobre inscripciones"""
    
    print("\n📝 Creando FAQs de inscripciones...")
    
    categoria = CategoriaFAQ.objects.get(slug='inscripciones')
    
    faqs_inscripciones = [
        {
            'pregunta': '¿Cómo me inscribo a un curso?',
            'respuesta': '''Para inscribirte a un curso en el Centro Fray Bartolomé de las Casas:

1. **Revisa los cursos disponibles** en nuestra página web
2. **Verifica las fechas límite** de inscripción de cada curso
3. **Completa el formulario de inscripción** correspondiente
4. **Presenta los documentos requeridos**
5. **Realiza el pago** de la matrícula

**Documentos generalmente requeridos:**
• Documento de identidad
• Certificado de estudios previos (si aplica)
• Fotografía reciente

**Estado actual:** La mayoría de nuestros cursos están en etapa de inscripción.

Para más información específica, contacta a nuestra secretaría.''',
            'destacada': True,
            'prioridad': 10,
            'variaciones': [
                '¿Cuál es el proceso de inscripción?',
                '¿Cómo me apunto a un curso?',
                '¿Qué necesito para inscribirme?',
                'Proceso de matrícula',
                '¿Cómo hago la inscripción?'
            ]
        },
        {
            'pregunta': '¿Cuándo empiezan las inscripciones?',
            'respuesta': '''Las inscripciones en el Centro de Formación Bíblica Católica están **actualmente abiertas** para la mayoría de nuestros cursos.

**Estado actual de inscripciones:**
• La mayoría de cursos están en "etapa de inscripción"
• Cada curso tiene su propia fecha límite
• Te recomendamos inscribirte lo antes posible

**Para verificar fechas específicas:**
• Consulta la información de cada curso individual
• Contacta nuestra secretaría para fechas exactas
• Revisa regularmente nuestra página web

¡No esperes hasta el último momento para inscribirte!''',
            'destacada': True,
            'prioridad': 9,
            'variaciones': [
                '¿Cuándo abren inscripciones?',
                '¿Hasta cuándo puedo inscribirme?',
                'Fechas de inscripción',
                '¿Cuándo inician las matrículas?',
                'Período de inscripciones'
            ]
        },
        {
            'pregunta': '¿Cuáles son los requisitos para inscribirme?',
            'respuesta': '''Los requisitos para inscribirte en el Centro de Formación Bíblica Católica son:

**Requisitos generales:**
• Ser mayor de edad (para la mayoría de cursos)
• Presentar documento de identidad válido
• Completar el formulario de inscripción

**Documentación requerida:**
• Cédula de identidad o pasaporte
• Certificado de estudios previos (según el curso)
• Fotografía reciente tamaño carnet
• Comprobante de pago de matrícula

**Requisitos específicos por área:**
• **Cursos de idiomas:** Nivel básico de lectoescritura
• **Teología:** Interés genuino en estudios bíblicos
• **Cursos para adolescentes:** Edad entre 13-17 años

**Proceso de admisión:**
Algunos cursos pueden requerir una entrevista o evaluación previa.

Para información específica sobre requisitos de cada curso, contacta nuestra secretaría.''',
            'destacada': True,
            'prioridad': 8,
            'variaciones': [
                '¿Qué documentos necesito?',
                'Requisitos de admisión',
                '¿Qué necesito para estudiar aquí?',
                'Documentos para inscripción',
                'Requisitos de ingreso'
            ]
        }
    ]
    
    for faq_data in faqs_inscripciones:
        variaciones = faq_data.pop('variaciones', [])
        
        faq, created = FAQ.objects.get_or_create(
            pregunta=faq_data['pregunta'],
            defaults={
                **faq_data,
                'categoria': categoria
            }
        )
        
        if created:
            print(f"   ✅ FAQ creada: {faq.pregunta}")
            
            # Crear variaciones
            for variacion in variaciones:
                FAQVariation.objects.create(
                    faq=faq,
                    texto_variacion=variacion
                )

def crear_faqs_generales():
    """Crear FAQs de información general"""
    
    print("\n🏢 Creando FAQs generales...")
    
    categoria = CategoriaFAQ.objects.get(slug='general')
    
    faqs_generales = [
        {
            'pregunta': '¿Dónde está ubicado el Centro de Formación Bíblica Católica?',
            'respuesta': '''El Centro de Formación Bíblica Católica está ubicado en una zona accesible de la ciudad.

**Para obtener nuestra dirección exacta y cómo llegar:**
• Consulta la sección de contacto en nuestra página web
• Revisa el footer de nuestro sitio web
• Llama a nuestra secretaría para indicaciones detalladas

**Facilidades de acceso:**
• Transporte público disponible
• Estacionamiento para visitantes
• Instalaciones accesibles

**Horarios de atención:**
• Consulta nuestros horarios de oficina
• Disponibilidad para consultas académicas

Para direcciones específicas y mapas, visita nuestra página de contacto.''',
            'destacada': True,
            'prioridad': 7,
            'variaciones': [
                '¿Dónde queda el centro?',
                'Ubicación del CFBC',
                '¿Cómo llego al centro?',
                'Dirección del centro',
                '¿Dónde están ubicados?'
            ]
        },
        {
            'pregunta': '¿Cómo puedo contactar al Centro de Formación Bíblica Católica?',
            'respuesta': '''Puedes contactarnos a través de varios medios:

**Información de contacto:**
• Consulta el footer de nuestra página web para teléfonos y emails
• Visita nuestra sección de contacto
• Síguenos en nuestras redes sociales

**Horarios de atención:**
• Secretaría académica: Consulta horarios en el sitio web
• Atención telefónica: Durante horarios de oficina
• Respuesta a emails: Dentro de 24-48 horas

**Para consultas específicas:**
• **Inscripciones:** Contacta la secretaría académica
• **Información de cursos:** Habla con nuestros coordinadores
• **Pagos y matrículas:** Oficina administrativa

**Redes sociales:**
Síguenos para noticias y actualizaciones constantes sobre nuestros programas.''',
            'destacada': False,
            'prioridad': 6,
            'variaciones': [
                '¿Cuál es el teléfono del centro?',
                'Información de contacto',
                '¿Cómo los contacto?',
                'Teléfono y email',
                'Datos de contacto'
            ]
        },
        {
            'pregunta': '¿Qué es el Centro de Formación Bíblica Católica?',
            'respuesta': '''El Centro de Formación Bíblica Católica (CFBC) es una institución educativa dedicada a la formación integral en diversas áreas del conocimiento.

**Nuestra misión:**
• Brindar educación de calidad en múltiples disciplinas
• Formar personas íntegras con valores sólidos
• Contribuir al desarrollo académico y espiritual de nuestros estudiantes

**Áreas de formación:**
• **Idiomas:** Inglés, Alemán, Italiano
• **Teología:** Estudios bíblicos y formación espiritual
• **Diseño:** Cursos básicos y avanzados
• **Humanidades:** Diversas disciplinas humanísticas
• **Programas para adolescentes:** Formación especializada

**Nuestros valores:**
• Excelencia académica
• Formación integral
• Compromiso social
• Valores cristianos

Ofrecemos cursos, diplomados, talleres y programas de grado según el área de estudio.''',
            'destacada': True,
            'prioridad': 8,
            'variaciones': [
                '¿Qué es el CFBC?',
                'Información sobre el centro',
                '¿De qué se trata esta institución?',
                'Misión del centro',
                '¿Qué hacen aquí?'
            ]
        }
    ]
    
    for faq_data in faqs_generales:
        variaciones = faq_data.pop('variaciones', [])
        
        faq, created = FAQ.objects.get_or_create(
            pregunta=faq_data['pregunta'],
            defaults={
                **faq_data,
                'categoria': categoria
            }
        )
        
        if created:
            print(f"   ✅ FAQ creada: {faq.pregunta}")
            
            # Crear variaciones
            for variacion in variaciones:
                FAQVariation.objects.create(
                    faq=faq,
                    texto_variacion=variacion
                )

def main():
    """Función principal"""
    
    print("🚀 Configurando contenido real del chatbot CFBC")
    print("=" * 60)
    
    # Crear categorías
    categorias = crear_categorias_reales()
    
    # Crear FAQs basadas en contenido real
    crear_faqs_cursos()
    crear_faqs_inscripciones()
    crear_faqs_generales()
    
    # Mostrar resumen
    print("\n📊 Resumen del contenido creado:")
    print(f"   Categorías: {CategoriaFAQ.objects.count()}")
    print(f"   FAQs: {FAQ.objects.count()}")
    print(f"   Variaciones: {FAQVariation.objects.count()}")
    
    print("\n🎉 ¡Contenido real configurado exitosamente!")
    print("\n📋 Próximos pasos:")
    print("   1. python manage.py rebuild_index")
    print("   2. Probar el chatbot con preguntas reales")
    print("   3. Agregar más FAQs desde el admin si es necesario")

if __name__ == "__main__":
    main()
