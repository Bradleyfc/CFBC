@echo off
REM Script para iniciar Django accesible desde la red WiFi local
REM Necesario para que la app Android en dispositivo físico pueda conectarse

echo =========================================
echo   Iniciando Django Server para Red WiFi
echo =========================================
echo.
echo [i] Servidor accesible en:
echo    - http://127.0.0.1:8000 (local)
echo    - http://192.168.1.101:8000 (red WiFi)
echo.
echo [+] Tu app Android debe usar:
echo    http://192.168.1.101:8000
echo.
echo [!] Firewall: Asegurate que el puerto 8000 este permitido
echo.
echo =========================================
echo.

REM Iniciar Django escuchando en todas las interfaces de red
python manage.py runserver 0.0.0.0:8000
