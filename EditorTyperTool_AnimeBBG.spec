# -*- mode: python ; coding: utf-8 -*-
# Spec minimalista (sin assets). Icono se maneja por linea de comandos en build.bat.

block_cipher = None

a = Analysis(
    ['EditorTyperTool - AnimeBBG.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='EditorTyperTool-AnimeBBG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
