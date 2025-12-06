@echo off
REM Script para eliminar la asociación de archivos .bbg con AnimeBBG Editor
REM Ejecutar como Administrador

echo ========================================
echo Eliminando asociación de archivos .bbg
echo ========================================
echo.

echo Eliminando registros de Windows...

REM Eliminar la asociación de extensión
reg delete "HKEY_CURRENT_USER\Software\Classes\.bbg" /f 2>nul
if errorlevel 1 (
    echo No se encontró la asociación .bbg ^(posiblemente ya está eliminada^)
) else (
    echo - Asociación .bbg eliminada
)

REM Eliminar el tipo de archivo
reg delete "HKEY_CURRENT_USER\Software\Classes\AnimeBBG.Project" /f 2>nul
if errorlevel 1 (
    echo No se encontró el tipo AnimeBBG.Project ^(posiblemente ya está eliminado^)
) else (
    echo - Tipo AnimeBBG.Project eliminado
)

echo.
echo ========================================
echo Asociación eliminada
echo ========================================
echo.
echo Los archivos .bbg ya no se abrirán automáticamente
echo con AnimeBBG Editor
echo.
pause
