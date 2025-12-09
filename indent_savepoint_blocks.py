"""
Indentar el código dentro de cada bloque with transaction.atomic()
"""

# Leer el archivo
with open('datos_archivados/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_savepoint_block = False
savepoint_indent = 0
block_start_line = 0

for i, line in enumerate(lines):
    # Detectar inicio de bloque savepoint
    if 'with transaction.atomic():  # Savepoint para cada' in line:
        in_savepoint_block = True
        savepoint_indent = len(line) - len(line.lstrip())
        block_start_line = i
        new_lines.append(line)
        print(f"📍 Línea {i+1}: Inicio de bloque savepoint (indent={savepoint_indent})")
        continue
    
    # Si estamos en un bloque savepoint
    if in_savepoint_block:
        # Detectar fin del bloque (except o siguiente for/def)
        current_indent = len(line) - len(line.lstrip()) if line.strip() else savepoint_indent + 4
        
        # Fin del bloque: except al mismo nivel que el try original
        if line.strip().startswith('except ') and current_indent <= savepoint_indent:
            in_savepoint_block = False
            new_lines.append(line)
            print(f"📍 Línea {i+1}: Fin de bloque savepoint")
            continue
        
        # Si la línea tiene contenido y está dentro del bloque
        if line.strip():
            # Agregar 4 espacios de indentación extra
            new_lines.append('    ' + line)
        else:
            # Líneas vacías sin cambios
            new_lines.append(line)
    else:
        new_lines.append(line)

# Guardar
with open('datos_archivados/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\n✅ Indentación aplicada exitosamente")
