@echo off
echo ========================================
echo    SETUP AUTOMATICO DEL PROYECTO
echo ========================================
echo.

echo [1/5] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)

echo [2/5] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [3/5] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo [4/5] Configurando Tailwind CSS...
python manage.py tailwind
if errorlevel 1 (
    echo ERROR: No se pudo compilar Tailwind CSS
    pause
    exit /b 1
)

echo [5/5] Aplicando migraciones...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: No se pudieron aplicar las migraciones
    pause
    exit /b 1
)

echo.
echo ========================================
echo        SETUP COMPLETADO! 🎉
echo ========================================
echo.
echo Para ejecutar el proyecto:
echo 1. Activar entorno: venv\Scripts\activate
echo 2. Servidor Django: python manage.py runserver
echo 3. Tailwind Watch: python manage.py tailwind --watch
echo.
pause