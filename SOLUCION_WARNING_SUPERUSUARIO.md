# 🔧 Solución - Warning al Crear Superusuario

## ❌ Problema
Al ejecutar `python3 manage.py createsuperuser` aparece este warning:
```
RuntimeWarning: Accessing the database during app initialization is discouraged. 
To fix this warning, avoid executing queries in AppConfig.ready() or when your app modules are imported.
```

## ✅ Solución Aplicada

He corregido el problema eliminando las consultas de base de datos del método `AppConfig.ready()`. Ahora los grupos se crean **solo** a través del signal `post_migrate`.

### 🔧 Cambios Realizados

1. **Eliminé** la verificación de grupos en `principal/apps.py`
2. **Mejoré** el signal `post_migrate` en `principal/signals.py`
3. **Creé** un comando manual para crear grupos: `crear_grupos_sistema.py`

## 🚀 Cómo Crear el Superusuario Ahora

### Paso 1: Crear Superusuario (Sin Warning)
```bash
python3 manage.py createsuperuser
```

### Paso 2: Crear Grupos del Sistema
```bash
python3 manage.py crear_grupos_sistema
```

### Paso 3: Verificar que Todo Funciona
```bash
python3 manage.py verificar_grupos
```

## 🎯 Alternativas para Crear Grupos

### Opción 1: Comando Manual (Recomendado)
```bash
python3 manage.py crear_grupos_sistema
```

### Opción 2: Ejecutar Migraciones
```bash
python3 manage.py migrate
```
Los grupos se crean automáticamente con el signal `post_migrate`.

### Opción 3: Script Independiente
```bash
python3 configurar_grupos_sistema.py
```

### Opción 4: Forzar Recreación
```bash
python3 manage.py crear_grupos_sistema --force
```

## 🔍 Verificar Grupos Creados

### En el Admin de Django
```
http://localhost:8000/admin/auth/group/
```

### Por Comando
```bash
python3 manage.py verificar_grupos
```

### Script de Prueba
```bash
python3 test_grupos.py
```

## 📋 Grupos que se Crean

1. **Administración**
2. **Blog Autor**
3. **Blog Moderador**
4. **Editor**
5. **Estudiantes**
6. **Profesores**
7. **Secretaría**

## ✅ Resultado

- ✅ **Sin warnings** al crear superusuario
- ✅ **Grupos se crean** automáticamente con migraciones
- ✅ **Comando manual** disponible si es necesario
- ✅ **Sistema robusto** que no falla la inicialización

---

**¡El warning está solucionado!** 🎉