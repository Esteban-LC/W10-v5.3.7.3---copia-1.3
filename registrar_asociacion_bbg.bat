@echo off
REM Script para registrar la asociación de archivos .bbg con AnimeBBG Editor
REM Ejecutar como Administrador

echo ========================================
echo Registrando AnimeBBG Editor para archivos .bbg
echo ========================================
echo.

REM Obtener la ruta actual del script
set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%dist\EditorTyperTool-AnimeBBG.exe"

REM Verificar si existe el ejecutable
if not exist "%EXE_PATH%" (
    echo ERROR: No se encontró el ejecutable en:
    echo %EXE_PATH%
    echo.
    echo Por favor, asegúrate de haber compilado la aplicación primero.
    pause
    exit /b 1
)

echo Ejecutable encontrado: %EXE_PATH%
echo.

REM Registrar la extensión .bbg
echo Registrando extensión .bbg...
reg add "HKEY_CURRENT_USER\Software\Classes\.bbg" /ve /d "AnimeBBG.Project" /f
if errorlevel 1 (
    echo ERROR: No se pudo registrar la extensión .bbg
    pause
    exit /b 1
)

REM Registrar el tipo de archivo
echo Registrando tipo de archivo AnimeBBG.Project...
reg add "HKEY_CURRENT_USER\Software\Classes\AnimeBBG.Project" /ve /d "Proyecto AnimeBBG" /f
if errorlevel 1 (
    echo ERROR: No se pudo registrar el tipo de archivo
    pause
    exit /b 1
)

REM Registrar el icono
echo Registrando icono...
reg add "HKEY_CURRENT_USER\Software\Classes\AnimeBBG.Project\DefaultIcon" /ve /d "%EXE_PATH%,0" /f

REM Registrar el comando para abrir
echo Registrando comando de apertura...
reg add "HKEY_CURRENT_USER\Software\Classes\AnimeBBG.Project\shell\open\command" /ve /d "\"%EXE_PATH%\" \"%%1\"" /f
if errorlevel 1 (
    echo ERROR: No se pudo registrar el comando de apertura
    pause
    exit /b 1
)

REM Actualizar el cache de Windows
echo.
echo Actualizando cache del sistema...
echo Se recomienda reiniciar el Explorador de Windows para ver los cambios.
echo.

echo ========================================
echo ¡Registro completado exitosamente!
echo ========================================
echo.
echo Ahora puedes hacer doble clic en archivos .bbg
echo para abrirlos directamente con AnimeBBG Editor
echo.
echo NOTA: Si no ves los cambios inmediatamente:
echo 1. Cierra todas las ventanas del Explorador
echo 2. Reinicia el Explorador de Windows (Ctrl+Shift+Esc, Procesos, reiniciar "Explorador de Windows")
echo 3. O reinicia el equipo
echo.
pause
