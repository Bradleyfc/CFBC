# 🚀 Inicio Rápido - APK CFBC

## Para generar APK de prueba AHORA MISMO:

### Desde WSL/Linux:
```bash
cd android-app
./build-apk.sh emulator debug
```

### Desde Windows CMD:
```cmd
cd android-app
build-apk.bat emulator debug
```

## ✅ Lo que necesitas:

1. **Servidor Django corriendo**:
   ```bash
   python manage.py runserver
   ```
   (Debe estar en 127.0.0.1:8000)

2. **APK se generará en**:
   ```
   app/build/outputs/apk/emulator/debug/app-emulator-debug.apk
   ```

3. **Instalar en emulador**:
   ```bash
   adb install -r app/build/outputs/apk/emulator/debug/app-emulator-debug.apk
   ```

## 🎯 Cambios importantes que hice:

### 1. Configuré 3 ambientes (flavors):
- **emulator**: Para Android Emulator (10.0.2.2 → tu 127.0.0.1:8000) ✅
- **wifi**: Para teléfono físico en tu WiFi (necesitas tu IP local)
- **production**: Para servidor en internet (necesitas dominio)

### 2. IP especial para emulador:
En lugar de `127.0.0.1`, el emulador usa **`10.0.2.2`** que mapea automáticamente a `127.0.0.1` de tu computadora host.

### 3. Scripts automáticos:
- `build-apk.sh` (Linux/WSL)
- `build-apk.bat` (Windows)

## 📱 Prueba en Emulador vs Teléfono Real

| Característica | Emulador | Teléfono Real |
|---|---|---|
| **IP a usar** | 10.0.2.2:8000 | Tu IP local (ej: 192.168.1.100:8000) |
| **Flavor** | `emulator` | `wifi` |
| **Django runserver** | `127.0.0.1:8000` | `0.0.0.0:8000` |
| **Configuración extra** | Ninguna ✅ | Cambiar IP en build.gradle.kts |

## 🔧 Si quieres probar en tu teléfono físico:

1. **Encuentra tu IP**:
   ```cmd
   ipconfig
   ```
   Busca algo como: `192.168.1.100`

2. **Edita** `app/build.gradle.kts`:
   ```kotlin
   create("wifi") {
       dimension = "environment"
       buildConfigField("String", "API_BASE_URL", "\"http://192.168.1.100:8000/\"")  // <-- TU IP
       buildConfigField("String", "WEB_BASE_URL", "\"http://192.168.1.100:8000/\"")  // <-- TU IP
       resValue("string", "env_name", "WiFi Local")
   }
   ```

3. **Configura Django** para aceptar conexiones de red:
   
   En `settings.py`:
   ```python
   ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '192.168.1.100']  # Agrega tu IP
   ```

4. **Inicia Django** escuchando en todas las interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

5. **Construye el APK**:
   ```bash
   ./build-apk.sh wifi debug
   ```

## ❓ ¿Cuál debo usar?

- **Para empezar y probar**: `emulator debug` ✅
  - Más fácil, no requiere configuración
  - Funciona con tu servidor en 127.0.0.1

- **Para probar en tu teléfono**: `wifi debug`
  - Requiere cambiar IP en código
  - Requiere configurar Django para red

- **Para subir a Play Store**: `production release`
  - Requiere dominio real en internet
  - Requiere keystore para firma

## 🆘 Ayuda

Ver documentación completa: [GUIA_CONSTRUCCION_APK.md](./GUIA_CONSTRUCCION_APK.md)
