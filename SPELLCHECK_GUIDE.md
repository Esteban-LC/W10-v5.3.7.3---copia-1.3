# 📝 Guía de Corrección Ortográfica

## ¿Qué es la corrección ortográfica?

Se ha agregado un sistema automático de **verificación y corrección de errores ortográficos en español** a tu editor. El sistema detecta palabras mal escritas, incluyendo:

- Errores simples: `accion` → `acción`
- Plurales: `estudiante` → `estudiantes` (detecta si es singular cuando debería ser plural)
- Conjugaciones: `gramatica` → `gramática`
- Tildes y acentos faltantes: `ortografia` → `ortografía`

### Diferencia con versión anterior:
A diferencia de otros correctores simples, **LanguageTool entiende la gramática española** y detecta:
- ✅ Plurales y singulares incorrectos
- ✅ Tiempos verbales
- ✅ Acentos y tildes
- ✅ Errores de ortografía complejos

## ¿Cómo funciona?

### 1. **Detección Automática en Tiempo Real**
Cuando escribes en el diálogo de "Pegar texto", las palabras con errores ortográficos aparecerán **subrayadas en rojo ondulado** automáticamente.

### 2. **Sugerencias Inteligentes**
- **Cuando pasas el cursor** sobre una palabra subrayada, el sistema muestra sugerencias de corrección en la barra de estado
- Ejemplo: `"accion"` → Sugerencias: `acción, facción, acciona`
- Las sugerencias están ordenadas por probabilidad (la primera es la más probable)

### 3. **Corrección Manual con Diálogo**
Haz clic en el botón **"🔍 Revisar Ortografía"** para abrir el diálogo de corrección interactivo.

#### Opciones de corrección:
- **Reemplazar**: Corrige solo la ocurrencia actual de la palabra
- **Reemplazar todo**: Corrige todas las ocurrencias en el texto
- **Ignorar**: Salta la palabra sin corregir

#### Características:
- Las palabras mal escritas se muestran en una lista con sus 3 mejores sugerencias
- Selecciona la palabra que deseas corregir
- Elige la sugerencia correcta del desplegable
- Aplica el cambio deseado

## Ejemplo de uso:

### Caso 1: Plurales
```
Entrada: "Globo 1: Los estudiente son inteligentes"
Palabra detectada: "estudiente"
Sugerencias: "estudiantes", "estudiante", "estúdiente"
Selecciona: "estudiantes"
Resultado: "Globo 1: Los estudiantes son inteligentes"
```

### Caso 2: Acentos faltantes
```
Entrada: "N/T: La acion fue importante"
Palabra detectada: "acion"
Sugerencias: "acción", "facción", "acciona"
Selecciona: "acción"
Resultado: "N/T: La acción fue importante"
```

## 📊 Ejemplos de Detección

| Error Original | Sugerencias (Top 3) | Corrección |
|---|---|---|
| `estudiente` | estudiante, estudiantes, estúdiente | ✅ estudiantes (plural) |
| `accion` | acción, facción, acciona | ✅ acción |
| `gramatica` | Gramática, Dramática, Gramatical | ✅ Gramática |
| `ortografia` | ortografía, ortografiá, orografía | ✅ ortografía |
| `Los estudiantes van` | - | ✓ Sin errores |

## Lenguajes soportados

Por defecto, el corrector funciona en **español (es-ES)**.

Si necesitas cambiar a otro idioma (requiere reiniciar la app):
1. Edita el archivo `EditorTyperTool - AnimeBBG.py`
2. Busca la línea: `self.spell_checker = LanguageTool('es-ES')`
3. Cambia `'es-ES'` al código de idioma deseado:
   - `'en-US'` para inglés (USA)
   - `'en-GB'` para inglés (Reino Unido)
   - `'fr-FR'` para francés
   - `'de-DE'` para alemán
   - `'it-IT'` para italiano
   - `'pt-BR'` para portugués (Brasil)
   - etc.

## Requisitos

- Python 3.10+
- `language-tool-python>=2.7.1` (se instala automáticamente)
- Conexión a internet (para descargar el diccionario la primera vez)

## Si el corrector no funciona

### "Función no disponible - El corrector ortográfico no está disponible"
**Solución**: Instala `language-tool-python`:
```powershell
pip install language-tool-python
```

### Las palabras no aparecen subrayadas
1. Asegúrate de que `language-tool-python` esté instalado
2. Reinicia la aplicación
3. Escribe una palabra claramente mal escrita como `"ortografia"` (sin acento)

### Errores de conexión o descargas lentas
- **Causa**: La primera vez que inicia, LanguageTool descarga ~255 MB del diccionario
- **Solución**: Espera a que termine la descarga (unos 30 segundos aproximadamente)
- **Nota**: Las siguientes veces será más rápido (usa caché local)

### El corrector sugiere palabras muy similares pero no la correcta
- **Nota**: Esto puede ocurrir con palabras muy deformadas
- **Consejo**: Intenta escribir palabras más cercanas a la correcta
- Ejemplo: `"estudnte"` (muy corto) vs `"estduiante"` (más parecida a "estudiante")

## ⚙️ Notas Técnicas

### Cambiar idioma:

Por defecto, el corrector es en **español (es-ES)**. Para cambiar:

1. Abre `EditorTyperTool - AnimeBBG.py`
2. Busca esta línea en la clase `SpellCheckTextEdit`:
   ```python
   self.spell_checker = LanguageTool('es-ES')
   ```
3. Cambia `'es-ES'` al idioma deseado

### Desempeño:
- Primera ejecución: ~30 segundos (descarga de diccionario)
- Verificaciones posteriores: Casi instantáneo (<100ms)
- Caché: Se guarda en `~/.cache/LanguageTool/`

## 📝 Notas Importantes

1. ✅ **No destructivo**: El corrector solo sugiere cambios, nunca los aplica automáticamente
2. ✅ **Español gramaticalmente correcto**: Entiende plurales, tiempos verbales, conjugaciones
3. ✅ **Integrado**: Se abre directamente desde el diálogo de pegar texto
4. ✅ **Inteligente**: Usa LanguageTool (herramienta profesional de código abierto)
5. ✅ **Rápido**: La verificación es casi instantánea después de la primera carga

## 🎓 Cómo instalar desde cero

Si necesitas instalar todo desde el principio:

```powershell
# Cambiar a la carpeta del proyecto
cd "d:\DD - Descargas\Typper\AnimeBbg\Typeador\W10-v5.3.7.3 - copia 1.3"

# Instalar las dependencias
pip install -r requirements.txt

# Ejecutar la app
python "EditorTyperTool - AnimeBBG.py"
```

¡Disfruta de la corrección ortográfica inteligente! 🎉
