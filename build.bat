@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM === Detecta 'py' o 'python' ===
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)

%PY% -V || (echo No se encontro Python. Agrega Python al PATH. & exit /b 1)

REM === venv limpio (opcional pero recomendado) ===
if not exist .venv (
  %PY% -m venv .venv
)
call .venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

REM === Icono opcional: busca primero assets\icons\app.ico y luego app.ico ===
set "ICON_OPT="
if exist "assets\icons\app.ico" (
  set "ICON_OPT=--icon ""assets\icons\app.ico"""
) else (
  if exist "app.ico" (
    set "ICON_OPT=--icon ""app.ico"""
  )
)

REM === Build onefile, GUI ===
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "EditorTyperTool-AnimeBBG" ^
  !ICON_OPT! ^
  "EditorTyperTool - AnimeBBG.py"

if errorlevel 1 (
  echo.
  echo *** ERROR: Fallo el build.
  exit /b 1
)

echo.
echo Build completo. Ejecutable en: dist\EditorTyperTool-AnimeBBG.exe
