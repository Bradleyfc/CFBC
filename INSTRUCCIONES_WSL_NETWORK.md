# 🌐 Solución: Django en WSL accesible desde la red

## El Problema

Django corre en **WSL** (Linux virtualizado), pero WSL2 usa una red interna que no es accesible directamente desde Windows ni desde tu red WiFi. Por eso ni tu navegador de Windows ni tu teléfono pueden conectarse.

## ✅ La Solución: Port Forwarding

Necesitamos "reenviar" el puerto 8000 de WSL a Windows para que sea accesible.

---

## 🚀 PASOS PARA CONFIGURAR

### 1. Ejecuta el script de configuración

**Abre PowerShell como ADMINISTRADOR:**
- Presiona `Windows + X`
- Selecciona "Windows PowerShell (Admin)" o "Terminal (Admin)"

**Navega al proyecto:**
```powershell
cd \\wsl.localhost\Ubuntu-24.04\home\bradley\CFBC
```

**Ejecuta el script:**
```powershell
.\configurar_wsl_portforward.ps1
```

Este script:
- ✅ Detecta la IP de WSL
- ✅ Detecta tu IP de Windows WiFi (192.168.1.101)
- ✅ Configura port forwarding automáticamente
- ✅ Configura el firewall

---

### 2. Verifica que Django esté corriendo

En tu terminal de WSL (donde corre Django), debería decir:
```
Starting development server at http://0.0.0.0:8000/
```

Si no está corriendo, inícialo:
```bash
cd ~/CFBC
./runserver_red.sh
```

---

### 3. Prueba la conexión

**Desde el navegador de Windows:**
```
http://localhost:8000
```
O
```
http://192.168.1.101:8000
```

**Desde tu teléfono:**
```
http://192.168.1.101:8000
```

Si funciona en Windows pero no en el teléfono, verifica que estén en la misma WiFi.

---

## 🔄 Cada vez que reinicies Windows

La configuración de port forwarding se pierde al reiniciar. Necesitas:

1. **Iniciar Django en WSL:**
   ```bash
   cd ~/CFBC
   ./runserver_red.sh
   ```

2. **Ejecutar el script de port forwarding** (PowerShell como Admin):
   ```powershell
   cd \\wsl.localhost\Ubuntu-24.04\home\bradley\CFBC
   .\configurar_wsl_portforward.ps1
   ```

---

## 🐛 Solución de Problemas

### Error: "No se pudo obtener la IP de WSL2"

WSL no está corriendo. Inicia WSL:
```cmd
wsl
```

### Error: "Access denied" al ejecutar el script

No ejecutaste PowerShell como Administrador. Click derecho > "Ejecutar como administrador"

### Funciona en Windows pero NO en el teléfono

1. **Verifica que estén en la misma WiFi:**
   - Teléfono: Settings > WiFi > Nombre de red
   - PC: Windows Settings > Network > WiFi > Nombre de red
   - Deben ser la misma

2. **Verifica tu IP actual:**
   ```powershell
   ipconfig
   ```
   Busca "Adaptador de LAN inalámbrica Wi-Fi" > "Dirección IPv4"
   
   Si cambió de `192.168.1.101`, actualiza:
   - `android-app/app/build.gradle.kts`
   - `cfbc/settings.py` (ALLOWED_HOSTS y CORS)

3. **Firewall de tu router:**
   Algunos routers bloquean comunicación entre dispositivos. Busca "AP Isolation" en la configuración del router y desactívalo.

### Django no responde después de configurar

Reinicia el servidor Django:
1. Detén Django (Ctrl+C en la terminal)
2. Vuelve a iniciar:
   ```bash
   ./runserver_red.sh
   ```

---

## 📋 Resumen del flujo

```
[Teléfono] --WiFi--> [Router] 
                      |
                      v
              [Windows: 192.168.1.101:8000]
                      |
              [Port Forward]
                      |
                      v
              [WSL: 172.x.x.x:8000]
                      |
                      v
              [Django Server]
```

---

## 💡 Alternativa: Ejecutar Django directamente en Windows

Si el port forwarding te da problemas, otra opción es ejecutar Django directamente en Windows (no en WSL):

1. Instala Python en Windows
2. Crea un entorno virtual en Windows
3. Ejecuta Django desde CMD/PowerShell
4. En ese caso `runserver 0.0.0.0:8000` funcionará directamente

Pero con el script de port forwarding debería funcionar perfectamente desde WSL.
