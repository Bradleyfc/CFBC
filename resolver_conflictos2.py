import os

# Archivos donde HEAD (main) es más actualizado - quedarse con HEAD
use_head = [
    '.gitignore',
    'cfbc/settings.py',
    'cfbc/urls.py',
    'requirements.txt',
    'templates/base.html',
    'templates/profile/estudiantes.html',
    'templates/profile/profesores.html',
    'principal/views.py',
]

# Archivos nuevos de course_documents - quedarse con THEIRS (subir-descargar-documentos)
use_theirs = [
    '.django_tailwind_cli/source.css',
    'course_documents/admin.py',
    'course_documents/apps.py',
    'course_documents/file_service.py',
    'course_documents/forms.py',
    'course_documents/indicator_service.py',
    'course_documents/migrations/0001_initial.py',
    'course_documents/models.py',
    'course_documents/permissions.py',
    'course_documents/services.py',
    'course_documents/tests.py',
    'course_documents/urls.py',
    'course_documents/views.py',
    'static/css/tailwind.css',
]

def resolve(filepath, keep='head'):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if '<<<<<<< HEAD' not in content:
        print(f'Sin conflictos: {filepath}')
        return

    lines = content.split('\n')
    result = []
    in_head = False
    in_theirs = False

    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            in_head = True
            in_theirs = False
        elif line.startswith('======='):
            in_head = False
            in_theirs = True
        elif line.startswith('>>>>>>>'):
            in_theirs = False
        elif keep == 'head' and in_head:
            result.append(line)
        elif keep == 'theirs' and in_theirs:
            result.append(line)
        elif not in_head and not in_theirs:
            result.append(line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))
    print(f'Resuelto ({keep}): {filepath}')

for f in use_head:
    resolve(f, 'head')

for f in use_theirs:
    resolve(f, 'theirs')

print('Listo.')
