#!/bin/bash

# Script para construir APKs de la aplicación CFBC Android
# Uso: ./build-apk.sh [emulator|wifi|production] [debug|release]

FLAVOR=${1:-emulator}
BUILD_TYPE=${2:-debug}

echo "========================================="
echo "  Construyendo APK CFBC"
echo "  Ambiente: $FLAVOR"
echo "  Tipo: $BUILD_TYPE"
echo "========================================="

# Validar flavor
case "$FLAVOR" in
    emulator)
        echo "📱 Ambiente: Android Emulator"
        echo "🔗 Conectará a: http://10.0.2.2:8000/"
        echo "ℹ️  10.0.2.2 es la IP especial del emulador que mapea a 127.0.0.1 del host"
        ;;
    wifi)
        echo "📱 Ambiente: Dispositivo físico en WiFi"
        echo "🔗 Conectará a: http://192.168.1.100:8000/"
        echo "⚠️  IMPORTANTE: Cambia la IP en app/build.gradle.kts si tu computadora tiene otra IP"
        echo "   Encuentra tu IP con: ipconfig (Windows) o ifconfig (Linux/Mac)"
        ;;
    production)
        echo "📱 Ambiente: Producción"
        echo "🔗 Conectará a: https://cfbc.example.com/"
        echo "⚠️  IMPORTANTE: Actualiza la URL en app/build.gradle.kts con tu dominio real"
        ;;
    *)
        echo "❌ Flavor inválido: $FLAVOR"
        echo ""
        echo "Uso: ./build-apk.sh [emulator|wifi|production] [debug|release]"
        echo ""
        echo "Flavors disponibles:"
        echo "  emulator   - Para Android Emulator (10.0.2.2 → 127.0.0.1)"
        echo "  wifi       - Para dispositivo físico en WiFi local"
        echo "  production - Para servidor en internet"
        echo ""
        echo "Build types:"
        echo "  debug   - APK con logging habilitado"
        echo "  release - APK optimizado para distribución"
        exit 1
        ;;
esac

# Construir el comando gradle
GRADLE_TASK="assemble${FLAVOR^}${BUILD_TYPE^}"

echo ""
echo "🔨 Ejecutando: ./gradlew $GRADLE_TASK"
echo ""

./gradlew $GRADLE_TASK

if [ $? -eq 0 ]; then
    APK_PATH="app/build/outputs/apk/$FLAVOR/$BUILD_TYPE/app-$FLAVOR-$BUILD_TYPE.apk"
    
    echo ""
    echo "✅ APK generado exitosamente!"
    echo "📦 Ubicación: $APK_PATH"
    echo ""
    echo "📲 Para instalarlo en tu dispositivo:"
    echo "   adb install -r $APK_PATH"
    echo ""
    
    if [ "$BUILD_TYPE" = "release" ] && [ ! -f "../cfbc-release-key.jks" ]; then
        echo "⚠️  ADVERTENCIA: Si el build falla, necesitas crear un keystore:"
        echo "   keytool -genkey -v -keystore ../cfbc-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias cfbc-key"
        echo ""
    fi
    
    echo "💡 Consejos:"
    echo "   - Asegúrate de que tu servidor Django esté corriendo"
    if [ "$FLAVOR" = "emulator" ]; then
        echo "   - El servidor debe estar en 127.0.0.1:8000 en tu computadora"
    elif [ "$FLAVOR" = "wifi" ]; then
        echo "   - El dispositivo y tu computadora deben estar en la misma red WiFi"
        echo "   - El servidor debe estar accesible en la red (no solo en 127.0.0.1)"
    fi
else
    echo ""
    echo "❌ Error al construir el APK"
    exit 1
fi
