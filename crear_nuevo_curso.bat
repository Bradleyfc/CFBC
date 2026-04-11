@echo off
echo ======================================================
echo Aplicando migraciones para los cambios en el modelo...
echo ======================================================
python manage.py makemigrations
python manage.py migrate
echo.
echo ======================================================
echo Creando nuevo curso academico...
echo ======================================================
python manage.py nuevo_curso
echo.
echo ======================================================
echo Proceso completado!
echo ======================================================
echo.
echo Recuerde que puede gestionar los cursos academicos desde el panel de administración.
echo - Activar/desactivar cursos
echo - Archivar cursos antiguos
echo - Ver historico de cursos
echo.
pause