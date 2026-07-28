# 📱 Documentación Completa: Proyecto Android CFBC

**Fecha**: 28 de Julio de 2026  
**Versión App**: 1.0.0  
**Estado**: 🟢 Funcionalmente completo

---

## 📑 Índice de Documentación

Este documento sirve como índice central para toda la documentación del proyecto Android.

---

## 🎯 Documentos Principales

### Para Desarrolladores

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Estado del Proyecto** | `android-app/ESTADO_PROYECTO.md` | Estado actual, progreso, problemas conocidos |
| **README Android** | `android-app/README.md` | Documentación técnica completa de la app |
| **Plan de Tareas** | `.kiro/specs/android-app-blog-and-profiles/tasks.md` | Plan de implementación detallado (27 tareas) |
| **Requerimientos** | `.kiro/specs/android-app-blog-and-profiles/requirements.md` | Especificación de requerimientos funcionales |
| **Diseño** | `.kiro/specs/android-app-blog-and-profiles/design.md` | Arquitectura y diseño técnico |

### Para Construcción de APK

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Inicio Rápido** | `android-app/INICIO_RAPIDO.md` | Guía express para generar APK |
| **Guía de Construcción** | `android-app/GUIA_CONSTRUCCION_APK.md` | Guía completa con todas las opciones |
| **Guía Teléfono Físico** | `android-app/GUIA_TELEFONO_FISICO.md` | Configuración específica para dispositivos físicos |
| **Pasos para Teléfono** | `PASOS_PARA_TELEFONO.md` | Checklist rápido paso a paso |

### Para Problemas de Red

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Instrucciones WSL Network** | `INSTRUCCIONES_WSL_NETWORK.md` | Solución de port forwarding WSL→Windows |
| **Script Port Forward** | `configurar_wsl_portforward.ps1` | Script automático de configuración |
| **Script Firewall** | `permitir_puerto_8000.ps1` | Script para configurar firewall |

### Scripts de Utilidad

| Script | Ubicación | Propósito |
|--------|-----------|-----------|
| `build-apk.sh` | `android-app/build-apk.sh` | Build de APK (Linux/WSL) |
| `build-apk.bat` | `android-app/build-apk.bat` | Build de APK (Windows) |
| `runserver_red.sh` | `runserver_red.sh` | Iniciar Django para red WiFi |
| `runserver_red.bat` | `runserver_red.bat` | Iniciar Django para red WiFi (Windows) |

---

## 🏗️ Resumen de Arquitectura

### Backend: Django REST API

```
Django Project (CFBC)
├── blog/                    # App de blog
│   ├── models.py           # Noticia, Categoria, Comentario, etc.
│   ├── api_views.py        # BlogPostViewSet, CategoryViewSet
│   ├── serializers.py      # BlogPostSerializer, etc.
│   └── api_urls.py         # /api/v1/blog/*
│
├── principal/              # App principal
│   ├── models.py          # Curso, Registro, CourseApplication
│   ├── api_views.py       # CourseViewSet, StudentProfileViewSet
│   ├── serializers.py     # CourseSerializer, StudentProfileSerializer
│   └── api_urls.py        # /api/v1/courses/*, /api/v1/profile/*
│
├── cfbc/
│   ├── settings.py        # Configuración Django
│   │   └── ALLOWED_HOSTS = ['127.0.0.1', '192.168.1.101']
│   │   └── CORS_ALLOWED_ORIGINS = [...]
│   │   └── REST_FRAMEWORK = {...}
│   └── urls.py            # Rutas globales
│
└── API Endpoints
    ├── /api/v1/home/                  # Dashboard público
    ├── /api/v1/courses/               # Cursos
    ├── /api/v1/blog/posts/            # Blog público
    ├── /api/v1/auth/login/            # Autenticación
    ├── /api/v1/profile/               # Perfil estudiante
    ├── /api/v1/applications/          # Solicitudes de curso
    ├── /api/v1/blog/author/*          # Dashboard autor
    ├── /api/v1/blog/moderator/*       # Dashboard moderador
    └── /api/v1/blog/editor/*          # Dashboard editor
```

### Frontend: Android App

```
android-app/
├── app/build.gradle.kts            # Configuración build
│   ├── Product Flavors
│   │   ├── emulator (10.0.2.2:8000)
│   │   ├── wifi (192.168.1.101:8000)
│   │   └── production (cfbc.example.com)
│   └── Build Types
│       ├── debug (logging ON, pinning OFF)
│       └── release (logging OFF, pinning ON)
│
└── app/src/main/java/com/cfbc/android/
    ├── di/                         # Hilt modules
    │   ├── NetworkModule           # Retrofit, OkHttp
    │   ├── DatabaseModule          # Room
    │   └── RepositoryModule        # Repositories
    │
    ├── data/
    │   ├── local/                  # Room database
    │   │   ├── entities/           # BlogPostEntity, CourseEntity, etc.
    │   │   ├── dao/                # BlogPostDao, CourseDao, etc.
    │   │   └── CfbcDatabase        # Room database
    │   │
    │   ├── remote/                 # API layer
    │   │   ├── dto/                # DTOs (BlogPostDto, etc.)
    │   │   ├── CfbcApiService      # Retrofit service
    │   │   └── NetworkDataSource   # Wrapper
    │   │
    │   └── repository/             # Repository implementations
    │       ├── BlogRepositoryImpl
    │       ├── CourseRepositoryImpl
    │       ├── AuthRepositoryImpl
    │       ├── ProfileRepositoryImpl
    │       ├── ModeratorRepositoryImpl
    │       └── EditorRepositoryImpl
    │
    ├── domain/                     # Domain models
    │   ├── BlogPost, Category
    │   ├── Course, Enrollment
    │   ├── StudentProfile
    │   └── Mappers (DTO → Domain)
    │
    ├── infrastructure/
    │   ├── network/
    │   │   ├── AuthInterceptor     # Inyecta token
    │   │   └── NetworkModule       # Config Retrofit/OkHttp
    │   └── security/
    │       └── SecurityManager     # EncryptedSharedPreferences
    │
    └── presentation/               # UI Layer
        ├── auth/                   # LoginFragment, AuthViewModel
        ├── home/                   # HomeFragment, HomeViewModel
        ├── blog/                   # BlogListFragment, BlogViewModel
        ├── course/                 # CourseListFragment, CourseViewModel
        ├── profile/                # ProfileFragment, ProfileViewModel
        ├── author/                 # AuthorDashboardFragment
        ├── moderator/              # ModeratorDashboardFragment
        ├── editor/                 # EditorDashboardFragment
        └── MainActivity            # Navigation host
```

---

## ⚙️ Configuración Actual

### URLs Configuradas

| Componente | Configuración Actual |
|------------|---------------------|
| **Django settings.py** | `ALLOWED_HOSTS = ['127.0.0.1', '192.168.1.101']` |
| **Django CORS** | `CORS_ALLOWED_ORIGINS = ['http://192.168.1.101:8000']` |
| **Android flavor wifi** | `API_BASE_URL = "http://192.168.1.101:8000/"` |
| **IP Windows WiFi** | `192.168.1.101` |
| **IP WSL (variable)** | Se obtiene con `wsl -- hostname -I` |

### Comandos Rápidos

```bash
# Iniciar Django para red WiFi
cd ~/CFBC
./runserver_red.sh

# Generar APK para teléfono físico
cd ~/CFBC/android-app
./build-apk.sh wifi debug

# Instalar en dispositivo
adb install -r app/build/outputs/apk/wifi/debug/app-wifi-debug.apk
```

---

## 🚧 Estado Actual de Implementación

### ✅ Completado (85%)

| Fase | Estado | Notas |
|------|--------|-------|
| **Phase 1**: Setup & Infrastructure | ✅ 100% | Gradle, Hilt, Room, Retrofit configurados |
| **Phase 2**: Django REST API | ✅ 95% | Endpoints funcionando, faltan tests |
| **Phase 3**: Android Data Layer | ✅ 100% | Repositories, DTOs, mappers completos |
| **Phase 4-7**: Presentation Layer | ✅ 100% | Todos los ViewModels y Fragments |
| **Phase 8**: Error Handling & Security | ✅ 100% | Caching, seguridad, manejo de errores |

### ⚠️ Pendiente (15%)

| Tarea | Tipo | Prioridad |
|-------|------|-----------|
| Property tests (serialización) | Testing | Media |
| Integration tests (Django API) | Testing | Media |
| Unit tests (Repositories) | Testing | Baja |
| Unit tests (ViewModels) | Testing | Baja |
| **Port forwarding WSL** | **Configuración** | **🔴 Alta** |

---

## 🔥 Problema Crítico: Acceso de Red

### El Problema

Django corre en **WSL2** (red virtualizada), no accesible directamente desde Windows ni desde la red WiFi.

### Síntomas

- ✅ Django corre: `Starting development server at http://0.0.0.0:8000/`
- ❌ Windows no puede acceder: `http://192.168.1.101:8000`
- ❌ Teléfono no puede acceder: `http://192.168.1.101:8000`

### Solución

**Configurar port forwarding de WSL a Windows** (PowerShell como Admin):

```powershell
# 1. Obtener IP de WSL
$wslIp = wsl -- hostname -I | ForEach-Object { $_.Trim().Split()[0] }

# 2. Crear port forwarding
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp

# 3. Configurar firewall
New-NetFirewallRule -DisplayName "WSL Django Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# 4. Verificar
netsh interface portproxy show v4tov4
```

**Script automático**: `configurar_wsl_portforward.ps1`

⚠️ **Nota**: La configuración se pierde al reiniciar Windows.

**Documentación completa**: `INSTRUCCIONES_WSL_NETWORK.md`

---

## 📊 Métricas del Proyecto

### Código

- **Backend**: ~15 endpoints REST, 8 ViewSets, 12 serializadores
- **Android**: ~30 clases, 14 Fragments, 9 ViewModels, 9 Repositories
- **Arquitectura**: MVVM + Clean Architecture
- **Tecnologías**: Kotlin, Hilt, Retrofit, Room, Material Design

### Funcionalidades

| Módulo | Funciones | Estado |
|--------|-----------|--------|
| Autenticación | Login, Logout, Token storage | ✅ 100% |
| Blog Público | List, Detail, Search, Filter | ✅ 100% |
| Cursos Públicos | List, Detail, Filter | ✅ 100% |
| Dashboard Estudiante | Profile, Enrollments, Grades, etc. | ✅ 100% |
| Aplicación Cursos | Apply, Cancel, List | ✅ 100% |
| Dashboard Autor | My Posts, Create, Edit | ✅ 100% |
| Dashboard Moderador | Reports, Sanctions, Metrics | ✅ 100% |
| Dashboard Editor | Review Queue, Publish/Reject | ✅ 100% |
| Caching Offline | LRU, 50 posts max | ✅ 100% |
| Seguridad | HTTPS, Tokens, Pinning | ✅ 100% |

### Tests

- **Property tests**: 0/1 (0%)
- **Integration tests**: 0/1 (0%)
- **Unit tests Repositories**: 0/5 (0%)
- **Unit tests ViewModels**: 0/3 (0%)
- **Total cobertura tests**: ~0%

---

## 🎯 Próximos Pasos

### Inmediato (Para usar la app)

1. **Configurar port forwarding WSL** → Ver `INSTRUCCIONES_WSL_NETWORK.md`
2. **Generar APK**: `./build-apk.sh wifi debug`
3. **Instalar en teléfono**: `adb install app-wifi-debug.apk`
4. **Probar**: Login, navegación, blog, cursos

### Corto Plazo (Testing)

1. Implementar property tests de serialización
2. Implementar integration tests de API
3. Implementar unit tests de repositories
4. Implementar unit tests de ViewModels

### Mediano Plazo (Producción)

1. Configurar servidor de producción real
2. Actualizar URLs de producción
3. Crear keystore para firma
4. Build y test APK release
5. Publicar en Play Store (opcional)

---

## 📞 Contacto y Soporte

### Documentación

- Ver índice completo arriba
- Todos los documentos están en el repositorio

### Problemas Comunes

| Problema | Solución | Documento |
|----------|----------|-----------|
| Teléfono no conecta | Port forwarding WSL | `INSTRUCCIONES_WSL_NETWORK.md` |
| Build falla | Ver guía de construcción | `GUIA_CONSTRUCCION_APK.md` |
| IP cambió | Actualizar configs | `GUIA_TELEFONO_FISICO.md` |
| Django no inicia | Activar venv, runserver | `runserver_red.sh` |

---

## 📝 Changelog

### v1.0.0 (28 Julio 2026)

- ✅ Implementación completa de todas las funcionalidades
- ✅ Django REST API con 15 endpoints
- ✅ App Android con 9 módulos principales
- ✅ Caching offline con LRU eviction
- ✅ Seguridad con tokens y HTTPS
- ✅ Multi-environment build (emulator/wifi/production)
- ✅ Documentación completa creada
- ⚠️ Tests pendientes de implementación
- 🚧 Port forwarding WSL requiere configuración manual

---

**Última actualización**: 28 de Julio de 2026  
**Mantenedor**: Bradley  
**Proyecto**: CFBC - Centro Fray Bartolomé de las Casas  
**Estado**: 🟢 Funcionalmente completo, listo para pruebas
