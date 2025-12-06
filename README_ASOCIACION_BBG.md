# Asociación de Archivos .bbg con AnimeBBG Editor

## Descripción

Este sistema permite que Windows asocie automáticamente los archivos `.bbg` con AnimeBBG Editor, permitiendo abrirlos con doble clic.

## Archivos Incluidos

- **`registrar_asociacion_bbg.bat`**: Script para registrar la asociación
- **`desregistrar_asociacion_bbg.bat`**: Script para eliminar la asociación
- **Modificación en `EditorTyperTool - AnimeBBG.py`**: Acepta argumentos de línea de comandos

## Instrucciones de Uso

### Opción 1: Usando el Ejecutable (.exe)

Si ya has compilado la aplicación con PyInstaller:

1. **Asegúrate** que existe el archivo: `dist\EditorTyperTool-AnimeBBG.exe`
2. **Clic derecho** en `registrar_asociacion_bbg.bat`
3. Selecciona **"Ejecutar como administrador"**
4. Espera a que aparezca el mensaje de éxito
5. **Reinicia el Explorador de Windows** (o reinicia el equipo)

Ahora al hacer doble clic en cualquier archivo `.bbg` se abrirá con AnimeBBG Editor.

### Opción 2: Usando Python directamente (.py)

Si ejecutas la aplicación con Python sin compilar:

1. Edita `registrar_asociacion_bbg.bat`
2. Cambia la línea:
   ```batch
   set "EXE_PATH=%SCRIPT_DIR%dist\EditorTyperTool-AnimeBBG.exe"
   ```
   Por:
   ```batch
   set "EXE_PATH=C:\Users\TuUsuario\AppData\Local\Programs\Python\Python313\pythonw.exe"
   ```
3. Cambia la línea del comando por:
   ```batch
   reg add "HKEY_CURRENT_USER\Software\Classes\AnimeBBG.Project\shell\open\command" /ve /d "\"C:\Path\To\pythonw.exe\" \"C:\Path\To\EditorTyperTool - AnimeBBG.py\" \"%%1\"" /f
   ```
   (Reemplaza las rutas con las correctas)

### Para Desinstalar la Asociación

1. **Clic derecho** en `desregistrar_asociacion_bbg.bat`
2. Selecciona **"Ejecutar como administrador"**
3. Los archivos `.bbg` volverán a su estado anterior

## Cómo Funciona

### 1. Modificación del Código Python

La función `main()` ahora procesa argumentos de línea de comandos:

```python
# Procesar archivos .bbg pasados como argumentos de línea de comandos
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        file_path = Path(arg)
        if file_path.exists() and file_path.suffix.lower() == '.bbg':
            win._open_single_project_bbg(str(file_path))
```

Cuando Windows ejecuta la aplicación con un archivo, lo pasa como argumento: `app.exe "archivo.bbg"`

### 2. Registro en Windows

El script `registrar_asociacion_bbg.bat` modifica el registro de Windows para:

- **Asociar la extensión .bbg** con el tipo "AnimeBBG.Project"
- **Definir el comando de apertura** para ejecutar la aplicación con el archivo como parámetro
- **Asignar el icono** de la aplicación a los archivos .bbg

## Verificación

Después de ejecutar el registro:

1. Navega a una carpeta con archivos `.bbg`
2. Observa que tienen el icono de AnimeBBG Editor
3. Haz **doble clic** en un archivo `.bbg`
4. **Resultado esperado**: La aplicación se abre y carga el proyecto automáticamente

## Solución de Problemas

### Los archivos .bbg no tienen el icono correcto

- Reinicia el Explorador de Windows (Ctrl+Shift+Esc → Procesos → Explorador de Windows → Reiniciar)
- O reinicia el equipo

### Al hacer doble clic no pasa nada

1. Verifica que el ejecutable existe en `dist\EditorTyperTool-AnimeBBG.exe`
2. Ejecuta `desregistrar_asociacion_bbg.bat` y luego `registrar_asociacion_bbg.bat` nuevamente
3. Verifica en el Registro de Windows: `HKEY_CURRENT_USER\Software\Classes\.bbg`

### El archivo se abre pero no carga el proyecto

- Verifica que el código modificado en `main()` se ejecutó correctamente
- Asegúrate de haber recompilado la aplicación después de modificar el código

## Notas Técnicas

- **Alcance del registro**: `HKEY_CURRENT_USER` (solo para el usuario actual)
- **No requiere permisos de administrador** para la asociación básica
- **Seguro**: No modifica configuraciones del sistema, solo del usuario
- **Reversible**: Usa `desregistrar_asociacion_bbg.bat` para revertir cambios
