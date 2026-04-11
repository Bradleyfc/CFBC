# Instrucciones de Uso - Historial de Usuarios

## Cómo Usar la Nueva Funcionalidad

### Para Usuarios del Sistema (Secretaría)

1. **Acceder al Listado de Usuarios**
   - Inicia sesión con una cuenta del grupo "Secretaría"
   - Ve a tu perfil
   - Click en "Listado de Usuarios Registrados"

2. **Ver el Historial de un Usuario**
   - En la tabla de usuarios, verás una nueva columna llamada "Historial"
   - Cada fila tiene un botón verde "Ver Historial" con un icono de reloj
   - Click en el botón del usuario cuyo historial deseas ver

3. **Navegar el Modal de Historial**
   - Se abrirá un modal con la información del usuario
   - El modal muestra 5 secciones:
     * Solicitudes de Inscripción
     * Matrículas
     * Aplicaciones a Cursos
     * Cuentas Bancarias
     * Cursos como Profesor
   - Cada sección muestra el número de registros entre paréntesis
   - Si no hay datos, verás "No hay registros"

4. **Cerrar el Modal**
   - Click en el botón "Cerrar"
   - Click en la X en la esquina superior derecha
   - Click fuera del modal
   - Presiona la tecla ESC

### Información Mostrada

#### Solicitudes de Inscripción
- Curso solicitado
- Fecha de solicitud
- Estado (aprobado, pendiente, rechazado)
- Tabla de origen
- Fecha de consolidación

#### Matrículas
- Curso matriculado
- Edición del curso
- Fecha de inscripción
- Estado actual
- Nota final
- Número de ausencias
- Tabla de origen

#### Aplicaciones a Cursos
- Curso aplicado
- Edición
- Fecha de solicitud
- Estado
- Nota final
- Información de beca
- Estado de pago

#### Cuentas Bancarias
- Número de cuenta
- Banco
- Tabla de origen
- Fecha de consolidación

#### Cursos como Profesor
- Cursos donde el usuario es profesor
- Tabla de origen
- Fecha de consolidación

## Para Desarrolladores

### Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

### Verificar la Implementación

```bash
python verificar_implementacion_final.py
```

### Estructura de la Respuesta JSON

La vista `/historial-usuario/<user_id>/` retorna:

```json
{
  "usuario": {
    "nombre": "Nombre Completo",
    "email": "email@example.com",
    "username": "username"
  },
  "solicitudes_inscripcion": [...],
  "cuentas_bancarias": [...],
  "matriculas": [...],
  "aplicaciones": [...],
  "cursos_como_profesor": [...]
}
```

### Agregar Nuevos Campos al Historial

Si necesitas agregar más información al historial:

1. **Modificar la vista** (`principal/views.py`):
   ```python
   # En la función obtener_historial_usuario
   historial_data['nueva_seccion'] = []
   # Agregar lógica para obtener datos
   ```

2. **Actualizar el JavaScript** (`templates/usuarios_registrados.html`):
   ```javascript
   // En la función mostrarHistorial
   html += generarSeccionHistorial(
       'Título de Nueva Sección',
       'icono_material',
       data.nueva_seccion,
       [
           { key: 'campo1', label: 'Etiqueta 1' },
           { key: 'campo2', label: 'Etiqueta 2' }
       ]
   );
   ```

### Solución de Problemas

#### El botón no aparece
- Verifica que estés logueado como usuario del grupo "Secretaría"
- Limpia la caché del navegador (Ctrl+F5)

#### El modal no se abre
- Abre la consola del navegador (F12)
- Busca errores de JavaScript
- Verifica que la URL `/historial-usuario/<id>/` esté configurada

#### No se muestran datos
- Los datos históricos actuales no tienen usuarios vinculados
- Esto es normal y se corregirá en futuras consolidaciones
- El modal mostrará "No hay registros" en cada sección

#### Error 403 (Forbidden)
- Solo usuarios del grupo "Secretaría" pueden acceder
- Verifica que tu usuario esté en el grupo correcto

#### Error 404 (Not Found)
- El usuario solicitado no existe
- Verifica el ID del usuario

## Mantenimiento

### Futuras Consolidaciones de Datos

Cuando se consoliden nuevos datos históricos, las relaciones con usuarios se preservarán automáticamente gracias a las correcciones en `datos_archivados/historical_data_saver.py`.

El código ahora busca el ID de usuario en tres campos posibles:
- `student_id` (usado en datos antiguos)
- `user_id` (estándar)
- `usuario_id` (español)

### Backup

Se creó un backup del template original:
- `templates/usuarios_registrados_backup.html`

Si necesitas revertir los cambios, puedes restaurar desde este archivo.

## Soporte

Para reportar problemas o sugerencias:
1. Verifica primero con `python verificar_implementacion_final.py`
2. Revisa los logs del servidor Django
3. Consulta la documentación en `HISTORIAL_USUARIOS_IMPLEMENTACION.md`
