# Guía para Construir y Probar el APK de CFBC

## 📋 Prerequisitos

1. **Java Development Kit (JDK) 17** instalado
2. **Android Studio** instalado (opcional, pero recomendado)
3. **Servidor Django** corriendo en tu computadora

## 🎯 Opciones de Construcción

El proyecto soporta tres **flavors** (ambientes) diferentes:

### 1. **emulator** - Para Android Emulator
- **IP**: `10.0.2.2:8000`
- **Uso**: Pruebas en el emulador de Android Studio
- **Nota**: `10.0.2.2` es la IP especial que el emulador mapea a `127.0.0.1` de tu computadora

### 2. **wifi** - Para dispositivo físico en WiFi
- **IP**: `192.168.1.100:8000` (debes cambiarla)
- **Uso**: Pruebas en tu teléfono físico conectado a la misma red WiFi
- **Importante**: Actualiza la IP en `app/build.gradle.kts` con la IP real de tu computadora

### 3. **production** - Para servidor en internet
- **URL**: `https://cfbc.example.com`
- **Uso**: Despliegue en producción
- **Importante**: Actualiza con tu dominio real en `app/build.gradle.kts`

## 🚀 Comandos de Construcción

### Método Rápido (Scripts automatizados)

#### Windows:
```cmd
# Para emulador (modo debug)
build-apk.bat emulator debug

# Para dispositivo físico WiFi (modo debug)
build-apk.bat wifi debug

# Para producción (modo release)
build-apk.bat production release
```

#### Linux/Mac/WSL:
```bash
# Dar permisos de ejecución
chmod +x build-apk.sh

# Para emulador (modo debug)
./build-apk.sh emulator debug

# Para dispositivo físico WiFi (modo debug)
./build-apk.sh wifi debug

# Para producción (modo release)
./build-apk.sh production release
```

### Método Manual (Gradle directo)

#### Windows:
```cmd
# Emulador + Debug
gradlew.bat assembleEmulatorDebug

# WiFi + Debug
gradlew.bat assembleWifiDebug

# Production + Release
gradlew.bat assembleProductionRelease
```

#### Linux/Mac/WSL:
```bash
# Emulador + Debug
./gradlew assembleEmulatorDebug

# WiFi + Debug
./gradlew assembleWifiDebug

# Production + Release
./gradlew assembleProductionRelease
```

## 📦 Ubicación de los APKs

Los APKs se generan en:
```
app/build/outputs/apk/{flavor}/{buildType}/app-{flavor}-{buildType}.apk
```

Ejemplos:
- `app/build/outputs/apk/emulator/debug/app-emulator-debug.apk`
- `app/build/outputs/apk/wifi/debug/app-wifi-debug.apk`
- `app/build/outputs/apk/production/release/app-production-release.apk`

## 📲 Instalar el APK en tu dispositivo

### Desde línea de comandos:
```bash
adb install -r app/build/outputs/apk/emulator/debug/app-emulator-debug.apk
```

### Desde el teléfono directamente:
1. Copia el archivo APK a tu teléfono
2. Abre el archivo desde el explorador de archivos
3. Permite instalación de fuentes desconocidas si te lo pide

## 🔧 Configuración para tu entorno

### Para usar con Emulador (127.0.0.1:8000)

Ya está configurado por defecto. Solo asegúrate de:
1. Tu servidor Django esté corriendo en `127.0.0.1:8000`
2. Usa el flavor `emulator`

```bash
./build-apk.sh emulator debug
```

### Para usar con dispositivo físico

1. **Encuentra tu IP local**:
   - Windows: `ipconfig` (busca IPv4 Address)
   - Linux/Mac: `ifconfig` o `ip addr`
   
2. **Actualiza `app/build.gradle.kts`**:
   ```kotlin
   create("wifi") {
       dimension = "environment"
       // Cambia esta IP por la de tu computadora
       buildConfigField("String", "API_BASE_URL", "\"http://TU_IP_AQUI:8000/\"")
       buildConfigField("String", "WEB_BASE_URL", "\"http://TU_IP_AQUI:8000/\"")
       resValue("string", "env_name", "WiFi Local")
   }
   ```

3. **Configura Django para aceptar conexiones externas**:
   
   Edita `settings.py`:
   ```python
   ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'TU_IP_LOCAL']
   ```
   
   Inicia el servidor con:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. **Construye el APK**:
   ```bash
   ./build-apk.sh wifi debug
   ```

## 🔐 Para builds de Release (producción)

Los builds de release requieren un keystore para firmar la aplicación:

### 1. Crear el keystore:
```bash
keytool -genkey -v -keystore cfbc-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias cfbc-key
```

Responde las preguntas y **guarda la contraseña de forma segura**.

### 2. Configurar variables de entorno (opcional):
```bash
# Linux/Mac/WSL
export KEYSTORE_PASSWORD="tu_password"
export KEY_PASSWORD="tu_password"

# Windows CMD
set KEYSTORE_PASSWORD=tu_password
set KEY_PASSWORD=tu_password

# Windows PowerShell
$env:KEYSTORE_PASSWORD="tu_password"
$env:KEY_PASSWORD="tu_password"
```

### 3. Construir el APK firmado:
```bash
./build-apk.sh production release
```

## 🐛 Solución de Problemas

### Error: "Connection refused" o "Unable to connect"

**En Emulador:**
- ✅ Usa el flavor `emulator` (IP: 10.0.2.2)
- ✅ Verifica que Django esté corriendo en 127.0.0.1:8000
- ❌ NO uses 192.168.x.x en el emulador

**En Dispositivo Físico:**
- ✅ Usa el flavor `wifi`
- ✅ Actualiza la IP en build.gradle.kts
- ✅ Dispositivo y computadora en la misma red WiFi
- ✅ Django corriendo con `runserver 0.0.0.0:8000`
- ✅ Firewall no bloqueando el puerto 8000

### Error: "SDK location not found"

Crea el archivo `local.properties` en la raíz del proyecto Android:
```properties
sdk.dir=C\:\\Users\\TU_USUARIO\\AppData\\Local\\Android\\Sdk
```
(Ajusta la ruta según tu instalación de Android SDK)

### Error: "Keystore file not found" (builds release)

Primero crea el keystore con el comando `keytool` mostrado arriba.

## 📊 Logs y Debugging

Para ver los logs de la app mientras corre:
```bash
adb logcat | grep -i cfbc
```

O filtra por tu paquete:
```bash
adb logcat | grep "com.cfbc.android"
```

## 🎯 Recomendación para Pruebas Iniciales

Para tus primeras pruebas, usa:
```bash
./build-apk.sh emulator debug
```

Esto te permite:
- ✅ Probar rápidamente sin configurar IPs
- ✅ Ver logs detallados
- ✅ Usar el emulador de Android Studio
- ✅ No requiere keystore

Una vez que funcione, puedes probar en dispositivo físico con el flavor `wifi`.
