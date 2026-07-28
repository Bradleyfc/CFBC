# 📱 Guía: Usar la App en tu Teléfono Físico

## ✅ Configuración completada

Tu sistema ya está configurado para usar con teléfono físico:
- **Tu IP WiFi**: `192.168.1.101`
- **URL del servidor**: `http://192.168.1.101:8000/`

## 🚀 Pasos para generar y probar el APK

### 1. Inicia Django para red WiFi

**Opción A - Desde WSL (Recomendado):**
```bash
cd ~/CFBC
./runserver_red.sh
```

**Opción B - Comando directo:**
```bash
cd ~/CFBC
python manage.py runserver 0.0.0.0:8000
```

**⚠️ Importante**: Debes usar `0.0.0.0:8000` en lugar de `127.0.0.1:8000` para que acepte conexiones de red.

### 2. Verifica que el servidor esté accesible

Desde tu teléfono, abre el navegador y ve a:
```
http://192.168.1.101:8000
```

Si ves tu sitio Django, ¡perfecto! Si no:
- Verifica que tu teléfono esté en la misma red WiFi
- Verifica que el firewall de Windows no esté bloqueando el puerto 8000

### 3. Construye el APK para WiFi

**Desde WSL:**
```bash
cd ~/CFBC/android-app
./build-apk.sh wifi debug
```

**Desde Windows CMD:**
```cmd
cd C:\ruta\a\CFBC\android-app
build-apk.bat wifi debug
```

El APK se generará en:
```
app/build/outputs/apk/wifi/debug/app-wifi-debug.apk
```

### 4. Instala el APK en tu teléfono

**Opción A - Con ADB (si está conectado por USB):**
```bash
adb install -r app/build/outputs/apk/wifi/debug/app-wifi-debug.apk
```

**Opción B - Directamente en el teléfono:**
1. Copia el archivo `app-wifi-debug.apk` a tu teléfono
2. Ábrelo desde el explorador de archivos
3. Permite instalación de fuentes desconocidas si te lo pide
4. Instala la app

### 5. Prueba la app

1. Abre la app CFBC en tu teléfono
2. Debería conectarse a `http://192.168.1.101:8000`
3. Intenta hacer login
4. Navega por las secciones

## 🔥 Configurar Firewall de Windows

Si tu teléfono no puede conectarse, probablemente necesites permitir el puerto 8000:

### Windows Defender Firewall:

1. Abre **Windows Defender Firewall con seguridad avanzada**
2. Click en **Reglas de entrada** > **Nueva regla...**
3. Tipo de regla: **Puerto**
4. Protocolo: **TCP**, Puerto específico: **8000**
5. Acción: **Permitir la conexión**
6. Perfil: Marcar **Privado** y **Público**
7. Nombre: `Django Development Server`

### O desde PowerShell (como administrador):

```powershell
New-NetFirewallRule -DisplayName "Django Dev Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

## 🐛 Solución de Problemas

### Error: "Unable to connect" o "Connection refused"

**Verificaciones:**

1. **Django corriendo correctamente:**
   ```bash
   # Debe decir "Starting development server at http://0.0.0.0:8000/"
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Misma red WiFi:**
   - Teléfono y computadora en la misma red
   - Verifica con: Settings > Wi-Fi (debe ser la misma red)

3. **Firewall no bloqueando:**
   - Prueba desde navegador del teléfono: `http://192.168.1.101:8000`
   - Si el navegador funciona pero la app no, el problema es la app
   - Si el navegador NO funciona, es problema de red/firewall

4. **IP correcta:**
   - Tu IP actual: `192.168.1.101`
   - Si cambió, actualiza en `app/build.gradle.kts` y recompila

### Error: "CORS" o "Cross-Origin"

Ya está configurado, pero verifica que `cfbc/settings.py` tenga:
```python
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1', '192.168.1.101']

CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://10.0.2.2:8000',
    'http://192.168.1.101:8000',  # Tu IP
]
```

### La app se cierra o crashea

Mira los logs:
```bash
adb logcat | grep -i cfbc
```

O filtra por el paquete:
```bash
adb logcat | grep "com.cfbc.android"
```

## 📊 Verificación de Red

### Desde WSL, prueba la conexión:
```bash
# Ver tu IP WSL
ip addr show eth0

# Probar conexión al servidor
curl http://192.168.1.101:8000
```

### Desde Windows, prueba la conexión:
```cmd
# Ver tu IP
ipconfig

# Probar si el puerto está abierto
netstat -an | findstr :8000
```

## 💡 Consejos

1. **Mantén Django corriendo** mientras usas la app
2. **No cierres la terminal** donde corre Django
3. **Verifica la IP** cada vez que reinicies tu computadora (puede cambiar)
4. **Usa la misma red WiFi** siempre

## 🔄 Si cambió tu IP

Si tu router te asignó una IP diferente:

1. **Encuentra la nueva IP:**
   ```cmd
   ipconfig
   ```
   (Busca "Adaptador de LAN inalámbrica Wi-Fi" > "Dirección IPv4")

2. **Actualiza** `app/build.gradle.kts`:
   ```kotlin
   create("wifi") {
       buildConfigField("String", "API_BASE_URL", "\"http://TU_NUEVA_IP:8000/\"")
       buildConfigField("String", "WEB_BASE_URL", "\"http://TU_NUEVA_IP:8000/\"")
   }
   ```

3. **Actualiza** `cfbc/settings.py`:
   ```python
   ALLOWED_HOSTS = [..., 'TU_NUEVA_IP']
   CORS_ALLOWED_ORIGINS = [..., 'http://TU_NUEVA_IP:8000']
   ```

4. **Recompila el APK:**
   ```bash
   ./build-apk.sh wifi debug
   ```

## ✅ Checklist Final

Antes de generar el APK, verifica:

- [ ] Django corriendo con `0.0.0.0:8000`
- [ ] Navegador del teléfono puede ver `http://192.168.1.101:8000`
- [ ] Teléfono y PC en la misma red WiFi
- [ ] Firewall permite puerto 8000
- [ ] `build.gradle.kts` tiene tu IP correcta
- [ ] `settings.py` tiene tu IP en ALLOWED_HOSTS y CORS

¡Todo listo para construir y probar tu APK! 🚀
