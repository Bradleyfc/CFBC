"""
Agregar savepoints individuales para cada operación de base de datos
"""

# Leer el archivo
with open('datos_archivados/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_combinar_function = False
line_count = 0

for i, line in enumerate(lines):
    line_count = i + 1
    
    # Detectar si estamos en la función combinar_datos_archivados
    if 'def combinar_datos_archivados(request):' in line:
        in_combinar_function = True
        new_lines.append(line)
        continue
    
    # Detectar fin de la función (siguiente def)
    if in_combinar_function and line.startswith('def ') and 'combinar_datos_archivados' not in line:
        in_combinar_function = False
    
    # Si estamos en la función, buscar los loops principales y agregar savepoints
    if in_combinar_function:
        # Para cada loop de datos, agregar transaction.atomic()
        if 'for dato in datos_auth_user:' in line:
            new_lines.append(line)
            # Agregar savepoint en la siguiente línea (después del try:)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])  # try:
                # Agregar with transaction.atomic() después del try
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada usuario\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_auth_user")
                # Saltar la siguiente línea porque ya la agregamos
                continue
        
        elif 'for dato in datos_user_groups:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada grupo\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_user_groups")
                continue
        
        elif 'for dato in datos_student_info:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada estudiante\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_student_info")
                continue
        
        elif 'for dato in datos_teacher_info:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada profesor\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_teacher_info")
                continue
        
        elif 'for dato in datos_cursos_academicos:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada curso académico\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_cursos_academicos")
                continue
        
        elif 'for dato in datos_cursos:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada curso\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_cursos")
                continue
        
        elif 'for dato in datos_matriculas:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada matrícula\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_matriculas")
                continue
        
        elif 'for dato in datos_asistencias:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada asistencia\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_asistencias")
                continue
        
        elif 'for dato in datos_calificaciones:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada calificación\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_calificaciones")
                continue
        
        elif 'for dato in datos_notas:' in line:
            new_lines.append(line)
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                new_lines.append(' ' * (indent + 4) + 'with transaction.atomic():  # Savepoint para cada nota\n')
                print(f"✅ Línea {i+2}: Agregado savepoint para datos_notas")
                continue
    
    new_lines.append(line)

# Guardar
with open('datos_archivados/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\n✅ Savepoints agregados exitosamente")
