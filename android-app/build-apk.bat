@echo off
REM Script para construir APKs de la aplicación CFBC Android (Windows)
REM Uso: build-apk.bat [emulator|wifi|production] [debug|release]

SET FLAVOR=%1
SET BUILD_TYPE=%2

IF "%FLAVOR%"=="" SET FLAVOR=emulator
IF "%BUILD_TYPE%"=="" SET BUILD_TYPE=debug

echo =========================================
echo   Construyendo APK CFBC
echo   Ambiente: %FLAVOR%
echo   Tipo: %BUILD_TYPE%
echo =========================================

REM Validar flavor
IF "%FLAVOR%"=="emulator" (
    echo [i] Ambiente: Android Emulator
    echo [^>] Conectara a: http://10.0.2.2:8000/
    echo [i] 10.0.2.2 es la IP especial del emulador que mapea a 127.0.0.1 del host
    SET GRADLE_TASK=assembleEmulatorDebug
    IF "%BUILD_TYPE%"=="release" SET GRADLE_TASK=assembleEmulatorRelease
    
) ELSE IF "%FLAVOR%"=="wifi" (
    echo [i] Ambiente: Dispositivo fisico en WiFi
    echo [^>] Conectara a: http://192.168.1.100:8000/
    echo [!] IMPORTANTE: Cambia la IP en app\build.gradle.kts si tu computadora tiene otra IP
    echo     Encuentra tu IP con: ipconfig
    SET GRADLE_TASK=assembleWifiDebug
    IF "%BUILD_TYPE%"=="release" SET GRADLE_TASK=assembleWifiRelease
    
) ELSE IF "%FLAVOR%"=="production" (
    echo [i] Ambiente: Produccion
    echo [^>] Conectara a: https://cfbc.example.com/
    echo [!] IMPORTANTE: Actualiza la URL en app\build.gradle.kts con tu dominio real
    SET GRADLE_TASK=assembleProductionDebug
    IF "%BUILD_TYPE%"=="release" SET GRADLE_TASK=assembleProductionRelease
    
) ELSE (
    echo [X] Flavor invalido: %FLAVOR%
    echo.
    echo Uso: build-apk.bat [emulator^|wifi^|production] [debug^|release]
    echo.
    echo Flavors disponibles:
    echo   emulator   - Para Android Emulator ^(10.0.2.2 -^> 127.0.0.1^)
    echo   wifi       - Para dispositivo fisico en WiFi local
    echo   production - Para servidor en internet
    echo.
    echo Build types:
    echo   debug   - APK con logging habilitado
    echo   release - APK optimizado para distribucion
    exit /b 1
)

echo.
echo [^>] Ejecutando: gradlew.bat %GRADLE_TASK%
echo.

call gradlew.bat %GRADLE_TASK%

IF %ERRORLEVEL% EQU 0 (
    SET APK_PATH=app\build\outputs\apk\%FLAVOR%\%BUILD_TYPE%\app-%FLAVOR%-%BUILD_TYPE%.apk
    
    echo.
    echo [OK] APK generado exitosamente!
    echo [^^>^^>] Ubicacion: %APK_PATH%
    echo.
    echo [^^>] Para instalarlo en tu dispositivo:
    echo    adb install -r %APK_PATH%
    echo.
    
    IF "%BUILD_TYPE%"=="release" (
        IF NOT EXIST "..\cfbc-release-key.jks" (
            echo [!] ADVERTENCIA: Si el build falla, necesitas crear un keystore:
            echo    keytool -genkey -v -keystore ..\cfbc-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias cfbc-key
            echo.
        )
    )
    
    echo [i] Consejos:
    echo    - Asegurate de que tu servidor Django este corriendo
    IF "%FLAVOR%"=="emulator" (
        echo    - El servidor debe estar en 127.0.0.1:8000 en tu computadora
    ) ELSE IF "%FLAVOR%"=="wifi" (
        echo    - El dispositivo y tu computadora deben estar en la misma red WiFi
        echo    - El servidor debe estar accesible en la red ^(no solo en 127.0.0.1^)
    )
) ELSE (
    echo.
    echo [X] Error al construir el APK
    exit /b 1
)
