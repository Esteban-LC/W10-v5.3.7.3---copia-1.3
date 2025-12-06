# ✅ Sistema de Instancia Única - COMPLETADO

## Problema Resuelto

❌ **Antes**: Hacer doble clic en archivos .bbg abría múltiples ventanas, cada una pidiendo login

✅ **Ahora**: Solo 1 ventana, todos los archivos se abren como pestañas, login solo 1 vez

## Implementación

### Cambios Realizados

1. **Agregada clase `SingleInstanceManager`** 
   - Usa `QLocalServer`/`QLocalSocket` para comunicación entre procesos
   - Detecta si ya hay una instancia corriendo
   - Envía archivos a la instancia existente

2. **Modificado `main()`**
   - Verifica instancia existente ANTES del login
   - Si existe → envía archivos y termina (sin login)
   - Si no existe → continúa con login normalmente
   - Inicia servidor para recibir archivos futuros

3. **Agregado import `QLocalServer`, `QLocalSocket`**

## Cómo Funciona

```
┌─────────────────────────────────────┐
│ Usuario hace doble clic en .bbg    │
└──────────────┬──────────────────────┘
               │
          ¿Ya hay app abierta?
               │
       ┌───────┴───────┐
       │ SÍ            │ NO
       │               │
   Enviar archivo  Abrir nueva ventana
   a ventana       + Login
   existente       + Iniciar servidor
       │               │
   Terminar        Abrir archivo
   (sin login)
```

## Pruebas Necesarias

Después de recompilar:

1. **Test básico**: Abre la app, luego doble clic en un .bbg → debe abrirse como pestaña
2. **Test múltiple**: Selecciona 3 archivos .bbg y abre → todos como pestañas
3. **Test no-login**: Con app abierta, ejecuta el .exe de nuevo → NO debe pedir login

## Próximos Pasos

1. **Recompilar el ejecutable**:
   ```bash
   pyinstaller "EditorTyperTool - AnimeBBG.spec"
   ```

2. **Registrar la asociación** (si aún no lo hiciste):
   ```bash
   registrar_asociacion_bbg.bat  # Ejecutar como administrador
   ```

3. **Probar**:
   - Doble clic en archivos .bbg
   - Verificar que se abren en la misma ventana
   - Verificar que solo pide login una vez
