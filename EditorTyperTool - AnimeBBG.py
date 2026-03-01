# -*- coding: utf-8 -*-
"""
MangaTextTool – Multi-Tab (v3.30, Marca de agua movible/redimensionable) + Tema,
Toolbar compacta, login por Discord/Sheets, ventana "Nosotros" y checkbox de Negrita.

Cambios vs v3.29:
- NUEVO: WatermarkItem (QGraphicsPixmapItem) con asa de redimensión y arrastre.
- La marca de agua ahora se puede mover y hacer más grande/chica directamente en el lienzo.
- Sin cambios de comportamiento en el resto del flujo.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from copy import deepcopy
import json, math, sys, re, os, base64
import urllib.request
import urllib.error
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Callable
import socket
import platform
from datetime import datetime, timezone
import webbrowser
from pathlib import Path
import threading
from queue import Queue
import zipfile
import shutil


from PyQt6.QtCore import Qt, QPointF, QRectF, QSettings, QBuffer, QByteArray, QIODevice, QSize, QTimer, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import (
    QAction, QColor, QFont, QGuiApplication, QImage, QPainter, QIcon,
    QPixmap, QTextCursor, QTextDocument, QTextOption, QShortcut, QKeySequence,
    QUndoStack, QUndoCommand, QTextBlockFormat, QPen, QCursor, QLinearGradient, QBrush,
    QFontDatabase, QTextCharFormat, QAbstractTextDocumentLayout, QPalette, QFontMetricsF, QTransform, QPainterPath
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QGraphicsDropShadowEffect, QGraphicsItem,
    QGraphicsPixmapItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView,
    QLabel, QMainWindow, QMessageBox, QPushButton, QSlider, QSpinBox, QToolBar,
    QDockWidget, QListWidget, QListWidgetItem, QFormLayout, QCheckBox, QWidget,
    QVBoxLayout, QDialog, QTextEdit, QDialogButtonBox, QColorDialog, QFontDialog,
    QTabWidget, QTabBar, QHBoxLayout, QComboBox, QDoubleSpinBox, QGridLayout, QStyleFactory,
    QToolButton, QStyle, QLineEdit, QFrame, QScrollArea, QMenu
)

# Import automated workflow module
try:
    from automated_workflow import WorkflowWizard, WorkflowData, TextBoxDetection
    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False
    print("[WARNING] automated_workflow module not found. Workflow features disabled.")

# Import pyspellchecker for Spanish
try:
    from spellchecker import SpellChecker
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False
    print("[WARNING] pyspellchecker not available. Spell checking disabled.")
# Import PSD support
try:
    from psd_tools import PSDImage
    PSD_AVAILABLE = True
except ImportError:
    PSD_AVAILABLE = False
    print("[WARNING] psd-tools not available. PSD import disabled.")



# Carpeta base del script
BASE_DIR = Path(__file__).resolve().parent

# Directorio de assets (ajústalo si tu ruta es diferente)
ASSETS = BASE_DIR / "assets"

# Links para los botones de la ventana "Nosotros"
ABOUT_LINKS = {
    "WEB": "https://animebbg.net/",
    "DISCORD": "https://discord.gg/knazKVcF",
    "PAYPAL": "https://animebbg.net/pages/donacion/",
}

# ---- Actualizaciones (GitHub Releases + version.json) ----
UPDATE_JSON_URL = "https://raw.githubusercontent.com/Esteban-LC/W10-v5.3.7.3---copia-1.3/main/version.json"

def _get_local_version() -> str:
    """Lee la version desde version.json local (empaquetado con PyInstaller o script)."""
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller extrae archivos a _MEIPASS
            base_path = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
        else:
            base_path = Path(__file__).parent
        version_file = base_path / "version.json"
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return str(data.get("version", "0.0.0")).strip()
    except Exception:
        pass
    return "0.0.0"

APP_VERSION = _get_local_version()

# ---------------- Control de accesos (Apps Script Web App) ----------------
# URL del Web App publicado en Apps Script (execute as: Me, acceso: Anyone)
ACCESS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwi41rSnEl522mfxqcFCco19JFIoz9dlN_nSp8zjphKvpMnVapxC3KitzdYCcmBF2uP-A/exec"

def check_user_exists_and_log(username: str) -> bool:
    """
    Verifica usuario via Apps Script Web App.
    Si existe, el script registra el log y devuelve ok=True.
    """
    username = username.strip()
    if not username:
        return False
    if not ACCESS_WEBAPP_URL:
        return False

    # Datos del dispositivo para el log remoto
    hostname = platform.node()
    system_str = platform.platform()
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip_local = "desconocida"

    payload = {
        "username": username,
        "ip": ip_local,
        "host": hostname,
        "system": system_str,
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            ACCESS_WEBAPP_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        result = json.loads(raw) if raw else {}
        return bool(result.get("ok"))
    except Exception:
        return False

# ---------------- Iconos ----------------
def _assets_dir() -> Path:
    base = getattr(sys, '_MEIPASS', None)
    return (Path(base) / 'assets') if base else Path(__file__).resolve().parent / 'assets'

ASSETS = _assets_dir()
print(f"[MangaTextTool] ASSETS dir: {ASSETS}")

def _emoji_icon(txt: str, size: int = 24) -> QIcon:
    pm = QPixmap(size, size); pm.fill(Qt.GlobalColor.transparent)
    qp = QPainter(pm); f = QFont('Segoe UI Emoji', int(size*0.8)); qp.setFont(f)
    qp.drawText(pm.rect(), int(Qt.AlignmentFlag.AlignCenter), txt); qp.end()
    return QIcon(pm)

def icon(name: str) -> QIcon:
    p = ASSETS / 'icons' / name
    if p.exists():
        # Preferir carga directa de QIcon (mejor para .ico multi-resolución)
        ic = QIcon(str(p))
        if not ic.isNull():
            return ic
        # Fallback para plataformas/plugins que no lean bien .ico directo
        pix = QPixmap(str(p))
        if not pix.isNull():
            ic = QIcon(pix)
            if not ic.isNull():
                return ic
    std_map = {
        'open.png': QStyle.StandardPixmap.SP_DirOpenIcon,
        'open-proj.png': QStyle.StandardPixmap.SP_DirOpenIcon,
        'save-proj.png': QStyle.StandardPixmap.SP_DialogSaveButton,
        'save.png': QStyle.StandardPixmap.SP_DialogSaveButton,
        'upload.png': QStyle.StandardPixmap.SP_ArrowUp,
        'trash.png': QStyle.StandardPixmap.SP_TrashIcon,
        'undo.png': QStyle.StandardPixmap.SP_ArrowBack,
        'redo.png': QStyle.StandardPixmap.SP_ArrowForward,
        'export.png': QStyle.StandardPixmap.SP_DriveHDIcon,
        'export-all.png': QStyle.StandardPixmap.SP_DriveHDIcon,
        'duplicate.png': QStyle.StandardPixmap.SP_FileIcon,
        'paste.png': QStyle.StandardPixmap.SP_DialogYesButton,
        'font.png': QStyle.StandardPixmap.SP_FileDialogDetailedView,
        'lock.png': QStyle.StandardPixmap.SP_DialogNoButton,
        'pin.png': QStyle.StandardPixmap.SP_DialogApplyButton,
        'pin-all.png': QStyle.StandardPixmap.SP_DialogApplyButton,
        'unlock.png': QStyle.StandardPixmap.SP_DialogResetButton,
        'auto.png': QStyle.StandardPixmap.SP_BrowserReload,
        'help.png': QStyle.StandardPixmap.SP_DialogHelpButton,
        'panel.png': QStyle.StandardPixmap.SP_ComputerIcon,
        'raw.png': QStyle.StandardPixmap.SP_FileIcon,
        'app.ico': QStyle.StandardPixmap.SP_DesktopIcon,
        'sun.png': QStyle.StandardPixmap.SP_DialogOpenButton,
        'moon.png': QStyle.StandardPixmap.SP_DialogCancelButton
    }
    try:
        if name in std_map:
            return QApplication.style().standardIcon(std_map[name])
    except Exception:
        pass
    emoji_map = {
        'open.png': '📂', 'open-proj.png': '📂', 'save-proj.png': '💾', 'save.png': '💾',
        'upload.png': '⤴️', 'trash.png': '🗑️', 'undo.png': '↩️', 'redo.png': '↪️',
        'export.png': '📤', 'export-all.png': '📤', 'duplicate.png': '🗐', 'paste.png': '📋',
        'font.png': '🔤', 'lock.png': '🔒', 'pin.png': '📌', 'pin-all.png': '📌',
        'unlock.png': '🔓', 'auto.png': '✨', 'help.png': '❓', 'panel.png': '🧩',
        'raw.png': '🖼️', 'app.ico': '🅰️', 'sun.png': '☀️', 'moon.png': '🌙'
    }
    return _emoji_icon(emoji_map.get(name, '❓'))

# ---------------- NOSOTROS (datos fijos) ----------------
ABOUT_INFO = {
    "YEAR": "2025",
    "PROJECT": "AnimeBBG Editor",
    "REV": f"AnimeBBG v{APP_VERSION}",
    "MAINTAINERS": "https://example.com/maintainers",
    "CONTRIBUTORS": "https://example.com/contributors",
    "ARTWORK": "https://example.com/artist",
    "HOME": "https://example.com",           # Tu web
    "REPO": "https://example.com/repo",
    "ISSUES": "https://example.com/issues",
    "WIKI": "https://example.com/wiki",
    "DISCORD": "https://example.com/discord",# Tu Discord
    "PAYPAL": "https://example.com/paypal",  # Tu PayPal
    "IMAGE": str(ASSETS / "icons" / "app.png"),     # Imagen de la app
}

# Windows: icono correcto en taskbar
if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('FansubTools.MangaTextTool')
    except Exception:
        pass

def _apply_win_icon(widget) -> None:
    """Fuerza el icono de la ventana en Windows (titulo + taskbar)."""
    if not sys.platform.startswith('win'):
        return
    ico_path = str(ASSETS / 'icons' / 'app.ico')
    if not Path(ico_path).exists():
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.LoadImageW.restype = ctypes.c_void_p
        user32.LoadImageW.argtypes = [
            ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint,
            ctypes.c_int, ctypes.c_int, ctypes.c_uint
        ]
        user32.SendMessageW.restype = ctypes.c_void_p
        user32.SendMessageW.argtypes = [
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p
        ]
        LR_LOADFROMFILE = 0x00000010
        IMAGE_ICON = 1
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        hbig = user32.LoadImageW(None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
        hsmall = user32.LoadImageW(None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        if not (hbig or hsmall):
            return

        # Garantiza que exista HWND antes de enviar mensajes
        widget.winId()
        hwnd = int(widget.winId())
        if hsmall:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hsmall)
        if hbig:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hbig)
    except Exception:
        pass

# ---------------- Utils ----------------
def qcolor_from_hex(s: str, default: str = "#000000") -> QColor:
    try: return QColor(s)
    except Exception: return QColor(default)

def clamp(v, a, b): return max(a, min(v, b))

# ---- Update helpers ----
def _parse_version(v: str) -> Tuple[int, ...]:
    nums = re.findall(r'\d+', v or "")
    return tuple(int(n) for n in nums) if nums else (0,)

def _is_newer_version(remote: str, local: str) -> bool:
    r = _parse_version(remote)
    l = _parse_version(local)
    # Normalize lengths for comparison
    max_len = max(len(r), len(l))
    r += (0,) * (max_len - len(r))
    l += (0,) * (max_len - len(l))
    return r > l

def _download_file(url: str, dest: Path, timeout: int = 15) -> None:
    """Descarga un archivo a disco."""
    req = urllib.request.Request(url, headers={"User-Agent": "AnimeBBG-Editor"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk)

def _find_update_payload(extract_dir: Path, exe_name: str) -> Optional[Path]:
    if (extract_dir / exe_name).exists():
        return extract_dir
    # Single top-level folder
    children = [p for p in extract_dir.iterdir() if p.is_dir()]
    if len(children) == 1 and (children[0] / exe_name).exists():
        return children[0]
    # Deep search
    for root, _dirs, files in os.walk(extract_dir):
        if exe_name in files:
            return Path(root)
    return None

def _run_self_update(download_url: str, parent: Optional[QMainWindow] = None) -> None:
    """Descarga la nueva versión y reemplaza la instalación actual mediante un .bat auxiliar."""
    if not sys.platform.startswith("win"):
        QMessageBox.information(
            parent or None,
            "Actualización",
            "La actualización automática integrada está disponible en Windows.\n"
            "Se abrirá la descarga para actualización manual."
        )
        webbrowser.open(download_url)
        return

    if not getattr(sys, "frozen", False):
        QMessageBox.information(
            parent or None,
            "Actualización",
            "La actualización automática solo funciona en el ejecutable.\n"
            "Se abrirá la descarga manual."
        )
        webbrowser.open(download_url)
        return

    exe_path = Path(sys.executable)
    if not exe_path.exists():
        QMessageBox.warning(parent or None, "Actualización", "No se encontró el ejecutable actual.")
        return

    try:
        tmp_dir = Path(tempfile.gettempdir()) / "animebbg_update"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        is_zip = download_url.lower().endswith(".zip")

        if is_zip:
            zip_path = tmp_dir / "update.zip"
            extract_dir = tmp_dir / "extract"
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
            extract_dir.mkdir(parents=True, exist_ok=True)

            _download_file(download_url, zip_path)
            if not zip_path.exists() or zip_path.stat().st_size == 0:
                raise RuntimeError("Descarga incompleta.")

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            payload_dir = _find_update_payload(extract_dir, exe_path.name)
            if not payload_dir:
                raise RuntimeError("No se encontró el ejecutable dentro del ZIP.")
        else:
            new_exe = tmp_dir / f"{exe_path.name}.new"
            _download_file(download_url, new_exe)
            if not new_exe.exists() or new_exe.stat().st_size == 0:
                raise RuntimeError("Descarga incompleta.")

        updater_bat = tmp_dir / "update_animebbg.bat"
        pid = os.getpid()

        if is_zip:
            app_dir = exe_path.parent
            payload = payload_dir
            bat_contents = f"""@echo off
setlocal
set EXE="{exe_path}"
set APPDIR="{app_dir}"
set NEWDIR="{payload}"
set PID={pid}
:waitloop
tasklist /FI "PID eq %PID%" | find "%PID%" >nul
if not errorlevel 1 (
    timeout /t 1 >nul
    goto waitloop
)
robocopy %NEWDIR% %APPDIR% /E /NFL /NDL /NJH /NJS /NC /NS >nul
start "" %EXE%
del "%~f0"
endlocal
"""
        else:
            bat_contents = f"""@echo off
setlocal
set NEW="{new_exe}"
set EXE="{exe_path}"
set PID={pid}
:waitloop
tasklist /FI "PID eq %PID%" | find "%PID%" >nul
if not errorlevel 1 (
    timeout /t 1 >nul
    goto waitloop
)
copy /y %NEW% %EXE% >nul
start "" %EXE%
del %NEW%
del "%~f0"
endlocal
"""
        updater_bat.write_text(bat_contents, encoding="utf-8")

        subprocess.Popen(
            ["cmd", "/c", str(updater_bat)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            close_fds=True
        )

        QMessageBox.information(
            parent or None,
            "Actualización",
            "La actualización se descargó. La aplicación se cerrará y se reiniciará sola."
        )
        app = QApplication.instance()
        if app:
            app.quit()
        sys.exit(0)
    except Exception as e:
        QMessageBox.warning(
            parent or None,
            "Actualización",
            f"No se pudo actualizar automáticamente:\n{e}"
        )

# ---- Font Utilities ----
def is_font_installed(family_name: str) -> bool:
    """Verifica si una fuente está instalada en el sistema."""
    families = QFontDatabase.families()
    if family_name in families:
        return True
    
    # Intento de búsqueda flexible para nombres como "Familia-Estilo"
    if "-" in family_name:
        base = family_name.split("-")[0]
        if base in families:
            return True
            
    return False

def get_safe_font_family(requested_family: str, fallback: str = "Arial") -> str:
    """Devuelve el nombre de la fuente solicitada si está disponible, sino el fallback."""
    if is_font_installed(requested_family):
        return requested_family
    return fallback

def rects_intersect(a: QRectF, b: QRectF) -> bool: return a.intersects(b)

# ---- UI Scaling ----
def get_ui_scale_factor() -> float:
    """Calcula el factor de escala basado en la resolución de pantalla."""
    try:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return 1.0
        
        geometry = screen.availableGeometry()
        width = geometry.width()
        height = geometry.height()
        
        # Referencia: 1920x1080 (escala 1.0)
        base_width = 1920
        base_height = 1080
        
        # Calcular escala basada en la dimensión menor para mejor adaptabilidad
        width_scale = width / base_width
        height_scale = height / base_height
        scale = min(width_scale, height_scale)
        
        # Limitar entre 0.6 (muy pequeño) y 1.2 (muy grande)
        return max(0.6, min(1.2, scale))
    except Exception:
        return 1.0

def scale_size(base_size: int, scale_factor: float) -> int:
    """Escala un tamaño entero."""
    return int(base_size * scale_factor)
# ---- Single Instance Manager ----
class SingleInstanceManager:
    """
    Gestiona una única instancia de la aplicación usando QLocalServer/QLocalSocket.
    Si se intenta abrir una segunda instancia, envía los archivos a la primera.
    """
    def __init__(self, app_id: str = "AnimeBBG_Editor_Instance"):
        self.app_id = app_id
        self.server = None
        self.main_window = None
    
    def is_already_running(self) -> bool:
        """Verifica si ya hay una instancia corriendo intentando conectarse."""
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        
        # Esperar un poco para ver si se conecta
        if socket.waitForConnected(500):
            # Hay otra instancia corriendo
            socket.disconnectFromServer()
            return True
        
        return False
    
    def send_files_to_existing_instance(self, file_paths: List[str]) -> bool:
        """Envía archivos a la instancia existente para que los abra."""
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        
        if not socket.waitForConnected(1000):
            return False
        
        # Enviar los archivos como JSON
        data = json.dumps({"files": file_paths}).encode('utf-8')
        socket.write(data)
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        
        return True
    
    def start_server(self, main_window):
        """Inicia el servidor local para recibir archivos de otras instancias."""
        self.main_window = main_window
        
        # Limpiar servidor previo si existe (por si acaso)
        QLocalServer.removeServer(self.app_id)
        
        self.server = QLocalServer()
        if not self.server.listen(self.app_id):
            print(f"No se pudo iniciar el servidor: {self.server.errorString()}")
            return False
        
        self.server.newConnection.connect(self._handle_new_connection)
        return True
    
    def _handle_new_connection(self):
        """Maneja conexiones entrantes de otras instancias."""
        client = self.server.nextPendingConnection()
        if not client:
            return
        
        # Leer datos cuando estén disponibles
        def read_data():
            data = client.readAll().data()
            if data:
                try:
                    message = json.loads(data.decode('utf-8'))
                    files = message.get('files', [])
                    
                    # Abrir los archivos en la ventana principal
                    if self.main_window and files:
                        for file_path in files:
                            if Path(file_path).exists():
                                self.main_window._open_single_project_bbg(file_path)
                        
                        # Traer la ventana al frente
                        self.main_window.activateWindow()
                        self.main_window.raise_()
                        
                except Exception as e:
                    print(f"Error procesando mensaje: {e}")
            
            client.deleteLater()
        
        client.readyRead.connect(read_data)

# ---- Undo helpers ----
def push_cmd(stack: QUndoStack, name: str, undo: Callable[[], None], redo: Callable[[], None]):
    class _Cmd(QUndoCommand):
        def __init__(self): super().__init__(name)
        def undo(self): 
            undo()
            # Marcar la pestaña como modificada después de deshacer
            _mark_scene_modified(stack)
        def redo(self): 
            redo()
            # Marcar la pestaña como modificada después de rehacer
            _mark_scene_modified(stack)
    stack.push(_Cmd())

def _mark_scene_modified(stack: QUndoStack):
    """Helper para marcar la pestaña asociada a un undo stack como modificada."""
    try:
        # El stack está asociado al PageContext.scene
        if hasattr(stack, 'parent') and stack.parent():
            scene_or_ctx = stack.parent()
            # Buscar el PageContext desde la ventana principal
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if hasattr(widget, 'mark_tab_modified') and hasattr(widget, 'tabs'):
                        # Es MangaTextTool, buscar el contexto con este stack
                        for i in range(widget.tabs.count()):
                            ctx = widget.tabs.widget(i)
                            if hasattr(ctx, 'undo_stack') and ctx.undo_stack == stack:
                                widget.mark_tab_modified(ctx)
                                return
    except Exception:
        pass  # Si algo falla, no importa mucho

def snapshot_styles(items: List['StrokeTextItem']):
    return {
        it: {
            'style': replace(it.style),
            'pos': QPointF(it.pos()),
            'rot': float(it.rotation()),
            'width': float(it.textWidth()),
            'name': it.name,
            'locked': it.locked,
        } for it in items
    }

def restore_from_snapshot(snap):
    for it, st in snap.items():
        it.style = st['style']; it.name = st['name']; it.setFont(it.style.to_qfont())
        it._apply_paragraph_to_doc(); it.setPos(st['pos']); it.setRotation(st['rot']); it.setTextWidth(st['width'])
        it.sync_default_text_color()
        it.set_locked(st['locked'])

def apply_to_selected(ctx: 'PageContext', items: List['StrokeTextItem'], name: str, apply_fn: Callable[[], None]):
    snap_before = snapshot_styles(items)
    def undo(): restore_from_snapshot(snap_before); ctx.scene.update()
    def redo():
        apply_fn()
        for it in items:
            it.sync_default_text_color()
        ctx.scene.update()
    push_cmd(ctx.undo_stack, name, undo, redo)

# ---------------- THEME / QSS ----------------
def _hex_to_rgb(hexstr: str) -> tuple[int,int,int]:
    s = hexstr.lstrip("#"); return int(s[0:2],16), int(s[2:4],16), int(s[4:6],16)

def accent_qcolor() -> QColor:
    app = QApplication.instance(); c = app.property("accent_color")
    return QColor(c) if c else QColor("#E11D48")

class Theme:
    @staticmethod
    def stylesheet(*, dark: bool, accent: str, radius: int = 8, scale_factor: float = 1.0) -> str:
        r,g,b = _hex_to_rgb(accent); a15=f"rgba({r},{g},{b},0.15)"; a30=f"rgba({r},{g},{b},0.30)"
        if dark:  bg="#0f1115"; alt="#111318"; panel="#181b20"; raised="#232731"; border="#2a2f3a"; text="#D7DBE7"
        else:     bg="#FAFAFC"; alt="#F2F3F7"; panel="#FFFFFF"; raised="#FFFFFF"; border="#DCDDE3"; text="#77777A"
        
        # ===== AJUSTE DE TAMAÑO DE TEXTO =====
        # Para cambiar el tamaño del texto de la UI, modifica el valor base (actualmente 10.2)
        # Ejemplo: 10.2 -> 11 para texto más grande, 10.2 -> 9.5 para texto más pequeño
        font_size = int(11.3 * scale_factor)
        
        # Aplicar escala a tamaños
        toolbar_padding = int(6 * scale_factor)
        toolbar_spacing = int(6 * scale_factor)
        button_padding_v = int(6 * scale_factor)
        button_padding_h = int(10 * scale_factor)
        tab_padding_v = int(8 * scale_factor)
        tab_padding_h = int(14 * scale_factor)
        tab_margin = int(2 * scale_factor)
        dock_padding = int(8 * scale_factor)
        list_item_padding = int(6 * scale_factor)
        input_padding_v = int(4 * scale_factor)
        input_padding_h = int(6 * scale_factor)
        slider_height = int(6 * scale_factor)
        slider_handle = int(14 * scale_factor)
        
        return f"""
        * {{ font-family: 'Inter','Segoe UI','Roboto','Arial'; font-size:{font_size}pt; color:{text}; }}
        QMainWindow {{ background:{bg}; }}
        QToolBar {{ background:{alt}; border:none; padding:{toolbar_padding}px; spacing:{toolbar_spacing}px; }}
        QToolButton {{ border-radius:{radius}px; padding:{button_padding_v}px {button_padding_h}px; }}
        QToolButton:hover {{ background:{a15}; }}
        QToolButton:pressed, QToolButton:checked {{ background:{a30}; border:1px solid {accent}; }}
        QTabWidget::pane {{ border:1px solid {border}; background:{panel}; }}
        QTabBar::tab {{ background:{panel}; border:1px solid {border}; padding:{tab_padding_v}px {tab_padding_h}px; margin:{tab_margin}px;
                        border-top-left-radius:{radius}px; border-top-right-radius:{radius}px; }}
        QTabBar::tab:selected {{ border-bottom-color:{panel}; }}
        QDockWidget::title {{ background:{alt}; padding:{dock_padding}px; border-bottom:1px solid {border}; }}
        QListWidget {{ background:{bg}; border:1px solid {border}; }}
        QListWidget::item {{ padding:{list_item_padding}px; border-radius:{max(0, radius-2)}px; }}
        QListWidget::item:selected {{ background:{a30}; border:1px solid {accent}; }}
        QPushButton {{ background:{raised}; border:1px solid {border}; border-radius:{radius}px; padding:{button_padding_v}px {button_padding_h*1.2:.0f}px; }}
        QPushButton:hover {{ border-color:{accent}; }}
        QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QTextEdit {{
            background:{bg}; border:1px solid {border}; border-radius:{max(0, radius-2)}px; padding:{input_padding_v}px {input_padding_h}px;
        }}
        QComboBox QAbstractItemView {{ background:{panel}; selection-background-color:{a30}; }}
        QSlider::groove:horizontal {{ height:{slider_height}px; background:{border}; border-radius:3px; }}
        QSlider::handle:horizontal {{ width:{slider_handle}px; margin:-5px 0; border-radius:7px; background:{accent}; }}
        QStatusBar {{ background:{alt}; border-top:1px solid {border}; }}
        """
    @staticmethod
    def apply(app: QApplication, *, dark: bool = True, accent: str = "#E11D48", radius: int = 8, scale_factor: float = 1.0):
        app.setStyle(QStyleFactory.create("Fusion"))
        app.setProperty("accent_color", accent)
        app.setProperty("ui_scale_factor", scale_factor)
        app.setStyleSheet(Theme.stylesheet(dark=dark, accent=accent, radius=radius, scale_factor=scale_factor))

# ---------------- Estilos ----------------
@dataclass
class TextStyle:
    font_family: str = "Arial"
    font_point_size: int = 34
    bold: bool = False
    italic: bool = False
    fill: str = "#000000"
    # Tipo de relleno: 'solid' | 'linear_gradient' | 'texture' | 'transparent'
    fill_type: str = 'solid'
    # Para degradado: lista de (pos, color) stops, pos 0.0-1.0
    gradient_stops: List[Tuple[float, str]] = None
    gradient_angle: int = 0
    # Para textura: ruta a imagen y si se repite (tile) o estira
    texture_path: str = ""
    texture_tile: bool = True
    texture_scale: float = 1.0
    texture_angle: int = 0
    # Deformacion tipo "warp" (Photoshop-like)
    warp_style: str = "none"      # none | arc | wave | flag | fish
    warp_vertical: bool = False   # False=horizontal, True=vertical
    warp_bend: int = 0            # -100..100
    warp_hdist: int = 0           # -100..100
    warp_vdist: int = 0           # -100..100
    outline: str = "#FFFFFF"
    outline_width: int = 3
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_dx: int = 2
    shadow_dy: int = 2
    shadow_blur: int = 8
    alignment: str = "center"
    line_spacing: float = 1.2
    auto_hyphenate: bool = True
    background_enabled: bool = False
    background_color: str = "#FFFFFF"
    background_opacity: float = 0.0
    capitalization: str = "mixed"
    def to_qfont(self) -> QFont:
        """Crea QFont desde este estilo."""
        f = QFont(self.font_family, self.font_point_size); f.setBold(self.bold); f.setItalic(self.italic)
        cap_map = {
            'mixed': QFont.Capitalization.MixedCase,
            'uppercase': QFont.Capitalization.AllUppercase,
            'lowercase': QFont.Capitalization.AllLowercase,
            'capitalize': QFont.Capitalization.Capitalize,
            'smallcaps': QFont.Capitalization.SmallCaps,
        }
        f.setCapitalization(cap_map.get(self.capitalization, QFont.Capitalization.MixedCase)); return f

def default_presets() -> Dict[str, TextStyle]:
    return {
        'TITULO': TextStyle(font_family='Bebas Neue', font_point_size=60, bold=True,
                            fill='#000000', outline='#FFFFFF', outline_width=4, alignment='center'),
        'N/T': TextStyle(font_family='Arial', font_point_size=22, italic=True,
                         fill='#111111', outline='#FFFFFF', outline_width=3, alignment='center',
                         background_enabled=False, background_color='#FFFFFF', background_opacity=0.0),
        'GLOBO': TextStyle(font_family='CC Wild Words', font_point_size=38,
                           fill='#000000', outline='#FFFFFF', outline_width=3, alignment='center'),
        'PENSAMIENTO': TextStyle(font_family='CC Wild Words', font_point_size=36, italic=True,
                                 fill='#000000', outline='#FFFFFF', outline_width=3, alignment='center'),
        'FUERA_GLOBO': TextStyle(font_family='Arial', font_point_size=30,
                                 fill='#111111', outline='#FFFFFF', outline_width=3, alignment='center'),
        'ANIDADO': TextStyle(font_family='Arial', font_point_size=26,
                             fill='#111111', outline='#FFFFFF', outline_width=3, alignment='center'),
        'CUADRO': TextStyle(font_family='CC Wild Words', font_point_size=30, bold=True,
                            fill='#000000', outline='#FFFFFF', outline_width=3, alignment='center',
                            background_enabled=False, background_color='#FFFFDD', background_opacity=0.0),
        'NOTA': TextStyle(font_family='Arial', font_point_size=22, italic=True,
                          fill='#333333', outline='#FFFFFF', outline_width=2, alignment='center'),
        'GRITOS': TextStyle(font_family='CC Wild Words', font_point_size=44, bold=True,
                            fill='#000000', outline='#FFFFFF', outline_width=4, alignment='center'),
        'GEMIDOS': TextStyle(font_family='Arial', font_point_size=32, italic=True,
                             fill='#111111', outline='#FFFFFF', outline_width=3, alignment='center'),
        'ONOMATOPEYAS': TextStyle(font_family='Bangers', font_point_size=60, bold=True,
                                  fill='#000000', outline='#FFFFFF', outline_width=5, alignment='center'),
        'TEXTO_NERVIOSO': TextStyle(font_family='Arial', font_point_size=34, italic=True,
                                    fill='#000000', outline='#FFFFFF', outline_width=3, alignment='center'),
    }

PRESETS: Dict[str, TextStyle] = default_presets()

# ---------------- Parseo identificadores ----------------
_RE_GLOBO = re.compile(r'^\s*(?:Globo\s*\d+|Globo\s*[A-Za-z]+)\s*:\s*(.+)$', re.IGNORECASE)
_RE_GNUM = re.compile(r'^\s*G\s*(\d+)\s*:\s*(.+)$', re.IGNORECASE)   # G1: G2: G3: -> GLOBO
_RE_NT = re.compile(r'^\s*N/T\s*:\s*(.+)$', re.IGNORECASE)
_RE_FUERA = re.compile(r'^\s*\*\s*:\s*(.+)$')
_RE_STAR = re.compile(r'^\s*\*(?!:)\s*(.+)$')                         # *texto / * texto -> FUERA_GLOBO
_RE_PENS_1 = re.compile(r'^\s*\(\)\s*:\s*(.+)$')
_RE_PENS_2 = re.compile(r'^\s*\((.+)\)\s*$')
_RE_CUADRO_1 = re.compile(r'^\s*\[\]\s*:\s*(.+)$')
_RE_CUADRO_2 = re.compile(r'^\s*\[(.+)\]\s*$')
_RE_TITULO = re.compile(r'^\s*TITULO\s*:\s*(.+)$', re.IGNORECASE)
_RE_GRITOS = re.compile(r'^\s*GRITOS\s*:\s*(.+)$', re.IGNORECASE)
_RE_GEMIDOS = re.compile(r'^\s*GEMIDOS\s*:\s*(.+)$', re.IGNORECASE)
_RE_ONO = re.compile(r'^\s*ONOMATOPEYAS?\s*:\s*(.+)$', re.IGNORECASE)
_RE_NERV = re.compile(r'^\s*TEXTO[_\s]?NERVIOSO\s*:\s*(.+)$', re.IGNORECASE)

def parse_identifier(line: str):
    s = line.strip()
    # Casos especiales para reconocer el tipo y dejar solo el texto
    m = _RE_PENS_1.match(s)
    if m:
        return 'PENSAMIENTO', m.group(1).strip()
    m = _RE_PENS_2.match(s)
    if m:
        return 'PENSAMIENTO', m.group(1).strip()
    m = _RE_CUADRO_1.match(s)
    if m:
        return 'CUADRO', m.group(1).strip()
    m = _RE_CUADRO_2.match(s)
    if m:
        return 'CUADRO', m.group(1).strip()

    # G1: / G2: / G3: -> alias de Globo N:
    m = _RE_GNUM.match(s)
    if m:
        return 'GLOBO', m.group(2).strip()

    for rx, key in [
        (_RE_GLOBO, 'GLOBO'), (_RE_NT, 'N/T'), (_RE_FUERA, 'FUERA_GLOBO'),
        (_RE_TITULO, 'TITULO'), (_RE_GRITOS, 'GRITOS'), (_RE_GEMIDOS, 'GEMIDOS'),
        (_RE_ONO, 'ONOMATOPEYAS'), (_RE_NERV, 'TEXTO_NERVIOSO'),
    ]:
        m = rx.match(s)
        if m:
            return key, m.group(1).strip()

    # * texto (sin dos puntos) -> FUERA_GLOBO
    m = _RE_STAR.match(s)
    if m:
        return 'FUERA_GLOBO', m.group(1).strip()
    if s.startswith('N/T:'): return 'N/T', s[4:].lstrip()
    if s.startswith('Globo X:'): return 'GLOBO', s[len('Globo X:'):].lstrip()
    if s.startswith('():'): return 'PENSAMIENTO', s[3:].lstrip()
    if s.startswith('[]:'): return 'CUADRO', s[3:].lstrip()
    if s.startswith('*:'):  return 'FUERA_GLOBO', s[2:].lstrip()
    if s.startswith('""'):  return 'TITULO', s[2:].lstrip()
    return 'GLOBO', s

# ---------------- Capa de imagen movible ----------------
class MovableImageLayer(QGraphicsPixmapItem):
    """Capa de imagen que puede ser seleccionada y movida en el lienzo."""
    def __init__(self, pixmap: QPixmap, layer_name: str = "Capa"):
        super().__init__(pixmap)
        self.name = layer_name
        self.layer_name = layer_name
        self.ordinal = -1
        self.locked = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self._dragging = False
    
    def paint(self, painter, option, widget=None):
        """Dibuja la capa con un borde de selección si está seleccionada."""
        super().paint(painter, option, widget)
        
        if self.isSelected():
            # Dibujar borde de selección
            painter.setPen(QPen(QColor("#E11D48"), 2, Qt.PenStyle.DashLine))
            painter.drawRect(self.boundingRect())
    
    def mousePressEvent(self, event):
        """Permite arrastrar la capa."""
        self._dragging = True
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Actualiza posición durante el arrastre."""
        if self._dragging:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Finaliza el arrastre."""
        self._dragging = False
        super().mouseReleaseEvent(event)
    
    def hoverEnterEvent(self, event):
        """Cambia cursor al pasar el mouse."""
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Restaura cursor normal."""
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverLeaveEvent(event)

# ---------------- Ítem de texto ----------------
class StrokeTextItem(QGraphicsTextItem):
    HANDLE_SIZE = 10; ROT_HANDLE_R = 7
    ROT_CORNER_R = 5
    ROT_CORNER_OFFSET = 10
    ROT_MIN_RADIUS = 60
    ROT_SENSITIVITY = 0.20
    SHOW_ORDINAL = True
    SOFT_HYPHEN = "\u00AD"
    _WORD_RX = re.compile(r"[A-Za-zÁÉÍÓÚÜÑñ]+", re.UNICODE)
    def __init__(self, text: str, style: TextStyle, name: str = "Texto"):
        super().__init__(text)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setDefaultTextColor(qcolor_from_hex(style.fill))
        self.style = style; self.name = name; self.locked: bool = False
        self.ordinal: int = -1
        self._suppress_overlays: bool = False
        # Rastrear si la fuente original está disponible (para advertencia tipo Photoshop)
        self.original_font_family: str = style.font_family
        self.font_missing_warning_shown: bool = False

        self._start_pos = QPointF(0, 0); self._old_text = text
        self._resizing = False; self._resize_start_width = 0.0; self._resize_start_pos = QPointF(0, 0)
        self._resize_alt_scale = False; self._start_font_pt = float(style.font_point_size); self._start_outline = float(style.outline_width)
        self._rotating = False; self._rot_start_angle = 0.0; self._rot_base = 0.0
        self._hyphenating = False
        self._raw_text = self._strip_soft_hyphens(text)
        # Un pequeño margen interno evita recortes en fuentes manuscritas/itálicas.
        try:
            self.document().setDocumentMargin(2.0)
        except Exception:
            pass
        # Aplicar fuente (Sin cambiar a fallback automático — solo detectar para advertencia)
        self.setFont(style.to_qfont()); self._apply_paragraph_to_doc()
        self.setTextWidth(400); self.apply_shadow(); self.background_enabled = style.background_enabled
        self._update_soft_hyphens()

    def _outline_offsets(self, ow: int) -> List[Tuple[int, int]]:
        """Offsets en disco para contorno más redondo (evita aspecto cuadrado)."""
        ow = int(max(0, ow))
        if ow <= 0:
            return []
        if ow <= 12:
            step = 1
        elif ow <= 24:
            step = 2
        else:
            step = 3
        r2 = ow * ow
        offsets: List[Tuple[int, int]] = []
        for dx in range(-ow, ow + 1, step):
            for dy in range(-ow, ow + 1, step):
                if dx == 0 and dy == 0:
                    continue
                if (dx * dx + dy * dy) <= (r2 + ow):
                    offsets.append((dx, dy))
        return offsets

    def _strip_soft_hyphens(self, text: str) -> str:
        return (text or "").replace(self.SOFT_HYPHEN, "")

    def get_raw_text(self) -> str:
        if self._raw_text is not None:
            return self._raw_text
        return self._strip_soft_hyphens(super().toPlainText())

    def setPlainText(self, text: str) -> None:
        raw = self._strip_soft_hyphens(text)
        self._raw_text = raw
        super().setPlainText(raw)
        self._apply_paragraph_to_doc()
        self._update_soft_hyphens()

    def setTextWidth(self, width: float) -> None:
        super().setTextWidth(width)
        self._update_soft_hyphens()

    def setFont(self, font: QFont) -> None:
        super().setFont(font)
        self._update_soft_hyphens()

    def _compute_soft_hyphen_positions(self, text: str) -> List[int]:
        if not text:
            return []
        max_width = float(self.textWidth() or 0)
        if max_width <= 0:
            return []
        fm = QFontMetricsF(self.font())
        avg = float(fm.averageCharWidth() or 0)
        if avg <= 0:
            return []
        hyphen_w = float(fm.horizontalAdvance("-") or 0)
        # Ancho disponible para texto (considerando el guión)
        usable = max(0.0, max_width - hyphen_w)

        # Umbral: si la palabra ocupa más del 80% del ancho, guionarla
        # Esto asegura que palabras largas se corten incluso si técnicamente caben
        threshold = usable * 0.8

        positions: List[int] = []
        offset = 0
        for line in text.splitlines(True):
            if line.endswith("\r\n"):
                core = line[:-2]; line_end = "\r\n"
            elif line.endswith("\n") or line.endswith("\r"):
                core = line[:-1]; line_end = line[-1]
            else:
                core = line; line_end = ""
            for m in self._WORD_RX.finditer(core):
                word = m.group(0)
                # Calcular el ancho real de la palabra completa
                word_width = float(fm.horizontalAdvance(word) or 0)

                # Aplicar guiones si:
                # 1. La palabra NO cabe en el ancho disponible, O
                # 2. La palabra ocupa más del 80% del ancho (umbral)
                if word_width <= threshold:
                    continue

                # Calcular cuántos caracteres caben en el ancho disponible
                chars_fit = 0
                accumulated_width = 0.0
                for char in word:
                    char_width = float(fm.horizontalAdvance(char) or 0)
                    if accumulated_width + char_width > usable:
                        break
                    accumulated_width += char_width
                    chars_fit += 1

                # Necesitamos al menos 3 caracteres para cortar
                if chars_fit < 3:
                    continue

                start = m.start()
                i = chars_fit
                while len(word) - i > 2:
                    remaining = len(word) - i
                    if remaining < 3:
                        break
                    positions.append(offset + start + i)
                    i += chars_fit
            offset += len(core) + len(line_end)
        return positions

    def _update_soft_hyphens(self):
        if self._hyphenating:
            return
        if self.textInteractionFlags() == Qt.TextInteractionFlag.TextEditorInteraction:
            return
        doc = self.document()
        if doc is None:
            return
        self._hyphenating = True
        try:
            text = doc.toPlainText()
            if self.SOFT_HYPHEN in text:
                cur = QTextCursor(doc)
                for pos in [i for i, ch in enumerate(text) if ch == self.SOFT_HYPHEN][::-1]:
                    cur.setPosition(pos)
                    cur.deleteChar()
                text = doc.toPlainText()
            self._raw_text = text
            if not getattr(self.style, 'auto_hyphenate', False):
                return
            positions = self._compute_soft_hyphen_positions(text)
            if positions:
                cur = QTextCursor(doc)
                for pos in sorted(positions, reverse=True):
                    cur.setPosition(pos)
                    cur.insertText(self.SOFT_HYPHEN)
        finally:
            self._hyphenating = False

    def _clear_soft_hyphens(self):
        doc = self.document()
        if doc is None:
            return
        text = doc.toPlainText()
        if self.SOFT_HYPHEN not in text:
            self._raw_text = text
            return
        cur = QTextCursor(doc)
        for pos in [i for i, ch in enumerate(text) if ch == self.SOFT_HYPHEN][::-1]:
            cur.setPosition(pos)
            cur.deleteChar()
        self._raw_text = doc.toPlainText()

    def sync_default_text_color(self):
        """Mantiene el color de texto en sync sin mutar en paint (evita parpadeo)."""
        try:
            if getattr(self.style, 'fill_type', 'solid') == 'transparent':
                target = QColor(0, 0, 0, 0)
            else:
                target = qcolor_from_hex(self.style.fill)
            if self.defaultTextColor() != target:
                self.setDefaultTextColor(target)
        except Exception:
            pass

    def _warp_row_params(self, t: float) -> Tuple[float, float]:
        style = str(getattr(self.style, 'warp_style', 'none') or 'none')
        bend = clamp(float(getattr(self.style, 'warp_bend', 0)) / 100.0, -1.0, 1.0)
        hdist = clamp(float(getattr(self.style, 'warp_hdist', 0)) / 100.0, -1.0, 1.0)
        vdist = clamp(float(getattr(self.style, 'warp_vdist', 0)) / 100.0, -1.0, 1.0)

        curve = 0.0
        sx = 1.0
        if style == 'arc':
            # Centrado para evitar que todo el texto se desplace a un solo lado
            curve = 1.8 * bend * ((1.0 - t * t) - 0.5)
            sx = 1.0 + hdist * t
        elif style == 'wave':
            curve = 1.35 * bend * math.sin((t + 1.0) * math.pi)
            sx = 1.0 + 0.6 * hdist * math.cos(t * math.pi)
        elif style == 'flag':
            curve = 1.5 * bend * math.sin((t + 1.0) * math.pi * 0.5)
            sx = 1.0 + hdist * math.sin(t * math.pi)
        elif style == 'fish':
            curve = 1.3 * bend * t
            sx = 1.0 + hdist * (1.0 - t * t)
        else:
            sx = 1.0 + hdist * t
        curve += 0.6 * vdist * t
        sx = clamp(sx, 0.25, 3.0)
        return curve, sx

    def _warp_extra_bounds(self, base_rect: QRectF) -> Tuple[float, float]:
        style = str(getattr(self.style, 'warp_style', 'none') or 'none')
        if style == 'none':
            return 0.0, 0.0
        bend = abs(float(getattr(self.style, 'warp_bend', 0)) / 100.0)
        hdist = abs(float(getattr(self.style, 'warp_hdist', 0)) / 100.0)
        vdist = abs(float(getattr(self.style, 'warp_vdist', 0)) / 100.0)
        vertical = bool(getattr(self.style, 'warp_vertical', False))

        if vertical:
            extra_x = base_rect.width() * (0.10 + 0.25 * hdist + 0.50 * bend + 0.20 * vdist)
            extra_y = base_rect.height() * (0.10 + 0.15 * hdist + 0.20 * bend + 0.50 * vdist)
        else:
            extra_x = base_rect.width() * (0.10 + 0.15 * hdist + 0.20 * bend + 0.50 * vdist)
            extra_y = base_rect.height() * (0.10 + 0.25 * hdist + 0.50 * bend + 0.20 * vdist)
        return extra_x, extra_y

    def _draw_warped_image(self, painter: QPainter, src: QImage, dst_top_left: QPointF):
        w = src.width()
        h = src.height()
        if w <= 1 or h <= 1:
            painter.drawImage(dst_top_left, src)
            return

        vertical = bool(getattr(self.style, 'warp_vertical', False))
        # Mayor amplitud para que el efecto se note claramente con valores altos.
        max_shift = (h * 0.55) if vertical else (w * 0.55)
        base_x = float(dst_top_left.x())
        base_y = float(dst_top_left.y())
        strip = 2  # Dibujar en bandas de 2 px con solape reduce "rallado" por remuestreo.

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if not vertical:
            for y in range(0, h, strip):
                y_center = min(h - 1, y + (strip * 0.5))
                t = (2.0 * y_center / max(1, h - 1)) - 1.0
                curve, sx = self._warp_row_params(t)
                dst_w = w * sx
                dx = (w - dst_w) * 0.5 + (curve * max_shift)
                src_h = min(strip, h - y)
                # +0.4 de solape para evitar costuras visibles entre bandas.
                dst = QRectF(base_x + dx, base_y + y, dst_w, float(src_h) + 0.4)
                painter.drawImage(dst, src, QRectF(0.0, float(y), float(w), float(src_h)))
        else:
            for x in range(0, w, strip):
                x_center = min(w - 1, x + (strip * 0.5))
                t = (2.0 * x_center / max(1, w - 1)) - 1.0
                curve, sy = self._warp_row_params(t)
                dst_h = h * sy
                dy = (h - dst_h) * 0.5 + (curve * max_shift)
                src_w = min(strip, w - x)
                # +0.4 de solape para evitar costuras visibles entre bandas.
                dst = QRectF(base_x + x, base_y + dy, float(src_w) + 0.4, dst_h)
                painter.drawImage(dst, src, QRectF(float(x), 0.0, float(src_w), float(h)))

        painter.restore()

    def _render_text_layers_for_warp(self, fill_type: str, ow: int) -> Tuple[QImage, QPointF]:
        br = super().boundingRect()
        pad = max(4, ow + 4)
        w = max(1, int(math.ceil(br.width())))
        h = max(1, int(math.ceil(br.height())))

        mask_img = QImage(w + pad*2, h + pad*2, QImage.Format.Format_ARGB32_Premultiplied)
        mask_img.fill(Qt.GlobalColor.transparent)
        mp = QPainter(mask_img)
        mp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        mp.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        mp.translate(pad - br.left(), pad - br.top())
        mctx = QAbstractTextDocumentLayout.PaintContext()
        mctx.palette.setColor(QPalette.ColorRole.Text, QColor('white'))
        self.document().documentLayout().draw(mp, mctx)
        mp.end()

        fill_img = QImage(mask_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
        fill_img.fill(Qt.GlobalColor.transparent)
        target_fill = qcolor_from_hex(self.style.fill)

        if fill_type != 'transparent':
            fp = QPainter(fill_img)
            fp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            if fill_type == 'solid':
                fp.fillRect(fill_img.rect(), target_fill)
            elif fill_type == 'linear_gradient' and self.style.gradient_stops:
                angle = float(getattr(self.style, 'gradient_angle', 0))
                rad = math.radians(angle)
                cx, cy = fill_img.width()/2, fill_img.height()/2
                dx = math.cos(rad) * cx
                dy = math.sin(rad) * cy
                grad = QLinearGradient(QPointF(cx - dx, cy - dy), QPointF(cx + dx, cy + dy))
                for pos, col in (getattr(self.style, 'gradient_stops', []) or []):
                    try:
                        grad.setColorAt(float(pos), qcolor_from_hex(col))
                    except Exception:
                        pass
                fp.fillRect(fill_img.rect(), grad)
            elif fill_type == 'texture' and getattr(self.style, 'texture_path', ''):
                tp = getattr(self.style, 'texture_path', '')
                pm = QPixmap(tp) if tp else QPixmap()
                if not pm.isNull():
                    tex_scale = float(getattr(self.style, 'texture_scale', 1.0) or 1.0)
                    tex_scale = clamp(tex_scale, 0.05, 10.0)
                    tex_angle = float(getattr(self.style, 'texture_angle', 0))
                    if getattr(self.style, 'texture_tile', True):
                        brush = QBrush(pm)
                        tr = QTransform()
                        tr.scale(tex_scale, tex_scale)
                        tr.rotate(tex_angle)
                        brush.setTransform(tr)
                        fp.fillRect(fill_img.rect(), brush)
                    else:
                        fp.fillRect(fill_img.rect(), target_fill)
                        fp.save()
                        fp.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                        cx = fill_img.width() / 2.0
                        cy = fill_img.height() / 2.0
                        fit_scale = min(fill_img.width() / max(1, pm.width()), fill_img.height() / max(1, pm.height()))
                        fp.translate(cx, cy)
                        fp.rotate(tex_angle)
                        fp.scale(fit_scale * tex_scale, fit_scale * tex_scale)
                        fp.translate(-pm.width() / 2.0, -pm.height() / 2.0)
                        fp.drawPixmap(0, 0, pm)
                        fp.restore()
                else:
                    fp.fillRect(fill_img.rect(), target_fill)
            else:
                fp.fillRect(fill_img.rect(), target_fill)

            fp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            fp.drawImage(0, 0, mask_img)
            fp.end()

        outline_img = QImage(mask_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
        outline_img.fill(Qt.GlobalColor.transparent)
        if ow > 0:
            ring = QImage(mask_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
            ring.fill(Qt.GlobalColor.transparent)
            rp = QPainter(ring)
            rp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rp.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            for dx, dy in self._outline_offsets(ow):
                rp.drawImage(dx, dy, mask_img)
            rp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
            rp.drawImage(0, 0, mask_img)
            rp.end()

            tp = QPainter(outline_img)
            tp.fillRect(outline_img.rect(), qcolor_from_hex(self.style.outline))
            tp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            tp.drawImage(0, 0, ring)
            tp.end()

        composed = QImage(mask_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
        composed.fill(Qt.GlobalColor.transparent)
        cp = QPainter(composed)
        cp.drawImage(0, 0, outline_img)
        cp.drawImage(0, 0, fill_img)
        cp.end()
        return composed, QPointF(br.left() - pad, br.top() - pad)

    def set_locked(self, v: bool, global_lock: bool = False):
        self.locked = bool(v)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, (not self.locked) and (not global_lock))
        self.update()
    def is_locked(self) -> bool: return self.locked

    def _apply_paragraph_to_doc(self):
        doc: QTextDocument = self.document()
        opt = QTextOption()
        align_map = {'center': Qt.AlignmentFlag.AlignHCenter, 'left': Qt.AlignmentFlag.AlignLeft,
                     'right': Qt.AlignmentFlag.AlignRight, 'justify': Qt.AlignmentFlag.AlignJustify}
        opt.setAlignment(align_map.get(self.style.alignment, Qt.AlignmentFlag.AlignLeft))
        opt.setWrapMode(QTextOption.WrapMode.WordWrap); doc.setDefaultTextOption(opt)
        cursor = QTextCursor(doc); cursor.select(QTextCursor.SelectionType.Document)
        fmt = cursor.blockFormat()
        pct = int(max(0.5, min(5.0, self.style.line_spacing)) * 100)
        try: lh_type = int(QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        except Exception: lh_type = 1
        fmt.setLineHeight(pct, lh_type); cursor.setBlockFormat(fmt)

    def apply_shadow(self):
        if self.style.shadow_enabled:
            eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(self.style.shadow_blur)
            eff.setOffset(self.style.shadow_dx, self.style.shadow_dy)
            eff.setColor(qcolor_from_hex(self.style.shadow_color)); self.setGraphicsEffect(eff)
        else:
            self.setGraphicsEffect(None)

    def _handle_rect(self) -> QRectF:
        br = super().boundingRect(); s = self.HANDLE_SIZE
        return QRectF(br.right()-s, br.bottom()-s, s, s)

    def _handle_hitbox(self) -> QRectF:
        """Hitbox más grande para facilitar el click en el resize handle"""
        br = super().boundingRect()
        s = self.HANDLE_SIZE
        # Hitbox 3x más grande que el visual
        hitbox_size = s * 3
        return QRectF(br.right()-hitbox_size, br.bottom()-hitbox_size, hitbox_size, hitbox_size)

    def _rot_handle_center(self) -> QPointF:
        br = super().boundingRect(); return QPointF((br.left()+br.right())/2.0, br.top()-14.0)
    def _rot_corner_centers(self) -> List[QPointF]:
        br = super().boundingRect()
        o = self.ROT_CORNER_OFFSET
        # Esquinas inferiores para rotación (izq y der)
        return [
            QPointF(br.left() - o,  br.bottom() + o),
            QPointF(br.right() + o, br.bottom() + o),
        ]
    def _hit_rot_corner(self, pos: QPointF) -> bool:
        r = self.ROT_CORNER_R + 3
        for c in self._rot_corner_centers():
            if (pos - c).manhattanLength() <= r:
                return True
        return False

    def boundingRect(self) -> QRectF:
        rect = super().boundingRect()
        pad = int(math.ceil(float(self.style.outline_width))) + 6
        ex, ey = self._warp_extra_bounds(rect)
        if ex > 0 or ey > 0:
            rect = rect.adjusted(-ex, -ey, ex, ey)
        if self.isSelected():
            # Aumentar espacio superior para evitar clipping de la palanca de rotación
            extra_top = 50; handle_pad = self.HANDLE_SIZE + 2
            extra_all = self.ROT_CORNER_OFFSET + self.ROT_CORNER_R + 2
            rect = rect.adjusted(-pad - extra_all, -pad - extra_top - extra_all,
                                 pad + handle_pad + extra_all, pad + handle_pad + extra_all)
        else:
            rect = rect.adjusted(-pad, -pad, pad, pad)
        return rect

    def shape(self):
        style = str(getattr(self.style, 'warp_style', 'none') or 'none')
        if style == 'none':
            return super().shape()
        # En modo deformado ampliamos hit area para permitir selección/arrastre fiable
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter: QPainter, option, widget=None):
        # Ocultar el cuadro de selección predeterminado (linea punteada blanca)
        # Esto elimina el ruido visual del boundingRect extendido.
        option.state &= ~QStyle.StateFlag.State_Selected
        fill_type = getattr(self.style, 'fill_type', 'solid')
        warp_style = str(getattr(self.style, 'warp_style', 'none') or 'none')
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # En modo edición (doble clic), dibujar normal para ver cursor/selección
        # y evitar artefactos del render deformado.
        if self.textInteractionFlags() == Qt.TextInteractionFlag.TextEditorInteraction:
            try:
                edit_color = qcolor_from_hex(self.style.outline if fill_type == 'transparent' else self.style.fill)
                if self.defaultTextColor() != edit_color:
                    self.setDefaultTextColor(edit_color)
            except Exception:
                pass
            super().paint(painter, option, widget)
            self._draw_overlays(painter)
            return

        if fill_type != 'transparent' and self.style.background_enabled and self.style.background_opacity > 0:
            br = super().boundingRect()
            c = QColor(qcolor_from_hex(self.style.background_color))
            c.setAlpha(int(clamp(self.style.background_opacity, 0, 1) * 255))
            painter.fillRect(br, c)

        ow = int(max(0, round(float(self.style.outline_width))))
        if warp_style != 'none':
            try:
                composed, pos = self._render_text_layers_for_warp(fill_type, ow)
                self._draw_warped_image(painter, composed, pos)
                self._draw_overlays(painter)
                return
            except Exception:
                pass

        if ow > 0 and fill_type != 'transparent':
            outline_col = qcolor_from_hex(self.style.outline)
            br = super().boundingRect()
            pad = ow + 3
            img_w = max(1, int(math.ceil(br.width())) + pad * 2)
            img_h = max(1, int(math.ceil(br.height())) + pad * 2)
            img = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
            img.fill(Qt.GlobalColor.transparent)

            img_p = QPainter(img)
            img_p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            img_p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            img_p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            img_p.translate(pad - br.left(), pad - br.top())
            
            # Use PaintContext to draw with outline color without modifying item state
            ctx = QAbstractTextDocumentLayout.PaintContext()
            ctx.palette.setColor(QPalette.ColorRole.Text, outline_col)
            self.document().documentLayout().draw(img_p, ctx)
            
            img_p.end()

            # Dibujar la imagen muestreada
            base_x = br.left() - pad
            base_y = br.top() - pad
            for dx, dy in self._outline_offsets(ow):
                painter.drawImage(QPointF(base_x + dx, base_y + dy), img)

        # Relleno
        try:
            target_fill = qcolor_from_hex(self.style.fill)

            if fill_type == 'solid':
                # For solid, rely on pre-synced defaultTextColor (avoid mutating in paint)
                super().paint(painter, option, widget)
            elif fill_type == 'transparent':
                # Texto hueco: genera el contorno en imagen intermedia y recorta el interior.
                br = super().boundingRect()
                if ow <= 0:
                    return
                pad = ow
                w = max(1, int(math.ceil(br.width())))
                h = max(1, int(math.ceil(br.height())))
                mask_img = QImage(w + pad*2, h + pad*2, QImage.Format.Format_ARGB32_Premultiplied)
                mask_img.fill(Qt.GlobalColor.transparent)
                mp = QPainter(mask_img)
                mp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                mp.translate(pad - br.left(), pad - br.top())
                mctx = QAbstractTextDocumentLayout.PaintContext()
                mctx.palette.setColor(QPalette.ColorRole.Text, QColor("white"))
                self.document().documentLayout().draw(mp, mctx)
                mp.end()

                ring = QImage(mask_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
                ring.fill(Qt.GlobalColor.transparent)
                rp = QPainter(ring)
                rp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                rp.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
                for dx, dy in self._outline_offsets(ow):
                    rp.drawImage(dx, dy, mask_img)
                rp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
                rp.drawImage(0, 0, mask_img)
                rp.end()

                tint = QImage(ring.size(), QImage.Format.Format_ARGB32_Premultiplied)
                tint.fill(Qt.GlobalColor.transparent)
                tp = QPainter(tint)
                tp.fillRect(tint.rect(), qcolor_from_hex(self.style.outline))
                tp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                tp.drawImage(0, 0, ring)
                tp.end()
                painter.drawImage(QPointF(br.left() - pad, br.top() - pad), tint)
            else:
                br = super().boundingRect()
                pad = 2
                w = max(1, int(math.ceil(br.width())))
                h = max(1, int(math.ceil(br.height())))

                    # Mask Image (Text in White)
                mask_img = QImage(w + pad*2, h + pad*2, QImage.Format.Format_ARGB32_Premultiplied)
                mask_img.fill(Qt.GlobalColor.transparent)
                mp = QPainter(mask_img)
                mp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                mp.translate(pad - br.left(), pad - br.top())

                # Draw Mask without state mutation
                ctx = QAbstractTextDocumentLayout.PaintContext()
                ctx.palette.setColor(QPalette.ColorRole.Text, QColor('white'))
                self.document().documentLayout().draw(mp, ctx)
                mp.end()

                # Fill Image
                fill_img = QImage(mask_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
                fill_img.fill(Qt.GlobalColor.transparent)
                fp = QPainter(fill_img)
                fp.setRenderHint(QPainter.RenderHint.Antialiasing, True)

                # Draw Gradient/Texture on Fill Image
                if fill_type == 'linear_gradient' and self.style.gradient_stops:
                    angle = float(getattr(self.style, 'gradient_angle', 0))
                    import math as _math
                    rad = _math.radians(angle)
                    cx, cy = fill_img.width()/2, fill_img.height()/2
                    dx = _math.cos(rad) * cx; dy = _math.sin(rad) * cy
                    x1 = cx - dx; y1 = cy - dy; x2 = cx + dx; y2 = cy + dy
                    grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))
                    stops = getattr(self.style, 'gradient_stops', []) or []
                    for pos, col in stops:
                        try: grad.setColorAt(float(pos), qcolor_from_hex(col))
                        except Exception: pass
                    fp.fillRect(fill_img.rect(), grad)
                elif fill_type == 'texture' and getattr(self.style, 'texture_path', ''):
                    tp = getattr(self.style, 'texture_path', '')
                    pm = QPixmap(tp) if tp else QPixmap()
                    if not pm.isNull():
                        tex_scale = float(getattr(self.style, 'texture_scale', 1.0) or 1.0)
                        tex_scale = clamp(tex_scale, 0.05, 10.0)
                        tex_angle = float(getattr(self.style, 'texture_angle', 0))
                        if getattr(self.style, 'texture_tile', True):
                            brush = QBrush(pm)
                            tr = QTransform()
                            tr.scale(tex_scale, tex_scale)
                            tr.rotate(tex_angle)
                            brush.setTransform(tr)
                            fp.fillRect(fill_img.rect(), brush)
                        else:
                            # Fondo base para cubrir zonas vacías al rotar/zoom
                            fp.fillRect(fill_img.rect(), target_fill)
                            fp.save()
                            fp.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                            cx = fill_img.width() / 2.0
                            cy = fill_img.height() / 2.0
                            fit_scale = min(fill_img.width() / max(1, pm.width()), fill_img.height() / max(1, pm.height()))
                            fp.translate(cx, cy)
                            fp.rotate(tex_angle)
                            fp.scale(fit_scale * tex_scale, fit_scale * tex_scale)
                            fp.translate(-pm.width() / 2.0, -pm.height() / 2.0)
                            fp.drawPixmap(0, 0, pm)
                            fp.restore()
                    else:
                        fp.fillRect(fill_img.rect(), target_fill)
                else:
                    fp.fillRect(fill_img.rect(), target_fill)
                fp.end()

                # Composite
                result = QImage(fill_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
                result.fill(Qt.GlobalColor.transparent)
                rp = QPainter(result)
                rp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                rp.drawImage(0, 0, fill_img)
                rp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                rp.drawImage(0, 0, mask_img)
                rp.end()

                painter.drawImage(QPointF(br.left()-pad, br.top()-pad), result)

                # Draw selection indicators if selected (since super().paint isn't called)
                if self.isSelected() or (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsFocusable and self.hasFocus()):
                     # We can't easily draw the exact cursor/selection overlay of QGraphicsTextItem manually
                     # without super().paint.
                     # But for gradient text, usually we accept losing the native cursor blink
                     # in exchange for the effect.
                     # However, to support editing, we might want to draw the cursor?
                     # A workaround: Draw standard paint with composition mode?
                     # For now, let's leave it as is (visual effect dominates).
                     pass

        except Exception:
            # Fallback
            super().paint(painter, option, widget)

        self._draw_overlays(painter)

    def _draw_overlays(self, painter: QPainter):
        try:
            if getattr(self, 'ordinal', -1) >= 0 and not getattr(self, '_suppress_overlays', False) and self.SHOW_ORDINAL:
                br = super().boundingRect()
                r = 10
                center = QPointF(br.left() + r + 6, br.top() + r + 6)
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor('#E11D48'))
                painter.drawEllipse(center, r, r)
                painter.setPen(QPen(QColor('white')))
                f = painter.font(); f.setBold(True); f.setPointSize(9); painter.setFont(f)
                painter.drawText(QRectF(center.x()-r, center.y()-r, 2*r, 2*r),
                                 int(Qt.AlignmentFlag.AlignCenter), str(self.ordinal))
                painter.restore()
        except Exception:
            pass

        if self.isSelected():
            br = super().boundingRect(); acc = accent_qcolor()
            painter.setPen(QPen(acc, 1, Qt.PenStyle.DashLine)); painter.drawRect(br)
            if not self.locked:
                painter.setOpacity(1.0)
                handle_color = QColor('#FF4500')
                border_color = QColor('white')

                painter.setPen(QPen(border_color, 2)); painter.setBrush(handle_color)
                painter.drawRect(self._handle_rect())

                c = self._rot_handle_center()
                top_mid = QPointF((br.left()+br.right())/2.0, br.top())
                painter.setPen(QPen(border_color, 2))
                painter.drawLine(top_mid, QPointF(c.x(), c.y() + self.ROT_HANDLE_R))
                painter.setPen(QPen(border_color, 2)); painter.setBrush(handle_color)
                painter.drawEllipse(c, self.ROT_HANDLE_R, self.ROT_HANDLE_R)

                painter.setPen(QPen(border_color, 2)); painter.setBrush(handle_color)
                for corner in self._rot_corner_centers():
                    painter.drawEllipse(corner, self.ROT_CORNER_R, self.ROT_CORNER_R)


    def hoverMoveEvent(self, event):
        if self.locked:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor)); super().hoverMoveEvent(event); return
        if self._handle_hitbox().contains(event.pos()):
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif self._hit_rot_corner(event.pos()):
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        else:
            c = self._rot_handle_center()
            if (event.pos() - c).manhattanLength() <= self.ROT_HANDLE_R + 3:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if self.locked:
            super().mousePressEvent(event); event.accept(); return
        self._start_pos = self.pos()
        if self._handle_hitbox().contains(event.pos()):
            self._resizing = True; self._resize_start_width = self.textWidth()
            self._resize_start_pos = event.pos()
            self._resize_alt_scale = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
            self._start_font_pt = float(self.style.font_point_size); self._start_outline = float(self.style.outline_width)
            event.accept(); return
        # Rotation on Alt+Drag (anywhere in item) OR Handle/Corner Click
        handle_clicked = False
        c = self._rot_handle_center()
        if (event.pos() - c).manhattanLength() <= self.ROT_HANDLE_R + 3:
            handle_clicked = True
        corner_clicked = self._hit_rot_corner(event.pos())

        if handle_clicked or corner_clicked or (QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier):
            self._rotating = True; self._rot_base = self.rotation()
            center_scene = self.mapToScene(super().boundingRect().center())
            pos_scene = self.mapToScene(event.pos())
            self._rot_start_angle = math.degrees(math.atan2(
                pos_scene.y()-center_scene.y(), pos_scene.x()-center_scene.x()))
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor)); event.accept(); return
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.locked: event.accept(); return
        if self._resizing:
            dx = event.pos().x() - self._resize_start_pos.x()
            new_w = clamp(self._resize_start_width + dx, 50, 2000); self.setTextWidth(new_w)
            alt_now = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
            if self._resize_alt_scale or alt_now:
                scale = max(0.1, new_w / max(1.0, self._resize_start_width))
                new_pt = clamp(self._start_font_pt * scale, 4, 200)
                new_ow = int(clamp(self._start_outline * scale, 0, 40))
                self.style.font_point_size = int(round(new_pt)); self.style.outline_width = int(new_ow)
                self.setFont(self.style.to_qfont())
            self.update()
            if scene := self.scene(): scene.update()
            return
        if self._rotating:
            center_scene = self.mapToScene(super().boundingRect().center())
            pos_scene = self.mapToScene(event.pos())
            # Evitar sensibilidad extrema cuando el cursor está muy cerca del centro
            dx = pos_scene.x() - center_scene.x()
            dy = pos_scene.y() - center_scene.y()
            if (dx * dx + dy * dy) < (self.ROT_MIN_RADIUS * self.ROT_MIN_RADIUS):
                return
            cur_angle = math.degrees(math.atan2(
                pos_scene.y()-center_scene.y(), pos_scene.x()-center_scene.x()))
            delta = (cur_angle - self._rot_start_angle) * self.ROT_SENSITIVITY
            new = self._rot_base + delta
            if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier:
                new = round(new / 15.0) * 15.0
            self.setRotation(new)
            if scene := self.scene(): scene.update()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.locked: event.accept(); return
        scene = self.scene()
        if self._resizing:
            self._resizing = False; new_w = self.textWidth(); old_w = self._resize_start_width
            scaled = self._resize_alt_scale or bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
            new_pt = float(self.style.font_point_size); old_pt = float(self._start_font_pt)
            new_ow = int(self.style.outline_width); old_ow = int(self._start_outline)
            if scene and hasattr(scene, 'undo_stack') and (
                abs(new_w - old_w) > 0.5 or (scaled and (abs(new_pt-old_pt)>0.01 or new_ow!=old_ow))
            ):
                stack = scene.undo_stack; item = self
                def undo():
                    item.setTextWidth(old_w)
                    if scaled:
                        item.style.font_point_size = int(round(old_pt))
                        item.style.outline_width = int(old_ow)
                        item.setFont(item.style.to_qfont())
                def redo():
                    item.setTextWidth(new_w)
                    if scaled:
                        item.style.font_point_size = int(round(new_pt))
                        item.style.outline_width = int(new_ow)
                        item.setFont(item.style.to_qfont())
                push_cmd(stack, "Escalar caja+fuente" if scaled else "Redimensionar caja", undo, redo)
            event.accept(); return

        if self._rotating:
            self._rotating = False; new = self.rotation(); old = self._rot_base
            if scene and hasattr(scene, 'undo_stack') and abs(new - old) > 0.01:
                item = self; stack = scene.undo_stack
                push_cmd(stack, "Rotar caja", lambda: item.setRotation(old),
                         lambda: item.setRotation(new))
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor)); event.accept(); return

        super().mouseReleaseEvent(event)
        if scene and hasattr(scene, 'undo_stack') and self.pos() != self._start_pos:
            item = self; old = QPointF(self._start_pos); new = QPointF(self.pos()); stack = scene.undo_stack
            push_cmd(stack, "Mover", lambda: item.setPos(old), lambda: item.setPos(new))

    def mouseDoubleClickEvent(self, event):
        if not self.locked:
            if self._handle_hitbox().contains(event.pos()): event.accept(); return
            if self._hit_rot_corner(event.pos()): event.accept(); return
            c = self._rot_handle_center()
            if (event.pos() - c).manhattanLength() <= self.ROT_HANDLE_R + 3: event.accept(); return
        self._clear_soft_hyphens()
        self._old_text = self.get_raw_text()
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        # Deja que Qt maneje la posición del cursor según el clic
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        scene = self.scene()
        self._raw_text = self._strip_soft_hyphens(self.document().toPlainText())
        if scene and hasattr(scene, 'undo_stack'):
            new = self.get_raw_text()
            if new != self._old_text:
                item = self; old = self._old_text; stack = scene.undo_stack
                push_cmd(stack, "Editar texto",
                         lambda: (item.setPlainText(old), item._apply_paragraph_to_doc()),
                         lambda: (item.setPlainText(new), item._apply_paragraph_to_doc()))
        self._update_soft_hyphens()

    def apply_bold_to_selection(self):
        """Aplica negrita solo al texto seleccionado (no a toda la caja)."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False
        
        # Obtener el formato actual de la selección
        fmt = cursor.charFormat()
        # Alternar negrita
        is_bold = fmt.fontWeight() == QFont.Weight.Bold
        fmt.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        
        # Aplicar el formato a la selección
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)
        return True

    def keyPressEvent(self, event):
        """Maneja atajos de teclado durante la edición de texto."""
        # Ctrl+B para aplicar negrita a la selección
        if event.key() == Qt.Key.Key_B and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.textInteractionFlags() == Qt.TextInteractionFlag.TextEditorInteraction:
                self.apply_bold_to_selection()
                event.accept()
                return
        # Pasar otros eventos al comportamiento por defecto
        super().keyPressEvent(event)



    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'pos': [self.pos().x(), self.pos().y()],
            'text': self.get_raw_text(),
            'width': self.textWidth(),
            'rotation': self.rotation(),
            'locked': bool(self.locked),
            'style': asdict(self.style),
            'ordinal': int(getattr(self, 'ordinal', -1)),
        }
    @staticmethod
    def from_dict(d: Dict) -> 'StrokeTextItem':
        st = TextStyle(**d['style'])
        item = StrokeTextItem(d.get('text', ''), st, name=d.get('name', 'Texto'))
        item.ordinal = int(d.get('ordinal', -1))
        item.setTextWidth(d.get('width', 400))
        # Guardar datos para aplicar DESPUÉS de agregarse a la escena
        item._restore_pos = QPointF(*d.get('pos', [0, 0]))
        item._restore_rotation = float(d.get('rotation', 0.0))
        item.set_locked(bool(d.get('locked', False)))
        item.apply_shadow()
        return item

# ---------------- Ítem de marca de agua ----------------
class WatermarkItem(QGraphicsPixmapItem):
    """Marca de agua arrastrable con asa de redimensión (esquina inferior derecha).
    Mantiene la relación de aspecto. Se dibuja por encima del fondo y por debajo del texto.
    Además, notifica cambios de posición/escala para que se persistan.
    """
    HANDLE_SIZE = 12
    def __init__(self, pm: QPixmap):
        super().__init__(pm)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self._resizing = False
        # callback opcional para avisar a PageContext
        self.on_changed = None  # type: Optional[Callable[["WatermarkItem"], None]]

    def _handle_rect(self) -> QRectF:
        br = super().boundingRect(); s = self.HANDLE_SIZE
        return QRectF(br.right()-s, br.bottom()-s, s, s)

    def _handle_hitbox(self) -> QRectF:
        """Hitbox más grande para facilitar el click en el resize handle"""
        br = super().boundingRect()
        s = self.HANDLE_SIZE
        # Hitbox 3x más grande que el visual
        hitbox_size = s * 3
        return QRectF(br.right()-hitbox_size, br.bottom()-hitbox_size, hitbox_size, hitbox_size)

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            acc = accent_qcolor(); br = super().boundingRect()
            painter.setPen(QPen(acc, 1, Qt.PenStyle.DashLine)); painter.drawRect(br)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(acc)
            painter.drawRect(self._handle_rect())

    def hoverMoveEvent(self, event):
        if self._handle_hitbox().contains(event.pos()):
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor if self.isSelected() else Qt.CursorShape.ArrowCursor))
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if self._handle_hitbox().contains(event.pos()):
            self._resizing = True; event.accept(); return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            pm = self.pixmap()
            if not pm.isNull():
                w, h = pm.width(), pm.height()
                new_w_local = max(10.0, event.pos().x())
                new_h_local = max(10.0, event.pos().y())
                sx = new_w_local / float(max(1, w))
                sy = new_h_local / float(max(1, h))
                s = clamp(max(sx, sy), 0.05, 10.0)
                self.setScale(s)
                self.update(); sc = self.scene(); sc and sc.update()
            event.accept(); return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing:
            self._resizing = False
            # avisar que cambió el tamaño/escala
            try:
                if callable(self.on_changed):
                    self.on_changed(self)
            except Exception:
                pass
            event.accept(); return
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            try:
                if callable(self.on_changed):
                    self.on_changed(self)
            except Exception:
                pass
        return super().itemChange(change, value)

class CanvasView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15; self.scale(factor, factor)
        else:
            super().wheelEvent(event)

class RawView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self._pix_item = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._zoom = 1.0
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    def set_pixmap(self, pix: Optional[QPixmap]):
        self.scene().clear(); self._pix_item = None
        if pix is None or pix.isNull(): self.resetTransform(); self._zoom = 1.0; return
        self._pix_item = self.scene().addPixmap(pix)
        self.scene().setSceneRect(self._pix_item.boundingRect())
        self.resetTransform(); self._zoom = 1.0
    def wheelEvent(self, event):
        delta = event.angleDelta().y(); factor = 1.15 if delta > 0 else 1/1.15
        self._zoom *= factor
        if self._zoom < 0.05: self._zoom = 0.05; return
        if self._zoom > 40.0: self._zoom = 40.0; return
        self.scale(factor, factor)

# ---------------- Pestaña ----------------
class PageContext(QWidget):
    def __init__(self, img: QPixmap | None = None, path: Optional[Path] = None):

        super().__init__()
        
        # Obtener factor de escala
        app = QApplication.instance()
        self.scale_factor = app.property("ui_scale_factor") if app else 1.0
        if not self.scale_factor:
            self.scale_factor = 1.0

        self.scene = QGraphicsScene(self)

        self.view = CanvasView(self.scene)

        self.undo_stack = QUndoStack(self)

        self.scene.undo_stack = self.undo_stack

        self.scene.selectionChanged.connect(self.on_scene_selection_changed)


        self.bg_item: Optional[QGraphicsPixmapItem] = None


        # Lista de globos/capas

        self.layer_list = QListWidget()

        self.layer_list.currentItemChanged.connect(self.on_layer_selected)
        # Enable drag & drop reordering so users can change layer stacking order
        from PyQt6.QtWidgets import QAbstractItemView
        self.layer_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        # Connect to rowsMoved to update scene Z-values after reorder
        try:
            self.layer_list.model().rowsMoved.connect(self._on_layers_reordered)
        except Exception:
            # Some PyQt versions may not emit this or model may be different
            pass


        # --- Panel colapsable al estilo Photoshop ---

        self.layer_panel = QWidget()

        panel_layout = QVBoxLayout(self.layer_panel)

        panel_layout.setContentsMargins(0, 0, 0, 0)

        panel_layout.setSpacing(0)


        self.layer_toggle_btn = QToolButton(self.layer_panel)

        self.layer_toggle_btn.setCheckable(True)

        self.layer_toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        # Flecha hacia la derecha ▶ cuando el panel está expandido

        self.layer_toggle_btn.setArrowType(Qt.ArrowType.RightArrow)

        self.layer_toggle_btn.setFixedWidth(scale_size(24, self.scale_factor))

        self.layer_toggle_btn.toggled.connect(self.toggle_layer_panel)


        panel_layout.addWidget(self.layer_toggle_btn, 0)

        panel_layout.addWidget(self.layer_list, 1)


        # Ancho normal cuando está expandido (escalado)

        self.layer_panel.setMaximumWidth(scale_size(180, self.scale_factor))


        self._next_ordinal = 1

        self.bg_image: Optional[QImage] = None


        # --- Marca de agua ---

        self.watermark_item: Optional[WatermarkItem] = None

        # Estado normalizado de la marca de agua (relativo a la imagen de fondo)

        self._wm_norm_pos: Optional[Tuple[float, float]] = None  # (x_rel, y_rel)

        self._wm_scale: float = 1.0

        self._wm_user_moved: bool = False

        # --- Tracking de cambios sin guardar ---
        self.has_unsaved_changes: bool = False
        self.saved_file_path: Optional[str] = None
        
        # --- Workflow automation data ---
        self.workflow_data: Optional[Dict] = None  # Stores detection data for persistence


        # Layout principal: lienzo + panel de globos

        lay = QHBoxLayout(self)

        lay.setContentsMargins(0, 0, 0, 0)

        lay.addWidget(self.view, 1)

        lay.addWidget(self.layer_panel, 0)


        self.background_path = str(path) if path else ""

        if img is not None:

            self.set_background(img)


    def toggle_layer_panel(self, checked: bool):

        """Colapsa/expande el panel de globos al estilo Photoshop."""

        if checked:

            # Colapsado: solo la tirita con el botón

            self.layer_list.hide()

            # Ancho reducido, casi solo el botón

            self.layer_panel.setMaximumWidth(self.layer_toggle_btn.width() + scale_size(8, self.scale_factor))

            # Flecha hacia la izquierda ◀ (indica que se puede expandir)

            self.layer_toggle_btn.setArrowType(Qt.ArrowType.LeftArrow)

        else:

            # Expandido: se ve la lista completa

            self.layer_list.show()

            self.layer_panel.setMaximumWidth(scale_size(180, self.scale_factor))

            # Flecha hacia la derecha ▶ (indica que se puede colapsar)

            self.layer_toggle_btn.setArrowType(Qt.ArrowType.RightArrow)


    def set_background(self, pix: QPixmap):

        # Limpiar escena y poner la imagen de fondo

        self.scene.clear()

        self.bg_item = QGraphicsPixmapItem(pix)

        self.scene.addItem(self.bg_item)

        self.layer_list.clear()

        self.bg_image = pix.toImage()


        # --- Añadir margen extra alrededor de la página para poder desplazarse más ---

        if self.bg_item is not None:

            rect = self.bg_item.boundingRect()


            MARGIN_X = 200       # margen a izquierda/derecha

            MARGIN_TOP = 100     # margen arriba

            MARGIN_BOTTOM = 600  # margen grande abajo para ver texto cercano al borde


            expanded = rect.adjusted(

                -MARGIN_X,

                -MARGIN_TOP,

                MARGIN_X,

                MARGIN_BOTTOM

            )

            self.scene.setSceneRect(expanded)


        # La marca de agua (si existe) se volverá a aplicar desde MangaTextTool
        self.scene.clear(); self.bg_item = QGraphicsPixmapItem(pix)
        self.scene.addItem(self.bg_item); self.layer_list.clear()
        self.bg_image = pix.toImage()
        # La marca de agua (si existe) se volverá a aplicar desde MangaTextTool

    # ---- Marca de agua: API del contexto ----
    def set_watermark(self, image_path: str, opacity: float = 0.2):
        try:
            pm = QPixmap(image_path)
        except Exception:
            return
        if pm.isNull():
            return
        # Guardar posición/escala actuales (si existían) en forma normalizada
        prev_norm = None; prev_scale = None
        if self.watermark_item is not None and self.bg_item is not None:
            try:
                br = self.bg_item.boundingRect()
                tl = self.bg_item.scenePos()
                pos = self.watermark_item.pos()
                nx = (pos.x() - tl.x()) / max(1.0, br.width())
                ny = (pos.y() - tl.y()) / max(1.0, br.height())
                prev_norm = (nx, ny)
                prev_scale = float(self.watermark_item.scale())
            except Exception:
                pass
        # eliminar anterior si existía
        if self.watermark_item is not None:
            try:
                self.scene.removeItem(self.watermark_item)
            except Exception:
                pass
            self.watermark_item = None
        # Crear nuevo ítem
        wm = WatermarkItem(pm)
        wm.setOpacity(clamp(opacity, 0.0, 1.0))
        self.watermark_item = wm
        # Conectar callback para persistir cambios
        try:
            wm.on_changed = lambda _=None: self._watermark_changed()
        except Exception:
            pass
        # Posición/escala inicial: 1) lo anterior del contexto; 2) lo que esté en settings globales; 3) esquina sup. izq.
        if self.bg_item is not None:
            br = self.bg_item.boundingRect(); tl = self.bg_item.scenePos()
            norm = prev_norm or (self._wm_norm_pos if self._wm_user_moved and self._wm_norm_pos is not None else None)
            if norm is None:
                try:
                    win = self.window()
                    if hasattr(win, 'wm_pos_norm') and win.wm_pos_norm:
                        norm = tuple(win.wm_pos_norm)
                except Exception:
                    norm = None
            if norm is not None:
                px = tl.x() + float(norm[0]) * br.width()
                py = tl.y() + float(norm[1]) * br.height()
                wm.setPos(QPointF(px, py))
            else:
                wm.setPos(QPointF(tl.x(), tl.y()))
            sc = prev_scale
            if sc is None:
                sc = self._wm_scale if self._wm_user_moved else None
            if sc is None:
                try:
                    win = self.window()
                    sc = float(getattr(win, 'wm_scale', 1.0))
                except Exception:
                    sc = 1.0
            wm.setScale(float(sc))
            wm.setZValue(self.bg_item.zValue() + 0.1)
        self.scene.addItem(wm)
        self.scene.update()

    def set_watermark_opacity(self, opacity: float):
        if self.watermark_item is not None:
            self.watermark_item.setOpacity(clamp(opacity, 0.0, 1.0))
            self.scene.update()

    def remove_watermark(self):
        if self.watermark_item is not None:
            try:
                self.scene.removeItem(self.watermark_item)
            except Exception:
                pass
            self.watermark_item = None
            self.scene.update()

    def _watermark_changed(self):
        """Se llama cuando el usuario mueve o redimensiona la marca de agua.
        Guarda posición normalizada y escala en el contexto y en QSettings (vía ventana).
        """
        if self.watermark_item is None or self.bg_item is None:
            return
        try:
            br = self.bg_item.boundingRect(); tl = self.bg_item.scenePos(); pos = self.watermark_item.pos()
            nx = (pos.x() - tl.x()) / max(1.0, br.width())
            ny = (pos.y() - tl.y()) / max(1.0, br.height())
            self._wm_norm_pos = (float(clamp(nx, 0.0, 1.0)), float(clamp(ny, 0.0, 1.0)))
            self._wm_scale = float(max(0.05, self.watermark_item.scale()))
            self._wm_user_moved = True
            # pedir a la ventana que persista
            try:
                win = self.window()
                if hasattr(win, '_update_wm_settings_from_ctx'):
                    win._update_wm_settings_from_ctx(self)
            except Exception:
                pass
        except Exception:
            pass

    def current_item(self) -> Optional[StrokeTextItem]:
        it = self.layer_list.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def selected_text_items(self) -> List[StrokeTextItem]:
        items = [it for it in self.scene.selectedItems() if isinstance(it, StrokeTextItem)]
        return items or ([self.current_item()] if self.current_item() else [])

    def add_item_and_list(self, item: StrokeTextItem):
        if item.scene() is None: 
            self.scene.addItem(item)
        
        # Aplicar posición y rotación guardadas INMEDIATAMENTE después de agregar a la escena
        # Usar QTimer para garantizar que Qt haya procesado el addItem() antes de setPos()
        def apply_transforms():
            try:
                # Helper to apply a stored position; make it relative to background if that seems intended
                def _apply_pos(stored_pos_attr):
                    stored = getattr(item, stored_pos_attr, None)
                    if stored is None:
                        return
                    try:
                        # Default: use stored directly
                        final = QPointF(stored)
                        # If item is in a scene with a PageContext that has a bg_item,
                        # and the stored coords lie within the background bounds, treat
                        # the stored coords as relative to the background top-left.
                        sc = item.scene()
                        if sc is not None and hasattr(sc, 'parent'):
                            ctx = sc.parent()
                            try:
                                bg = getattr(ctx, 'bg_item', None)
                                if bg is not None and isinstance(bg, QGraphicsPixmapItem):
                                    pm = bg.pixmap()
                                    if not pm.isNull():
                                        w = pm.width(); h = pm.height()
                                        if 0 <= stored.x() <= w and 0 <= stored.y() <= h:
                                            final = bg.pos() + stored
                            except Exception:
                                pass
                        item.setPos(final)
                    except Exception:
                        pass
                    try:
                        delattr(item, stored_pos_attr)
                    except Exception:
                        pass

                if hasattr(item, '_restore_pos'):
                    _apply_pos('_restore_pos')
                if hasattr(item, '_restore_rotation'):
                    try: item.setRotation(item._restore_rotation)
                    except Exception: pass
                    try: delattr(item, '_restore_rotation')
                    except Exception: pass
                if hasattr(item, '_pending_pos'):
                    _apply_pos('_pending_pos')
                if hasattr(item, '_pending_rotation'):
                    try: item.setRotation(item._pending_rotation)
                    except Exception: pass
                    try: delattr(item, '_pending_rotation')
                    except Exception: pass
            except Exception:
                pass
        
        # Ejecutar en el próximo ciclo de eventos
        QTimer.singleShot(0, apply_transforms)
        
        try:
            if getattr(item, 'ordinal', -1) < 0:
                item.ordinal = self._next_ordinal
                self._next_ordinal += 1
        except Exception:
            pass
        text_label = f"{item.ordinal:02d} · {item.name}" if getattr(item, 'ordinal', -1) >= 0 else item.name
        li = QListWidgetItem(text_label); li.setData(Qt.ItemDataRole.UserRole, item)
        li.setToolTip("Fijado" if item.locked else "")
        self.layer_list.addItem(li); self.layer_list.setCurrentItem(li)
        # Recalcular Z-values para que el índice de la lista refleje el apilamiento
        try:
            self._recalc_z_from_list()
        except Exception:
            pass

    def _recalc_z_from_list(self):
        """Recalcula los z-values de todos los items según el orden actual de la lista.

        El índice 0 de la lista se considera el topmost (mayor Z).
        """
        try:
            count = self.layer_list.count()
            for i in range(count):
                it = self.layer_list.item(i)
                obj = it.data(Qt.ItemDataRole.UserRole)
                try:
                    if isinstance(obj, QGraphicsItem):
                        obj.setZValue(count - i)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_layers_reordered(self, parent, start, end, destination, row):
        """Recalculate Z-values for items according to the new list order.

        The item at list index 0 will be treated as topmost (higher Z).
        """
        try:
            count = self.layer_list.count()
            for i in range(count):
                it = self.layer_list.item(i)
                obj = it.data(Qt.ItemDataRole.UserRole)
                # Many layer objects are QGraphicsItem-derived; set Z accordingly
                try:
                    if isinstance(obj, QGraphicsItem):
                        obj.setZValue(count - i)
                except Exception:
                    pass
        except Exception:
            pass

    def remove_item_from_list(self, item: StrokeTextItem):
        for i in range(self.layer_list.count()):
            it = self.layer_list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) is item:
                self.layer_list.takeItem(i); break

    def on_layer_selected(self, cur: QListWidgetItem, prev: QListWidgetItem):
        item = self.current_item()
        if not item:
            try:
                win = self.window()
                if hasattr(win, "_update_font_button_state"):
                    win._update_font_button_state([])
            except Exception:
                pass
            return
        for i in range(self.layer_list.count()):
            itw = self.layer_list.item(i); obj: StrokeTextItem = itw.data(Qt.ItemDataRole.UserRole)
            obj.setSelected(obj is item)
        try:
            win = self.window()
            if hasattr(win, "_sync_props_from_item"): win._sync_props_from_item(item)
        except Exception: pass

    def on_scene_selection_changed(self):
        sel = self.scene.selectedItems()
        if not sel:
            try:
                win = self.window()
                if hasattr(win, "_update_font_button_state"):
                    win._update_font_button_state([])
            except Exception:
                pass
            return
        item = sel[0]
        for i in range(self.layer_list.count()):
            it = self.layer_list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) is item:
                if self.layer_list.currentRow() != i: self.layer_list.setCurrentRow(i)
                break
        try:
            win = self.window()
            if hasattr(win, "_sync_props_from_item"): win._sync_props_from_item(item)
        except Exception: pass

# ---------------- Ocultador de selección para export ----------------
class _SelectionHider:
    def __init__(self, scene: QGraphicsScene):
        self.scene = scene
        self.states: List[dict] = []
    def __enter__(self):
        for it in self.scene.items():
            try:
                is_sel = bool(it.isSelected())
            except Exception:
                is_sel = False
            state = {'it': it, 'sel': is_sel}
            if isinstance(it, StrokeTextItem):
                state['had_focus'] = bool(it.hasFocus())
                try:
                    state['flags'] = it.textInteractionFlags()
                except Exception:
                    state['flags'] = None
                try:
                    cur = it.textCursor()
                    state['cursor_pos'] = cur.position()
                    state['cursor_anc'] = cur.anchor()
                    if cur.hasSelection():
                        cur.clearSelection()
                        it.setTextCursor(cur)
                except Exception:
                    state['cursor_pos'] = state['cursor_anc'] = None
                try:
                    state['suppress'] = getattr(it, '_suppress_overlays', False)
                    it._suppress_overlays = True
                except Exception:
                    state['suppress'] = False
                try:
                    it.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                except Exception:
                    pass
                try:
                    it.clearFocus()
                except Exception:
                    pass
            if is_sel:
                try:
                    it.setSelected(False)
                except Exception:
                    pass
            self.states.append(state)
        try:
            self.scene.clearSelection()
        except Exception:
            pass
        self.scene.update()
        return self
    def __exit__(self, exc_type, exc, tb):
        for s in self.states:
            it = s.get('it')
            try:
                if isinstance(it, StrokeTextItem):
                    try:
                        it._suppress_overlays = s.get('suppress', False)
                    except Exception:
                        pass
                    if s.get('flags') is not None:
                        try:
                            it.setTextInteractionFlags(s['flags'])
                        except Exception:
                            pass
                    if s.get('cursor_pos') is not None:
                        try:
                            cur = it.textCursor()
                            anc = s.get('cursor_anc', s['cursor_pos'])
                            cur.setPosition(anc)
                            cur.setPosition(s['cursor_pos'], QTextCursor.MoveMode.KeepAnchor)
                            it.setTextCursor(cur)
                        except Exception:
                            pass
                    if s.get('had_focus'):
                        try:
                            it.setFocus()
                        except Exception:
                            pass
                if s.get('sel'):
                    it.setSelected(True)
            except Exception:
                pass
        self.scene.update()

# ---------------- Persistencia de presets ----------------
def load_presets_from_settings(settings: QSettings) -> Dict[str, TextStyle]:
    data = settings.value('presets_json', type=str)
    if not data: return default_presets()
    try:
        raw = json.loads(data); out: Dict[str, TextStyle] = {}
        for k, v in raw.items(): out[k] = TextStyle(**v)
        return out
    except Exception: return default_presets()

def save_presets_to_settings(settings: QSettings, presets: Dict[str, TextStyle]):
    raw = {k: asdict(v) for k, v in presets.items()}
    settings.setValue('presets_json', json.dumps(raw))

def upgrade_presets_with_defaults(presets: Dict[str, TextStyle]) -> bool:
    defs = default_presets(); changed = False
    for k, v in defs.items():
        if k not in presets: presets[k] = v; changed = True
    return changed

# ---------------- Login Dialog ----------------
class LoginDialog(QDialog):
    """
    Diálogo de acceso simple:
    - Pide usuario de Discord.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Obtener factor de escala
        scale = get_ui_scale_factor()

        self.setWindowTitle("Acceso - AnimeBBG Editor")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setFixedSize(scale_size(500, scale), scale_size(280, scale))
        self.setModal(True)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(scale_size(24, scale), scale_size(24, scale), 
                                     scale_size(24, scale), scale_size(24, scale))
        mainLayout.setSpacing(scale_size(12, scale))
        
        # Tamaños de fuente escalados
        label_font_size = int(13 * scale)
        input_padding = f"{int(10*scale)}px {int(12*scale)}px"
        button_padding = f"{int(8*scale)}px {int(22*scale)}px"
        subtitle_font_size = int(12 * scale)

        self.setStyleSheet(f"""
        QDialog {{
            background-color: #020617;
        }}
        QLabel {{
            color: #e5e7eb;
            font-size: {label_font_size}px;
        }}
        QLineEdit {{
            padding: {input_padding};
            border-radius: 8px;
            border: 1px solid #4b5563;
            background-color: #020617;
            color: #f9fafb;
        }}
        QLineEdit:focus {{
            border: 1px solid #ec4899;
        }}
        QPushButton {{
            padding: {button_padding};
            border-radius: 999px;
            background-color: #ec4899;
            color: white;
            border: none;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: #f472b6;
        }}
        QPushButton:disabled {{
            background-color: #4b5563;
            color: #9ca3af;
        }}
        """)

        title = QLabel("Usuario de Discord")
        tfont = title.font()
        tfont.setPointSize(int(15 * scale))
        tfont.setBold(True)
        title.setFont(tfont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Ingresa tu usuario de Discord")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: #9ca3af; font-size: {subtitle_font_size}px;")

        mainLayout.addWidget(title)
        mainLayout.addWidget(subtitle)

        formLayout = QVBoxLayout()
        lbl_user = QLabel("Usuario de Discord")
        self.edit_user = QLineEdit(self)
        self.edit_user.setPlaceholderText("Usuario1234")

        formLayout.addWidget(lbl_user)
        formLayout.addWidget(self.edit_user)

        info = QLabel(
            "Aviso: Esto es solo una verficación para quienes sean del Scan\n"
            "Solo es una medida preventiva."
        )
        info.setWordWrap(True)
        info_font_size = int(11 * scale)
        info.setStyleSheet(f"color: #6b7280; font-size: {info_font_size}px;")
        formLayout.addWidget(info)

        mainLayout.addLayout(formLayout)
        mainLayout.addStretch(1)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch(1)

        self.loginButton = QPushButton("Acceder", self)
        self.loginButton.setEnabled(False)
        self.loginButton.setDefault(True)

        btn_font_size = int(14 * scale)
        btn_padding = f"{int(6*scale)}px {int(16*scale)}px"
        self.loginButton.setStyleSheet(f"""
    QPushButton {{
        background-color: #2e86de;
        color: white;
        border-radius: 8px;
        padding: {btn_padding};
        font-size: {btn_font_size}px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #1b4f72;
    }}
    QPushButton:pressed {{
        background-color: #154360;
    }}
    QPushButton:disabled {{
        background-color: #b0b0b0;
        color: #eeeeee;
    }}
""")

        buttonLayout.addWidget(self.loginButton)
        mainLayout.addLayout(buttonLayout)

        self.edit_user.textChanged.connect(self._on_text_changed)
        self.edit_user.returnPressed.connect(self._try_accept)
        self.loginButton.clicked.connect(self._try_accept)

    def _on_text_changed(self, text: str):
        self.loginButton.setEnabled(bool(text.strip()))

    def _try_accept(self):
        if not self.edit_user.text().strip():
            return
        self.accept()

    def get_username(self) -> str:
        return self.edit_user.text().strip()

# ---------------- Ventana "Nosotros" ----------------
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Obtener factor de escala
        scale = get_ui_scale_factor()

        self.setWindowTitle("Nosotros – AnimeBBG")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setModal(True)
        self.resize(scale_size(460, scale), scale_size(320, scale))

        main = QVBoxLayout(self)
        main.setContentsMargins(scale_size(16, scale), scale_size(16, scale), 
                               scale_size(16, scale), scale_size(16, scale))
        main.setSpacing(scale_size(10, scale))

        # Línea superior
        top_line = QFrame()
        top_line.setFrameShape(QFrame.Shape.HLine)
        top_line.setFrameShadow(QFrame.Shadow.Sunken)
        top_line.setStyleSheet("QFrame{border: 2px solid #b91c1c;}")
        main.addWidget(top_line)

        card = QFrame()
        card.setObjectName("AboutCard")
        card.setStyleSheet("""
            QFrame#AboutCard {
                background-color: #141821;
                border: 1px solid #2a2f3a;
                border-radius: 8px;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 11px;
            }
            QLabel[role='title'] {
                color:#f97316;
                font-size: 14px;
                font-weight: 600;
            }
        """)

        g = QGridLayout(card)
        g.setContentsMargins(10, 10, 10, 10)
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(6)

        # Imagen
        img_lbl = QLabel()
        pm = QPixmap(ABOUT_INFO.get("IMAGE", ""))
        if not pm.isNull():
            img_lbl.setPixmap(pm.scaled(
                120, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            img_lbl.setText("Sin imagen")
            img_lbl.setStyleSheet("color:#9ca3af;")
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setFixedSize(120, 120)
        g.addWidget(img_lbl, 0, 0, 4, 1)

        # Título principal
        title = QLabel(f"{ABOUT_INFO['PROJECT']}")
        title.setProperty("role", "title")
        g.addWidget(title, 0, 1, 1, 2)

        l1 = QLabel(
            f"© {ABOUT_INFO['YEAR']}  –  rev. <code>{ABOUT_INFO['REV']}</code>"
        )
        l1.setTextFormat(Qt.TextFormat.RichText)
        g.addWidget(l1, 1, 1, 1, 2)

        dev = QLabel(
            f"<b>Desarrollo:</b> "
            f"<a href='{ABOUT_INFO['MAINTAINERS']}'>Maintainers</a> · "
            f"<a href='{ABOUT_INFO['CONTRIBUTORS']}'>Contributors</a>"
        )
        dev.setOpenExternalLinks(True)
        g.addWidget(dev, 2, 1, 1, 2)

        art = QLabel(
            f"<b>Arte:</b> "
            f"<a href='{ABOUT_INFO['ARTWORK']}'>AnimeBBG</a>"
        )
        art.setOpenExternalLinks(True)
        g.addWidget(art, 3, 1, 1, 2)

        # Fila de iconos (web, discord, paypal)
        help_row = QLabel(
            " <a href='{HOME}'>🌐 Web</a> &nbsp; "
            "<a href='{DISCORD}'>👥 Discord</a> &nbsp; "
            "<a href='{PAYPAL}'>💸 Paypal</a> ".format(**ABOUT_INFO)
        )
        help_row.setOpenExternalLinks(True)
        help_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        g.addWidget(help_row, 4, 1, 1, 2)

        main.addWidget(card)

        # Línea inferior
        bot_line = QFrame()
        bot_line.setFrameShape(QFrame.Shape.HLine)
        bot_line.setFrameShadow(QFrame.Shadow.Sunken)
        bot_line.setStyleSheet("QFrame{border: 2px solid #b91c1c;}")
        main.addWidget(bot_line)

        # Botón cerrar
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

# -------- QTextEdit con verificación ortográfica en hilo separado --------
class SpellCheckTextEdit(QTextEdit):
    """QTextEdit personalizado con verificación ortográfica asíncrona para español"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spell_checker = None
        self.errors = []
        self.error_positions = {}  # Almacena posiciones de errores
        self.check_thread = None
        self.checking = False
        self.pending_check = False
        self.debounce_timer = None  # Timer para debounce
        

        
        # Conectar eventos
        self.textChanged.connect(self._on_text_changed_debounced)
        self.cursorPositionChanged.connect(self._update_cursor_info)

        # Inicializar path del diccionario personalizado
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent
        self.dict_path = base_dir / "custom_dictionary.json"

        # Palabras comunes que el diccionario por defecto suele marcar como error
        self.COMMON_MISSING = {
            # SER
            'soy', 'eres', 'es', 'somos', 'sois', 'son',
            'fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron',
            'era', 'eras', 'éramos', 'erais', 'eran',
            'seré', 'serás', 'será', 'seremos', 'seréis', 'serán',
            'sería', 'serías', 'seríamos', 'seríais', 'serían',
            'sido', 'siendo',
            # ESTAR
            'estoy', 'estás', 'está', 'estamos', 'estáis', 'están',
            'estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron',
            'estaba', 'estabas', 'estábamos', 'estabais', 'estaban',
            'estaré', 'estarás', 'estará', 'estaremos', 'estaréis', 'estarán',
            'estaría', 'estarías', 'estaríamos', 'estaríais', 'estarían',
            'estado', 'estando',
            # HABER
            'he', 'has', 'ha', 'hemos', 'habéis', 'han',
            'hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron',
            'había', 'habías', 'habíamos', 'habíais', 'habían',
            'habré', 'habrás', 'habrá', 'habremos', 'habréis', 'habrán',
            'habría', 'habrías', 'habríamos', 'habríais', 'habrían',
            'hay', 'habido', 'habiendo',
            # TENER
            'tengo', 'tienes', 'tiene', 'tenemos', 'tenéis', 'tienen',
            'tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvisteis', 'tuvieron',
            'tenía', 'tenías', 'teníamos', 'teníais', 'tenían',
            'tendré', 'tendrás', 'tendrá', 'tendremos', 'tendréis', 'tendrán',
            'tendría', 'tendrías', 'tendríamos', 'tendríais', 'tendrían',
            'tenido', 'teniendo',
            # HACER
            'hago', 'haces', 'hace', 'hacemos', 'hacéis', 'hacen',
            'hice', 'hiciste', 'hizo', 'hicimos', 'hicisteis', 'hicieron',
            'hacía', 'hacías', 'hacíamos', 'hacíais', 'hacían',
            'haré', 'harás', 'hará', 'haremos', 'haréis', 'harán',
            'haría', 'harías', 'haríamos', 'haríais', 'harían',
            'hecho', 'haciendo',
            # PODER
            'puedo', 'puedes', 'puede', 'podemos', 'podéis', 'pueden',
            'pude', 'pudiste', 'pudo', 'pudimos', 'pudisteis', 'pudieron',
            'podía', 'podías', 'podíamos', 'podíais', 'podían',
            'podré', 'podrás', 'podrá', 'podremos', 'podréis', 'podrán',
            'podría', 'podrías', 'podríamos', 'podríais', 'podrían',
            'podido', 'pudiendo',
            # DECIR
            'digo', 'dices', 'dice', 'decimos', 'decís', 'dicen',
            'dije', 'dijiste', 'dijo', 'dijimos', 'dijisteis', 'dijeron',
            'decía', 'decías', 'decíamos', 'decíais', 'decían',
            'diré', 'dirás', 'dirá', 'diremos', 'diréis', 'dirán',
            'diría', 'dirías', 'diríamos', 'diríais', 'dirían',
            'dicho', 'diciendo',
            # IR
            'voy', 'vas', 'va', 'vamos', 'vais', 'van',
            'fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron',
            'iba', 'ibas', 'íbamos', 'ibais', 'iban',
            'iré', 'irás', 'irá', 'iremos', 'iréis', 'irán',
            'iría', 'irías', 'iríamos', 'iríais', 'irían',
            'ido', 'yendo',
            # VER
            'veo', 'ves', 've', 'vemos', 'veis', 'ven',
            'vi', 'viste', 'vio', 'vimos', 'visteis', 'vieron',
            'veía', 'veías', 'veíamos', 'veíais', 'veían',
            'veré', 'verás', 'verá', 'veremos', 'veréis', 'verán',
            'vería', 'verías', 'veríamos', 'veríais', 'verían',
            'visto', 'viendo',
            # DAR
            'doy', 'das', 'da', 'damos', 'dais', 'dan',
            'di', 'diste', 'dio', 'dimos', 'disteis', 'dieron',
            'daba', 'dabas', 'dábamos', 'dabais', 'daban',
            'daré', 'darás', 'dará', 'daremos', 'daréis', 'darán',
            'daría', 'darías', 'daríamos', 'daríais', 'darían',
            'dado', 'dando',
            # SABER
            'sé', 'sabes', 'sabe', 'sabemos', 'sabéis', 'saben',
            'supe', 'supiste', 'supo', 'supimos', 'supisteis', 'supieron',
            'sabía', 'sabías', 'sabíamos', 'sabíais', 'sabían',
            'sabré', 'sabrás', 'sabrá', 'sabremos', 'sabréis', 'sabrán',
            'sabría', 'sabrías', 'sabríamos', 'sabríais', 'sabrían',
            'sabido', 'sabiendo',
            # QUERER
            'quiero', 'quieres', 'quiere', 'queremos', 'queréis', 'quieren',
            'quise', 'quisiste', 'quiso', 'quisimos', 'quisisteis', 'quisieron',
            'quería', 'querías', 'queríamos', 'queríais', 'querían',
            'querré', 'querrás', 'querrá', 'querremos', 'querréis', 'querrán',
            'querría', 'querrías', 'querríamos', 'querríais', 'querrían',
            'querido', 'queriendo',
            # LLEGAR
            'llego', 'llegas', 'llega', 'llegamos', 'llegáis', 'llegan',
            'llegué', 'llegaste', 'llegó', 'llegamos', 'llegasteis', 'llegaron',
            'llegaba', 'llegabas', 'llegábamos', 'llegabais', 'llegaban',
            'llegaré', 'llegarás', 'llegará', 'llegaremos', 'llegaréis', 'llegarán',
            'llegaría', 'llegarías', 'llegaríamos', 'llegaríais', 'llegarían',
            'llegado', 'llegando',
            # PASAR (y qué pasó)
            'paso', 'pasas', 'pasa', 'pasamos', 'pasáis', 'pasan',
            'pasé', 'pasaste', 'pasó', 'pasamos', 'pasasteis', 'pasaron',
            'pasaba', 'pasabas', 'pasábamos', 'pasabais', 'pasaban',
            'pasaré', 'pasarás', 'pasará', 'pasaremos', 'pasaréis', 'pasarán',
            'pasado', 'pasando',
            # PONER
            'pongo', 'pones', 'pone', 'ponemos', 'ponéis', 'ponen',
            'puse', 'pusiste', 'puso', 'pusimos', 'pusisteis', 'pusieron',
            'ponía', 'ponías', 'poníamos', 'poníais', 'ponían',
            'pondré', 'pondrás', 'pondrá', 'pondremos', 'pondréis', 'pondrán',
            'pondría', 'pondrías', 'pondríamos', 'pondríais', 'pondrían',
            'puesto', 'poniendo',
            # CREER
            'creo', 'crees', 'cree', 'creemos', 'creéis', 'creen',
            'creí', 'creíste', 'creyó', 'creímos', 'creísteis', 'creyeron',
            'creía', 'creías', 'creíamos', 'creíais', 'creían',
            'creeré', 'creerás', 'creerá', 'creeremos', 'creeréis', 'creerán',
            'creído', 'creyendo',
            # DEJAR
            'dejo', 'dejas', 'deja', 'dejamos', 'dejáis', 'dejan',
            'dejé', 'dejaste', 'dejó', 'dejamos', 'dejasteis', 'dejaron',
            'dejaba', 'dejabas', 'dejábamos', 'dejabais', 'dejaban',
            'dejaré', 'dejarás', 'dejará', 'dejaremos', 'dejaréis', 'dejarán',
            'dejado', 'dejando',
            # SEGUIR
            'sigo', 'sigues', 'sigue', 'seguimos', 'seguís', 'siguen',
            'seguí', 'seguiste', 'siguió', 'seguimos', 'seguisteis', 'siguieron',
            'seguía', 'seguías', 'seguíamos', 'seguíais', 'seguían',
            'seguiré', 'seguirás', 'seguirá', 'seguiremos', 'seguiréis', 'seguirán',
            'seguido', 'siguiendo',
            # ENCONTRAR
            'encuentro', 'encuentras', 'encuentra', 'encontramos', 'encontráis', 'encuentran',
            'encontré', 'encontraste', 'encontró', 'encontramos', 'encontrasteis', 'encontraron',
            'encontraba', 'encontrabas', 'encontrábamos', 'encontrabais', 'encontraban',
            'encontraré', 'encontrarás', 'encontrará', 'encontraremos', 'encontraréis', 'encontrarán',
            'encontrado', 'encontrando',
            # LLAMAR
            'llamo', 'llamas', 'llama', 'llamamos', 'llamáis', 'llaman',
            'llamé', 'llamaste', 'llamó', 'llamamos', 'llamasteis', 'llamaron',
            'llamaba', 'llamabas', 'llamábamos', 'llamabais', 'llamaban',
            'llamaré', 'llamarás', 'llamará', 'llamaremos', 'llamaréis', 'llamarán',
            'llamado', 'llamando',
            # VENIR
            'vengo', 'vienes', 'viene', 'venimos', 'venís', 'vienen',
            'vine', 'viniste', 'vino', 'vinimos', 'vinisteis', 'vinieron',
            'venía', 'venías', 'veníamos', 'veníais', 'venían',
            'vendré', 'vendrás', 'vendrá', 'vendremos', 'vendréis', 'vendrán',
            'vendría', 'vendrías', 'vendríamos', 'vendríais', 'vendrían',
            'venido', 'viniendo',
            # PENSAR
            'pienso', 'piensas', 'piensa', 'pensamos', 'pensáis', 'piensan',
            'pensé', 'pensaste', 'pensó', 'pensamos', 'pensasteis', 'pensaron',
            'pensaba', 'pensabas', 'pensábamos', 'pensabais', 'pensaban',
            'pensaré', 'pensarás', 'pensará', 'pensaremos', 'pensaréis', 'pensarán',
            'pensado', 'pensando',
            # SALIR
            'salgo', 'sales', 'sale', 'salimos', 'salís', 'salen',
            'salí', 'saliste', 'salió', 'salimos', 'salisteis', 'salieron',
            'salía', 'salías', 'salíamos', 'salíais', 'salían',
            'saldré', 'saldrás', 'saldrá', 'saldremos', 'saldréis', 'saldrán',
            'saldría', 'saldrías', 'saldríamos', 'saldríais', 'saldrían',
            'salido', 'saliendo',
            # SENTIR
            'siento', 'sientes', 'siente', 'sentimos', 'sentís', 'sienten',
            'sentí', 'sentiste', 'sintió', 'sentimos', 'sentisteis', 'sintieron',
            'sentía', 'sentías', 'sentíamos', 'sentíais', 'sentían',
            'sentiré', 'sentirás', 'sentirá', 'sentiremos', 'sentiréis', 'sentirán',
            'sentido', 'sintiendo',
            # PREGUNTAR
            'pregunto', 'preguntas', 'pregunta', 'preguntamos', 'preguntáis', 'preguntan',
            'pregunté', 'preguntaste', 'preguntó', 'preguntamos', 'preguntasteis', 'preguntaron',
            'preguntaba', 'preguntabas', 'preguntábamos', 'preguntabais', 'preguntaban',
            'preguntaré', 'preguntarás', 'preguntará', 'preguntaremos', 'preguntaréis', 'preguntarán',
            'preguntado', 'preguntando',
            # HABLAR
            'hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan',
            'hablé', 'hablaste', 'habló', 'hablamos', 'hablasteis', 'hablaron',
            'hablaba', 'hablabas', 'hablábamos', 'hablabais', 'hablaban',
            'hablaré', 'hablarás', 'hablará', 'hablaremos', 'hablaréis', 'hablarán',
            'hablado', 'hablando',
            # VIVIR
            'vivo', 'vives', 'vive', 'vivimos', 'vivís', 'viven',
            'viví', 'viviste', 'vivió', 'vivimos', 'vivisteis', 'vivieron',
            'vivía', 'vivías', 'vivíamos', 'vivíais', 'vivían',
            'viviré', 'vivirás', 'vivirá', 'viviremos', 'viviréis', 'vivirán',
            'vivido', 'viviendo',
            # TOMAR
            'tomo', 'tomas', 'toma', 'tomamos', 'tomáis', 'toman',
            'tomé', 'tomaste', 'tomó', 'tomamos', 'tomasteis', 'tomaron',
            'tomaba', 'tomabas', 'tomábamos', 'tomabais', 'tomaban',
            'tomaré', 'tomarás', 'tomará', 'tomaremos', 'tomaréis', 'tomarán',
            'tomado', 'tomando',
            # OTROS COMUNES
            'aquí', 'allí', 'ahí', 'allá', 'acá',
            'quizás', 'tal vez', 'además', 'través', 'después', 'atrás', 'aún',
            'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas',
            'enseguida', 'ahora', 'antes', 'entonces', 'luego', 'tarde', 'temprano', 'pronto',
            'mimi', 'stella', 'prunu', 'vainilla', 'vaynilla',
            # De la lista de tildes
            'próxima', 'dónde', 'está', 'lección', 'comenzó', 'perdí', 'montón', 'recién',
            'iba', 'había', 'podía', 'decía'
        }

        # Inicializar corrector si está disponible
        if SPELLCHECK_AVAILABLE:
            try:
                local_dict_path = None
                
                # 1. Intentar cargar desde recursos embebidos (PyInstaller --add-data)
                if hasattr(sys, '_MEIPASS'):
                    embedded_path = Path(sys._MEIPASS) / "es.json.gz"
                    if embedded_path.exists():
                        local_dict_path = embedded_path

                # 2. Si no, intentar archivo local junto al ejecutable/script
                if not local_dict_path:
                    side_path = base_dir / "es.json.gz"
                    if side_path.exists():
                        local_dict_path = side_path

                if local_dict_path:
                    self.spell_checker = SpellChecker(language=None, local_dictionary=str(local_dict_path))
                else:
                    # Fallback a descarga/default (requiere internet 1ra vez)
                    self.spell_checker = SpellChecker(language='es')

                # Cargar palabras comunes faltantes
                self.spell_checker.word_frequency.load_words(self.COMMON_MISSING)
                # Cargar diccionario personalizado
                self._load_custom_dictionary()
            except Exception as e:
                print(f"[WARNING] No se pudo inicializar SpellChecker: {e}")
                self.spell_checker = None
    
    def _load_custom_dictionary(self):
        """Carga palabras del archivo JSON personalizado"""
        if not self.dict_path.exists():
            return
        try:
            with open(self.dict_path, 'r', encoding='utf-8') as f:
                custom_words = json.load(f)
                if isinstance(custom_words, list):
                    self.spell_checker.word_frequency.load_words(custom_words)
        except Exception as e:
            print(f"[ERROR] Error cargando diccionario personalizado: {e}")

    def add_to_dictionary(self, word: str):
        """Añade una palabra al diccionario y guarda en disco"""
        if not self.spell_checker:
            return
        
        # Añadir a la instancia actual
        self.spell_checker.word_frequency.load_words([word])
        
        # Guardar en disco
        try:
            current_words = []
            if self.dict_path.exists():
                with open(self.dict_path, 'r', encoding='utf-8') as f:
                    current_words = json.load(f)
            
            if word not in current_words:
                current_words.append(word)
                with open(self.dict_path, 'w', encoding='utf-8') as f:
                    json.dump(current_words, f, ensure_ascii=False, indent=2)
            
            # Re-verificar el texto para limpiar el error visual
            self._on_text_changed()
            
        except Exception as e:
            print(f"[ERROR] Error guardando palabra en diccionario: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo guardar la palabra: {e}")

    def _on_text_changed_debounced(self):
        """Aplica debounce para no verificar cada letra (optimización)"""
        if self.debounce_timer:
            self.debounce_timer.stop()
        
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._on_text_changed)
        self.debounce_timer.start(500)
    
    def _on_text_changed(self):
        """Inicia verificación en hilo separado (no bloquea la UI)"""
        if not self.spell_checker:
            return
        
        # Si ya hay una verificación en curso, marcar para verificar después
        if self.checking:
            self.pending_check = True
            return
        
        self.pending_check = False
        self.checking = True
        
        # Obtener texto actual
        text = self.toPlainText()
        
        # Iniciar verificación en hilo separado
        self.check_thread = threading.Thread(target=self._check_spelling_thread, args=(text,), daemon=True)
        self.check_thread.start()

    def _check_spelling_thread(self, text: str):
        """Verifica ortografía en hilo separado (no bloquea la UI) usando pyspellchecker y reglas personalizadas para tildes"""
        try:
            if not text.strip():
                self.errors = []
                self.error_positions = {}
                QTimer.singleShot(0, self._clear_highlights)
                self.checking = False
                if self.pending_check:
                    self._on_text_changed()
                return

            # Palabras frecuentes que requieren tilde y su forma correcta
            tildes = {
                'proxima': 'próxima',
                'donde': 'dónde',
                'esta': 'está',
                'leccion': 'lección',
                'comenzo': 'comenzó',
                'perdi': 'perdí',
                'monton': 'montón',
                'recien': 'recién',
                'hiba': 'iba',
                'habia': 'había',
                'podia': 'podía',
                'decia': 'decía',
                'mimi': 'Mimi',
                'stella': 'Stella',
                'prunu': 'Prunu',
            }

            words = re.findall(r'\w+', text, re.UNICODE)
            unknown = self.spell_checker.unknown(words)
            misspelled = set(unknown) if unknown else set()
            # Añadir palabras sin tilde a los errores
            for w in words:
                if w.lower() in tildes and w != tildes[w.lower()]:
                    misspelled.add(w)

            error_positions = {}
            errors = []

            for match in re.finditer(r'\w+', text, re.UNICODE):
                word = match.group(0)
                if word in misspelled:
                    start = match.start()
                    end = match.end()
                    # Simular objeto error para compatibilidad
                    class Error:
                        def __init__(self, word, offset, errorLength, replacements):
                            self.word = word
                            self.offset = offset
                            self.errorLength = errorLength
                            self.replacements = replacements
                    # Sugerencias: primero la forma con tilde si aplica
                    suggestions = []
                    if word.lower() in tildes:
                        suggestions.append(tildes[word.lower()])
                    cands = self.spell_checker.candidates(word)
                    if cands:
                        suggestions += [s for s in cands if s not in suggestions]
                    error = Error(word, start, end-start, suggestions)
                    error_positions[start] = (end, error)
                    errors.append(error)

            self.errors = errors
            self.error_positions = error_positions

            QTimer.singleShot(0, self._highlight_misspelled)
            QTimer.singleShot(0, self._update_cursor_info)

        except Exception as e:
            print(f"[ERROR] Error al verificar ortografía: {e}")
            self.errors = []
            self.error_positions = {}
            QTimer.singleShot(0, self._clear_highlights)
        finally:
            self.checking = False
            if self.pending_check:
                QTimer.singleShot(100, self._on_text_changed)
    

    
    def _highlight_misspelled(self):
        """Resalta las palabras mal escritas con subrayado rojo"""
        doc = self.document()
        cursor = QTextCursor(doc)
        
        # Limpiar todos los formatos
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = cursor.charFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)  # Remover subrayado
        cursor.setCharFormat(fmt)
        
        # Aplicar subrayado rojo a palabras mal escritas
        for start_pos, (end_pos, error) in self.error_positions.items():
            cursor = QTextCursor(doc)
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
            
            fmt = cursor.charFormat()
            fmt.setUnderlineColor(QColor("#EF4444"))  # Rojo
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)  # Wavy underline
            cursor.setCharFormat(fmt)
    
    def _clear_highlights(self):
        """Limpia todos los resaltados"""
        doc = self.document()
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = cursor.charFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
        cursor.setCharFormat(fmt)
    
    def _update_cursor_info(self):
        """Muestra sugerencias de palabras cuando el cursor está sobre una palabra"""
        if not self.spell_checker or not self.errors:
            return
        
        try:
            cursor_pos = self.textCursor().position()
            
            # Buscar el error en la posición actual del cursor
            for start_pos, (end_pos, error) in self.error_positions.items():
                if start_pos <= cursor_pos <= end_pos:
                    # Encontramos un error bajo el cursor
                    suggestions = error.replacements[:5] if error.replacements else []
                    word_text = self.toPlainText()[start_pos:end_pos]
                    
                    if suggestions:
                        # Mostrar sugerencias en la barra de estado
                        parent = self.parent()
                        while parent and not isinstance(parent, QMainWindow):
                            parent = parent.parent()
                        
                        if isinstance(parent, QMainWindow):
                            sugg_text = ', '.join(suggestions)
                            parent.statusBar().showMessage(f'"{word_text}" → {sugg_text}', 3000)
                    break
        
        except Exception:
            pass  # Ignorar errores
    
    def get_errors_with_suggestions(self) -> dict:
        """Retorna diccionario de errores con sus sugerencias, incluyendo sugerencias personalizadas"""
        corrections = {}
        text = self.toPlainText()
        # Sugerencias personalizadas para palabras y frases frecuentes
        custom_suggestions = {
            'muxa': ['mucho', 'muda', 'mula', 'musa'],
            'muxo': ['mucho', 'mudo', 'muxa'],
            'muxos': ['muchos', 'mucho'],
            'desde ase': ['desde hace', 'desde ese', 'desde hace tiempo'],
            'ase': ['hace', 'ase'],
        }
        for start_pos, (end_pos, error) in self.error_positions.items():
            word = text[start_pos:end_pos]
            suggestions = error.replacements[:5] if error.replacements else []
            # Si hay sugerencias personalizadas, las agregamos al inicio
            if word in custom_suggestions:
                # Evitar duplicados
                custom = [s for s in custom_suggestions[word] if s not in suggestions]
                suggestions = custom + suggestions
            if suggestions:
                corrections[word] = suggestions
        return corrections
    
    def apply_replacement(self, start_pos: int, end_pos: int, replacement: str):
        """Aplica un reemplazo en el texto, asegurando que cubre toda la palabra incorrecta"""
        doc = self.document()
        text = self.toPlainText()
        # Obtener el texto actual en el rango
        word_in_range = text[start_pos:end_pos]
        # Si el rango no cubre toda la palabra, expandir a los límites de la palabra
        import re
        # Buscar el inicio de la palabra
        word_start = start_pos
        while word_start > 0 and re.match(r'\w', text[word_start-1]):
            word_start -= 1
        # Buscar el final de la palabra
        word_end = end_pos
        while word_end < len(text) and re.match(r'\w', text[word_end]):
            word_end += 1
        # Usar el rango expandido si es diferente
        if (word_start != start_pos) or (word_end != end_pos):
            start_pos, end_pos = word_start, word_end
        cursor = QTextCursor(doc)
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(replacement)

# -------- Diálogo para corrección ortográfica --------
class SpellCheckDialog(QDialog):
    """Diálogo para revisar y corregir errores ortográficos"""
    
    def __init__(self, text_edit: SpellCheckTextEdit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Corrección Ortográfica")
        self.setGeometry(100, 100, 600, 400)
        self.text_edit = text_edit
        self.corrections_applied = {}
        
        layout = QVBoxLayout(self)
        
        # Información
        info_label = QLabel("Palabras con errores ortográficos detectadas:")
        layout.addWidget(info_label)
        
        # Area de sugerencias
        self.suggestion_list = QListWidget()
        layout.addWidget(self.suggestion_list)
        
        # Controles de corrección
        controls = QHBoxLayout()
        
        self.word_label = QLabel("")
        controls.addWidget(self.word_label)
        
        self.suggestion_combo = QComboBox()
        controls.addWidget(self.suggestion_combo)
        
        self.replace_btn = QPushButton("Reemplazar")
        self.replace_btn.clicked.connect(self._replace_word)
        controls.addWidget(self.replace_btn)
        
        self.replace_all_btn = QPushButton("Reemplazar todo")
        self.replace_all_btn.clicked.connect(self._replace_all_word)
        controls.addWidget(self.replace_all_btn)
        
        self.ignore_btn = QPushButton("Ignorar")
        self.ignore_btn.clicked.connect(self._ignore_word)
        controls.addWidget(self.ignore_btn)

        self.add_dict_btn = QPushButton("Agregar a Dicc.")
        self.add_dict_btn.setToolTip("Guardar palabra en diccionario personalizado")
        self.add_dict_btn.clicked.connect(self._add_to_dict)
        controls.addWidget(self.add_dict_btn)
        
        layout.addLayout(controls)
        
        # Botones finales
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        
        # Cargar palabras mal escritas
        self._populate_misspelled_words()
    
    def _populate_misspelled_words(self):
        """Carga las palabras mal escritas en la lista"""
        corrections = self.text_edit.get_errors_with_suggestions()
        
        if not corrections:
            QMessageBox.information(self, "Corrección Ortográfica", "¡No hay errores ortográficos!")
            self.reject()
            return
        
        self.error_dict = {}  # Mapeo de palabra a (start_pos, end_pos, error_obj)
        
        for (start_pos, (end_pos, error)), (word, suggestions) in zip(
            self.text_edit.error_positions.items(), 
            corrections.items()
        ):
            item = QListWidgetItem(f"{word}  →  {', '.join(suggestions[:3])}")
            item.setData(Qt.ItemDataRole.UserRole, word)
            item.setData(Qt.ItemDataRole.UserRole + 1, suggestions)
            item.setData(Qt.ItemDataRole.UserRole + 2, (start_pos, end_pos, error))
            self.suggestion_list.addItem(item)
            self.error_dict[word] = (start_pos, end_pos, error)
        
        # Seleccionar el primer error
        if self.suggestion_list.count() > 0:
            self.suggestion_list.setCurrentRow(0)
            self._on_word_selected(0)
        
        self.suggestion_list.itemSelectionChanged.connect(
            lambda: self._on_word_selected(self.suggestion_list.currentRow())
        )
    
    def _on_word_selected(self, idx):
        """Cuando se selecciona una palabra de la lista"""
        if idx < 0:
            return
        
        item = self.suggestion_list.item(idx)
        if not item:
            return
        
        word = item.data(Qt.ItemDataRole.UserRole)
        suggestions = item.data(Qt.ItemDataRole.UserRole + 1)
        
        self.word_label.setText(f"Palabra: <b>{word}</b>")
        self.suggestion_combo.clear()
        self.suggestion_combo.addItems(suggestions if suggestions else [])
        self.current_error_item = item
    
    def _replace_word(self):
        """Reemplaza solo la ocurrencia actual"""
        if self.suggestion_list.currentRow() < 0:
            return
        
        row = self.suggestion_list.currentRow()
        item = self.suggestion_list.item(row)
        word = item.data(Qt.ItemDataRole.UserRole)
        suggestion = self.suggestion_combo.currentText()
        
        if not suggestion:
            QMessageBox.warning(self, "Error", "Selecciona una sugerencia primero")
            return
        
        # Obtener información del error
        start_pos, end_pos, error = item.data(Qt.ItemDataRole.UserRole + 2)
        
        # Calcular diferencia de longitud
        original_len = end_pos - start_pos
        new_len = len(suggestion)
        delta = new_len - original_len
        
        # Aplicar reemplazo directo en la posición
        self.text_edit.apply_replacement(start_pos, end_pos, suggestion)
        
        self.corrections_applied[word] = suggestion
        
        # Actualizar posiciones de TODOS los ítems siguientes en la lista
        # ya que el texto se ha desplazado
        for i in range(self.suggestion_list.count()):
            if i == row: continue
            
            other_item = self.suggestion_list.item(i)
            o_start, o_end, o_error = other_item.data(Qt.ItemDataRole.UserRole + 2)
            
            # Si el otro error está después de este, desplazarlo
            if o_start > start_pos:
                o_start += delta
                o_end += delta
                other_item.setData(Qt.ItemDataRole.UserRole + 2, (o_start, o_end, o_error))
        
        # Remover de la lista y actualizar
        self.suggestion_list.takeItem(row)
        
        if self.suggestion_list.count() == 0:
            QMessageBox.information(self, "Corrección Ortográfica", "¡Todas las palabras han sido revisadas!")
            self.accept()
    
    def _replace_all_word(self):
        """Reemplaza todas las ocurrencias de la palabra"""
        if self.suggestion_list.currentRow() < 0:
            return
        
        item = self.suggestion_list.item(self.suggestion_list.currentRow())
        word = item.data(Qt.ItemDataRole.UserRole)
        suggestion = self.suggestion_combo.currentText()
        
        if not suggestion:
            QMessageBox.warning(self, "Error", "Selecciona una sugerencia primero")
            return
        
        # Reemplazar todas las ocurrencias en el texto
        # Nota: Esto invalida todos los índices actuales, por lo que cerramos el diálogo
        # para forzar un re-escaneo.
        text = self.text_edit.toPlainText()
        new_text = text.replace(word, suggestion)
        self.text_edit.setPlainText(new_text)
        
        self.corrections_applied[word] = suggestion
        
        QMessageBox.information(self, "Reemplazar Todo", 
            f"Se han reemplazado todas las ocurrencias de '{word}' por '{suggestion}'.\n\n"
            "El diálogo se cerrará para recalcular los errores restantes.")
        self.accept()
    
    def _ignore_word(self):
        """Ignora la palabra actual sin corregir"""
        if self.suggestion_list.currentRow() >= 0:
            self.suggestion_list.takeItem(self.suggestion_list.currentRow())
            
            if self.suggestion_list.count() == 0:
                QMessageBox.information(self, "Corrección Ortográfica", "¡Todas las palabras han sido revisadas!")
                self.accept()

    def _add_to_dict(self):
        """Añade la palabra actual al diccionario personalizado"""
        if self.suggestion_list.currentRow() < 0:
            return

        item = self.suggestion_list.item(self.suggestion_list.currentRow())
        word = item.data(Qt.ItemDataRole.UserRole)
        
        # Llamar al método del editor
        self.text_edit.add_to_dictionary(word)
        
        # Remover de la lista ya que ahora es correcta
        self.suggestion_list.takeItem(self.suggestion_list.currentRow())
        
        QMessageBox.information(self, "Diccionario", f"Palabra '{word}' añadida al diccionario.")
        
        if self.suggestion_list.count() == 0:
            QMessageBox.information(self, "Corrección Ortográfica", "¡Todas las palabras han sido revisadas!")
            self.accept()

# ---------------- Helpers UI panel de propiedades ----------------
class ToggleSwitch(QCheckBox):
    """QCheckBox con apariencia de toggle switch (pill)."""
    _H = 18
    _W = 34

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self._W, self._H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        return QSize(self._W, self._H)

    def paintEvent(self, _event):
        from PyQt6.QtGui import QPainterPath
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        h = r.height()
        w = r.width()
        radius = h / 2
        track_color = QColor("#3B82F6") if self.isChecked() else QColor("#374151")
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, radius, radius)
        p.fillPath(path, track_color)
        margin = 3
        thumb_d = h - margin * 2
        thumb_x = (w - thumb_d - margin) if self.isChecked() else margin
        p.setBrush(QColor("#FFFFFF"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(thumb_x), margin, int(thumb_d), int(thumb_d))
        p.end()

    def mousePressEvent(self, _event):
        self.setChecked(not self.isChecked())


class ColorSwatch(QPushButton):
    """Boton swatch de color."""
    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color = color
        self._update_style()

    def set_color(self, color: str):
        self._color = color
        self._update_style()

    def _update_style(self):
        self.setStyleSheet(
            f"QPushButton {{ background:{self._color}; border-radius:10px; border:2px solid #374151; }}"
            f"QPushButton:hover {{ border:2px solid #6B7280; }}"
        )


class PropSection(QWidget):
    """Seccion colapsable del panel de propiedades."""
    def __init__(self, title: str, icon_char: str = "*", parent=None):
        super().__init__(parent)
        self._collapsed = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 3)
        outer.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(26)
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.setStyleSheet(
            "QWidget { background: #161B27; border-radius: 5px; }"
            "QWidget:hover { background: #1E2636; }"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(5)

        icon_lbl = QLabel(icon_char)
        icon_lbl.setStyleSheet("color: #E11D48; font-size: 9px; background: transparent;")
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 9px; font-weight: 700; letter-spacing: 1px; background: transparent;"
        )
        self._arrow = QLabel("v")
        self._arrow.setStyleSheet("color: #4B5563; font-size: 9px; background: transparent;")

        hl.addWidget(icon_lbl)
        hl.addWidget(title_lbl)
        hl.addStretch()
        hl.addWidget(self._arrow)

        self._content = QWidget()
        self._content.setStyleSheet("QWidget { background: transparent; }")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(2, 5, 2, 2)
        self._content_layout.setSpacing(6)

        outer.addWidget(header)
        outer.addWidget(self._content)
        header.mousePressEvent = self._toggle

    def _toggle(self, _event):
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = bool(collapsed)
        self._content.setVisible(not self._collapsed)
        self._arrow.setText(">" if self._collapsed else "v")

    def content_layout(self):
        return self._content_layout


def _prop_row(label: str, widget, label_width: int = 80) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(5)
    lbl = QLabel(label)
    lbl.setFixedWidth(label_width)
    lbl.setStyleSheet("color: #9CA3AF; font-size: 10px;")
    row.addWidget(lbl)
    row.addWidget(widget, 1)
    return row


def _prop_toggle_row(label: str, toggle: ToggleSwitch, extra=None) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(5)
    lbl = QLabel(label)
    lbl.setStyleSheet("color: #CBD5E1; font-size: 10px;")
    row.addWidget(lbl, 1)
    if extra:
        row.addWidget(extra)
    row.addWidget(toggle)
    return row


# ---------------- Ventana principal ----------------
class MangaTextTool(QMainWindow):
    def __init__(self, username: str = ""):
        super().__init__()
        self.currentUser = username
        
        # Obtener factor de escala para UI responsiva
        scale = get_ui_scale_factor()

        self.setWindowTitle("EditorTyperTool – Animebbg")
        self.setWindowIcon(icon('app.ico'))
        _apply_win_icon(self)
        self.resize(scale_size(1400, scale), scale_size(930, scale))
        self.lock_move = False

        self.settings = QSettings('FansubTools', 'MangaTextTool')
        global PRESETS; PRESETS = load_presets_from_settings(self.settings)
        if upgrade_presets_with_defaults(PRESETS): save_presets_to_settings(self.settings, PRESETS)

        if str(self.settings.value('shadow_default_migrated', '0')) != '1':
            for st in PRESETS.values(): st.shadow_enabled = False
            save_presets_to_settings(self.settings, PRESETS); self.settings.setValue('shadow_default_migrated', '1')
        if str(self.settings.value('background_default_migrated', '0')) != '1':
            for st in PRESETS.values(): st.background_enabled = False; st.background_opacity = 0.0
            save_presets_to_settings(self.settings, PRESETS); self.settings.setValue('background_default_migrated', '1')

        # --- Estado persistente de la marca de agua ---
        self.wm_path: str = str(self.settings.value('wm_path', ''))
        self.wm_enabled: bool = str(self.settings.value('wm_enabled', '0')) == '1'
        try:
            self.wm_opacity_pct: int = int(self.settings.value('wm_opacity', 20))
        except Exception:
            self.wm_opacity_pct = 20
        # Posición (normalizada) y escala recordadas globalmente
        try:
            px = self.settings.value('wm_pos_x'); py = self.settings.value('wm_pos_y')
            self.wm_pos_norm = (float(px), float(py)) if px is not None and py is not None else None
        except Exception:
            self.wm_pos_norm = None
        try:
            self.wm_scale = float(self.settings.value('wm_scale', 1.0))
        except Exception:
            self.wm_scale = 1.0
        
        # Ruta del último proyecto guardado (para auto-guardar)
        self.last_saved_project_path = None

        self.tabs = QTabWidget(); self.tabs.setTabsClosable(False)
        self.setCentralWidget(self.tabs)
        self.tabs.tabBar().currentChanged.connect(lambda _i: self._refresh_tab_close_buttons())
        self.tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setStyleSheet(
            "QTabBar::scroller { width: 74px; background:#111827; border:1px solid #1F2937; border-radius:6px; margin-left:2px; }"
            "QTabBar QToolButton {"
            "background:transparent; color:#94A3B8; border:none;"
            "min-width:28px; max-width:30px; min-height:22px; max-height:22px; margin:0; padding:0 2px; font-size:16px; font-weight:500;"
            "}"
            "QTabBar QToolButton:hover { background:#1F2937; color:#E2E8F0; }"
            "QTabBar QToolButton:pressed { background:#263042; }"
            "QTabBar QToolButton:disabled { color:#475569; background:transparent; }"
        )

        self._dark_theme = True

        # Ventana emergente "Nosotros"
        self.about_dialog = AboutDialog(self)

        # Crear UI
        self._build_toolbar()
        self._build_right_panel()
        self._build_raw_dock()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        QShortcut(QKeySequence("Ctrl+F4"), self, activated=self.close_current_tab)

        # Atajos
        QShortcut(QKeySequence('T'), self, activated=self.add_text_paste_dialog)
        QShortcut(QKeySequence('Delete'), self, activated=self.delete_selected)
        QShortcut(QKeySequence.StandardKey.Undo, self, activated=self.do_undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, activated=self.do_redo)
        QShortcut(QKeySequence('S'), self, activated=self.auto_place_selected)
        QShortcut(QKeySequence("Left"),  self, activated=lambda: self.nudge_selected(dx=-1))
        QShortcut(QKeySequence("Right"), self, activated=lambda: self.nudge_selected(dx=+1))
        QShortcut(QKeySequence("Up"),    self, activated=lambda: self.nudge_selected(dy=-1))
        QShortcut(QKeySequence("Down"),  self, activated=lambda: self.nudge_selected(dy=+1))
        QShortcut(QKeySequence("Shift+Left"),  self, activated=lambda: self.nudge_selected(dx=-1, step=10))
        QShortcut(QKeySequence("Shift+Right"), self, activated=lambda: self.nudge_selected(dx=+1, step=10))
        QShortcut(QKeySequence("Shift+Up"),    self, activated=lambda: self.nudge_selected(dy=-1, step=10))
        QShortcut(QKeySequence("Shift+Down"),  self, activated=lambda: self.nudge_selected(dy=+1, step=10))

        self.statusBar().showMessage("Listo")
        self._refresh_tab_close_buttons()

        # Sincroniza estado inicial de controles de marca de agua
        try:
            self.wm_enable_chk.setChecked(self.wm_enabled)
            self.wm_op_slider.setValue(int(clamp(self.wm_opacity_pct, 0, 100)))
            self._wm_update_controls_enabled()
        except Exception:
            pass

    # ---------- helpers ----------
    def current_ctx(self) -> Optional[PageContext]:
        w = self.tabs.currentWidget(); return w if isinstance(w, PageContext) else None
    def current_item(self) -> Optional[StrokeTextItem]:
        ctx = self.current_ctx(); return ctx.current_item() if ctx else None
    def _selected_items(self) -> List[StrokeTextItem]:
        ctx = self.current_ctx(); return ctx.selected_text_items() if ctx else []
    def _apply_movable_state(self, item: StrokeTextItem):
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, (not item.locked) and (not self.lock_move))
    def _apply_movable_all_current(self):
        ctx = self.current_ctx()
        if not ctx: return
        for it in ctx.scene.items():
            if isinstance(it, StrokeTextItem): self._apply_movable_state(it)
        ctx.scene.update()
    
    def toggle_text_numbers(self):
        StrokeTextItem.SHOW_ORDINAL = self.show_nums_act.isChecked()
        # Force update all scenes
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, PageContext) and w.scene:
                w.scene.update()
    
    def mark_tab_modified(self, ctx: Optional[PageContext] = None):
        """Marca una pestaña como modificada (con cambios sin guardar)."""
        if ctx is None:
            ctx = self.current_ctx()
        if not ctx or not isinstance(ctx, PageContext):
            return
        
        ctx.has_unsaved_changes = True
        
        # Añadir asterisco al título de la pestaña si no lo tiene
        idx = self.tabs.indexOf(ctx)
        if idx >= 0:
            current_name = self.tabs.tabText(idx)
            if not current_name.startswith('*'):
                self.tabs.setTabText(idx, f"*{current_name}")

    def check_for_updates(self, show_up_to_date: bool = True):
        """Consulta un version.json remoto y ofrece descargar si hay una version nueva."""
        if not UPDATE_JSON_URL or "TU_USUARIO" in UPDATE_JSON_URL:
            if show_up_to_date:
                QMessageBox.information(
                    self,
                    "Actualizaciones",
                    "Configura UPDATE_JSON_URL con la URL real de tu version.json."
                )
            return

        try:
            req = urllib.request.Request(
                UPDATE_JSON_URL,
                headers={"User-Agent": "AnimeBBG-Editor"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(data)
            remote_version = str(payload.get("version", "")).strip()
            assets = payload.get("assets", {})
            if isinstance(assets, dict):
                if sys.platform.startswith("win"):
                    download_url = str(assets.get("windows", "")).strip()
                elif sys.platform.startswith("linux"):
                    download_url = str(assets.get("linux", "")).strip()
                elif sys.platform == "darwin":
                    download_url = str(assets.get("macos", "")).strip()
                else:
                    download_url = ""
            else:
                download_url = ""
            # Compatibilidad con formato antiguo de version.json
            if not download_url:
                download_url = str(payload.get("url", "")).strip()
            notes = str(payload.get("notes", "")).strip()

            if not remote_version or not download_url:
                raise ValueError("version.json incompleto (version/url o assets por plataforma).")

            if _is_newer_version(remote_version, APP_VERSION):
                msg = QMessageBox(self)
                msg.setWindowTitle("Actualizacion disponible")
                msg.setText(f"Hay una nueva version: {remote_version}")
                if notes:
                    msg.setInformativeText(notes)
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg.button(QMessageBox.StandardButton.Yes).setText("Actualizar ahora")
                msg.button(QMessageBox.StandardButton.No).setText("Luego")
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    _run_self_update(download_url, parent=self)
            else:
                if show_up_to_date:
                    QMessageBox.information(self, "Actualizaciones", "Ya tienes la ultima version.")

        except Exception as e:
            if show_up_to_date:
                QMessageBox.warning(self, "Actualizaciones", f"No se pudo buscar actualizaciones:\n{e}")

    def closeEvent(self, event):
        # Verificar si hay pestañas con cambios sin guardar
        unsaved_tabs = []
        for i in range(self.tabs.count()):
            ctx = self.tabs.widget(i)
            if isinstance(ctx, PageContext) and ctx.has_unsaved_changes:
                tab_name = self.tabs.tabText(i)
                if tab_name.startswith('*'):
                    tab_name = tab_name[1:]
                unsaved_tabs.append((i, ctx, tab_name))
        
        if unsaved_tabs:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Cerrar aplicación")
            
            if len(unsaved_tabs) == 1:
                dlg.setText("Hay 1 pestaña con cambios sin guardar.")
            else:
                dlg.setText(f"Hay {len(unsaved_tabs)} pestañas con cambios sin guardar.")
            
            dlg.setInformativeText("¿Deseas guardar los cambios antes de salir?")
            
            if len(unsaved_tabs) == 1:
                btn_save = dlg.addButton("Guardar y salir", QMessageBox.ButtonRole.AcceptRole)
            else:
                btn_save = dlg.addButton("Guardar todas y salir", QMessageBox.ButtonRole.AcceptRole)
            
            btn_discard = dlg.addButton("Salir sin guardar", QMessageBox.ButtonRole.DestructiveRole)
            btn_cancel = dlg.addButton(QMessageBox.StandardButton.Cancel)
            
            dlg.exec()
            clicked = dlg.clickedButton()
            
            if clicked == btn_cancel:
                event.ignore()
                return
            elif clicked == btn_save:
                if len(unsaved_tabs) == 1:
                    # Guardar solo la pestaña con cambios
                    idx, ctx, name = unsaved_tabs[0]
                    self.tabs.setCurrentIndex(idx)
                    self.save_project_bbg_embed()
                    if ctx.has_unsaved_changes:  # Si canceló
                        event.ignore()
                        return
                else:
                    # Guardar todas las pestañas
                    self.save_all_bbg_embed()
                    # Verificar si alguna todavía tiene cambios (canceló)
                    for i, ctx, name in unsaved_tabs:
                        if ctx.has_unsaved_changes:
                            event.ignore()
                            return
        
        # Guardar presets y cerrar
        save_presets_to_settings(self.settings, PRESETS)
        super().closeEvent(event)

    def do_undo(self): ctx = self.current_ctx();  ctx and ctx.undo_stack.undo()
    def do_redo(self): ctx = self.current_ctx();  ctx and ctx.undo_stack.redo()

    def add_tab_for_image(self, path: Path):
        pix = QPixmap(str(path))
        if pix.isNull(): QMessageBox.warning(self, "Error", f"No se pudo cargar: {path}"); return

        # Calcular factor de escala basado en el tamaño de la imagen
        # Imagen base de referencia: 1920x1080 (Full HD)
        base_width = 1920.0
        base_height = 1080.0
        img_width = float(pix.width())
        img_height = float(pix.height())

        # Calcular factor de escala (promedio de ancho y alto)
        scale_w = img_width / base_width
        scale_h = img_height / base_height
        scale_factor = (scale_w + scale_h) / 2.0

        # Limitar el factor de escala para evitar fuentes demasiado grandes o pequeñas
        scale_factor = max(0.5, min(scale_factor, 2.0))

        # Aplicar escala a los PRESETS temporalmente
        global PRESETS
        original_presets = {k: replace(v) for k, v in PRESETS.items()}

        for key, preset in PRESETS.items():
            preset.font_point_size = int(round(preset.font_point_size * scale_factor))

        ctx = PageContext(pix, path)

        # Restaurar PRESETS originales
        PRESETS = original_presets

        idx = self.tabs.addTab(ctx, path.name); self.tabs.setCurrentIndex(idx)
        self._refresh_tab_close_buttons()
        # Aplica marca de agua si corresponde
        self._apply_wm_to_ctx(ctx)

    def close_tab(self, idx: int):
        ctx = self.tabs.widget(idx)
        if not isinstance(ctx, PageContext):
            self.tabs.removeTab(idx)
            return
        
        # Verificar si hay cambios sin guardar
        if ctx.has_unsaved_changes:
            tab_name = self.tabs.tabText(idx)
            if tab_name.startswith('*'):
                tab_name = tab_name[1:]  # Quitar asterisco para el diálogo
            
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Cerrar pestaña")
            dlg.setText(f"La pestaña '{tab_name}' tiene cambios sin guardar.")
            dlg.setInformativeText("¿Deseas guardar los cambios antes de cerrar?")
            
            btn_save = dlg.addButton("Guardar y cerrar", QMessageBox.ButtonRole.AcceptRole)
            btn_discard = dlg.addButton("Cerrar sin guardar", QMessageBox.ButtonRole.DestructiveRole)
            btn_cancel = dlg.addButton(QMessageBox.StandardButton.Cancel)
            
            dlg.exec()
            clicked = dlg.clickedButton()
            
            if clicked == btn_cancel:
                return  # No cerrar
            elif clicked == btn_save:
                # Guardar antes de cerrar
                old_idx = self.tabs.currentIndex()
                self.tabs.setCurrentIndex(idx)
                self.save_project_bbg_embed()
                # Si canceló el guardado, no cerrar
                if ctx.has_unsaved_changes:
                    self.tabs.setCurrentIndex(old_idx)
                    return
                self.tabs.setCurrentIndex(old_idx)
        
        # Limpiar referencia RAW asociada a esta pestaña
        if ctx in self._raw_per_tab:
            del self._raw_per_tab[ctx]
        
        # Proceder a cerrar
        self.tabs.removeTab(idx)
        self._refresh_tab_close_buttons()
        ctx.deleteLater()

    def close_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self.close_tab(idx)

    def _show_tab_context_menu(self, pos):
        try:
            bar = self.tabs.tabBar()
            idx = bar.tabAt(pos)
            if idx < 0:
                return
            menu = QMenu(bar)
            act_close = menu.addAction("Cerrar pestaña")
            act = menu.exec(bar.mapToGlobal(pos))
            if act == act_close:
                self.close_tab(idx)
        except Exception:
            pass

    def _refresh_tab_close_buttons(self):
        """Sin botones de cierre embebidos para evitar cierres accidentales."""
        self._enhance_tab_nav_buttons()

    def _enhance_tab_nav_buttons(self):
        """Hace visibles/claros los botones de navegar pestañas y menú de pestañas."""
        try:
            bar = self.tabs.tabBar()
            for btn in bar.findChildren(QToolButton):
                arrow = btn.arrowType()
                if arrow == Qt.ArrowType.LeftArrow:
                    btn.setArrowType(Qt.ArrowType.NoArrow)
                    btn.setText("‹")
                    btn.setToolTip("Pestañas anteriores")
                    btn.setAutoRaise(True)
                    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                elif arrow == Qt.ArrowType.RightArrow:
                    btn.setArrowType(Qt.ArrowType.NoArrow)
                    btn.setText("›")
                    btn.setToolTip("Pestañas siguientes")
                    btn.setAutoRaise(True)
                    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                elif arrow == Qt.ArrowType.DownArrow:
                    btn.setArrowType(Qt.ArrowType.NoArrow)
                    btn.setText("⋯")
                    btn.setToolTip("Más pestañas")
                    btn.setAutoRaise(True)
                    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        except Exception:
            pass

    # ---------- UI ----------
    def add_act(self, tb: QToolBar, icon_name: str, tip: str, slot: Callable,
                shortcut: str | None = None, checkable: bool = False) -> QAction:
        act = QAction(icon(icon_name), "" if not icon(icon_name).isNull() else tip,
                      self, checkable=checkable)
        act.setToolTip(tip)
        if shortcut: act.setShortcut(QKeySequence(shortcut))
        act.triggered.connect(slot)
        tb.addAction(act); return act

    def _build_toolbar(self):
        tb = QToolBar("Tools"); tb.setMovable(False); self.addToolBar(tb)

        # Botón tema
        self.theme_btn = QToolButton(); self.theme_btn.setCheckable(True); self.theme_btn.setChecked(True)
        self.theme_btn.setToolTip("Alternar tema claro/oscuro"); self.theme_btn.setIcon(icon('moon.png'))
        self.theme_btn.clicked.connect(self._toggle_theme_btn); tb.addWidget(self.theme_btn)

        # Acciones principales
        open_act     = self.add_act(tb, 'open.png', "Abrir imagen(es) o proyecto(s) • Ctrl+O", self.open_images, "Ctrl+O")
        
        # Workflow automático (nuevo)
        if WORKFLOW_AVAILABLE:
            workflow_act = self.add_act(tb, 'auto.png', "Workflow Automático (RAW → Limpias → Textos) • Ctrl+W", 
                                       self.start_automated_workflow, "Ctrl+W")
        
        add_text     = self.add_act(tb, 'paste.png', "Pegar texto (una línea por caja) • T", self.add_text_paste_dialog)
        dup          = self.add_act(tb, 'duplicate.png', "Duplicar elemento seleccionado", self.duplicate_selected)
        delete       = self.add_act(tb, 'trash.png', "Eliminar elemento seleccionado • Supr", self.delete_selected)
        undo_act     = self.add_act(tb, 'undo.png', "Deshacer • Ctrl+Z", self.do_undo)
        redo_act     = self.add_act(tb, 'redo.png', "Rehacer • Ctrl+Y", self.do_redo)
        export_one   = self.add_act(tb, 'export.png', "Exportar imagen de la pestaña actual", self.export_png_current)
        export_all   = self.add_act(tb, 'export-all.png', "Exportar todas las pestañas a una carpeta", self.export_all_prompt)
        save_bbg     = self.add_act(tb, 'save-proj.png', "Guardar proyecto (.bbg) • Ctrl+S", self.save_project_bbg_embed, "Ctrl+S")
        fonts_cfg    = self.add_act(tb, 'font.png', "Definir fuentes por simbología", self.configure_fonts_per_preset)
        exp_p        = self.add_act(tb, 'save.png', "Exportar presets de fuentes a JSON", self.export_presets_json)
        imp_p        = self.add_act(tb, 'upload.png', "Importar presets de fuentes desde JSON", self.import_presets_json)

        self.lock_move_act = self.add_act(tb, 'lock.png', "Bloqueo global de movimiento • M",
                                          lambda: self.set_movement_locked(self.lock_move_act.isChecked()),
                                          "M", checkable=True)
        
        # Toggle Text Numbers
        self.show_nums_act = self.add_act(tb, '', "Mostrar/Ocultar numeración • N",
                                          self.toggle_text_numbers, "N", checkable=True)
        self.show_nums_act.setText("123")  # Fallback text since no icon
        self.show_nums_act.setChecked(StrokeTextItem.SHOW_ORDINAL)
        
        lock_sel    = self.add_act(tb, 'pin.png', "Fijar seleccionados • Ctrl+L", self.lock_selected_items, "Ctrl+L")
        lock_all    = self.add_act(tb, 'pin-all.png', "Fijar TODOS en pestaña • Ctrl+Shift+L", self.lock_all_items_current_tab, "Ctrl+Shift+L")
        unlock_sel  = self.add_act(tb, 'unlock.png', "Desbloquear seleccionados • Ctrl+U", self.unlock_selected_items_confirm, "Ctrl+U")
        close_tab_act = self.add_act(tb, 'trash.png', "Cerrar pestaña actual • Ctrl+F4", self.close_current_tab, "Ctrl+F4")

        info = self.add_act(tb, 'help.png', "Ayuda: atajos y consejos", lambda: QMessageBox.information(self, "Ayuda",
            "Workflow Automático (Ctrl+W) → automatiza RAW → Traducción → Imágenes Limpias → Colocación de textos.\n"
            "Ctrl+esquina: escala; círculo superior: rotar.\n"
            "Fijar seleccionados: bloquea movimiento, rotación y resize (sigue seleccionable)."))

        # Actualizaciones
        update_act = self.add_act(tb, 'upload.png', "Buscar actualizaciones", lambda: self.check_for_updates(True))

        # Alternar paneles
        self.toggle_props_act = QAction(icon('panel.png'), "", self, checkable=True)
        self.toggle_props_act.setToolTip("Mostrar/ocultar panel de propiedades")
        self.toggle_props_act.toggled.connect(lambda vis: self.prop_dock.setVisible(vis)); tb.addAction(self.toggle_props_act)

        self.toggle_raw_act = QAction(icon('raw.png'), "", self, checkable=True)
        self.toggle_raw_act.setToolTip("Mostrar/ocultar referencia RAW"); tb.addAction(self.toggle_raw_act)

        # Botón Nosotros (ventana emergente)
        self.about_act = QAction(icon('app.ico'), "", self)
        self.about_act.setToolTip("Mostrar información de Nosotros")
        self.about_act.triggered.connect(self.show_about_dialog)
        tb.addAction(self.about_act)

        # Espacio y label de usuario
        tb.addSeparator()
        user_lbl = QLabel(f"  Usuario: {self.currentUser}  ")
        font = user_lbl.font(); font.setBold(True); user_lbl.setFont(font)
        user_lbl.setStyleSheet("color:#f97316;")
        tb.addWidget(user_lbl)

        # Estética toolbar
        key_actions = [open_act, add_text, dup, delete, undo_act, redo_act, export_one, export_all, save_bbg]
        any_missing = any(a.icon().isNull() for a in key_actions)
        if any_missing:
            tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            open_act.setText("Abrir"); add_text.setText("Pegar"); dup.setText("Duplicar"); delete.setText("Eliminar")
            undo_act.setText("Deshacer"); redo_act.setText("Rehacer"); export_one.setText("Exportar")
            export_all.setText("Exportar todas"); save_bbg.setText("Guardar")
        else:
            tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        
        # ===== AJUSTE DE TAMAÑO DE ICONOS DEL TOOLBAR =====
        # Para cambiar el tamaño de los iconos del toolbar, modifica los valores (actualmente 25, 25)
        # Ejemplo: QSize(25, 25) -> QSize(30, 30) para iconos más grandes
        #          QSize(25, 25) -> QSize(20, 20) para iconos más pequeños
        tb.setIconSize(QSize(25, 25))
        self.toggle_raw_act.toggled.connect(lambda vis: self.raw_dock.setVisible(vis))
        self._setup_toolbar_extension_button(tb)

    def _setup_toolbar_extension_button(self, tb: QToolBar):
        """Estilo del botón de desbordamiento del toolbar (cuando faltan espacio)."""
        tb.setStyleSheet(
            "QToolButton#qt_toolbar_ext_button {"
            "background:#182132; color:#E2E8F0; border:1px solid #334155; border-radius:8px;"
            "padding:2px 10px; min-width:72px; min-height:22px; font-weight:700;"
            "}"
            "QToolButton#qt_toolbar_ext_button:hover { background:#24324A; color:#FFFFFF; border-color:#5B6B86; }"
            "QToolButton#qt_toolbar_ext_button:pressed { background:#2C3E5A; }"
        )

        def _wire_ext_btn():
            try:
                ext = tb.findChild(QToolButton, "qt_toolbar_ext_button")
                if not ext:
                    return
                ext.setToolTip("Mas opciones del toolbar")
                ext.setText("Opciones")
                ext.setAutoRaise(False)
                ext.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
                ext.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            except Exception:
                pass

        # Qt crea este botón dinámicamente; lo refrescamos al inicio y en resize.
        QTimer.singleShot(0, _wire_ext_btn)
        orig_resize = tb.resizeEvent
        def _resize_hook(event):
            orig_resize(event)
            QTimer.singleShot(0, _wire_ext_btn)
        tb.resizeEvent = _resize_hook

    def show_about_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Nosotros – AnimeBBG")
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setFixedSize(500, 420)

        dlg.setStyleSheet("""
        QDialog { 
            background-color: #020617; 
        }
        QLabel {
            color: #e5e7eb;
            font-size: 12px;
        }
        QFrame#line {
            border: 2px solid #b91c1c;
        }
        QFrame#Card {
            background-color: #020617;
            border-radius: 10px;
            border: 1px solid #4b5563;
        }
        QToolButton {
            border: none;
        }
        QPushButton {
            padding: 6px 18px;
            border-radius: 999px;
            background-color: #ec4899;
            color: white;
            border: none;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #f472b6;
        }
        """)

        main = QVBoxLayout(dlg)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(10)

        # Línea roja superior
        top_line = QFrame()
        top_line.setObjectName("line")
        top_line.setFrameShape(QFrame.Shape.HLine)
        main.addWidget(top_line)

        # Tarjeta central
        card = QFrame()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # ---- LOGO GRANDE (app.png) ----
        logo_label = QLabel()
        logo_pix = QPixmap(str(ASSETS / "icons" / "app.png"))
        if not logo_pix.isNull():
            logo_label.setPixmap(
                logo_pix.scaled(
                    180, 180,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            logo_label.setText("AnimeBBG")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(logo_label, 0, 0, 3, 1)

        # Título / info (sin Desarrollo / Arte)
        title = QLabel("<b>AnimeBBG Editor</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#f97316; font-size:25px;")
        grid.addWidget(title, 0, 1)

        subtitle = QLabel(f"© 2025 – versión {APP_VERSION}")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color:#9ca3af; font-size:12px;")
        grid.addWidget(subtitle, 1, 1)

        # ---- SOLO ICONOS COMO BOTONES (SIN TEXTO) ----
        icons_layout = QHBoxLayout()
        icons_layout.addStretch(1)

        def make_icon_button(filename: str, url: str) -> QToolButton:
            btn = QToolButton()
            pix = QPixmap(str(ASSETS / "icons" / filename))
            if not pix.isNull():
                btn.setIcon(QIcon(pix))
            else:
                emoji_map = {
                    "web.png": "🌐",
                    "discord.png": "💬",
                    "paypal.png": "💲",
                }
                pm = QPixmap(40, 40)
                pm.fill(Qt.GlobalColor.transparent)
                p = QPainter(pm)
                f = QFont("Segoe UI Emoji", 24)
                p.setFont(f)
                p.drawText(pm.rect(), int(Qt.AlignmentFlag.AlignCenter), emoji_map.get(filename, "❓"))
                p.end()
                btn.setIcon(QIcon(pm))

            # ===== AJUSTE DE TAMAÑO DE ICONOS DEL DIÁLOGO "NOSOTROS" =====
            # Para cambiar el tamaño de los iconos (Web, Discord, PayPal), modifica los valores (actualmente 41, 41)
            # Ejemplo: QSize(41, 41) -> QSize(50, 50) para iconos más grandes
            #          QSize(41, 41) -> QSize(35, 35) para iconos más pequeños
            btn.setIconSize(QSize(41, 41))
            btn.setAutoRaise(True)
            btn.clicked.connect(lambda checked=False, u=url: webbrowser.open(u))
            return btn

        icons_layout.addWidget(make_icon_button("web.png",     ABOUT_LINKS["WEB"]))
        icons_layout.addWidget(make_icon_button("discord.png", ABOUT_LINKS["DISCORD"]))
        icons_layout.addWidget(make_icon_button("paypal.png",  ABOUT_LINKS["PAYPAL"]))

        icons_layout.addStretch(1)
        grid.addLayout(icons_layout, 2, 1)

        main.addWidget(card)

        # Línea roja inferior
        bottom_line = QFrame()
        bottom_line.setObjectName("line")
        bottom_line.setFrameShape(QFrame.Shape.HLine)
        main.addWidget(bottom_line)

        # Botón Cerrar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(dlg.accept)
        btn_layout.addWidget(close_btn)
        main.addLayout(btn_layout)

        dlg.exec()

    def _build_right_panel(self):
        PANEL_SS = """
            QScrollArea, QWidget#PropContent { background: #0D1117; border: none; }
            QComboBox, QSpinBox {
                background: #1E2636; color: #E2E8F0;
                border: 1px solid #2D3748; border-radius: 4px;
                padding: 2px 6px; font-size: 10px; max-height: 22px;
            }
            QComboBox::drop-down { border: none; width: 16px; }
            QComboBox QAbstractItemView {
                background: #1E2636; color: #E2E8F0;
                selection-background-color: #E11D48; font-size: 10px;
            }
            QSlider::groove:horizontal { height: 3px; background: #2D3748; border-radius: 1px; }
            QSlider::handle:horizontal { background: #E11D48; border-radius: 5px; width: 10px; height: 10px; margin: -4px 0; }
            QSlider::sub-page:horizontal { background: #E11D48; border-radius: 1px; }
            QPushButton#PropBtn {
                background: #1E2636; color: #CBD5E1;
                border: 1px solid #2D3748; border-radius: 4px;
                padding: 3px 8px; font-size: 10px; text-align: left; max-height: 22px;
            }
            QPushButton#PropBtn:hover { background: #263045; border-color: #4B5563; }
            QPushButton#BoldSelBtn {
                background: #1E2636; color: #CBD5E1;
                border: 1px solid #374151; border-radius: 4px;
                padding: 3px; font-size: 10px; font-weight: 600; max-height: 22px;
            }
            QPushButton#BoldSelBtn:hover { background: #263045; }
            QPushButton#AlignBtn {
                background: #1E2636; color: #9CA3AF;
                border: 1px solid #2D3748; border-radius: 4px;
                padding: 2px; font-size: 11px; min-width: 24px; max-height: 22px;
            }
            QPushButton#AlignBtn:hover { background: #263045; color: #E2E8F0; }
            QPushButton#AlignBtn:checked {
                background: #374151; color: #E2E8F0; border-color: #4B5563;
            }
            QLabel#ValLabel { color: #6B7280; font-size: 9px; min-width: 24px; }
        """

        self.prop_dock = QDockWidget("Propiedades", self)
        self.prop_dock.setObjectName("PropDock")

        self.prop_panel = QWidget()
        self.prop_panel.setStyleSheet(PANEL_SS)
        root_vbox = QVBoxLayout(self.prop_panel)
        root_vbox.setContentsMargins(0, 0, 0, 0)
        root_vbox.setSpacing(0)

        self.prop_toggle_btn = QToolButton(self.prop_panel)
        self.prop_toggle_btn.setCheckable(True)
        self.prop_toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.prop_toggle_btn.setArrowType(Qt.ArrowType.RightArrow)
        self.prop_toggle_btn.setFixedWidth(24)
        self.prop_toggle_btn.toggled.connect(self.toggle_prop_panel)
        root_vbox.addWidget(self.prop_toggle_btn, 0)

        self.prop_content_widget = QWidget()
        self.prop_content_widget.setObjectName("PropContent")
        scroll = QScrollArea()
        scroll.setWidget(self.prop_content_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root_vbox.addWidget(scroll, 1)

        screen = QGuiApplication.primaryScreen()
        geom = screen.availableGeometry() if screen else None
        screen_h = geom.height() if geom else 768
        compact_laptop = screen_h <= 900

        main_layout = QVBoxLayout(self.prop_content_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2 if compact_laptop else 3)

        self.symb_combo = QComboBox()
        self.symb_combo.addItems(list(PRESETS.keys()))
        self.symb_combo.currentIndexChanged.connect(self.on_symbol_changed)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 2000)
        self.width_spin.valueChanged.connect(self.on_width_changed)

        self.cap_combo = QComboBox()
        self.cap_combo.addItems(["Normal", "MAYÚSCULAS", "minúsculas"])
        self.cap_combo.currentIndexChanged.connect(self.on_capitalization_changed)

        self.bold_chk = ToggleSwitch()
        self.bold_chk.setToolTip("Aplica negrita a toda la caja de texto")
        self.bold_chk.stateChanged.connect(self.on_bold_toggle)

        self.bold_sel_btn = QPushButton("Negrita selectiva (Ctrl+B)")
        self.bold_sel_btn.setObjectName("BoldSelBtn")
        self.bold_sel_btn.setToolTip("Doble clic en la caja, selecciona texto y usa este botón o Ctrl+B")
        self.bold_sel_btn.clicked.connect(self.apply_bold_to_current_selection)

        self.font_btn = QPushButton("Fuente")
        self.font_btn.setObjectName("PropBtn")
        self.font_btn.setEnabled(False)
        self.font_btn.setToolTip("Selecciona una caja de texto para ver/cambiar su fuente")
        self.font_btn.clicked.connect(self.choose_font)

        self.fill_btn = QPushButton()
        self.fill_btn.hide()
        self.fill_btn.clicked.connect(lambda: self.choose_color('fill'))
        self._fill_swatch = ColorSwatch("#000000")
        self._fill_swatch.clicked.connect(lambda: self.choose_color('fill'))

        self.out_btn = QPushButton()
        self.out_btn.hide()
        self.out_btn.clicked.connect(lambda: self.choose_color('outline'))
        self._out_swatch = ColorSwatch("#FFFFFF")
        self._out_swatch.clicked.connect(lambda: self.choose_color('outline'))

        self.no_stroke_chk = ToggleSwitch()
        self.no_stroke_chk.stateChanged.connect(self.on_no_stroke_toggle)

        self.outw_slider = QSlider(Qt.Orientation.Horizontal)
        self.outw_slider.setRange(0, 40)
        self.outw_slider.setSingleStep(1)
        self.outw_slider.setPageStep(1)
        self.outw_slider.setTickInterval(1)
        self.outw_slider.setValue(3)
        self.outw_slider.valueChanged.connect(self.on_outline_width)
        self.outw_slider.valueChanged.connect(self._on_outline_slider_ui_changed)
        self.outw_label = QLabel("3")
        self.outw_label.setObjectName("ValLabel")
        self.outw_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.outw_spin = QSpinBox()
        self.outw_spin.setRange(0, 40)
        self.outw_spin.setFixedWidth(52)
        self.outw_spin.setValue(3)
        self.outw_spin.valueChanged.connect(lambda v: self.outw_slider.setValue(v))

        self.shadow_chk = ToggleSwitch()
        self.shadow_chk.stateChanged.connect(self.on_shadow_toggle)

        self.bg_chk = ToggleSwitch()
        self.bg_chk.stateChanged.connect(self.on_bg_toggle)

        self.bg_btn = QPushButton()
        self.bg_btn.hide()
        self.bg_btn.clicked.connect(lambda: self.choose_color('background_color'))
        self._bg_swatch = ColorSwatch("#FFFFFF")
        self._bg_swatch.clicked.connect(lambda: self.choose_color('background_color'))

        self.bg_op = QSlider(Qt.Orientation.Horizontal)
        self.bg_op.setRange(0, 100)
        self.bg_op.setValue(100)
        self.bg_op.valueChanged.connect(self.on_bg_op)
        self._bg_op_label = QLabel("100")
        self._bg_op_label.setObjectName("ValLabel")
        self._bg_op_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.bg_op.valueChanged.connect(lambda v: self._bg_op_label.setText(str(v)))

        self.align_combo = QComboBox()
        self.align_combo.addItems(["Izquierda", "Centro", "Derecha", "Justificar"])
        self.align_combo.setCurrentIndex(1)
        self.align_combo.currentIndexChanged.connect(self.on_alignment_changed)
        self.align_combo.hide()

        self.linespace_slider = QSlider(Qt.Orientation.Horizontal)
        self.linespace_slider.setRange(80, 300)
        self.linespace_slider.setValue(120)
        self.linespace_slider.valueChanged.connect(lambda v: self.on_linespacing_changed(v / 100))
        self.linespace_label = QLabel("1.20")
        self.linespace_label.setObjectName("ValLabel")
        self.linespace_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.linespace_slider.valueChanged.connect(lambda v: self.linespace_label.setText(f"{v/100:.2f}"))

        self.hyphen_chk = ToggleSwitch()
        self.hyphen_chk.setToolTip("Inserta guiones suaves para cortar palabras largas sin desbordar")
        self.hyphen_chk.stateChanged.connect(self.on_hyphenate_toggle)

        # Warp / Deformar texto
        self.warp_style_combo = QComboBox()
        self.warp_style_combo.addItems(["Ninguno", "Arco", "Onda", "Bandera", "Pez"])
        self.warp_style_combo.currentIndexChanged.connect(self.on_warp_controls_changed)
        self.warp_orient_combo = QComboBox()
        self.warp_orient_combo.addItems(["Horizontal", "Vertical"])
        self.warp_orient_combo.currentIndexChanged.connect(self.on_warp_controls_changed)

        self.warp_bend_slider = QSlider(Qt.Orientation.Horizontal)
        self.warp_bend_slider.setRange(-100, 100)
        self.warp_bend_slider.setValue(0)
        self.warp_bend_slider.valueChanged.connect(self.on_warp_controls_changed)
        self.warp_bend_label = QLabel("0")
        self.warp_bend_label.setObjectName("ValLabel")
        self.warp_bend_slider.valueChanged.connect(lambda v: self.warp_bend_label.setText(str(v)))

        self.warp_hdist_slider = QSlider(Qt.Orientation.Horizontal)
        self.warp_hdist_slider.setRange(-100, 100)
        self.warp_hdist_slider.setValue(0)
        self.warp_hdist_slider.valueChanged.connect(self.on_warp_controls_changed)
        self.warp_hdist_label = QLabel("0")
        self.warp_hdist_label.setObjectName("ValLabel")
        self.warp_hdist_slider.valueChanged.connect(lambda v: self.warp_hdist_label.setText(str(v)))

        self.warp_vdist_slider = QSlider(Qt.Orientation.Horizontal)
        self.warp_vdist_slider.setRange(-100, 100)
        self.warp_vdist_slider.setValue(0)
        self.warp_vdist_slider.valueChanged.connect(self.on_warp_controls_changed)
        self.warp_vdist_label = QLabel("0")
        self.warp_vdist_label.setObjectName("ValLabel")
        self.warp_vdist_slider.valueChanged.connect(lambda v: self.warp_vdist_label.setText(str(v)))

        self.wm_enable_chk = ToggleSwitch()
        self.wm_enable_chk.toggled.connect(self.on_wm_enable_toggled)

        self.wm_pick_btn = QPushButton("Elegir imagen...")
        self.wm_pick_btn.setObjectName("PropBtn")
        self.wm_pick_btn.clicked.connect(self.choose_wm_image)

        self.wm_op_slider = QSlider(Qt.Orientation.Horizontal)
        self.wm_op_slider.setRange(0, 100)
        self.wm_op_slider.setValue(100)
        self.wm_op_slider.valueChanged.connect(self.on_wm_opacity_changed)
        self._wm_op_label = QLabel("100")
        self._wm_op_label.setObjectName("ValLabel")
        self._wm_op_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.wm_op_slider.valueChanged.connect(lambda v: self._wm_op_label.setText(str(v)))

        def slider_row(slider, val_label):
            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(slider, 1)
            row.addWidget(val_label)
            return row

        align_row_layout = QHBoxLayout()
        align_row_layout.setSpacing(4)
        self._align_btns = []
        for i, lbl in enumerate(["L", "C", "R", "J"]):
            btn = QPushButton(lbl)
            btn.setObjectName("AlignBtn")
            btn.setCheckable(True)
            btn.setChecked(i == 1)
            btn.clicked.connect(lambda checked, ix=i: self._on_align_btn(ix))
            align_row_layout.addWidget(btn)
            self._align_btns.append(btn)
        self.align_combo.currentIndexChanged.connect(self._sync_align_btns)

        sec_general = PropSection("General", "#")
        cl = sec_general.content_layout()
        cl.addLayout(_prop_row("Simbologia", self.symb_combo))
        dbl = QHBoxLayout()
        dbl.setSpacing(6)
        w_grp = QVBoxLayout()
        w_grp.setSpacing(2)
        w_grp.addWidget(QLabel("Ancho caja", styleSheet="color:#9CA3AF;font-size:9px;"))
        self.width_spin.setFixedWidth(58)
        w_grp.addWidget(self.width_spin)
        c_grp = QVBoxLayout()
        c_grp.setSpacing(2)
        c_grp.addWidget(QLabel("Mayus/minus", styleSheet="color:#9CA3AF;font-size:9px;"))
        c_grp.addWidget(self.cap_combo)
        dbl.addLayout(w_grp)
        dbl.addLayout(c_grp)
        cl.addLayout(dbl)
        main_layout.addWidget(sec_general)

        sec_typo = PropSection("Tipografia", "T")
        cl = sec_typo.content_layout()
        cl.addLayout(_prop_toggle_row("Negrita (toda la caja)", self.bold_chk))
        cl.addWidget(self.bold_sel_btn)
        fc_row = QHBoxLayout()
        fc_row.setSpacing(6)
        fc_row.addWidget(self.font_btn, 1)
        color_grp = QVBoxLayout()
        color_grp.setSpacing(2)
        color_grp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_color = QLabel("Color", styleSheet="color:#9CA3AF;font-size:9px;")
        lbl_color.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_grp.addWidget(lbl_color)
        color_grp.addWidget(self._fill_swatch)
        fc_row.addLayout(color_grp)
        cl.addLayout(fc_row)
        ls_hdr = QHBoxLayout()
        ls_hdr.addWidget(QLabel("Interlineado", styleSheet="color:#9CA3AF;font-size:9px;"))
        ls_hdr.addStretch()
        ls_hdr.addWidget(self.linespace_label)
        cl.addLayout(ls_hdr)
        cl.addLayout(slider_row(self.linespace_slider, QLabel()))
        cl.addWidget(QLabel("Alineacion", styleSheet="color:#9CA3AF;font-size:9px;"))
        cl.addLayout(align_row_layout)
        cl.addLayout(_prop_toggle_row("Guionado automatico", self.hyphen_chk))
        main_layout.addWidget(sec_typo)

        sec_warp = PropSection("Deformar", "W")
        cl = sec_warp.content_layout()
        cl.addLayout(_prop_row("Estilo", self.warp_style_combo))
        cl.addLayout(_prop_row("Orientacion", self.warp_orient_combo))
        wh = QHBoxLayout()
        wh.addWidget(QLabel("Curvar", styleSheet="color:#9CA3AF;font-size:9px;"))
        wh.addStretch()
        wh.addWidget(self.warp_bend_label)
        cl.addLayout(wh)
        cl.addLayout(slider_row(self.warp_bend_slider, QLabel()))
        hh = QHBoxLayout()
        hh.addWidget(QLabel("Dist. horizontal", styleSheet="color:#9CA3AF;font-size:9px;"))
        hh.addStretch()
        hh.addWidget(self.warp_hdist_label)
        cl.addLayout(hh)
        cl.addLayout(slider_row(self.warp_hdist_slider, QLabel()))
        vh = QHBoxLayout()
        vh.addWidget(QLabel("Dist. vertical", styleSheet="color:#9CA3AF;font-size:9px;"))
        vh.addStretch()
        vh.addWidget(self.warp_vdist_label)
        cl.addLayout(vh)
        cl.addLayout(slider_row(self.warp_vdist_slider, QLabel()))
        sec_warp.set_collapsed(True)
        main_layout.addWidget(sec_warp)

        sec_appr = PropSection("Apariencia", "A")
        cl = sec_appr.content_layout()
        cl.addLayout(_prop_toggle_row("Trazo", self.no_stroke_chk, self._out_swatch))
        gsr_hdr = QHBoxLayout()
        gsr_hdr.addWidget(QLabel("Grosor trazo", styleSheet="color:#9CA3AF;font-size:9px;"))
        gsr_hdr.addStretch()
        gsr_hdr.addWidget(self.outw_spin)
        gsr_hdr.addWidget(self.outw_label)
        cl.addLayout(gsr_hdr)
        cl.addLayout(slider_row(self.outw_slider, QLabel()))
        cl.addLayout(_prop_toggle_row("Sombra", self.shadow_chk))
        main_layout.addWidget(sec_appr)

        sec_bg = PropSection("Ajustes de fondo", "B")
        cl = sec_bg.content_layout()
        cl.addLayout(_prop_toggle_row("Fondo caja", self.bg_chk, self._bg_swatch))
        op_hdr = QHBoxLayout()
        op_hdr.addWidget(QLabel("Opacidad fondo", styleSheet="color:#9CA3AF;font-size:9px;"))
        op_hdr.addStretch()
        op_hdr.addWidget(self._bg_op_label)
        cl.addLayout(op_hdr)
        cl.addLayout(slider_row(self.bg_op, QLabel()))
        sec_bg.set_collapsed(True)
        main_layout.addWidget(sec_bg)

        sec_wm = PropSection("Marca de agua", "M")
        cl = sec_wm.content_layout()
        cl.addLayout(_prop_toggle_row("Usar marca", self.wm_enable_chk))
        cl.addLayout(_prop_row("Imagen", self.wm_pick_btn))
        wm_hdr = QHBoxLayout()
        wm_hdr.addWidget(QLabel("Opacidad marca", styleSheet="color:#9CA3AF;font-size:9px;"))
        wm_hdr.addStretch()
        wm_hdr.addWidget(self._wm_op_label)
        cl.addLayout(wm_hdr)
        cl.addLayout(slider_row(self.wm_op_slider, QLabel()))
        # Oculta esta sección al inicio porque es una opción secundaria.
        sec_wm.set_collapsed(True)
        main_layout.addWidget(sec_wm)

        if compact_laptop:
            # En pantallas bajas, iniciar secciones secundarias colapsadas
            sec_bg.set_collapsed(True)

        main_layout.addStretch()
        self.prop_panel.setMaximumWidth(16777215)
        self.prop_dock.setWidget(self.prop_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.prop_dock)
        # Ancho fijo y consistente para evitar diferencias visuales por resolución/DPI.
        target_width = 260
        self.prop_dock.setMinimumWidth(220)
        self.prop_dock.setMaximumWidth(300)
        QTimer.singleShot(
            0,
            lambda: self.resizeDocks([self.prop_dock], [target_width], Qt.Orientation.Horizontal)
        )
        try:
            self.prop_dock.visibilityChanged.connect(self._on_prop_visibility_changed)
            for tb in self.findChildren(QToolBar):
                tb.addAction(self.toggle_props_act)
                break
        except Exception:
            pass
        self._apply_bg_controls_state()

    def _on_align_btn(self, index: int):
        for i, btn in enumerate(self._align_btns):
            btn.setChecked(i == index)
        self.align_combo.blockSignals(True)
        self.align_combo.setCurrentIndex(index)
        self.align_combo.blockSignals(False)
        self.on_alignment_changed(index)

    def _sync_align_btns(self, index: int):
        if not hasattr(self, "_align_btns"):
            return
        for i, btn in enumerate(self._align_btns):
            btn.setChecked(i == index)

    def _on_prop_visibility_changed(self, visible: bool):
        """Sincroniza la acción del toolbar con el dock de propiedades,
        ignorando cambios cuando la ventana está minimizada.
        """
        if self.isMinimized():
            return
        self.toggle_props_act.blockSignals(True)
        self.toggle_props_act.setChecked(visible)
        self.toggle_props_act.blockSignals(False)

    def toggle_prop_panel(self, checked: bool):
        """Colapsa/expande el panel de propiedades al estilo Photoshop."""
        if checked:
            # Colapsado: solo la tirita con el botón
            self.prop_content_widget.hide()
            # Ancho reducido, casi solo el botón
            self.prop_panel.setMaximumWidth(self.prop_toggle_btn.width() + 8)
            # Flecha hacia la izquierda ◀ (indica que se puede expandir)
            self.prop_toggle_btn.setArrowType(Qt.ArrowType.LeftArrow)
        else:
            # Expandido: se ve el contenido completo
            self.prop_content_widget.show()
            self.prop_panel.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
            # Flecha hacia la derecha ▶ (indica que se puede colapsar)
            self.prop_toggle_btn.setArrowType(Qt.ArrowType.RightArrow)

    # ---------------- Acciones principales ----------------
    def open_images(self):
        filter_str = "Todos los archivos soportados (*.png *.jpg *.jpeg *.webp *.bbg"
        if PSD_AVAILABLE:
            filter_str += " *.psd"
        filter_str += ");;Imágenes (*.png *.jpg *.jpeg *.webp);;Proyectos (*.bbg)"
        if PSD_AVAILABLE:
            filter_str += ";;Photoshop (*.psd)"
        
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Abrir imagen(es), proyecto(s) o PSD", 
            "", 
            filter_str
        )
        if not files: 
            return
        
        # Procesar cada archivo según su extensión
        for f in files:
            file_path = Path(f)
            suffix = file_path.suffix.lower()
            if suffix == '.bbg':
                # Es un archivo .bbg, usar la función de abrir proyecto
                self._open_single_project_bbg(str(file_path))
            elif suffix == '.psd' and PSD_AVAILABLE:
                # Es un archivo PSD
                self.open_psd_file(str(file_path))
            else:
                # Es una imagen
                self.add_tab_for_image(file_path)

    def _push_add_command(self, ctx: 'PageContext', item: StrokeTextItem, pos: QPointF):
        def undo(): ctx.scene.removeItem(item); ctx.remove_item_from_list(item)
        def redo(): item.setPos(pos); ctx.add_item_and_list(item); item.set_locked(item.locked, self.lock_move)
        push_cmd(ctx.undo_stack, "Añadir caja", undo, redo)

    def add_text_paste_dialog(self):
        ctx = self.current_ctx()
        if not ctx: QMessageBox.information(self, "Sin pestaña", "Abre una imagen antes de pegar texto."); return
        dlg = QDialog(self); dlg.setWindowTitle("Pegar texto – una línea por caja")
        dlg.setMinimumWidth(600)
        dlg.setMinimumHeight(400)
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("Identificadores (opcionales): Globo 1:, G1:, N/T:, *: (FUERA_GLOBO), ():, (texto), []:, [texto].\n`//` crea ANIDADO inline. (Se quita el identificador)."))
        
        # Usar SpellCheckTextEdit en lugar de QTextEdit
        te = SpellCheckTextEdit(); te.setPlaceholderText("Globo 1: Texto...\n(): Pensamiento\n[Nota en cuadro]")
        te.setPlainText(QGuiApplication.clipboard().text()); v.addWidget(te)
        
        # Fila de opciones
        spell_check_controls = QHBoxLayout()

        # Toggle: omitir * al inicio de línea (se guarda en QSettings)
        strip_star_chk = QCheckBox("Omitir  *  al inicio de línea")
        strip_star_chk.setToolTip(
            "Si está activo, las líneas que empiecen con * (sin dos puntos) \n"
            "se insertan como GLOBO normal quitando el asterisco."
        )
        saved_strip = str(self.settings.value('paste_strip_star', '0')) == '1'
        strip_star_chk.setChecked(saved_strip)
        strip_star_chk.toggled.connect(
            lambda checked: self.settings.setValue('paste_strip_star', '1' if checked else '0')
        )
        spell_check_controls.addWidget(strip_star_chk)
        spell_check_controls.addStretch()

        spell_check_btn = QPushButton("🔍 Revisar Ortografía")
        spell_check_btn.setToolTip("Verifica y corrige errores ortográficos")
        spell_check_btn.clicked.connect(lambda: self._open_spellcheck_dialog(te))
        spell_check_controls.addWidget(spell_check_btn)
        v.addLayout(spell_check_controls)
        
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); v.addWidget(bb)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        do_strip_star = strip_star_chk.isChecked()

        lines = [ln for ln in te.toPlainText().splitlines() if ln.strip()]
        if not lines: return
        y = 50
        for line in lines:
            # Si el toggle está activo, quitar * al inicio antes de parsear
            if do_strip_star:
                stripped = line.lstrip()
                if stripped.startswith('*') and not stripped.startswith('*:'):
                    line = stripped[1:].lstrip()
            preset_key, clean = parse_identifier(line)
            parts = [p.strip() for p in clean.split('//') if p.strip()] or [clean.strip()]
            first_style = None
            for idx, seg in enumerate(parts):
                if not seg:
                    continue
                if idx == 0:
                    use_preset = preset_key
                    style = replace(PRESETS.get(use_preset, PRESETS['GLOBO']))
                    # Guardar el estilo del primer globo
                    first_style = replace(style)
                else:
                    use_preset = preset_key  # Mantener el mismo nombre
                    # Usar una copia del estilo del primer globo
                    style = replace(first_style) if first_style else replace(PRESETS['ANIDADO'])
                item = StrokeTextItem(seg, style, name=use_preset)
                item.setFont(item.style.to_qfont())
                self._push_add_command(ctx, item, QPointF(50, y))
                y += 70
    
    def _open_spellcheck_dialog(self, text_edit: SpellCheckTextEdit):
        """Abre el diálogo de corrección ortográfica"""
        if not SPELLCHECK_AVAILABLE:
            QMessageBox.warning(
                self,
                "Función no disponible",
                "El corrector ortográfico no está disponible.\n"
                "Instala: pip install pyspellchecker"
            )
            return

        if not text_edit.spell_checker:
            QMessageBox.warning(
                self,
                "Error de inicialización",
                "No se pudo cargar el diccionario de español.\n\n"
                "Posibles causas:\n"
                "1. Falta conexión a internet (para descargar el diccionario por primera vez).\n"
                "2. El archivo de diccionario no está incluido en el ejecutable."
            )
            return
        
        # Forzar una verificación
        text_edit._on_text_changed()
        
        # Abrir diálogo
        spell_dlg = SpellCheckDialog(text_edit, self)
        spell_dlg.exec()

    # ---------------- Workflow Automático ----------------
    def start_automated_workflow(self):
        """Inicia el workflow automático de traducción"""
        if not WORKFLOW_AVAILABLE:
            QMessageBox.warning(
                self,
                "Módulo no disponible",
                "El módulo de workflow automático no está disponible.\n"
                "Asegúrate de que automated_workflow.py esté en la misma carpeta."
            )
            return
        
        try:
            # Run the wizard
            wizard = WorkflowWizard(self, presets=list(PRESETS.keys()))
            workflow_data = wizard.run()
            
            if not workflow_data:
                return  # User cancelled
            
            # Apply the workflow data
            self._apply_workflow_data(workflow_data)
            
            self.statusBar().showMessage(
                f"✅ Workflow completado: {len(workflow_data.clean_image_paths)} imagen(es) procesada(s)", 
                5000
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error en Workflow",
                f"Ocurrió un error durante el workflow automático:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()
    
    def _apply_workflow_data(self, workflow_data: 'WorkflowData'):
        """Aplica los datos del workflow: crea pestañas y coloca textos automáticamente"""
        from pathlib import Path
        
        raw_size = self._get_raw_image_size(getattr(workflow_data, "raw_image_path", ""))
        
        # For each clean image, create a tab and place text boxes
        for clean_image_path in workflow_data.clean_image_paths:
            # Load the clean image
            pix = QPixmap(clean_image_path)
            if pix.isNull():
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo cargar la imagen: {Path(clean_image_path).name}"
                )
                continue
            
            # Create a new tab
            ctx = PageContext(pix, Path(clean_image_path))
            idx = self.tabs.addTab(ctx, Path(clean_image_path).name)
            self._refresh_tab_close_buttons()
            
            # Store workflow data in context for persistence
            ctx.workflow_data = workflow_data.to_dict()
            
            # Apply watermark if enabled
            self._apply_wm_to_ctx(ctx)
            
            # Place text boxes according to detections
            clean_size = pix.size()
            scale_x, scale_y = 1.0, 1.0
            if raw_size and raw_size.width() > 0 and raw_size.height() > 0:
                scale_x = clean_size.width() / raw_size.width()
                scale_y = clean_size.height() / raw_size.height()
            for detection in workflow_data.detections:
                self._place_text_from_detection(ctx, detection, scale_x=scale_x, scale_y=scale_y)
            
            # Mark as modified (has unsaved changes)
            self.mark_tab_modified(ctx)
        
        # Switch to the first created tab
        if workflow_data.clean_image_paths:
            # Find the first tab we just created
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if isinstance(widget, PageContext):
                    tab_name = self.tabs.tabText(i).lstrip('*')
                    if tab_name == Path(workflow_data.clean_image_paths[0]).name:
                        self.tabs.setCurrentIndex(i)
                        break
    
    def _get_raw_image_size(self, raw_path: str) -> Optional[QSize]:
        if not raw_path:
            return None
        try:
            img = QImage(raw_path)
            if img.isNull():
                return None
            return img.size()
        except Exception:
            return None

    def _auto_fit_text_item_to_rect(self, item: 'StrokeTextItem', rect: QRectF,
                                    min_pt: int = 6, max_pt: Optional[int] = None):
        """Ajusta el tamaño de fuente para que el texto quepa dentro del rect."""
        text = item.get_raw_text().strip()
        if not text:
            return

        item.setTextWidth(max(10.0, rect.width()))
        item._apply_paragraph_to_doc()

        base_pt = max(1, int(item.style.font_point_size))
        base_outline = int(item.style.outline_width)
        if max_pt is None:
            max_pt = max(base_pt, int(rect.height() * 2))

        low, high = min_pt, max_pt
        best = min_pt

        def _apply_size(pt: int):
            item.style.font_point_size = int(pt)
            if base_pt > 0:
                item.style.outline_width = int(round(base_outline * (pt / base_pt)))
            item.setFont(item.style.to_qfont())
            item._apply_paragraph_to_doc()

        while low <= high:
            mid = (low + high) // 2
            _apply_size(mid)
            doc_h = item.document().size().height()
            if doc_h <= rect.height():
                best = mid
                low = mid + 1
            else:
                high = mid - 1

        _apply_size(best)

    def _place_text_from_detection(self, ctx: 'PageContext', detection: 'TextBoxDetection',
                                   scale_x: float = 1.0, scale_y: float = 1.0):
        """Coloca una caja de texto en el contexto según una detección"""
        # Get the preset style
        style = PRESETS.get(detection.preset, PRESETS['GLOBO'])
        
        # Create the text item
        item = StrokeTextItem(detection.text, replace(style), name=detection.preset)
        item.ordinal = detection.id
        
        # Set position from detection
        rect = detection.get_qrectf()
        if scale_x != 1.0 or scale_y != 1.0:
            rect = QRectF(
                rect.x() * scale_x,
                rect.y() * scale_y,
                rect.width() * scale_x,
                rect.height() * scale_y
            )
        item.setPos(QPointF(rect.x(), rect.y()))
        
        # Set width from detection
        item.setTextWidth(rect.width())
        
        # Add to scene and list
        ctx.add_item_and_list(item)
        
        # Apply font
        item.setFont(item.style.to_qfont())
        item._apply_paragraph_to_doc()
        item.apply_shadow()

        # Auto-fit font size to the detected box height
        self._auto_fit_text_item_to_rect(item, rect)

    # ---------------- Propiedades ----------------
    def _sync_props_from_item(self, item: StrokeTextItem):
        self._update_font_button_state(self._selected_items())
        bs = [self.width_spin, self.outw_slider, self.align_combo, self.linespace_slider,
              self.symb_combo, self.no_stroke_chk, self.hyphen_chk,
              self.shadow_chk, self.bg_chk, self.bg_op, self.cap_combo, self.bold_chk,
              self.warp_style_combo, self.warp_orient_combo,
              self.warp_bend_slider, self.warp_hdist_slider, self.warp_vdist_slider]
        if hasattr(self, 'outw_spin'):
            bs.append(self.outw_spin)
        for w in bs: w.blockSignals(True)

        # NUEVO: Mostrar advertencia si la fuente original no está disponible (tipo Photoshop)
        suppress_warning = self.settings.value("suppress_font_warning", False, type=bool)
        
        should_warn = (hasattr(item, 'original_font_family') and 
                       item.original_font_family != item.style.font_family and 
                       not is_font_installed(item.original_font_family) and
                       not item.font_missing_warning_shown and
                       not suppress_warning)

        if should_warn:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Fuente faltante")
            msg_box.setText(f"La fuente '{item.original_font_family}' no está instalada en tu sistema.")
            msg_box.setInformativeText(
                f"Se está usando '{item.style.font_family}' como fallback.\n\n"
                f"Si editas este texto, se guardará con la fuente fallback. "
                f"Para restaurar la fuente original, instálala en tu sistema e reabre el proyecto."
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Checkbox to suppress future warnings
            cb = QCheckBox("No volver a mostrar este mensaje")
            msg_box.setCheckBox(cb)
            
            msg_box.exec()
            
            if cb.isChecked():
                self.settings.setValue("suppress_font_warning", True)

            item.font_missing_warning_shown = True

        self.width_spin.setValue(int(item.textWidth()))
        
        # Actualizar slider de grosor trazo
        outw_value = item.style.outline_width
        self.outw_slider.setValue(outw_value)
        self.outw_label.setText(str(outw_value))
        if hasattr(self, 'outw_spin'):
            self.outw_spin.setValue(int(outw_value))
        
        self.no_stroke_chk.setChecked(item.style.outline_width == 0); self._apply_no_stroke_enabled_state()

        self.bold_chk.setChecked(bool(item.style.bold))

        align_map = {'left': 0, 'center': 1, 'right': 2, 'justify': 3}
        self.align_combo.setCurrentIndex(align_map.get(item.style.alignment, 1))
        self._sync_align_btns(self.align_combo.currentIndex())
        
        # Actualizar sliders
        linespace_value = int(float(item.style.line_spacing) * 100)
        self.linespace_slider.setValue(linespace_value)
        self.linespace_label.setText(f"{linespace_value/100:.2f}")

        self.hyphen_chk.setChecked(bool(getattr(item.style, 'auto_hyphenate', False)))


        self.shadow_chk.setChecked(bool(item.style.shadow_enabled))
        self.bg_chk.setChecked(bool(item.style.background_enabled))
        try: self.bg_op.setValue(int(clamp(item.style.background_opacity, 0, 1)*100))
        except Exception: self.bg_op.setValue(0)

        try: idx = list(PRESETS.keys()).index(item.name)
        except ValueError: idx = 0
        self.symb_combo.setCurrentIndex(idx)

        cap_map_to_idx = {'mixed':0, 'uppercase':1, 'lowercase':2, 'capitalize':3, 'smallcaps':4}
        self.cap_combo.setCurrentIndex(cap_map_to_idx.get(getattr(item.style, 'capitalization', 'mixed'), 0))

        warp_map = {'none': 0, 'arc': 1, 'wave': 2, 'flag': 3, 'fish': 4}
        ws = str(getattr(item.style, 'warp_style', 'none') or 'none')
        self.warp_style_combo.setCurrentIndex(warp_map.get(ws, 0))
        self.warp_orient_combo.setCurrentIndex(1 if bool(getattr(item.style, 'warp_vertical', False)) else 0)
        wb = int(getattr(item.style, 'warp_bend', 0) or 0)
        wh = int(getattr(item.style, 'warp_hdist', 0) or 0)
        wv = int(getattr(item.style, 'warp_vdist', 0) or 0)
        self.warp_bend_slider.setValue(wb)
        self.warp_hdist_slider.setValue(wh)
        self.warp_vdist_slider.setValue(wv)
        self.warp_bend_label.setText(str(wb))
        self.warp_hdist_label.setText(str(wh))
        self.warp_vdist_label.setText(str(wv))

        if hasattr(self, '_fill_swatch'):
            self._fill_swatch.set_color(item.style.fill)
        if hasattr(self, '_out_swatch'):
            self._out_swatch.set_color(item.style.outline)
        if hasattr(self, '_bg_swatch'):
            self._bg_swatch.set_color(item.style.background_color)

        self._apply_bg_controls_state()
        for w in bs: w.blockSignals(False)

    def _apply_no_stroke_enabled_state(self):
        no_stroke = self.no_stroke_chk.isChecked()
        self.outw_slider.setEnabled(not no_stroke)
        self.outw_label.setEnabled(not no_stroke)
        if hasattr(self, 'outw_spin'):
            self.outw_spin.setEnabled(not no_stroke)
        self.out_btn.setEnabled(not no_stroke)
        if hasattr(self, '_out_swatch'):
            self._out_swatch.setEnabled(not no_stroke)

    def _on_outline_slider_ui_changed(self, v: int):
        self.outw_label.setText(str(int(v)))
        if hasattr(self, 'outw_spin'):
            self.outw_spin.blockSignals(True)
            self.outw_spin.setValue(int(v))
            self.outw_spin.blockSignals(False)

    def _apply_bg_controls_state(self):
        enabled = self.bg_chk.isChecked()
        self.bg_btn.setEnabled(enabled); self.bg_op.setEnabled(enabled)
        if hasattr(self, '_bg_swatch'):
            self._bg_swatch.setEnabled(enabled)

    def _update_font_button_state(self, selected_items: Optional[List[StrokeTextItem]] = None):
        """Sincroniza el botón de fuente con la selección actual."""
        if not hasattr(self, "font_btn"):
            return
        items = selected_items if selected_items is not None else self._selected_items()

        if not items:
            self.font_btn.setText("Fuente")
            self.font_btn.setToolTip("Selecciona una caja de texto para ver/cambiar su fuente")
            self.font_btn.setEnabled(False)
            return

        if len(items) > 1:
            self.font_btn.setText("Fuentes (seleccion multiple)")
            self.font_btn.setToolTip("Seleccion multiple detectada. Cambia la fuente una caja a la vez.")
            self.font_btn.setEnabled(False)
            return

        family = str(getattr(items[0].style, 'font_family', '') or "Fuente")
        short_name = family if len(family) <= 28 else (family[:25] + "...")
        self.font_btn.setText(short_name)
        self.font_btn.setToolTip(f"Fuente actual: {family}\nClic para cambiar.")
        self.font_btn.setEnabled(True)

    def on_symbol_changed(self, _idx: int):
        items = self._selected_items()
        if not items: return
        key = self.symb_combo.currentText(); base = PRESETS.get(key, PRESETS['GLOBO']); ctx = self.current_ctx()
        def do():
            for it in items:
                it.name = key
                it.style.font_family = base.font_family; it.style.font_point_size = base.font_point_size
                it.setFont(it.style.to_qfont()); it._apply_paragraph_to_doc()
        apply_to_selected(ctx, items, f"Aplicar simbología: {key}", do)

    def on_alignment_changed(self, idx: int):
        items = self._selected_items();  ctx = self.current_ctx()
        if not items or not ctx: return
        new = ['left','center','right','justify'][idx]
        apply_to_selected(ctx, items, "Alinear párrafo (varias)",
                          lambda: [setattr(it.style, 'alignment', new) or it._apply_paragraph_to_doc()
                                   for it in items])

    def on_linespacing_changed(self, val: float):
        items = self._selected_items(); ctx = self.current_ctx()
        if not items or not ctx: return
        new = float(val)
        apply_to_selected(ctx, items, "Interlineado (varias)",
                          lambda: [setattr(it.style, 'line_spacing', new) or it._apply_paragraph_to_doc()
                                   for it in items])

    def on_hyphenate_toggle(self, state: int):
        items = self._selected_items(); ctx = self.current_ctx()
        if not items or not ctx: return
        new = bool(state)
        apply_to_selected(ctx, items, "Guionado automático",
                          lambda: [setattr(it.style, 'auto_hyphenate', new) or it._update_soft_hyphens()
                                   for it in items])

    def on_warp_controls_changed(self, *_):
        items = self._selected_items()
        ctx = self.current_ctx()
        if not items or not ctx:
            return
        style_keys = ['none', 'arc', 'wave', 'flag', 'fish']
        style_key = style_keys[self.warp_style_combo.currentIndex()] if 0 <= self.warp_style_combo.currentIndex() < len(style_keys) else 'none'
        vertical = (self.warp_orient_combo.currentIndex() == 1)
        bend = int(self.warp_bend_slider.value())
        hdist = int(self.warp_hdist_slider.value())
        vdist = int(self.warp_vdist_slider.value())

        def do():
            for it in items:
                it.style.warp_style = style_key
                it.style.warp_vertical = vertical
                it.style.warp_bend = bend
                it.style.warp_hdist = hdist
                it.style.warp_vdist = vdist
                it.update()
            if ctx and ctx.scene:
                ctx.scene.update()

        apply_to_selected(ctx, items, "Deformar texto", do)

    def on_rotation_changed(self, deg: float):
        items = self._selected_items(); ctx = self.current_ctx()
        if not items or not ctx: return
        new = float(deg)
        apply_to_selected(ctx, items, "Rotación (varias)",
                          lambda: [it.setRotation(new) for it in items])

    def on_capitalization_changed(self, idx: int):
        items = self._selected_items(); ctx = self.current_ctx()
        if not items or not ctx: return
        keys = ['mixed', 'uppercase', 'lowercase', 'capitalize', 'smallcaps']; new = keys[idx]
        apply_to_selected(ctx, items, "Capitalización",
                          lambda: [setattr(it.style, 'capitalization', new) or it.setFont(it.style.to_qfont())
                                   for it in items])

    def on_width_changed(self, v: int):
        item = self.current_item()
        if item:
            ctx = self.current_ctx()
            apply_to_selected(ctx, [item], "Ancho caja", lambda: item.setTextWidth(v))
            self._sync_props_from_item(item)

    def on_bold_toggle(self, state: int):
        items = self._selected_items(); ctx = self.current_ctx()
        if not items or not ctx: return
        new_bold = bool(state)
        def do():
            for it in items:
                it.style.bold = new_bold
                it.setFont(it.style.to_qfont())
        apply_to_selected(ctx, items, "Negrita", do)

    def apply_bold_to_current_selection(self):
        """Aplica negrita a la selecci\u00f3n actual cuando se presiona el bot\u00f3n."""
        ctx = self.current_ctx()
        if not ctx:
            QMessageBox.information(self, "Negrita selectiva", "No hay ninguna pesta\u00f1a abierta.")
            return
        
        item = ctx.current_item()
        if not item:
            QMessageBox.information(self, "Negrita selectiva", "Selecciona una caja de texto primero.")
            return
        
        # Verificar si el item est\u00e1 en modo edici\u00f3n
        if item.textInteractionFlags() != Qt.TextInteractionFlag.TextEditorInteraction:
            QMessageBox.information(self, "Negrita selectiva", 
                "Haz doble clic en la caja de texto para editarla, luego selecciona el texto que quieres en negrita.")
            return
        
        # Aplicar negrita a la selecci\u00f3n
        if not item.apply_bold_to_selection():
            QMessageBox.information(self, "Negrita selectiva", 
                "Selecciona el texto que quieres poner en negrita primero.")


    def choose_font(self):
        ctx = self.current_ctx()
        if not ctx: return
        items = self._selected_items()
        if not items:
            self._update_font_button_state(items)
            return
        if len(items) != 1:
            self._update_font_button_state(items)
            QMessageBox.information(self, "Fuente", "Selecciona una sola caja de texto para cambiar la fuente.")
            return
        item = items[0]
        base = item.style.to_qfont()
        font, ok = QFontDialog.getFont(base, self, "Elegir fuente")
        if not ok: return
        new_family, new_pt, new_bold, new_italic = font.family(), font.pointSize(), font.bold(), font.italic()
        apply_to_selected(ctx, [item], "Cambiar fuente", lambda: [
            setattr(item.style, 'font_family', new_family),
            setattr(item.style, 'font_point_size', new_pt),
            setattr(item.style, 'bold', new_bold),
            setattr(item.style, 'italic', new_italic),
            item.setFont(item.style.to_qfont()),
            item._apply_paragraph_to_doc()
        ])
        self._sync_props_from_item(item)

    def _get_current_qcolor(self, which: str, item: StrokeTextItem) -> QColor:
        return {'fill': qcolor_from_hex(item.style.fill, "#000000"),
                'outline': qcolor_from_hex(item.style.outline, "#FFFFFF"),
                'background_color': qcolor_from_hex(item.style.background_color, "#FFFFFF")}.get(which, QColor("#000000"))
    def choose_color(self, which: str):
        """Selector extendido para `fill`, `outline` y `background_color`.
        Para `fill` permite elegir relleno sólido, degradado lineal simple (2 stops) o una textura (imagen).
        Con preview en vivo: los cambios se aplican inmediatamente a la caja de texto.
        """
        item = self.current_item()
        if not item: return

        if which != 'fill':
            # Mantener comportamiento previo para outline y background
            initial = self._get_current_qcolor(which, item)
            color_dialog = QColorDialog(initial, self)
            color_dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
            color_dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
            result = color_dialog.exec()
            if result == QColorDialog.DialogCode.Accepted:
                final_color = color_dialog.selectedColor().name(QColor.NameFormat.HexRgb)
                ctx = self.current_ctx()
                if which == 'outline':
                    old = item.style.outline
                    def undo(): item.style.outline = old; item.update()
                    def redo(): item.style.outline = final_color; item.update()
                    push_cmd(ctx.undo_stack, "Cambiar color", undo, redo)
                    if hasattr(self, '_out_swatch'):
                        self._out_swatch.set_color(final_color)
                else:
                    old = item.style.background_color
                    def undo(): item.style.background_color = old; item.update()
                    def redo(): item.style.background_color = final_color; item.update()
                    push_cmd(ctx.undo_stack, "Cambiar color fondo", undo, redo)
                    if hasattr(self, '_bg_swatch'):
                        self._bg_swatch.set_color(final_color)
            return

        # --- Fill chooser (solid / gradient / texture) con preview en vivo ---
        ctx = self.current_ctx()
        
        # Snapshot inicial para poder revertir si se cancela
        old_snapshot = {
            'fill_type': item.style.fill_type,
            'fill': item.style.fill,
            'gradient_stops': list(item.style.gradient_stops) if item.style.gradient_stops else None,
            'gradient_angle': item.style.gradient_angle,
            'texture_path': item.style.texture_path,
            'texture_tile': item.style.texture_tile,
            'texture_scale': float(getattr(item.style, 'texture_scale', 1.0)),
            'texture_angle': int(getattr(item.style, 'texture_angle', 0)),
        }
        
        def on_preview_update(spec):
            """Callback para actualizar la caja en tiempo real mientras cambias en el diálogo."""
            try:
                item.style.fill_type = spec.get('fill_type', 'solid')
                item.style.fill = spec.get('fill', item.style.fill)
                item.style.gradient_stops = spec.get('gradient_stops')
                item.style.gradient_angle = int(spec.get('gradient_angle', 0))
                item.style.texture_path = spec.get('texture_path', '')
                item.style.texture_tile = bool(spec.get('texture_tile', True))
                item.style.texture_scale = float(spec.get('texture_scale', 1.0))
                item.style.texture_angle = int(spec.get('texture_angle', 0))
                item.sync_default_text_color()
                item.update()
                if hasattr(self, '_fill_swatch'):
                    self._fill_swatch.set_color(item.style.fill)
            except Exception:
                pass
        
        dlg = FillChooserDialog(self, item.style, on_update_callback=on_preview_update)
        
        if dlg.exec() != QDialog.DialogCode.Accepted:
            # Si cancela, revertir al estado anterior
            item.style.fill_type = old_snapshot['fill_type']
            item.style.fill = old_snapshot['fill']
            item.style.gradient_stops = old_snapshot['gradient_stops']
            item.style.gradient_angle = old_snapshot['gradient_angle']
            item.style.texture_path = old_snapshot['texture_path']
            item.style.texture_tile = old_snapshot['texture_tile']
            item.style.texture_scale = old_snapshot['texture_scale']
            item.style.texture_angle = old_snapshot['texture_angle']
            item.sync_default_text_color()
            item.update()
            if ctx and ctx.scene:
                ctx.scene.update()
            return
        
        # Si acepta, registrar el cambio en el undo stack
        new_spec = dlg.get_result()
        if not new_spec:
            return
        
        def undo():
            item.style.fill_type = old_snapshot['fill_type']
            item.style.fill = old_snapshot['fill']
            item.style.gradient_stops = old_snapshot['gradient_stops']
            item.style.gradient_angle = old_snapshot['gradient_angle']
            item.style.texture_path = old_snapshot['texture_path']
            item.style.texture_tile = old_snapshot['texture_tile']
            item.style.texture_scale = old_snapshot['texture_scale']
            item.style.texture_angle = old_snapshot['texture_angle']
            item.sync_default_text_color()
            item.update(); ctx and ctx.scene.update()

        def redo():
            item.style.fill_type = new_spec.get('fill_type', 'solid')
            item.style.fill = new_spec.get('fill', item.style.fill)
            item.style.gradient_stops = new_spec.get('gradient_stops')
            item.style.gradient_angle = int(new_spec.get('gradient_angle', 0))
            item.style.texture_path = new_spec.get('texture_path', '')
            item.style.texture_tile = bool(new_spec.get('texture_tile', True))
            item.style.texture_scale = float(new_spec.get('texture_scale', 1.0))
            item.style.texture_angle = int(new_spec.get('texture_angle', 0))
            item.sync_default_text_color()
            item.update(); ctx and ctx.scene.update()

        push_cmd(ctx.undo_stack, "Cambiar relleno texto", undo, redo)

    def on_no_stroke_toggle(self, state: int):
        item = self.current_item(); ctx = self.current_ctx()
        if not item or not ctx: return
        no_stroke = bool(state)
        def do():
            item.style.outline_width = 0 if no_stroke else (item.style.outline_width or 3)
            # Actualizar el slider también
            self.outw_slider.blockSignals(True)
            self.outw_slider.setValue(item.style.outline_width)
            self.outw_label.setText(str(item.style.outline_width))
            self.outw_slider.blockSignals(False)
            if hasattr(self, 'outw_spin'):
                self.outw_spin.blockSignals(True)
                self.outw_spin.setValue(int(item.style.outline_width))
                self.outw_spin.blockSignals(False)
        apply_to_selected(ctx, [item], "Sin trazo", do)
        self._apply_no_stroke_enabled_state()

    def on_outline_width(self, v: int):
        item = self.current_item(); ctx = self.current_ctx()
        if not item or not ctx: return
        def do():
            item.style.outline_width = v
            self.no_stroke_chk.blockSignals(True)
            self.no_stroke_chk.setChecked(v == 0)
            self.no_stroke_chk.blockSignals(False)
            item.update()  # Forzar actualización visual
            if ctx.scene:
                ctx.scene.update()
        apply_to_selected(ctx, [item], "Grosor trazo", do)
        self._apply_no_stroke_enabled_state()

    def on_shadow_toggle(self, state):
        item = self.current_item(); ctx = self.current_ctx()
        if item and ctx:
            apply_to_selected(ctx, [item], "Sombra",
                              lambda: (setattr(item.style, 'shadow_enabled', bool(state)), item.apply_shadow()))

    def on_bg_toggle(self, state):
        item = self.current_item(); ctx = self.current_ctx()
        if item and ctx:
            apply_to_selected(ctx, [item], "Fondo caja",
                              lambda: setattr(item.style, 'background_enabled', bool(state)))
            self._apply_bg_controls_state()

    def on_bg_op(self, v: int):
        item = self.current_item(); ctx = self.current_ctx()
        if item and ctx:
            apply_to_selected(ctx, [item], "Opacidad fondo",
                              lambda: setattr(item.style, 'background_opacity', clamp(v/100.0, 0, 1)))

    # ---- Marca de agua: lógica UI ----
    def _wm_update_controls_enabled(self):
        has_path = bool(self.wm_path)
        self.wm_op_slider.setEnabled(self.wm_enabled and has_path)

    def choose_wm_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen de marca de agua", "", "Imágenes (*.png *.jpg *.jpeg *.webp)")
        if not file:
            return
        self.wm_path = file
        self.settings.setValue('wm_path', self.wm_path)
        if self.wm_enabled:
            # Re-crear explícitamente en cada pestaña pero conservando posición/escala previas.
            for i in range(self.tabs.count()):
                ctx = self.tabs.widget(i)
                if isinstance(ctx, PageContext):
                    ctx.set_watermark(self.wm_path, opacity=self.wm_opacity_pct/100.0)
        self._wm_update_controls_enabled()

    def on_wm_enable_toggled(self, enabled: bool):
        self.wm_enabled = bool(enabled)
        self.settings.setValue('wm_enabled', '1' if self.wm_enabled else '0')
        if self.wm_enabled:
            self._apply_wm_all_tabs()
        else:
            # remover en todas
            for i in range(self.tabs.count()):
                ctx = self.tabs.widget(i)
                if isinstance(ctx, PageContext):
                    ctx.remove_watermark()
        self._wm_update_controls_enabled()

    def on_wm_opacity_changed(self, value: int):
        self.wm_opacity_pct = int(clamp(value, 0, 100))
        self.settings.setValue('wm_opacity', self.wm_opacity_pct)
        if not self.wm_enabled:
            return
        # Actualiza opacidad de las pestañas
        for i in range(self.tabs.count()):
            ctx = self.tabs.widget(i)
            if isinstance(ctx, PageContext):
                if ctx.watermark_item is None and self.wm_path:
                    ctx.set_watermark(self.wm_path, opacity=self.wm_opacity_pct/100.0)
                else:
                    ctx.set_watermark_opacity(self.wm_opacity_pct/100.0)

    def _apply_wm_to_ctx(self, ctx: Optional[PageContext]):
        if not isinstance(ctx, PageContext):
            return
        if self.wm_enabled and self.wm_path:
            # Si ya existe en la pestaña, solo actualiza opacidad para no perder posición/escala.
            if ctx.watermark_item is None:
                ctx.set_watermark(self.wm_path, opacity=self.wm_opacity_pct/100.0)
            else:
                ctx.set_watermark_opacity(self.wm_opacity_pct/100.0)
        else:
            ctx.remove_watermark()

    def _update_wm_settings_from_ctx(self, ctx: 'PageContext'):
        """Persistir en QSettings la última posición (normalizada) y escala."""
        try:
            if ctx._wm_norm_pos is not None:
                self.wm_pos_norm = tuple(ctx._wm_norm_pos)
                self.settings.setValue('wm_pos_x', self.wm_pos_norm[0])
                self.settings.setValue('wm_pos_y', self.wm_pos_norm[1])
            self.wm_scale = float(ctx._wm_scale)
            self.settings.setValue('wm_scale', self.wm_scale)
        except Exception:
            pass

    def _apply_wm_all_tabs(self):
        for i in range(self.tabs.count()):
            self._apply_wm_to_ctx(self.tabs.widget(i))

    def duplicate_selected(self):
        ctx = self.current_ctx()
        if not ctx: return
        item = ctx.current_item()
        if not item: return
        d = item.to_dict(); d['pos'][1] += 40
        new = StrokeTextItem.from_dict(d); new.name = item.name + " copia"
        new.set_locked(new.locked, self.lock_move)
        def undo(): ctx.scene.removeItem(new); ctx.remove_item_from_list(new)
        def redo(): ctx.add_item_and_list(new)
        push_cmd(ctx.undo_stack, "Duplicar", undo, redo)
        # El push_cmd ya marca como modificado gracias a _mark_scene_modified

    def nudge_selected(self, dx=0, dy=0, step=1):
        ctx = self.current_ctx()
        if not ctx: return
        items = [it for it in ctx.selected_text_items() if isinstance(it, StrokeTextItem)]
        items = [it for it in items if (not it.locked) and (not self.lock_move)]
        if not items: return
        def do():
            for it in items:
                it.setPos(it.pos() + QPointF(dx*step, dy*step))
        apply_to_selected(ctx, items, "Mover con flechas", do)

    def delete_selected(self):
        ctx = self.current_ctx()
        if not ctx: return
        items = ctx.selected_text_items()
        if not items: return
        def undo():
            for it in items: ctx.add_item_and_list(it)
        def redo():
            for it in items: ctx.scene.removeItem(it); ctx.remove_item_from_list(it)
        push_cmd(ctx.undo_stack, f"Eliminar {len(items)} item(s)", undo, redo)
        # El push_cmd ya marca como modificado gracias a _mark_scene_modified

    def _set_lock_tooltips(self, ctx: 'PageContext'):
        for i in range(ctx.layer_list.count()):
            itw = ctx.layer_list.item(i); obj: StrokeTextItem = itw.data(Qt.ItemDataRole.UserRole)
            itw.setToolTip("Fijado" if obj.locked else "")

    def lock_selected_items(self):
        ctx = self.current_ctx()
        if not ctx: return
        items = [it for it in ctx.selected_text_items() if not it.locked] or ctx.selected_text_items()
        if not items:
            QMessageBox.information(self, "Fijar seleccionados", "Selecciona al menos una caja de texto."); return
        apply_to_selected(ctx, items, "Fijar seleccionados",
                          lambda: [it.set_locked(True, self.lock_move) for it in items])
        self._set_lock_tooltips(ctx)

    def lock_all_items_current_tab(self):
        ctx = self.current_ctx()
        if not ctx: return
        items = [it for it in ctx.scene.items() if isinstance(it, StrokeTextItem)]
        if not items:
            QMessageBox.information(self, "Fijar TODOS", "No hay cajas de texto en esta pestaña."); return
        apply_to_selected(ctx, items, "Fijar TODOS",
                          lambda: [it.set_locked(True, self.lock_move) for it in items])
        self._set_lock_tooltips(ctx)

    def unlock_selected_items_confirm(self):
        ctx = self.current_ctx()
        if not ctx: return
        items = ctx.selected_text_items()
        if not items:
            QMessageBox.information(self, "Desbloquear", "Selecciona al menos una caja fijada."); return
        if self.lock_move:
            resp = QMessageBox.question(self, "Bloqueo global activo",
                "Tienes activo el bloqueo global (M).\n¿Quieres desactivarlo para poder mover ítems desbloqueados?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if resp == QMessageBox.StandardButton.Yes: self.lock_move_act.setChecked(False)
            else: return
        n = sum(1 for it in items if it.locked)
        if n == 0:
            QMessageBox.information(self, "Desbloquear", "Ninguno de los seleccionados está fijado."); return
        if QMessageBox.question(self, "Confirmar desbloqueo", f"¿Desbloquear {n} elemento(s) seleccionado(s)?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes) != QMessageBox.StandardButton.Yes:
            return
        apply_to_selected(ctx, items, "Desbloquear seleccionados",
                          lambda: [it.set_locked(False, self.lock_move) for it in items])
        self._set_lock_tooltips(ctx)

    def export_presets_json(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Exportar presets", "presets.json", "JSON (*.json)")
        if not fname: return
        try:
            raw = {k: asdict(v) for k, v in PRESETS.items()}
            with open(fname, "w", encoding="utf-8") as f: json.dump(raw, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Exportar", "¡Presets exportados correctamente!")
        except Exception as e:
            QMessageBox.warning(self, "Exportar", f"No se pudo exportar:\n{e}")

    def import_presets_json(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Importar presets", "", "JSON (*.json)")
        if not fname: return
        try:
            with open(fname, "r", encoding="utf-8") as f: raw = json.load(f)
            for k, v in raw.items(): PRESETS[k] = TextStyle(**v)
            if upgrade_presets_with_defaults(PRESETS): pass
            save_presets_to_settings(self.settings, PRESETS)
            self.symb_combo.blockSignals(True); self.symb_combo.clear(); self.symb_combo.addItems(list(PRESETS.keys())); self.symb_combo.blockSignals(False)
            QMessageBox.information(self, "Importar", "Presets importados/actualizados.")
        except Exception as e:
            QMessageBox.warning(self, "Importar", f"No se pudo importar:\n{e}")

    def set_movement_locked(self, locked: bool):
        self.lock_move = bool(locked); self._apply_movable_all_current()

    def _occupied_rects(self, ctx: 'PageContext', exclude: Optional[List[StrokeTextItem]] = None) -> List[QRectF]:
        return [it.mapToScene(it.boundingRect()).boundingRect() for it in ctx.scene.items()
                if isinstance(it, StrokeTextItem) and (not exclude or it not in exclude)]

    def _find_free_position_near(self, ctx: 'PageContext', start: QPointF, size: Tuple[float,float], occ: List[QRectF]) -> QPointF:
        w,h = size; offsets = [QPointF(0,0)]; step = 20
        for radius in range(step, 420, step):
            for dx in (-radius, 0, radius):
                for dy in (-radius, 0, radius):
                    offsets.append(QPointF(dx, dy))
        for off in offsets:
            pos = start + off; r = QRectF(pos.x(), pos.y(), w, h)
            if not any(rects_intersect(r, o) for o in occ): return pos
        return start

    def auto_place_selected(self):
        ctx = self.current_ctx()
        if not ctx: return
        items = [it for it in ctx.selected_text_items() if not it.locked]
        if not items:
            QMessageBox.information(self, "Auto-colocar", "Selecciona al menos una caja NO fijada."); return
        base = ctx.bg_item.boundingRect().center() if ctx.bg_item else QPointF(0, 0)
        occ = self._occupied_rects(ctx, exclude=items)
        def do():
            angle_step = 360.0 / max(1, len(items)); angle = 0.0; radius = 10.0
            for it in items:
                br = it.mapToScene(it.boundingRect()).boundingRect(); w,h = br.width(), br.height()
                target = QPointF(base.x() + radius*math.cos(math.radians(angle)) - w/2,
                                 base.y() + radius*math.sin(math.radians(angle)) - h/2)
                pos = self._find_free_position_near(ctx, target, (w,h), occ)
                it.setPos(pos); occ.append(QRectF(pos.x(), pos.y(), w, h))
                angle += angle_step; radius += 8.0
        apply_to_selected(ctx, items, "Auto-colocar", do)

    def _build_raw_dock(self):
        self.raw_dock = QDockWidget("Referencia (idioma original)", self)
        self.raw_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.raw_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                  QDockWidget.DockWidgetFeature.DockWidgetClosable |
                                  QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        host = QWidget(self.raw_dock); v = QVBoxLayout(host); btns = QHBoxLayout()
        self.btn_load_raw = QPushButton("Cargar imagen RAW…", host); self.btn_load_raw.clicked.connect(self.load_raw_image)
        self.btn_clear_raw = QPushButton("Borrar referencia", host); self.btn_clear_raw.clicked.connect(self.clear_raw_image)
        btns.addWidget(self.btn_load_raw); btns.addWidget(self.btn_clear_raw); v.addLayout(btns)

        self.raw_view = RawView(host); v.addWidget(self.raw_view); host.setLayout(v); self.raw_dock.setWidget(host)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.raw_dock)
        try:
            self.splitDockWidget(self.prop_dock, self.raw_dock, Qt.Orientation.Vertical)
        except Exception:
            pass

        self.raw_dock.hide()
        self.raw_dock.visibilityChanged.connect(self._on_raw_visibility_changed)
        for tb in self.findChildren(QToolBar):
            tb.addAction(self.toggle_raw_act); break

        self._raw_per_tab: Dict['PageContext', Optional[QPixmap]] = {}

    def _on_raw_visibility_changed(self, visible: bool):
        """Sincroniza la acción del toolbar con el dock RAW,
        ignorando cambios cuando la ventana está minimizada.
        """
        if self.isMinimized():
            return
        self.toggle_raw_act.blockSignals(True)
        self.toggle_raw_act.setChecked(visible)
        self.toggle_raw_act.blockSignals(False)

    def _on_tab_changed(self, idx: int):
        ctx = self.tabs.widget(idx)
        if isinstance(ctx, PageContext):
            pix = self._raw_per_tab.get(ctx); self._set_raw_pixmap(pix)
            # aplica marca de agua al cambiar de pestaña
            self._apply_wm_to_ctx(ctx)
            ci = self.current_item()
            if ci:
                self._sync_props_from_item(ci)
            else:
                self._update_font_button_state([])
        else:
            self._update_font_button_state([])

    def _set_raw_pixmap(self, pix: Optional[QPixmap]):
        if pix is None or pix.isNull():
            self.raw_view.set_pixmap(None); self.raw_dock.setWindowTitle("Referencia (idioma original)"); return
        self.raw_view.set_pixmap(pix); self.raw_dock.setWindowTitle(f"Referencia (idioma original) – {pix.width()}×{pix.height()}")

    def load_raw_image(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Cargar imagen RAW", "", "Imágenes (*.png *.jpg *.jpeg *.webp)")
        if not files: return
        path = files[0]; pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, "RAW", "No se pudo cargar la imagen seleccionada."); return
        ctx = self.current_ctx()
        if ctx:
            self._raw_per_tab[ctx] = pix; self._set_raw_pixmap(pix); self.raw_dock.show()
            self.statusBar().showMessage(f"Referencia RAW cargada: {Path(path).name}")

    def clear_raw_image(self):
        ctx = self.current_ctx()
        if ctx and ctx in self._raw_per_tab: self._raw_per_tab[ctx] = None
        self._set_raw_pixmap(None); self.statusBar().showMessage("Referencia RAW borrada")

    # ---------- Guardar/Abrir proyecto .bbg ----------
    def save_project_bbg_embed(self):
        ctx = self.current_ctx()
        if not ctx or ctx.bg_image is None:
            QMessageBox.information(self, "Guardar", "Abre una imagen primero."); return
        
        items = [it for it in ctx.scene.items() if isinstance(it, StrokeTextItem)]
        data_items = [it.to_dict() for it in items]
        arr = QByteArray(); buf = QBuffer(arr); buf.open(QIODevice.OpenModeFlag.WriteOnly)
        ctx.bg_image.save(buf, b"PNG"); bg_b64 = base64.b64encode(bytes(arr)).decode("ascii")
        
        payload = {
            "schema_version": 1,
            "background_name": getattr(ctx, "background_path", "") or "",
            "background_mime": "image/png",
            "background_b64": bg_b64,
            "items": data_items,
            "workflow_data": getattr(ctx, "workflow_data", None)  # Save workflow data
        }
        
        # Si ya hay un archivo guardado, sobrescribirlo automáticamente
        if self.last_saved_project_path:
            fname = self.last_saved_project_path
        else:
            # Primera vez guardando: usar el nombre de la imagen de fondo como sugerencia
            if hasattr(ctx, 'background_path') and ctx.background_path:
                # Obtener el nombre base de la imagen y cambiar extensión a .bbg
                img_name = Path(ctx.background_path).stem  # nombre sin extensión
                suggested = f"{img_name}.bbg"
            else:
                suggested = "proyecto.bbg"
            
            fname, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto editable (.bbg)", suggested, "Proyecto (*.bbg)")
            if not fname:
                return
            # Guardar la ruta para futuros guardados automáticos
            self.last_saved_project_path = fname
        
        try:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            # Mostrar mensaje breve en la barra de estado en lugar de diálogo
            self.statusBar().showMessage(f"✓ Proyecto guardado: {Path(fname).name}", 3000)
            
            # Limpiar flag de cambios sin guardar
            ctx.has_unsaved_changes = False
            ctx.saved_file_path = fname
            
            # Quitar asterisco del título de la pestaña
            idx = self.tabs.indexOf(ctx)
            if idx >= 0:
                current_name = self.tabs.tabText(idx)
                if current_name.startswith('*'):
                    self.tabs.setTabText(idx, current_name[1:])
        except Exception as e:
            QMessageBox.warning(self, "Guardar", "No se pudo guardar:\n" + str(e))

    # 🔹 NUEVA VERSIÓN: abrir múltiples proyectos .bbg a la vez
    def open_project_bbg_embed(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Abrir proyecto(s) (.bbg)",
            "",
            "Proyecto (*.bbg)"
        )
        if not files:
            return

        abiertos = 0
        for fname in files:
            if self._open_single_project_bbg(fname):
                abiertos += 1

        if abiertos == 1:
            self.statusBar().showMessage("1 proyecto cargado.")
        elif abiertos > 1:
            self.statusBar().showMessage(f"{abiertos} proyectos cargados.")

    def _open_single_project_bbg(self, fname: str) -> bool:
        """Abre un único archivo .bbg y lo agrega como pestaña. Devuelve True si se abrió bien."""
        try:
            with open(fname, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Proyecto", f"No se pudo leer el archivo:\n{fname}\n\n{e}")
            return False

        b64 = raw.get("background_b64")
        if not b64:
            QMessageBox.warning(self, "Proyecto", f"El proyecto no contiene imagen embebida:\n{fname}")
            return False

        try:
            img_bytes = base64.b64decode(b64.encode("ascii"))
        except Exception as e:
            QMessageBox.warning(self, "Proyecto", f"Imagen embebida inválida en:\n{fname}\n\n{e}")
            return False

        img = QImage.fromData(img_bytes, "PNG")
        if img.isNull():
            QMessageBox.warning(self, "Proyecto", f"No se pudo reconstruir la imagen:\n{fname}")
            return False

        pix = QPixmap.fromImage(img)
        ctx = PageContext(pix, Path(fname))
        
        # Load workflow data if present
        if "workflow_data" in raw and raw["workflow_data"]:
            ctx.workflow_data = raw["workflow_data"]
        
        for d in raw.get("items", []):
            try:
                ctx.add_item_and_list(StrokeTextItem.from_dict(d))
            except Exception:
                pass

        idx = self.tabs.addTab(ctx, Path(fname).name)
        self.tabs.setCurrentIndex(idx)
        self._refresh_tab_close_buttons()
        self.statusBar().showMessage(f"Proyecto cargado: {Path(fname).name}")
        
        # Guardar la ruta del proyecto para auto-guardar
        self.last_saved_project_path = fname
        
        # Inicializar el tracking de cambios (el proyecto recién abierto no tiene cambios)
        ctx.has_unsaved_changes = False
        ctx.saved_file_path = fname

        # aplica marca de agua si procede
        self._apply_wm_to_ctx(ctx)
        return True

    def open_psd_file(self, fname: str) -> bool:
        """Abre un archivo PSD y extrae imagen(es) y textos."""
        if not PSD_AVAILABLE:
            QMessageBox.warning(self, "PSD", "psd-tools no está instalado. No se puede abrir PSD."); return False
        
        try:
            psd = PSDImage.open(fname)
        except Exception as e:
            QMessageBox.warning(self, "PSD", f"No se pudo abrir el archivo PSD:\n{fname}\n\n{e}"); return False
        
        # Obtener capas de imagen (PixelLayer con píxeles)
        image_layers = [layer for layer in psd if not layer.is_group() and hasattr(layer, 'has_pixels') and layer.has_pixels()]
        
        if not image_layers:
            QMessageBox.warning(self, "PSD", "No se encontraron capas de imagen en el PSD."); return False
        
        # Usar la primera capa de imagen como fondo principal
        bg_layer = image_layers[0]
        
        # Convertir capa de imagen a QPixmap
        try:
            img_pil = bg_layer.composite()
            if img_pil is None:
                QMessageBox.warning(self, "PSD", "No se pudo extraer la imagen de la capa."); return False
            
            # Convertir PIL Image a QPixmap
            img_data = QByteArray()
            buf = QBuffer(img_data)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            img_pil.save(buf, "PNG")
            buf.close()
            
            bg_image = QImage.fromData(img_data, "PNG")
            if bg_image.isNull():
                QMessageBox.warning(self, "PSD", "No se pudo convertir la imagen."); return False
            
            pix = QPixmap.fromImage(bg_image)
        except Exception as e:
            QMessageBox.warning(self, "PSD", f"Error extrayendo imagen:\n{e}"); return False
        
        # Crear contexto
        ctx = PageContext(pix, Path(fname))
        
        # Construir listas de items (no los añadimos aún): primero textos, luego overlays
        overlay_items = []
        for i, img_layer in enumerate(image_layers[1:], start=1):
            try:
                overlay_pil = img_layer.composite()
                if overlay_pil is None:
                    continue
                overlay_data = QByteArray()
                overlay_buf = QBuffer(overlay_data)
                overlay_buf.open(QIODevice.OpenModeFlag.WriteOnly)
                overlay_pil.save(overlay_buf, "PNG")
                overlay_buf.close()
                overlay_img = QImage.fromData(overlay_data, "PNG")
                if overlay_img.isNull():
                    continue
                overlay_pix = QPixmap.fromImage(overlay_img)
                overlay_item = MovableImageLayer(overlay_pix, f"Capa {i}: {getattr(img_layer, 'name', 'IMPORTADO')}")
                overlay_item._pending_pos = QPointF(getattr(img_layer, 'left', 0), getattr(img_layer, 'top', 0))
                overlay_items.append(overlay_item)
            except Exception as e:
                print(f"Error preparando capa de imagen {i}: {e}")
                continue
        
        # Extraer capas de texto
        text_layers = [layer for layer in psd.descendants() if layer.kind == "type"]
        
        text_items = []
        for text_layer in text_layers:
            try:
                text_str = getattr(text_layer, 'text', '')
                if not text_str:
                    continue
                left = getattr(text_layer, 'left', 0)
                top = getattr(text_layer, 'top', 0)
                style = replace(PRESETS['GLOBO'])
                item = StrokeTextItem(text_str, style, name="IMPORTADO")
                item._pending_pos = QPointF(left, top)
                text_items.append(item)
            except Exception as e:
                print(f"Error preparando texto importado: {e}")
                continue

        # Añadir primero los textos (para que queden en la parte superior de la lista), luego las overlays
        for it in text_items:
            try: ctx.add_item_and_list(it)
            except Exception:
                ctx.scene.addItem(it)
        for ov in overlay_items:
            try: ctx.add_item_and_list(ov)
            except Exception:
                ctx.scene.addItem(ov)
        
        idx = self.tabs.addTab(ctx, f"{Path(fname).stem} (PSD)")
        self.tabs.setCurrentIndex(idx)
        self._refresh_tab_close_buttons()
        num_images = len(image_layers)
        self.statusBar().showMessage(f"PSD cargado: {Path(fname).name} - {num_images} imagen(es) + {len(text_layers)} texto(s)")
        
        # No guardamos ruta de guardado automático para PSD
        ctx.has_unsaved_changes = True
        return True

    def export_png_current(self):
        ctx = self.current_ctx()
        if not ctx or not ctx.bg_item:
            QMessageBox.information(self, "Nada que exportar", "Abre una imagen primero."); return
        suggested = "salida.png"
        fname, _ = QFileDialog.getSaveFileName(self, "Exportar imagen", suggested, "PNG (*.png);;JPG (*.jpg)")
        if not fname: return
        self._render_scene_to_file(ctx.scene, ctx.bg_item, Path(fname))

    def export_all_prompt(self):
        if self.tabs.count() == 0:
            QMessageBox.information(self, "Exportar", "No hay pestañas abiertas."); return
        dlg = QMessageBox(self); dlg.setWindowTitle("Exportar todas"); dlg.setText("¿Qué deseas exportar para todas las pestañas?")
        btn_img = dlg.addButton("Imágenes (PNG)", QMessageBox.ButtonRole.AcceptRole)
        btn_bbg = dlg.addButton("Proyectos (.bbg)", QMessageBox.ButtonRole.ActionRole)
        dlg.addButton(QMessageBox.StandardButton.Cancel)
        dlg.exec()
        clicked = dlg.clickedButton()
        if clicked == btn_img:
            self.export_png_all()
        elif clicked == btn_bbg:
            self.save_all_bbg_embed()
        else:
            return

    def save_all_bbg_embed(self):
        if self.tabs.count() == 0:
            QMessageBox.information(self, "Guardar", "No hay pestañas abiertas."); return
        folder = QFileDialog.getExistingDirectory(self, "Guardar TODOS los proyectos (.bbg) en carpeta")
        if not folder: return
        base = Path(folder); saved = 0
        for i in range(self.tabs.count()):
            ctx = self.tabs.widget(i)
            if not isinstance(ctx, PageContext) or ctx.bg_image is None: continue
            try:
                items = [it for it in ctx.scene.items() if isinstance(it, StrokeTextItem)]
                data_items = [it.to_dict() for it in items]
                arr = QByteArray(); buf = QBuffer(arr); buf.open(QIODevice.OpenModeFlag.WriteOnly)
                ctx.bg_image.save(buf, b"PNG"); bg_b64 = base64.b64encode(bytes(arr)).decode("ascii")
                payload = {
                    "schema_version": 1,
                    "background_name": getattr(ctx, 'background_path', "") or "",
                    "background_mime": "image/png",
                    "background_b64": bg_b64,
                    "items": data_items
                }
                name = Path(getattr(ctx, 'background_path', f"pagina_{i+1}")).stem or f"pagina_{i+1}"
                out = base / f"{name}.bbg"
                with open(out, "w", encoding="utf-8") as f: json.dump(payload, f, ensure_ascii=False, indent=2)
                
                # Limpiar flag de cambios sin guardar
                ctx.has_unsaved_changes = False
                ctx.saved_file_path = str(out)
                
                # Quitar asterisco del título de la pestaña
                current_name = self.tabs.tabText(i)
                if current_name.startswith('*'):
                    self.tabs.setTabText(i, current_name[1:])
                
                saved += 1
            except Exception as e:
                print("save_all_bbg_embed error:", e)
        QMessageBox.information(self, "Guardar", f"Guardados {saved} proyecto(s) .bbg en: {base}")

    def export_png_all(self):
        if self.tabs.count() == 0:
            QMessageBox.information(self, "Nada que exportar", "No hay pestañas abiertas."); return
        folder = QFileDialog.getExistingDirectory(self, "Exportar todas en carpeta")
        if not folder: return
        base = Path(folder)
        for i in range(self.tabs.count()):
            ctx = self.tabs.widget(i)
            if not isinstance(ctx, PageContext) or not ctx.bg_item: continue
            name = Path(getattr(ctx, 'background_path', f"pagina_{i+1}")).stem or f"pagina_{i+1}"
            out = base / f"{name}.png"; self._render_scene_to_file(ctx.scene, ctx.bg_item, out)
        QMessageBox.information(self, "Exportación", "¡Exportación completa!")

    def _render_scene_to_file(self, scene: QGraphicsScene, bg_item: QGraphicsPixmapItem, out_path: Path):
        rect = bg_item.boundingRect()
        img = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32); img.fill(QColor("white").rgb())
        p = QPainter(img)
        class _SelectionHiderLocal(_SelectionHider): pass
        with _SelectionHiderLocal(scene): scene.render(p, target=QRectF(img.rect()), source=rect)
        p.end(); img.save(str(out_path))

    def configure_fonts_per_preset(self):
        dlg = FontsPerPresetDialog(self, PRESETS)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        apply_existing = dlg.apply_changes(); save_presets_to_settings(self.settings, PRESETS)
        try: current_key = self.symb_combo.currentText()
        except Exception: current_key = None
        self.symb_combo.blockSignals(True); self.symb_combo.clear(); self.symb_combo.addItems(list(PRESETS.keys()))
        if current_key in PRESETS: self.symb_combo.setCurrentText(current_key)
        self.symb_combo.blockSignals(False)
        if apply_existing:
            for i in range(self.tabs.count()):
                ctx = self.tabs.widget(i)
                if not isinstance(ctx, PageContext): continue
                for r in range(ctx.layer_list.count()):
                    itw = ctx.layer_list.item(r); item: StrokeTextItem = itw.data(Qt.ItemDataRole.UserRole)
                    if item and item.name in PRESETS:
                        st = PRESETS[item.name]
                        item.style.font_family = st.font_family; item.style.font_point_size = st.font_point_size
                        item.setFont(item.style.to_qfont()); item._apply_paragraph_to_doc()
                ctx.scene.update()
        if (ci := self.current_item()): self._sync_props_from_item(ci)

    def apply_sentence_case_selected(self):
        items = self._selected_items(); ctx = self.current_ctx()
        if not items or not ctx: return
        def sentence_case(s: str) -> str:
            out = []
            for line in s.splitlines():
                if not line.strip(): out.append(line); continue
                prefix_len = len(line) - len(line.lstrip()); suffix_len = len(line) - len(line.rstrip())
                core = line.strip(); core = core[:1].upper() + core[1:].lower() if core else core
                out.append(line[:prefix_len] + core + line[len(line)-suffix_len:])
            return "\n".join(out)
        prev = [it.get_raw_text() for it in items]; new = [sentence_case(t) for t in prev]
        def do():
            for it, newt in zip(items, new):
                it.setPlainText(newt); it._apply_paragraph_to_doc()
        apply_to_selected(ctx, items, "Mayúscula inicial (frase)", do)

    def _toggle_theme_btn(self, checked: bool):
        self._dark_theme = not getattr(self, "_dark_theme", True)
        app = QApplication.instance()
        scale = app.property("ui_scale_factor") or 1.0
        if self._dark_theme:
            self.theme_btn.setIcon(icon('moon.png'))
            Theme.apply(app, dark=True, accent=app.property("accent_color") or "#E11D48", scale_factor=scale)
        else:
            self.theme_btn.setIcon(icon('sun.png'))
            Theme.apply(app, dark=False, accent=app.property("accent_color") or "#E11D48", scale_factor=scale)


# ---------------- Widgets de soporte para el Gestor de Estilos ----------------

class StylePreviewWidget(QWidget):
    """Widget que muestra una vista previa del estilo de texto."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 80)
        self.setMaximumHeight(100)
        self._style: Optional[TextStyle] = None
        self._text = "Ejemplo Abc"
    
    def set_style(self, style: TextStyle):
        self._style = style
        self.update()
    
    def set_preview_text(self, text: str):
        self._text = text or "Ejemplo Abc"
        self.update()
    
    def paintEvent(self, event):
        if not self._style:
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo
        p.fillRect(self.rect(), QColor("#1a1a2e"))
        
        # Configurar fuente
        font = self._style.to_qfont()
        preview_size = min(self._style.font_point_size, 28)
        font.setPointSize(preview_size)
        p.setFont(font)
        
        text = self._text
        fm = p.fontMetrics()
        text_rect = fm.boundingRect(text)
        
        x = (self.width() - text_rect.width()) // 2
        y = (self.height() + fm.ascent() - fm.descent()) // 2
        
        # Dibujar outline si existe
        if self._style.outline_width > 0:
            outline_color = QColor(self._style.outline)
            pen = QPen(outline_color, max(1, self._style.outline_width // 2))
            p.setPen(pen)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        p.drawText(x + dx, y + dy, text)
        
        # Dibujar texto principal
        p.setPen(QColor(self._style.fill))
        p.drawText(x, y, text)
        
        p.end()


class StyleEditorWidget(QWidget):
    """Widget para editar todas las propiedades de un estilo."""
    styleChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._style: Optional[TextStyle] = None
        self._building = False
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        scroll = QWidget()
        form = QFormLayout(scroll)
        form.setSpacing(6)
        
        # Fuente
        font_row = QHBoxLayout()
        self.font_btn = QPushButton("Elegir fuente…")
        self.font_btn.clicked.connect(self._pick_font)
        self.font_label = QLabel("Arial")
        self.font_label.setStyleSheet("color: #888; font-style: italic;")
        font_row.addWidget(self.font_btn)
        font_row.addWidget(self.font_label, 1)
        form.addRow("Fuente:", font_row)
        
        # Tamaño
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 200)
        self.size_spin.setValue(34)
        self.size_spin.valueChanged.connect(self._on_change)
        form.addRow("Tamaño:", self.size_spin)
        
        # Negrita / Itálica
        style_row = QHBoxLayout()
        self.bold_chk = QCheckBox("Negrita")
        self.bold_chk.stateChanged.connect(self._on_change)
        self.italic_chk = QCheckBox("Itálica")
        self.italic_chk.stateChanged.connect(self._on_change)
        style_row.addWidget(self.bold_chk)
        style_row.addWidget(self.italic_chk)
        style_row.addStretch()
        form.addRow("Estilo:", style_row)
        
        # Color de relleno
        fill_row = QHBoxLayout()
        self.fill_btn = QPushButton()
        self.fill_btn.setFixedSize(60, 24)
        self.fill_btn.clicked.connect(self._pick_fill_color)
        self.fill_label = QLabel("#000000")
        fill_row.addWidget(self.fill_btn)
        fill_row.addWidget(self.fill_label)
        fill_row.addStretch()
        form.addRow("Color texto:", fill_row)
        
        # Color de trazo
        outline_row = QHBoxLayout()
        self.outline_btn = QPushButton()
        self.outline_btn.setFixedSize(60, 24)
        self.outline_btn.clicked.connect(self._pick_outline_color)
        self.outline_label = QLabel("#FFFFFF")
        outline_row.addWidget(self.outline_btn)
        outline_row.addWidget(self.outline_label)
        outline_row.addStretch()
        form.addRow("Color trazo:", outline_row)
        
        # Grosor trazo
        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setRange(0, 20)
        self.outline_width_spin.setValue(3)
        self.outline_width_spin.valueChanged.connect(self._on_change)
        form.addRow("Grosor trazo:", self.outline_width_spin)
        
        # Alineación
        self.align_combo = QComboBox()
        self.align_combo.addItems(["Izquierda", "Centro", "Derecha", "Justificar"])
        self.align_combo.setCurrentIndex(1)
        self.align_combo.currentIndexChanged.connect(self._on_change)
        form.addRow("Alineación:", self.align_combo)
        
        # Interlineado
        self.linespace_spin = QDoubleSpinBox()
        self.linespace_spin.setRange(0.5, 3.0)
        self.linespace_spin.setSingleStep(0.1)
        self.linespace_spin.setValue(1.2)
        self.linespace_spin.valueChanged.connect(self._on_change)
        form.addRow("Interlineado:", self.linespace_spin)

        self.hyphen_chk = QCheckBox("Guionado automático")
        self.hyphen_chk.stateChanged.connect(self._on_change)
        form.addRow("Guionado:", self.hyphen_chk)
        
        # Capitalización
        self.cap_combo = QComboBox()
        self.cap_combo.addItems(["Normal", "MAYÚSCULAS", "minúsculas", "Capitalizar", "Versalitas"])
        self.cap_combo.currentIndexChanged.connect(self._on_change)
        form.addRow("Capitalización:", self.cap_combo)
        
        # Sombra
        self.shadow_chk = QCheckBox("Habilitar sombra")
        self.shadow_chk.stateChanged.connect(self._on_change)
        form.addRow("Sombra:", self.shadow_chk)
        
        layout.addWidget(scroll)
    
    def set_style(self, style: TextStyle):
        self._building = True
        self._style = style
        
        self.font_label.setText(style.font_family)
        self.size_spin.setValue(style.font_point_size)
        self.bold_chk.setChecked(style.bold)
        self.italic_chk.setChecked(style.italic)
        
        self._update_color_btn(self.fill_btn, style.fill)
        self.fill_label.setText(style.fill)
        self._update_color_btn(self.outline_btn, style.outline)
        self.outline_label.setText(style.outline)
        
        self.outline_width_spin.setValue(style.outline_width)
        
        align_map = {'left': 0, 'center': 1, 'right': 2, 'justify': 3}
        self.align_combo.setCurrentIndex(align_map.get(style.alignment, 1))
        
        self.linespace_spin.setValue(style.line_spacing)

        self.hyphen_chk.setChecked(bool(getattr(style, 'auto_hyphenate', False)))
        
        cap_map = {'mixed': 0, 'uppercase': 1, 'lowercase': 2, 'capitalize': 3, 'smallcaps': 4}
        self.cap_combo.setCurrentIndex(cap_map.get(style.capitalization, 0))
        
        self.shadow_chk.setChecked(style.shadow_enabled)
        
        self._building = False
    
    def get_style(self) -> Optional[TextStyle]:
        return self._style
    
    def _update_color_btn(self, btn: QPushButton, color: str):
        btn.setStyleSheet(f"background-color: {color}; border: 1px solid #555;")
    
    def _on_change(self):
        if self._building or not self._style:
            return
        
        self._style.font_point_size = self.size_spin.value()
        self._style.bold = self.bold_chk.isChecked()
        self._style.italic = self.italic_chk.isChecked()
        self._style.outline_width = self.outline_width_spin.value()
        
        align_keys = ['left', 'center', 'right', 'justify']
        self._style.alignment = align_keys[self.align_combo.currentIndex()]
        
        self._style.line_spacing = self.linespace_spin.value()

        self._style.auto_hyphenate = self.hyphen_chk.isChecked()
        
        cap_keys = ['mixed', 'uppercase', 'lowercase', 'capitalize', 'smallcaps']
        self._style.capitalization = cap_keys[self.cap_combo.currentIndex()]
        
        self._style.shadow_enabled = self.shadow_chk.isChecked()
        
        self.styleChanged.emit()
    
    def _pick_font(self):
        if not self._style:
            return
        cur = self._style.to_qfont()
        font, ok = QFontDialog.getFont(cur, self, "Elegir fuente")
        if ok:
            self._style.font_family = font.family()
            self._style.font_point_size = font.pointSize()
            self._style.bold = font.bold()
            self._style.italic = font.italic()
            self.font_label.setText(font.family())
            self.size_spin.setValue(font.pointSize())
            self.bold_chk.setChecked(font.bold())
            self.italic_chk.setChecked(font.italic())
            self.styleChanged.emit()
    
    def _pick_fill_color(self):
        if not self._style:
            return
        color = QColorDialog.getColor(QColor(self._style.fill), self, "Color de texto")
        if color.isValid():
            self._style.fill = color.name()
            self._update_color_btn(self.fill_btn, color.name())
            self.fill_label.setText(color.name())
            self.styleChanged.emit()
    
    def _pick_outline_color(self):
        if not self._style:
            return
        color = QColorDialog.getColor(QColor(self._style.outline), self, "Color de trazo")
        if color.isValid():
            self._style.outline = color.name()
            self._update_color_btn(self.outline_btn, color.name())
            self.outline_label.setText(color.name())
            self.styleChanged.emit()


# ---------------- Diálogo de fuentes por simbología (Mejorado estilo TypeR) ----------------

class FontsPerPresetDialog(QDialog):
    """Diálogo mejorado para gestionar estilos/fuentes por simbología (estilo TypeR)."""
    
    def __init__(self, parent, presets: Dict[str, TextStyle]):
        super().__init__(parent)
        self.setWindowTitle("Gestor de Estilos – Definir fuentes por simbología")
        self.setMinimumSize(800, 600)
        self.presets = presets
        self._current_key: Optional[str] = None
        self._apply_existing = False
        
        self._build_ui()
        self._populate_list()
        
        # Seleccionar el primero
        if self.style_list.count() > 0:
            self.style_list.setCurrentRow(0)
    
    def _build_ui(self):
        # Layout principal vertical
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        
        # === Contenedor horizontal para los dos paneles ===
        panels_widget = QWidget()
        panels_layout = QHBoxLayout(panels_widget)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(12)
        
        # === Panel izquierdo: Lista de estilos ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Título
        title_lbl = QLabel("Estilos disponibles")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(title_lbl)
        
        # Lista de estilos
        self.style_list = QListWidget()
        self.style_list.setMinimumWidth(200)
        self.style_list.currentRowChanged.connect(self._on_style_selected)
        left_layout.addWidget(self.style_list)
        
        # Botones de gestión
        btn_row = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Nuevo")
        self.add_btn.setToolTip("Crear nuevo estilo")
        self.add_btn.clicked.connect(self._add_style)
        btn_row.addWidget(self.add_btn)
        
        self.dup_btn = QPushButton("📋 Duplicar")
        self.dup_btn.setToolTip("Duplicar estilo seleccionado")
        self.dup_btn.clicked.connect(self._duplicate_style)
        btn_row.addWidget(self.dup_btn)
        
        self.del_btn = QPushButton("🗑️ Eliminar")
        self.del_btn.setToolTip("Eliminar estilo seleccionado")
        self.del_btn.clicked.connect(self._delete_style)
        btn_row.addWidget(self.del_btn)
        
        left_layout.addLayout(btn_row)
        
        # Botones de importar/exportar
        io_row = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 Exportar")
        self.export_btn.setToolTip("Exportar estilo seleccionado a JSON")
        self.export_btn.clicked.connect(self._export_style)
        io_row.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("📥 Importar")
        self.import_btn.setToolTip("Importar estilo desde JSON")
        self.import_btn.clicked.connect(self._import_style)
        io_row.addWidget(self.import_btn)
        
        left_layout.addLayout(io_row)
        
        # Restaurar defaults
        self.reset_btn = QPushButton("🔄 Restaurar defaults")
        self.reset_btn.setToolTip("Restaurar estilos predeterminados")
        self.reset_btn.clicked.connect(self._reset_defaults)
        left_layout.addWidget(self.reset_btn)
        
        panels_layout.addWidget(left_panel)
        
        # === Panel derecho: Editor de estilo ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Nombre del estilo
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Nombre:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del estilo")
        self.name_edit.textChanged.connect(self._on_name_changed)
        name_row.addWidget(self.name_edit)
        right_layout.addLayout(name_row)
        
        # Vista previa
        preview_group = QFrame()
        preview_group.setStyleSheet("QFrame { background: #1a1a2e; border: 1px solid #333; border-radius: 6px; }")
        preview_layout = QVBoxLayout(preview_group)
        
        preview_title = QLabel("Vista previa")
        preview_title.setStyleSheet("color: #888; font-size: 11px; background: transparent; border: none;")
        preview_layout.addWidget(preview_title)
        
        self.preview_widget = StylePreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        
        right_layout.addWidget(preview_group)
        
        # Editor de propiedades
        editor_group = QFrame()
        editor_group.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 6px; }")
        editor_layout = QVBoxLayout(editor_group)
        
        self.style_editor = StyleEditorWidget()
        self.style_editor.styleChanged.connect(self._on_style_changed)
        editor_layout.addWidget(self.style_editor)
        
        right_layout.addWidget(editor_group, 1)
        
        panels_layout.addWidget(right_panel, 1)
        
        # Añadir paneles al layout principal
        main_layout.addWidget(panels_widget, 1)
        
        # === Botones de diálogo (abajo) ===
        self.apply_chk = QCheckBox("Aplicar cambios a elementos existentes de cada tipo")
        main_layout.addWidget(self.apply_chk)
        
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)
    
    def _populate_list(self):
        self.style_list.clear()
        for key in self.presets.keys():
            item = QListWidgetItem(key)
            self.style_list.addItem(item)
    
    def _on_style_selected(self, row: int):
        if row < 0:
            self._current_key = None
            return
        
        self._current_key = self.style_list.item(row).text()
        style = self.presets.get(self._current_key)
        
        if style:
            self.name_edit.blockSignals(True)
            self.name_edit.setText(self._current_key)
            self.name_edit.blockSignals(False)
            
            self.style_editor.set_style(style)
            self.preview_widget.set_style(style)
    
    def _on_style_changed(self):
        if self._current_key and self._current_key in self.presets:
            self.preview_widget.set_style(self.presets[self._current_key])
    
    def _on_name_changed(self, new_name: str):
        if not self._current_key or not new_name.strip():
            return
        
        new_name = new_name.strip().upper()
        
        if new_name == self._current_key:
            return
        
        if new_name in self.presets:
            return
        
        # Renombrar
        style = self.presets.pop(self._current_key)
        self.presets[new_name] = style
        self._current_key = new_name
        
        # Actualizar lista
        current_row = self.style_list.currentRow()
        self.style_list.item(current_row).setText(new_name)
    
    def _add_style(self):
        name, ok = self._get_unique_name("NUEVO_ESTILO")
        if not ok:
            return
        
        # Crear estilo con valores por defecto
        new_style = TextStyle()
        self.presets[name] = new_style
        
        # Añadir a la lista y seleccionar
        item = QListWidgetItem(name)
        self.style_list.addItem(item)
        self.style_list.setCurrentItem(item)
    
    def _duplicate_style(self):
        if not self._current_key:
            return
        
        name, ok = self._get_unique_name(f"{self._current_key}_COPIA")
        if not ok:
            return
        
        # Duplicar el estilo actual
        original = self.presets[self._current_key]
        new_style = replace(original)
        self.presets[name] = new_style
        
        # Añadir a la lista y seleccionar
        item = QListWidgetItem(name)
        self.style_list.addItem(item)
        self.style_list.setCurrentItem(item)
    
    def _delete_style(self):
        if not self._current_key:
            return
        
        # No permitir eliminar si solo queda uno
        if len(self.presets) <= 1:
            QMessageBox.warning(self, "No se puede eliminar", 
                              "Debe haber al menos un estilo.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar el estilo '{self._current_key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.presets[self._current_key]
            row = self.style_list.currentRow()
            self.style_list.takeItem(row)
            
            if self.style_list.count() > 0:
                self.style_list.setCurrentRow(0)
    
    def _export_style(self):
        if not self._current_key:
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, f"Exportar estilo '{self._current_key}'",
            f"{self._current_key}.json", "JSON (*.json)"
        )
        
        if path:
            style = self.presets[self._current_key]
            data = {self._current_key: asdict(style)}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Exportado", 
                                   f"Estilo exportado a:\n{path}")
    
    def _import_style(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar estilo", "", "JSON (*.json)"
        )
        
        if not path:
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported = 0
            for key, val in data.items():
                # Si ya existe, preguntar
                if key in self.presets:
                    reply = QMessageBox.question(
                        self, "Estilo existente",
                        f"El estilo '{key}' ya existe. ¿Sobrescribir?",
                        QMessageBox.StandardButton.Yes | 
                        QMessageBox.StandardButton.No |
                        QMessageBox.StandardButton.Cancel
                    )
                    if reply == QMessageBox.StandardButton.Cancel:
                        return
                    if reply == QMessageBox.StandardButton.No:
                        continue
                
                self.presets[key] = TextStyle(**val)
                imported += 1
            
            self._populate_list()
            QMessageBox.information(self, "Importado", 
                                   f"Se importaron {imported} estilo(s).")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al importar:\n{e}")
    
    def _reset_defaults(self):
        reply = QMessageBox.question(
            self, "Restaurar defaults",
            "¿Restaurar todos los estilos predeterminados?\n"
            "Los estilos personalizados se mantendrán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            defaults = default_presets()
            for key, style in defaults.items():
                self.presets[key] = style
            
            self._populate_list()
            if self.style_list.count() > 0:
                self.style_list.setCurrentRow(0)
    
    def _get_unique_name(self, base: str) -> tuple:
        """Pide un nombre único para el estilo."""
        name = base
        counter = 1
        while name in self.presets:
            name = f"{base}_{counter}"
            counter += 1
        
        text, ok = QLineEdit.getText(
            QLineEdit(), "Nombre del estilo", "Nombre:", 
            QLineEdit.EchoMode.Normal, name
        ) if False else (name, True)  # Simplificado: usar nombre generado
        
        # Validar
        if ok:
            name = name.strip().upper()
            if not name:
                return "", False
        
        return name, ok
    
    def apply_changes(self) -> bool:
        return self.apply_chk.isChecked()


class GradientEditBar(QWidget):
    """
    Widget tipo 'Photoshop' para editar el degradado.
    - Muestra barra con preview.
    - Handles abajo para mover stops.
    - Click en área vacía = nuevo stop.
    - Drag handles = mover.
    - Click handle = seleccionar (emitir signal).
    - Drag afuera / Supr = borrar.
    """
    # Emite (posición, color_hex) cuando se selecciona un stop
    stopSelected = pyqtSignal(float, str)
    # Emite la lista completa de stops [(pos, hex), ...] cada vez que cambia algo
    gradientChanged = pyqtSignal(list)

    HANDLE_SIZE = 10  # Tamaño del triangulito/cuadrado del handle

    def __init__(self, stops: List[Tuple[float, str]] = None, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50)
        self.setMouseTracking(True)
        # Stops es lista de (pos, hex)
        # Asegurar orden
        self.stops = sorted(stops if stops else [(0.0, "#000000"), (1.0, "#FFFFFF")], key=lambda x: x[0])
        self.selected_index = -1
        self._dragging_index = -1
        self._hover_index = -1

    def set_stops(self, stops: List[Tuple[float, str]]):
        self.stops = sorted(stops, key=lambda x: x[0])
        self.update()

    def get_stops(self) -> List[Tuple[float, str]]:
        return self.stops

    def set_selected_stop_color(self, color_hex: str):
        if 0 <= self.selected_index < len(self.stops):
            pos, _ = self.stops[self.selected_index]
            self.stops[self.selected_index] = (pos, color_hex)
            self.update()
            self.gradientChanged.emit(self.stops)

    def set_selected_stop_pos(self, pos: float):
        if 0 <= self.selected_index < len(self.stops):
            _, col = self.stops[self.selected_index]
            pos = max(0.0, min(1.0, pos))
            self.stops[self.selected_index] = (pos, col)
            # Reordenar y mantener selección
            # (Un poco tricky mantener el índice correcto al reordenar pero para UX simple basta)
            self.stops.sort(key=lambda x: x[0])
            # Buscar dónde quedó
            for i, (p, c) in enumerate(self.stops):
                if p == pos and c == col:
                    self.selected_index = i
                    break
            self.update()
            self.gradientChanged.emit(self.stops)

    def delete_selected_stop(self):
        if 0 <= self.selected_index < len(self.stops):
            if len(self.stops) <= 2:
                # Opcional: impedir borrar si hay menos de 2
                return
            self.stops.pop(self.selected_index)
            self.selected_index = -1
            self.update()
            self.gradientChanged.emit(self.stops)
            # Emitir -1 para indicar des-selección
            self.stopSelected.emit(-1.0, "")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h_bar = self.height() - self.HANDLE_SIZE - 5 # Altura de la barra de color
        bar_rect = QRectF(0, 0, w, h_bar)

        # 1. Fondo checkerboard para alpha
        step = 10
        p.setPen(Qt.PenStyle.NoPen)
        for y in range(0, int(h_bar), step):
            for x in range(0, w, step):
                if ((x//step) + (y//step)) % 2 == 0:
                    p.setBrush(QColor("#CCCCCC"))
                else:
                    p.setBrush(QColor("#FFFFFF"))
                p.drawRect(x, y, step, step)

        # 2. Gradiente
        grad = QLinearGradient(0, 0, w, 0)
        for pos, col in self.stops:
            grad.setColorAt(pos, QColor(col))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(bar_rect)
        p.setPen(QPen(QColor("#888888"), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(bar_rect)

        # 3. Handles
        for i, (pos, col) in enumerate(self.stops):
            x = int(pos * w)
            y_start = h_bar + 2
            
            # Dibujar triangulito + cuadrado
            # Forma simple: Rect con borde
            h_rect = self._handle_rect(x, y_start)
            
            p.setBrush(QColor(col))
            if i == self.selected_index:
                p.setPen(QPen(QColor("#00AAFF"), 2)) # Azul si seleccionado
            elif i == self._hover_index:
                p.setPen(QPen(QColor("#FFFFFF"), 2)) # Blanco si hover
            else:
                p.setPen(QPen(QColor("#000000"), 1))
            
            p.drawRect(h_rect)

        p.end()

    def _handle_rect(self, x_center, y_top):
        s = self.HANDLE_SIZE
        return QRectF(x_center - s/2, y_top, s, s)

    def mousePressEvent(self, event):
        pos = event.pos()
        x, y = pos.x(), pos.y()
        w = self.width()
        
        # Verificar clicks en handles existentes
        clicked_index = -1
        h_bar = self.height() - self.HANDLE_SIZE - 5
        
        # Revisar en orden inverso (arriba los últimos)
        for i in range(len(self.stops)-1, -1, -1):
            stop_pos, _ = self.stops[i]
            rect = self._handle_rect(stop_pos * w, h_bar + 2)
            # Expandir hit area un poco
            hit_rect = rect.adjusted(-3, -3, 3, 3)
            if hit_rect.contains(QPointF(x, y)):
                clicked_index = i
                break
        
        if clicked_index != -1:
            self.selected_index = clicked_index
            self._dragging_index = clicked_index
            self.update()
            s_pos, s_col = self.stops[self.selected_index]
            self.stopSelected.emit(s_pos, s_col)
            return

        # Si click en la barra de gradiente vacía -> crear nuevo stop
        if y < h_bar:
            new_pos = max(0.0, min(1.0, x / w))
            # Calcular color en ese punto interpolando
            # Truco: usar un gradiente temporal de 1px
            grad = QLinearGradient(0, 0, 100, 0)
            for p, c in self.stops:
                grad.setColorAt(p, QColor(c))
            # Muestrear no es trivial sin QImage, así que hacemos estimación simple o usamos el último seleccionado
            # Mejor: añadir blanco o negro por defecto, el usuario lo cambiará.
            # O mejor aún: interpolar matemáticamente.
            # Para simplicidad visual, usaremos el mismo color que el stop anterior o blanco.
            new_col = "#FFFFFF" 
            
            self.stops.append((new_pos, new_col))
            self.stops.sort(key=lambda x: x[0])
            # Seleccionar el nuevo
            for i, (p, c) in enumerate(self.stops):
                if p == new_pos and c == new_col:
                    self.selected_index = i
                    self._dragging_index = i
                    break
            self.update()
            self.gradientChanged.emit(self.stops)
            s_pos, s_col = self.stops[self.selected_index]
            self.stopSelected.emit(s_pos, s_col)

    def mouseMoveEvent(self, event):
        x = event.pos().x()
        w = self.width()

        if self._dragging_index != -1:
            # Mover stop
            # Si arrastra muy abajo -> borrar? Photoshop lo hace.
            # Implementemos mover simple 0-1
            new_pos = max(0.0, min(1.0, x / w))
            _, col = self.stops[self._dragging_index]
            self.stops[self._dragging_index] = (new_pos, col)
            # Ordenar dinámicamente puede ser confuso mientras arrastras, pero necesario para el rendering correcto
            self.stops.sort(key=lambda x: x[0])
            # Re-encontrar índice
            for i, (p, c) in enumerate(self.stops):
                if p == new_pos and c == col:
                    self._dragging_index = i
                    self.selected_index = i
                    break
            
            self.update()
            self.gradientChanged.emit(self.stops)
            self.stopSelected.emit(new_pos, col)
        else:
            # Hover check
            h_bar = self.height() - self.HANDLE_SIZE - 5
            hover_idx = -1
            for i in range(len(self.stops)-1, -1, -1):
                stop_pos, _ = self.stops[i]
                rect = self._handle_rect(stop_pos * w, h_bar + 2)
                if rect.contains(QPointF(x, event.pos().y())):
                    hover_idx = i
                    break
            if hover_idx != self._hover_index:
                self._hover_index = hover_idx
                self.update()

    def mouseReleaseEvent(self, event):
        self._dragging_index = -1

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected_stop()


class FillChooserDialog(QDialog):
    """Diálogo avanzado de relleno con editor de gradiente estilo Photoshop.
    """
    def __init__(self, parent, style: TextStyle, on_update_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Estilo y Relleno")
        self.resize(550, 480)
        self.style = style
        self.on_update_callback = on_update_callback
        self._last_preview_spec = None
        
        # 1. Main Layout
        main_layout = QVBoxLayout(self)
        
        # 2. Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- TAB 1: SÓLIDO ---
        solid_w = QWidget(); sl = QVBoxLayout(solid_w)
        sl_form = QFormLayout()
        self.solid_btn = QPushButton("Elegir color…")
        self.solid_preview = QLabel(); self.solid_preview.setFixedSize(100, 30); self.solid_preview.setStyleSheet("border: 1px solid #555;")
        self.solid_transparent_chk = QCheckBox("Relleno transparente (solo trazo)")
        sl_form.addRow("Color:", self.solid_btn)
        sl_form.addRow("Vista:", self.solid_preview)
        sl_form.addRow("", self.solid_transparent_chk)
        sl.addLayout(sl_form); sl.addStretch()
        self.tabs.addTab(solid_w, "Color Sólido")

        # --- TAB 2: DEGRADADO (Advanced) ---
        grad_w = QWidget()
        gl = QVBoxLayout(grad_w)
        
        # Preset bar (Grid pequeño de botones)
        # Por brevedad, pondremos unos pocos presets
        presets_layout = QHBoxLayout()
        presets_label = QLabel("Presets:")
        presets_layout.addWidget(presets_label)
        
        self.preset_btns = []
        # (Nombre, stops)
        sample_grads = [
            ("B/N", [(0.0, "#000000"), (1.0, "#FFFFFF")]),
            ("Sunset", [(0.0, "#1A2980"), (1.0, "#26D0CE")]),
            ("Fire", [(0.0, "#f12711"), (1.0, "#f5af19")]),
            ("Rainbow", [(0.0,"#FF0000"),(0.2,"#FFFF00"),(0.4,"#00FF00"),(0.6,"#00FFFF"),(0.8,"#0000FF"),(1.0,"#FF00FF")]),
        ]
        
        for name, stops in sample_grads:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setToolTip(name)
            # Set gradient background for button
            qss_grad = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, "
            qss_stops = ""
            for p, c in stops: qss_stops += f"stop:{p} {c}, "
            qss_grad += qss_stops[:-2] + ")"
            btn.setStyleSheet(f"background: {qss_grad}; border:1px solid #777;")
            btn.clicked.connect(lambda _, s=stops: self._load_gradient_stops(s))
            presets_layout.addWidget(btn)
        presets_layout.addStretch()
        gl.addLayout(presets_layout)

        # Editor Bar
        self.grad_bar = GradientEditBar(getattr(style, 'gradient_stops', None))
        gl.addWidget(self.grad_bar)
        
        # Controls area
        controls_group = QFrame(); controls_group.setStyleSheet("background: #222; border-radius: 4px; padding: 4px;")
        cg_lay = QGridLayout(controls_group)
        
        cg_lay.addWidget(QLabel("Color:"), 0, 0)
        self.stop_color_btn = QPushButton(" ")
        self.stop_color_btn.setFixedSize(50, 24)
        cg_lay.addWidget(self.stop_color_btn, 0, 1)
        
        cg_lay.addWidget(QLabel("Posición (%):"), 0, 2)
        self.stop_pos_spin = QDoubleSpinBox()
        self.stop_pos_spin.setRange(0, 100); self.stop_pos_spin.setSingleStep(1); self.stop_pos_spin.setSuffix("%")
        cg_lay.addWidget(self.stop_pos_spin, 0, 3)
        
        self.stop_del_btn = QPushButton("Eliminar")
        cg_lay.addWidget(self.stop_del_btn, 0, 4)
        
        gl.addWidget(controls_group)
        
        # Angle control
        angle_lay = QHBoxLayout()
        angle_lay.addWidget(QLabel("Ángulo Global:"))
        self.angle_spin = QSpinBox(); self.angle_spin.setRange(-360, 360); self.angle_spin.setValue(int(getattr(style, 'gradient_angle', 0)))
        self.angle_spin.setSuffix("°")
        angle_lay.addWidget(self.angle_spin)
        angle_lay.addStretch()
        gl.addLayout(angle_lay)
        
        gl.addStretch()
        self.tabs.addTab(grad_w, "Degradado")

        # --- TAB 3: TEXTURA ---
        tex_w = QWidget(); tl = QVBoxLayout(tex_w)
        self.tex_pick = QPushButton("Elegir imagen…")
        self.tex_path_lbl = QLabel(getattr(style, 'texture_path', '') or "(ninguna)")
        self.tex_tile_chk = QCheckBox("Repetir (tile)"); self.tex_tile_chk.setChecked(getattr(style, 'texture_tile', True))
        tl.addWidget(self.tex_pick); tl.addWidget(self.tex_path_lbl); tl.addWidget(self.tex_tile_chk)

        # Zoom y rotacion de textura
        tex_scale_row = QHBoxLayout()
        tex_scale_row.addWidget(QLabel("Zoom:"))
        self.tex_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.tex_scale_slider.setRange(10, 500)   # 10% - 500%
        self.tex_scale_spin = QDoubleSpinBox()
        self.tex_scale_spin.setRange(0.10, 5.00)
        self.tex_scale_spin.setSingleStep(0.05)
        self.tex_scale_spin.setDecimals(2)
        self.tex_scale_spin.setSuffix("x")
        tex_scale_row.addWidget(self.tex_scale_slider, 1)
        tex_scale_row.addWidget(self.tex_scale_spin)
        tl.addLayout(tex_scale_row)

        tex_rot_row = QHBoxLayout()
        tex_rot_row.addWidget(QLabel("Rotación:"))
        self.tex_rot_slider = QSlider(Qt.Orientation.Horizontal)
        self.tex_rot_slider.setRange(-360, 360)
        self.tex_rot_spin = QSpinBox()
        self.tex_rot_spin.setRange(-360, 360)
        self.tex_rot_spin.setSuffix("°")
        tex_rot_row.addWidget(self.tex_rot_slider, 1)
        tex_rot_row.addWidget(self.tex_rot_spin)
        tl.addLayout(tex_rot_row)

        self.tex_preview = QLabel(); self.tex_preview.setFixedSize(200, 100); self.tex_preview.setStyleSheet("border: 1px solid #555;")
        tl.addWidget(self.tex_preview)
        tl.addStretch()
        self.tabs.addTab(tex_w, "Textura")

        # Buttons
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); main_layout.addWidget(bb)

        # --- CONNECTIONS ---
        # Solid
        self.solid_btn.clicked.connect(self._pick_solid)
        self.solid_transparent_chk.stateChanged.connect(self._on_solid_transparent_changed)
        
        # Gradient
        self.grad_bar.stopSelected.connect(self._on_stop_selected_ui)
        self.grad_bar.gradientChanged.connect(self._on_grad_changed_ui)
        self.stop_color_btn.clicked.connect(self._pick_stop_color)
        self.stop_pos_spin.valueChanged.connect(self._on_spin_pos_changed)
        self.stop_del_btn.clicked.connect(self.grad_bar.delete_selected_stop)
        self.angle_spin.valueChanged.connect(self._notify_update)
        
        # Texture
        self.tex_pick.clicked.connect(self._pick_texture)
        self.tex_tile_chk.stateChanged.connect(self._notify_update)
        self.tex_tile_chk.stateChanged.connect(self._update_tex_preview)
        self.tex_scale_slider.valueChanged.connect(self._on_tex_scale_slider_changed)
        self.tex_scale_spin.valueChanged.connect(self._on_tex_scale_spin_changed)
        self.tex_rot_slider.valueChanged.connect(self._on_tex_rot_slider_changed)
        self.tex_rot_spin.valueChanged.connect(self._on_tex_rot_spin_changed)
        
        self.tabs.currentChanged.connect(self._notify_update)

        # Init state
        self._solid_color = getattr(style, 'fill', '#000000')
        self._solid_transparent = (getattr(style, 'fill_type', 'solid') == 'transparent')
        self._tex_path = getattr(style, 'texture_path', '')
        self._tex_tile = bool(getattr(style, 'texture_tile', True))
        self._tex_scale = float(getattr(style, 'texture_scale', 1.0) or 1.0)
        self._tex_angle = int(getattr(style, 'texture_angle', 0) or 0)
        self._tex_scale = clamp(self._tex_scale, 0.10, 5.00)
        self._tex_angle = int(clamp(self._tex_angle, -360, 360))

        self.tex_scale_slider.blockSignals(True)
        self.tex_scale_spin.blockSignals(True)
        self.tex_rot_slider.blockSignals(True)
        self.tex_rot_spin.blockSignals(True)
        self.tex_scale_slider.setValue(int(round(self._tex_scale * 100)))
        self.tex_scale_spin.setValue(self._tex_scale)
        self.tex_rot_slider.setValue(self._tex_angle)
        self.tex_rot_spin.setValue(self._tex_angle)
        self.tex_scale_slider.blockSignals(False)
        self.tex_scale_spin.blockSignals(False)
        self.tex_rot_slider.blockSignals(False)
        self.tex_rot_spin.blockSignals(False)
        self.solid_transparent_chk.blockSignals(True)
        self.solid_transparent_chk.setChecked(self._solid_transparent)
        self.solid_transparent_chk.blockSignals(False)
        
        # Initial UI sync
        self._update_solid_preview()
        self._update_tex_preview()
        
        # Set initial tab
        ft = getattr(style, 'fill_type', 'solid')
        if ft == 'linear_gradient': self.tabs.setCurrentIndex(1)
        elif ft == 'texture': self.tabs.setCurrentIndex(2)
        else: self.tabs.setCurrentIndex(0)

    # --- SOLID LOGIC ---
    def _pick_solid(self):
        if self._solid_transparent:
            return
        c = qcolor_from_hex(self._solid_color)
        dlg = QColorDialog(c, self)
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        
        # Live preview
        def on_change():
            curr = dlg.currentColor()
            if curr.isValid():
                self._solid_color = curr.name(QColor.NameFormat.HexRgb)
                self._update_solid_preview()
                self._notify_update()
                
        dlg.currentColorChanged.connect(on_change)
        # Some platforms/Qt versions don't emit currentColorChanged on every drag, timer helper
        t = QTimer(dlg)
        t.timeout.connect(on_change)
        t.start(100)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            on_change() # Ensure final setting
        else:
            # Revert if cancelled? The previous implementation didn't strictly revert on cancel in the snapshot, 
            # but usually users expect live preview to stick if they play with it, OR revert. 
            # The 'choose_color' wrapper handles the snapshot revert if FillChooserDialog is cancelled.
            pass

    def _update_solid_preview(self):
        if self._solid_transparent:
            self.solid_preview.setText("TRANSP.")
            self.solid_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.solid_preview.setStyleSheet(
                "border: 1px solid #777;"
                "color: #E2E8F0;"
                "background: repeating-linear-gradient(45deg, #202534, #202534 6px, #141a27 6px, #141a27 12px);"
            )
            self.solid_btn.setEnabled(False)
        else:
            self.solid_preview.setText("")
            self.solid_preview.setStyleSheet(f"background-color: {self._solid_color}; border: 1px solid #777;")
            self.solid_btn.setEnabled(True)

    def _on_solid_transparent_changed(self, state: int):
        self._solid_transparent = bool(state)
        self._update_solid_preview()
        self._notify_update()

    # --- GRADIENT LOGIC ---
    def _load_gradient_stops(self, stops):
        self.grad_bar.set_stops(stops)
        self._notify_update()

    def _on_stop_selected_ui(self, pos, col):
        if pos < 0: # Des-selected
            self.stop_color_btn.setEnabled(False)
            self.stop_pos_spin.setEnabled(False)
            self.stop_del_btn.setEnabled(False)
            self.stop_color_btn.setStyleSheet("")
        else:
            self.stop_color_btn.setEnabled(True)
            self.stop_pos_spin.setEnabled(True)
            self.stop_del_btn.setEnabled(True)
            self.stop_color_btn.setStyleSheet(f"background-color: {col}; border: none;")
            self.stop_pos_spin.blockSignals(True)
            self.stop_pos_spin.setValue(pos * 100.0)
            self.stop_pos_spin.blockSignals(False)

    def _on_grad_changed_ui(self, stops):
        self._notify_update()

    def _pick_stop_color(self):
        # Usar color actual del stop seleccionado
        if self.grad_bar.selected_index == -1: return
        _, curr_hex = self.grad_bar.stops[self.grad_bar.selected_index]
        
        dlg = QColorDialog(QColor(curr_hex), self)
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)

        def on_change():
            curr = dlg.currentColor()
            if curr.isValid():
                new_hex = curr.name(QColor.NameFormat.HexRgb)
                self.grad_bar.set_selected_stop_color(new_hex)
                self.stop_color_btn.setStyleSheet(f"background-color: {new_hex}; border: none;")
                # gradientChanged signal from grad_bar will trigger _notify_update
        
        dlg.currentColorChanged.connect(on_change)
        t = QTimer(dlg)
        t.timeout.connect(on_change)
        t.start(100)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            on_change()


    def _on_spin_pos_changed(self, val):
        self.grad_bar.set_selected_stop_pos(val / 100.0)

    # --- TEXTURE LOGIC ---
    def _pick_texture(self):
        f, _ = QFileDialog.getOpenFileName(self, "Textura", "", "Imágenes (*.png *.jpg *.jpeg *.webp)")
        if f:
            self._tex_path = f
            self.tex_path_lbl.setText(f)
            self._update_tex_preview()
            self._notify_update()

    def _on_tex_scale_slider_changed(self, v: int):
        self._tex_scale = clamp(v / 100.0, 0.10, 5.00)
        self.tex_scale_spin.blockSignals(True)
        self.tex_scale_spin.setValue(self._tex_scale)
        self.tex_scale_spin.blockSignals(False)
        self._update_tex_preview()
        self._notify_update()

    def _on_tex_scale_spin_changed(self, v: float):
        self._tex_scale = clamp(float(v), 0.10, 5.00)
        self.tex_scale_slider.blockSignals(True)
        self.tex_scale_slider.setValue(int(round(self._tex_scale * 100)))
        self.tex_scale_slider.blockSignals(False)
        self._update_tex_preview()
        self._notify_update()

    def _on_tex_rot_slider_changed(self, v: int):
        self._tex_angle = int(clamp(v, -360, 360))
        self.tex_rot_spin.blockSignals(True)
        self.tex_rot_spin.setValue(self._tex_angle)
        self.tex_rot_spin.blockSignals(False)
        self._update_tex_preview()
        self._notify_update()

    def _on_tex_rot_spin_changed(self, v: int):
        self._tex_angle = int(clamp(v, -360, 360))
        self.tex_rot_slider.blockSignals(True)
        self.tex_rot_slider.setValue(self._tex_angle)
        self.tex_rot_slider.blockSignals(False)
        self._update_tex_preview()
        self._notify_update()

    def _update_tex_preview(self):
        self.tex_preview.setPixmap(QPixmap())
        if self._tex_path and os.path.exists(self._tex_path):
            pm = QPixmap(self._tex_path)
            if not pm.isNull():
                w = self.tex_preview.width()
                h = self.tex_preview.height()
                canvas = QPixmap(w, h)
                canvas.fill(QColor("#141922"))
                p = QPainter(canvas)
                p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

                if self.tex_tile_chk.isChecked():
                    brush = QBrush(pm)
                    tr = QTransform()
                    tr.scale(self._tex_scale, self._tex_scale)
                    tr.rotate(self._tex_angle)
                    brush.setTransform(tr)
                    p.fillRect(0, 0, w, h, brush)
                else:
                    fit = min((w - 12) / max(1, pm.width()), (h - 12) / max(1, pm.height()))
                    p.translate(w / 2.0, h / 2.0)
                    p.rotate(self._tex_angle)
                    p.scale(fit * self._tex_scale, fit * self._tex_scale)
                    p.translate(-pm.width() / 2.0, -pm.height() / 2.0)
                    p.drawPixmap(0, 0, pm)
                p.end()
                self.tex_preview.setPixmap(canvas)
                self.tex_preview.setText("")
            else:
                self.tex_preview.setPixmap(QPixmap())
                self.tex_preview.setText("Error cargando imagen")
        else:
            self.tex_preview.setPixmap(QPixmap())
            self.tex_preview.setText("(Sin imagen)")

    # --- COMMON ---
    def _notify_update(self):
        if callable(self.on_update_callback):
            spec = self.get_current_spec()
            if self._last_preview_spec is not None and spec == self._last_preview_spec:
                return
            self._last_preview_spec = deepcopy(spec)
            self.on_update_callback(spec)

    def get_current_spec(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            return {
                'fill_type': 'transparent' if self._solid_transparent else 'solid',
                'fill': self._solid_color
            }
        elif idx == 1:
            return {
                'fill_type': 'linear_gradient',
                'gradient_stops': self.grad_bar.get_stops(),
                'gradient_angle': self.angle_spin.value()
            }
        else:
            return {
                'fill_type': 'texture',
                'texture_path': self._tex_path,
                'texture_tile': self.tex_tile_chk.isChecked(),
                'texture_scale': float(self._tex_scale),
                'texture_angle': int(self._tex_angle),
            }

    def get_result(self):
        return self.get_current_spec()


# ---------------- main ----------------
def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(icon('app.ico'))
    
    # Calcular y aplicar factor de escala
    scale = get_ui_scale_factor()
    Theme.apply(app, dark=True, accent="#E11D48", radius=10, scale_factor=scale)
    
    # ===== SINGLE INSTANCE: Verificar si ya hay una instancia corriendo =====
    instance_manager = SingleInstanceManager()
    
    # Recopilar archivos .bbg de los argumentos
    bbg_files = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            file_path = Path(arg)
            if file_path.exists() and file_path.suffix.lower() == '.bbg':
                bbg_files.append(str(file_path.absolute()))
    
    # Si ya hay una instancia corriendo, enviarle los archivos y terminar
    if instance_manager.is_already_running():
        if bbg_files:
            # Enviar archivos a la instancia existente
            if instance_manager.send_files_to_existing_instance(bbg_files):
                print(f"Archivos enviados a la instancia existente: {bbg_files}")
            else:
                print("No se pudieron enviar archivos a la instancia existente")
        else:
            # No hay archivos, solo traer la ventana existente al frente
            print("Ya hay una instancia corriendo. Activándola...")
        
        sys.exit(0)
    
    # ===== Esta es la primera instancia, continuar normalmente =====
    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    username = login.get_username()
    if not username:
        QMessageBox.warning(None, "Acceso denegado", "Debes escribir un usuario de Discord.")
        sys.exit(0)

    try:
        ok = check_user_exists_and_log(username)
    except Exception as e:
        QMessageBox.critical(
            None,
            "Error de autenticación",
            f"No se pudo verificar el usuario.\n\nDetalle técnico:\n{e}"
        )
        sys.exit(1)

    if not ok:
        QMessageBox.warning(None, "Acceso denegado", "Usuario no autorizado.")
        sys.exit(0)

    win = MangaTextTool(username=username)
    
    # Iniciar el servidor para recibir archivos de otras instancias
    instance_manager.start_server(win)
    
    win.show()
    _apply_win_icon(win)
    
    # Abrir archivos .bbg pasados como argumentos iniciales
    if bbg_files:
        for file_path in bbg_files:
            win._open_single_project_bbg(file_path)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
