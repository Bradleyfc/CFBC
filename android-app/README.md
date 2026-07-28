# CFBC Android App

Aplicación móvil Android para el Centro Fray Bartolomé de las Casas (CFBC). Proporciona acceso a cursos, blog, perfiles de estudiantes y paneles de gestión de contenido con autenticación segura y caché offline.

## 📋 Requisitos

| Herramienta | Versión |
|---|---|
| **Android Studio** | Hedgehog (2023.1.1) o superior |
| **JDK** | 17 (Amazon Corretto 17, Eclipse Temurin 17, o JetBrains Runtime 17) |
| **Gradle** | 8.5 (incluido via wrapper) |
| **Android SDK** | API 34 (compileSdk), API 24 (minSdk) |
| **Kotlin** | 1.9.22 |

## 🚀 Inicio Rápido

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd cfbc/android-app
```

### 2. Generar el wrapper de Gradle (solo si no existe)

```bash
gradle wrapper --gradle-version 8.5
```

### 3. Compilar

```bash
# Debug (conexión a servidor local)
./gradlew assembleDebug

# Release (producción)
./gradlew assembleRelease

# Staging
./gradlew assembleStaging
```

### 4. Instalar en dispositivo/emulador

```bash
# Instalar debug APK
./gradlew installDebug
```

## 🏗️ Arquitectura

El proyecto sigue **MVVM + Clean Architecture** con las siguientes capas:

```
com.cfbc
├── android/         # Capa de presentación (Android framework)
│   └── presentation/
│       ├── adapter/         # Adaptadores RecyclerView
│       ├── author/          # Dashboard de autor
│       ├── blog/            # Blog público
│       ├── courses/         # Cursos
│       ├── editor/          # Dashboard de editor
│       ├── home/            # Pantalla principal
│       ├── login/           # Autenticación
│       ├── moderator/       # Dashboard de moderador
│       ├── profile/         # Perfil de estudiante
│       └── student/         # Secciones WebView
│
├── app/              # Capa de datos y dominio (independiente de Android)
│   ├── data/
│   │   ├── local/           # Room database, DAOs, entidades
│   │   ├── model/           # Modelos Result (Success/Error/Loading)
│   │   ├── remote/          # NetworkDataSource
│   │   └── repository/      # Repositorios (Blog, Auth, Course, etc.)
│   ├── infrastructure/
│   │   ├── network/         # Retrofit, OkHttp, AuthInterceptor
│   │   └── security/        # EncryptedSharedPreferences
│   └── presentation/
│       ├── model/           # UiModels, UiState, UiEvent
│       └── viewmodel/       # ViewModels (Auth, Blog, Course, etc.)
```

### Principios

- **Offline-first**: Los repositorios intentan la red primero, fallback a caché local
- **Cache LRU**: Posts del blog cacheados (máx. 50 posts o 30 días)
- **Token seguro**: Almacenado en EncryptedSharedPreferences (Android Keystore)
- **Hilt DI**: Inyección de dependencias con Dagger Hilt
- **MVVM**: ViewModels exponen StateFlow + eventos one-shot (Channel)

## 🔧 Build Variants

El proyecto tiene **3 variantes de compilación** que configuran automáticamente las URLs y opciones:

| Variante | API_BASE_URL | Certificate Pinning | Logging | ID de App |
|---|---|---|---|---|
| **debug** | `http://192.168.1.100:8000/` | ❌ Deshabilitado | ✅ Activado | `com.cfbc.android.debug` |
| **staging** | `https://staging.cfbc.example.com/` | ✅ Habilitado | ✅ Activado | `com.cfbc.android.staging` |
| **release** | `https://cfbc.example.com/` | ✅ Habilitado | ❌ Deshabilitado | `com.cfbc.android` |

### Configurar IP Local (Desarrollo)

Para desarrollo local, cambia la IP en `app/build.gradle.kts`:

```kotlin
debug {
    buildConfigField("String", "API_BASE_URL", "\"http://TU_IP_LOCAL:8000/\"")
}
```

O ejecuta el servidor Django con:

```bash
# En el directorio del proyecto Django
cd /ruta/a/CFBC
python manage.py runserver 0.0.0.0:8000
```

## 📡 API Endpoints

Todos los endpoints usan `Accept: application/json; version=1.0` en el header.

### 🔓 Públicos (sin autenticación)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/v1/home/` | Inicio: cursos disponibles (10) + últimas noticias (5) |
| `GET` | `/api/v1/courses/` | Lista de cursos (paginado, filtrar por `area`, `tipo`) |
| `GET` | `/api/v1/courses/{id}/` | Detalle de curso |
| `GET` | `/api/v1/blog/posts/` | Posts publicados (paginado, filtrar por `categoria`, `destacada`, `search`) |
| `GET` | `/api/v1/blog/posts/{slug}/` | Detalle de post (por slug o ID) |
| `GET` | `/api/v1/blog/categories/` | Lista de categorías |

### 🔐 Autenticación

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/v1/auth/login/` | Login: `{"username", "password"}` → devuelve `token`, `username`, `groups` |
| `POST` | `/api/v1/auth/logout/` | Logout (requiere `Authorization: Token <token>`) |

### 👤 Perfil de Estudiante (requiere token)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/v1/profile/` | Perfil del usuario autenticado |
| `PATCH` | `/api/v1/profile/` | Actualizar perfil (campos editables) |
| `GET` | `/api/v1/enrollments/` | Matrículas del usuario |
| `GET` | `/api/v1/grades/` | Calificaciones |
| `GET` | `/api/v1/attendance/` | Asistencias (opcional `?course=ID`) |
| `GET` | `/api/v1/evaluations/` | Evaluaciones |
| `GET` | `/api/v1/history/` | Historial académico |

### 📝 Solicitudes de Cursos (requiere token)

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/v1/applications/` | Solicitar inscripción: `{"course": ID}` |
| `GET` | `/api/v1/applications/` | Listar mis solicitudes |
| `GET` | `/api/v1/applications/{id}/` | Detalle de solicitud |
| `POST` | `/api/v1/applications/{id}/cancel/` | Cancelar solicitud pendiente |

### ✍️ Blog - Autor (requiere grupo "Blog Autor")

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/v1/blog/author/posts/` | Mis posts |
| `GET` | `/api/v1/blog/author/posts/by-status/{estado}/` | Filtrar por estado |
| `POST` | `/api/v1/blog/author/posts/` | Crear post (como borrador) |
| `PATCH` | `/api/v1/blog/author/posts/{id}/` | Actualizar post |
| `DELETE` | `/api/v1/blog/author/posts/{id}/` | Eliminar borrador |

### 🛡️ Blog - Moderador (requiere grupo "Blog Moderador")

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/v1/blog/moderator/reports/` | Reportes pendientes |
| `POST` | `/api/v1/blog/moderator/reports/{id}/approve/` | Aprobar reporte (oculta comentario) |
| `POST` | `/api/v1/blog/moderator/reports/{id}/reject/` | Rechazar reporte |
| `GET` | `/api/v1/blog/moderator/sanctions/` | Sanciones activas |
| `GET` | `/api/v1/blog/moderator/metrics/` | Métricas de la comunidad |

### 📰 Blog - Editor (requiere grupo "Editor")

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/v1/blog/editor/posts/pending_review/` | Posts pendientes de revisión |
| `GET` | `/api/v1/blog/editor/posts/recently_published/` | Posts publicados (últimos 7 días) |
| `GET` | `/api/v1/blog/editor/posts/` | Buscar posts por autor (`?search=username`) |
| `POST` | `/api/v1/blog/editor/posts/{id}/publish/` | Publicar post |
| `POST` | `/api/v1/blog/editor/posts/{id}/reject/` | Rechazar post (con notas) |
| `PATCH` | `/api/v1/blog/editor/posts/{id}/update_notes/` | Actualizar notas del editor |

## 📦 Dependencias Principales

| Librería | Versión | Propósito |
|---|---|---|
| **Kotlin** | 1.9.22 | Lenguaje principal |
| **Hilt** | 2.50 | Inyección de dependencias |
| **Retrofit** | 2.9.0 | Cliente HTTP |
| **OkHttp** | 4.12.0 | Capa de red (logging, pinning) |
| **Room** | 2.6.1 | Base de datos local (SQLite) |
| **Navigation** | 2.7.7 | Navegación entre fragments |
| **Coil** | 2.5.0 | Carga de imágenes asíncrona |
| **Material Design** | 1.11.0 | Componentes UI |
| **Security Crypto** | 1.1.0-alpha06 | EncryptedSharedPreferences |
| **Kotlinx Serialization** | 1.6.2 | Serialización JSON |
| **Kotest** | 5.8.0 | Testing (unit + property-based) |
| **MockK** | 1.13.9 | Mocking para tests |

## 🧪 Testing

### Tests Unitarios (JVM)

```bash
./gradlew testDebugUnitTest
```

### Tests de Instrumentación (Android)

```bash
# Requiere emulador o dispositivo
./gradlew connectedDebugAndroidTest
```

### Cobertura de Tests

| Tipo | Framework | Cobertura |
|---|---|---|
| **Property-based** | Kotest Property Testing | Serialización JSON round-trip |
| **Unit tests** | Kotest + MockK | ViewModels, Repositorios |
| **Integration** | MockWebServer | Endpoints API |
| **UI** | Espresso | Flujos de usuario |

## 🗺️ Navegación

La app usa **Navigation Component** con 14 destinos:

```
loginFragment → homeFragment (hub principal)
                    ├── coursesListFragment → courseDetailFragment
                    ├── blogListFragment → blogPostFragment
                    ├── profileFragment → studentSectionsFragment (WebView)
                    ├── applicationsListFragment
                    ├── authorDashboardFragment → blogEditorFragment / blogPostFragment
                    └── moderatorDashboardFragment
                    └── editorDashboardFragment → blogPostFragment
```

### Control de Acceso por Roles

Las cards de dashboard en la pantalla principal se muestran según el grupo del usuario:

| Grupo | Cards Visibles |
|---|---|
| Sin autenticar | Cursos, Blog |
| Estudiantes | + Solicitudes, Perfil |
| Blog Autor | + Dashboard Autor |
| Blog Moderador | + Dashboard Moderador |
| Editor | + Dashboard Editor |

## 🔒 Seguridad

- **Token JWT/Token**: Almacenado en `EncryptedSharedPreferences` (cifrado AES-256 con Android Keystore)
- **Certificate Pinning**: Activado en producción (OkHttp CertificatePinner)
- **HTTPS obligatorio**: En producción, todas las conexiones usan HTTPS
- **Contraseñas**: Nunca se almacenan localmente
- **Timeout de sesión**: Re-autenticación requerida después de 5 minutos en background
- **ProGuard**: Ofuscación y minificación en release builds

## 💾 Caché Offline

| Tipo de Dato | Límite de Caché | Política de Evicción |
|---|---|---|
| Posts del blog | 50 posts o 30 días | LRU (least recently viewed) |
| Cursos | Ilimitado | Reemplazo en nueva carga |
| Perfil | 1 por usuario | Reemplazo en nueva carga |
| Matrículas | Ilimitado | Reemplazo en nueva carga |

## 🐛 Solución de Problemas

### Error: `Related model 'principal.semestrecurso' cannot be resolved`

Al ejecutar tests de Django, asegúrate de que la migración `evaluaciones/0007` dependa de `principal/0021_semestrecurso`, no de `principal/0001_initial`.

### Error: `null value in column "categoria_id"`

Al crear posts vía API, el campo `categoria_id` es requerido (opcional). Si no se proporciona, se asigna la primera categoría disponible. Usa `PrimaryKeyRelatedField` (no `IntegerField`) para validar que la categoría existe.

### Error: Versión inválida en header "Accept"

Todos los endpoints requieren el header: `Accept: application/json; version=1.0`

## 📚 Recursos Adicionales

- [Spec del Proyecto](../.kiro/specs/android-app-blog-and-profiles/tasks.md) — Lista detallada de tareas
- [Documentación Django API](../docs/) — Documentación del backend
- [Wiki del Proyecto](https://github.com/...) — Wiki del proyecto
