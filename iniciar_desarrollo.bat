@echo off
echo ========================================
echo      INICIANDO MODO DESARROLLO
echo ========================================
echo.

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo Abriendo 2 terminales:
echo - Terminal 1: Servidor Django (puerto 8000)
echo - Terminal 2: Tailwind Watch (compilacion automatica)
echo.

echo Presiona CTRL+C en cualquier terminal para detener
echo.

start "Django Server" cmd /k "venv\Scripts\activate.bat && python manage.py runserver"
start "Tailwind Watch" cmd /k "venv\Scripts\activate.bat && python manage.py tailwind --watch"

echo Terminales iniciadas! Revisa las ventanas abiertas.
pause