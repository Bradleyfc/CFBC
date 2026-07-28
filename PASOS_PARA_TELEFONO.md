# 📱 PASOS RÁPIDOS: App en Teléfono Físico

## Tu configuración:
- **IP WiFi de tu PC**: `192.168.1.101`
- **URL servidor**: `http://192.168.1.101:8000/`

---

## 🚀 Sigue estos pasos en orden:

### PASO 1: Inicia el servidor Django en modo red
```bash
cd ~/CFBC
./runserver_red.sh
```

O manualmente:
```bash
python manage.py runserver 0.0.0.0:8000
```

**⚠️ IMPORTANTE**: Usa `0.0.0.0:8000` NO `127.0.0.1:8000`

Deberías ver:
```
Starting development server at http://0.0.0.0:8000/
```

---

### PASO 2: Verifica que tu teléfono puede conectarse

Desde el **navegador de tu teléfono**, ve a:
```
http://192.168.1.101:8000
```

✅ **Si funciona**: Ves tu sitio Django → Continúa al Paso 3

❌ **Si NO funciona**: Lee la sección "Solución de Problemas" abajo

---

### PASO 3: Construye el APK para WiFi

```bash
cd ~/CFBC/android-app
./build-apk.sh wifi debug
```

Esto tomará unos minutos. El APK se generará en:
```
app/build/outputs/apk/wifi/debug/app-wifi-debug.apk
```

---

### PASO 4: Instala el APK en tu teléfono

**Opción A - Con cable USB (ADB):**
```bash
adb install -r app/build/outputs/apk/wifi/debug/app-wifi-debug.apk
```

**Opción B - Directamente:**
1. Copia `app-wifi-debug.apk` a tu teléfono (por USB, email, etc.)
2. Abre el archivo en tu teléfono
3. Permite instalación de fuentes desconocidas
4. Instala

---

### PASO 5: Prueba la app

1. Abre **CFBC Debug** en tu teléfono
2. Intenta hacer login
3. Navega por las secciones

---

## 🆘 Solución de Problemas

### ❌ El navegador del teléfono NO puede conectarse

**Verifica:**

1. **Misma red WiFi:**
   - Teléfono y PC conectados a la misma red WiFi
   - Ve a Ajustes > WiFi en tu teléfono

2. **Firewall de Windows:**
   
   Ejecuta como **Administrador** en PowerShell:
   ```powershell
   New-NetFirewallRule -DisplayName "Django Dev" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```

3. **Django corriendo:**
   ```bash
   # Verifica que diga "0.0.0.0:8000" NO "127.0.0.1:8000"
   python manage.py runserver 0.0.0.0:8000
   ```

4. **Prueba desde Windows:**
   Abre navegador en tu PC y ve a:
   ```
   http://192.168.1.101:8000
   ```
   Si funciona en PC pero no en teléfono → Problema de firewall

---

### ❌ La app crashea o no conecta

**Ver logs:**
```bash
adb logcat | grep -i cfbc
```

**Verifica que el APK sea el correcto:**
- Debe decir "WiFi" en algún lugar de la app
- Si dice "Emulator", compilaste el flavor incorrecto

**Recompila si es necesario:**
```bash
cd ~/CFBC/android-app
./build-apk.sh wifi debug
```

---

### ⚠️ "Connection refused" en la app

1. **Django debe estar corriendo** mientras usas la app
2. **Usa 0.0.0.0:8000** no 127.0.0.1:8000
3. **Verifica la IP** no cambió:
   ```cmd
   ipconfig
   ```
   (Busca "Wi-Fi" > "Dirección IPv4")

---

## 📋 Checklist antes de construir APK

- [ ] Django corriendo con `runserver 0.0.0.0:8000`
- [ ] Navegador del teléfono ve `http://192.168.1.101:8000` ✅
- [ ] Teléfono y PC en la misma WiFi ✅
- [ ] Firewall permite puerto 8000 ✅

Si todos tienen ✅, ejecuta:
```bash
cd ~/CFBC/android-app
./build-apk.sh wifi debug
```

---

## 📚 Más información

- Guía detallada: `android-app/GUIA_TELEFONO_FISICO.md`
- Guía construcción: `android-app/GUIA_CONSTRUCCION_APK.md`
- Inicio rápido: `android-app/INICIO_RAPIDO.md`

---

## 💡 Tip Final

Si tu IP cambia en el futuro (común en redes WiFi):
1. Ve a `android-app/app/build.gradle.kts`
2. Busca `create("wifi")`
3. Actualiza las URLs con tu nueva IP
4. Recompila el APK

¡Buena suerte! 🚀
