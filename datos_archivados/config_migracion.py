# Configuración para optimizar el rendimiento de migración
# Especialmente importante para bases de datos grandes (>40,000 registros)

# Configuración de lotes para actualizaciones de progreso
LOTE_ACTUALIZACION_PROGRESO = 100  # Actualizar progreso cada 100 registros (era 50)
LOTE_CONTEO_REGISTROS = 5  # Contar registros migrados cada 5 tablas (era cada tabla)

# Configuración de timeouts
TIMEOUT_MIGRACION_MINUTOS = 45  # Aumentar timeout de 30 a 45 minutos
TIMEOUT_TABLA_MINUTOS = 10  # Timeout por tabla individual

# Configuración de cache
CACHE_TIMEOUT_SEGUNDOS = 1800  # 30 minutos
CACHE_UPDATE_INTERVAL = 3  # Actualizar cache cada 3 segundos

# Configuración de logging para bases de datos grandes
LOG_CADA_N_REGISTROS = 500  # Log cada 500 registros en lugar de cada 50

# Configuración de memoria
USAR_TRANSACCIONES_ATOMICAS = True  # Usar transacciones para mejor rendimiento
BATCH_SIZE_INSERCION = 100  # Insertar registros en lotes de 100

# Configuración específica para el modal de resumen
MOSTRAR_MODAL_AUTOMATICO = True  # Mostrar modal automáticamente al completar
RECARGAR_PAGINA_AUTOMATICO = False  # No recargar automáticamente, esperar acción del usuario

# Configuración de verificación de estado
INTERVALO_VERIFICACION_SEGUNDOS = 3  # Verificar estado cada 3 segundos
MAX_INTENTOS_RECONEXION = 3  # Máximo 3 intentos de reconexión

# Configuración para debugging
DEBUG_MIGRACION = False  # Activar solo para debugging
VERBOSE_LOGGING = False  # Logging detallado solo si es necesario