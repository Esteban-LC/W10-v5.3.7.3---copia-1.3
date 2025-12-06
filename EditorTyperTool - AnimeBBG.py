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
import json, math, sys, re, os, base64
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Callable
import socket
import platform
from datetime import datetime
import webbrowser  # asegúrate de tener esto importado arriba
from pathlib import Path

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from PyQt6.QtCore import Qt, QPointF, QRectF, QSettings, QBuffer, QByteArray, QIODevice, QSize, QTimer
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import (
    QAction, QColor, QFont, QGuiApplication, QImage, QPainter, QIcon,
    QPixmap, QTextCursor, QTextDocument, QTextOption, QShortcut, QKeySequence,
    QUndoStack, QUndoCommand, QTextBlockFormat, QPen, QCursor, QLinearGradient, QBrush
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QGraphicsDropShadowEffect, QGraphicsItem,
    QGraphicsPixmapItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView,
    QLabel, QMainWindow, QMessageBox, QPushButton, QSlider, QSpinBox, QToolBar,
    QDockWidget, QListWidget, QListWidgetItem, QFormLayout, QCheckBox, QWidget,
    QVBoxLayout, QDialog, QTextEdit, QDialogButtonBox, QColorDialog, QFontDialog,
    QTabWidget, QHBoxLayout, QComboBox, QDoubleSpinBox, QGridLayout, QStyleFactory,
    QToolButton, QStyle, QLineEdit, QFrame
)

# Import automated workflow module
try:
    from automated_workflow import WorkflowWizard, WorkflowData, TextBoxDetection
    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False
    print("[WARNING] automated_workflow module not found. Workflow features disabled.")

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

GSPREAD_CREDS = {
  "type": "service_account",
  "project_id": "animebbg-editor",
  "private_key_id": "3aaf1270a3109c1323cea6b2a28ade84f04b31a1",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCjGyOQe8yFlLW9\nQZi+YMflBtaANrBE9IBo8iu3Z3HfADbjWjvEkP2zpIkobVDVnhdBn48AtPAFGXIe\n0YkTqmo3sxfAjLuQ8ZO8BFgy/99DqH814HrGQUVgznaLwxI6BbuPC78L9ats6SG9\neBuDivm54B3sLz1mNt951AA726ruaRg8fFrCLwUQMSLxnH/PWkoQCx34fT8/zRT7\nxn8fwZC9BCrr0G1tZJRY3JHuuuhTDdcoPs5jYZIycJgWssZBeLOzDYiboZGQkrjz\nsG30ANkgUv1Ef/zkm3AW5b6J5DR922AOYVOBXkBnr/77JgcoG+J2gsSsmENgTArp\n6wNCDMInAgMBAAECggEABnImH6mk1Yqg/A/Bl5R/kd+JTpvar37yLDOV4rOl3mhF\nwwpn3kbUn+rauMxJK4gJ50AFCMQd0DXHOsyRHEPZ2sWrJKLrLrk9W2rYiXtvOV9J\nV7m9YGRn94FxUeitqblcRjTyoehdk/pKqRA8FiDB6cSfqhvb01RL1Ka6M6Nkx/Mz\nJ6onn4FGcH/OLGYSX5HjzDQjMqrGESdfdXCLchYIh3JbsSUUMcd52wiSz3Sdh4o3\netFgB3Ja0umE8T8idoXxNq0Ttp9yDMOq8f0x75rdO92me0m/hu/9L4AOKVFnPIAm\niLLr2bEyb8RC4JGRbo0g1tKhK2nsaGjZs0lfF8UEQQKBgQDSKWyGCj1Xr8uipQGL\nPtI6fWKxFL5U17ZkNvtS3M4LnHRjrj5AJdPm2G3DsBvSUvLGY0ruy6RAMW7l+mBI\nttZtqme29s3k4q7plNSPJm4FNC7HjAmYbeMkcBTva4mkzrrX64YDrLtRcJNIM/ut\n6sngWwvZcfBc6X/qs06xQv4S0QKBgQDGrk/AyUBcWUF00Dz6umoTUdL8hqPCre0d\nz0VA9LhaFWdWnC9mhd40qrHV84756f2CiGCD++1UpXH+idTK3pv5RYFoHE+ONxwt\nsw7hSziZ7dVMwbsbDjF2mXK+xdWpya1gtpR8pOQoACL56IentUJA+baS3EC6Jmnd\nxzV8x+STdwKBgQCD+xm5L9MIL1FeCevnS4Nw0e9Zr+I7m+BiHRlGF36aUh3Rv8o+\nNMNXlJGSNBW0xvzJ0+9p+Z9j5Od1LACtiY0t/7b0cxgoZqdb72hxobu0Luo1zN71\nyAS+jFjJZqphQqaaFMHrqt1ULrN/w42J0goHiIXvf5tobgc0GHkR3zV6EQKBgAmy\nsoPnjvOzC6XnEELw3IKq6NCYxd+X284rsuazy1fiWZP5tbqcaDdL6bhW1jDOwigf\n/g4TOwd5t/HDypZIfXaSdPmfACch+4cjiWNn55Bj8ph3kGmGrNVsMhSr1X0fMg5Z\nezAGYHivYQWv2wdNqrk/NzE9/Q7ZFyvTMIIxw6+LAoGATRjg4DtRQPIk/CHt+ZLY\ngSiAhZytFW1yu5AeEGHBZVC4JTvEmNBnq53/NGXJjohX1wBeDDak7qqk7bhxDqtg\nAz0bpDFHphqz96Ky+78MtuGnX+pyZsQ8DjiaJ64FJTxmUha8HzbijIA7N6xrs+/a\n9nT0GxPPiTDla3l96d1Ip3E=\n-----END PRIVATE KEY-----\n",
  "client_email": "animebbg-sheets@animebbg-editor.iam.gserviceaccount.com",
  "client_id": "115397576522399044320",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/animebbg-sheets%40animebbg-editor.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# ---------------- Control de accesos con Google Sheets ----------------

GSCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Carpeta donde está este script
BASE_DIR = Path(__file__).resolve().parent

# Archivo JSON de credenciales (en la misma carpeta que el .py)
GSPREAD_SHEET_ID = "186A5hhWdp0L2y3bCFsTxOfitSmOD1eFKIBlrj6m4lfk"  # ID del Google Sheet

def get_gspread_client():
    """Devuelve un cliente gspread autenticado con la cuenta de servicio usando las credenciales en el código."""
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GSPREAD_CREDS, GSCOPE)
    return gspread.authorize(creds)

def check_user_exists_and_log(username: str) -> bool:
    """
    Verifica si 'username' existe en la hoja 'usuarios'.
    Si existe, registra un log en la hoja 'logs' y devuelve True.
    Si no existe, devuelve False.
    """
    username = username.strip()
    if not username:
        return False

    gc = get_gspread_client()
    sh = gc.open_by_key(GSPREAD_SHEET_ID)

    # Hoja de usuarios (nombres en columna A)
    ws_users = sh.worksheet("usuarios")
    users = ws_users.col_values(1)
    if username not in users:
        return False

    # Hoja de logs
    ws_logs = sh.worksheet("logs")

    # Datos del dispositivo
    hostname = platform.node()
    system_str = platform.platform()

    # IP local (no necesariamente IP pública)
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip_local = "desconocida"

    # Marca de tiempo (UTC)
    now = datetime.utcnow().isoformat(timespec="seconds")

    # Se registra: fecha/hora, usuario, ip, hostname, sistema
    ws_logs.append_row([now, username, ip_local, hostname, system_str])

    return True

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
        ic = QIcon(str(p))
        if not ic.isNull(): return ic
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
    "REV": "AnimeBBG v5.3.2",
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

# ---------------- Utils ----------------
def qcolor_from_hex(s: str, default: str = "#000000") -> QColor:
    try: return QColor(s)
    except Exception: return QColor(default)

def clamp(v, a, b): return max(a, min(v, b))
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
        it.set_locked(st['locked'])

def apply_to_selected(ctx: 'PageContext', items: List['StrokeTextItem'], name: str, apply_fn: Callable[[], None]):
    snap_before = snapshot_styles(items)
    def undo(): restore_from_snapshot(snap_before); ctx.scene.update()
    def redo(): apply_fn(); ctx.scene.update()
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
    # Tipo de relleno: 'solid' | 'linear_gradient' | 'texture'
    fill_type: str = 'solid'
    # Para degradado: lista de (pos, color) stops, pos 0.0-1.0
    gradient_stops: List[Tuple[float, str]] = None
    gradient_angle: int = 0
    # Para textura: ruta a imagen y si se repite (tile) o estira
    texture_path: str = ""
    texture_tile: bool = True
    outline: str = "#FFFFFF"
    outline_width: int = 3
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_dx: int = 2
    shadow_dy: int = 2
    shadow_blur: int = 8
    alignment: str = "center"
    line_spacing: float = 1.2
    background_enabled: bool = False
    background_color: str = "#FFFFFF"
    background_opacity: float = 0.0
    capitalization: str = "mixed"
    def to_qfont(self) -> QFont:
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
_RE_NT = re.compile(r'^\s*N/T\s*:\s*(.+)$', re.IGNORECASE)
_RE_FUERA = re.compile(r'^\s*\*\s*:\s*(.+)$')
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
    for rx, key in [
        (_RE_GLOBO, 'GLOBO'), (_RE_NT, 'N/T'), (_RE_FUERA, 'FUERA_GLOBO'), (_RE_PENS_1, 'PENSAMIENTO'),
        (_RE_PENS_2, 'PENSAMIENTO'), (_RE_CUADRO_1, 'CUADRO'), (_RE_CUADRO_2, 'CUADRO'), (_RE_TITULO, 'TITULO'),
        (_RE_GRITOS, 'GRITOS'), (_RE_GEMIDOS, 'GEMIDOS'), (_RE_ONO, 'ONOMATOPEYAS'), (_RE_NERV, 'TEXTO_NERVIOSO'),
    ]:
        m = rx.match(s)
        if m: return key, m.group(1).strip()
    if s.startswith('N/T:'): return 'N/T', s[4:].lstrip()
    if s.startswith('Globo X:'): return 'GLOBO', s[len('Globo X:'):].lstrip()
    if s.startswith('():'): return 'PENSAMIENTO', s[3:].lstrip()
    if s.startswith('[]:'): return 'CUADRO', s[3:].lstrip()
    if s.startswith('*:'):  return 'FUERA_GLOBO', s[2:].lstrip()
    if s.startswith('""'):  return 'TITULO', s[2:].lstrip()
    return 'GLOBO', s

# ---------------- Ítem de texto ----------------
class StrokeTextItem(QGraphicsTextItem):
    HANDLE_SIZE = 10; ROT_HANDLE_R = 7
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

        self._start_pos = QPointF(0, 0); self._old_text = text
        self._resizing = False; self._resize_start_width = 0.0; self._resize_start_pos = QPointF(0, 0)
        self._resize_alt_scale = False; self._start_font_pt = float(style.font_point_size); self._start_outline = float(style.outline_width)
        self._rotating = False; self._rot_start_angle = 0.0; self._rot_base = 0.0
        self.setFont(style.to_qfont()); self._apply_paragraph_to_doc()
        self.setTextWidth(400); self.apply_shadow(); self.background_enabled = style.background_enabled

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
    def _rot_handle_center(self) -> QPointF:
        br = super().boundingRect(); return QPointF((br.left()+br.right())/2.0, br.top()-14.0)

    def boundingRect(self) -> QRectF:
        rect = super().boundingRect(); pad = self.style.outline_width + 4
        if self.isSelected():
            extra_top = 20; handle_pad = self.HANDLE_SIZE + 2
            rect = rect.adjusted(-pad, -pad - extra_top, pad + handle_pad, pad + handle_pad)
        else:
            rect = rect.adjusted(-pad, -pad, pad, pad)
        return rect

    def paint(self, painter: QPainter, option, widget=None):
        if self.style.background_enabled and self.style.background_opacity > 0:
            br = super().boundingRect()
            c = QColor(qcolor_from_hex(self.style.background_color))
            c.setAlpha(int(clamp(self.style.background_opacity, 0, 1) * 255))
            painter.fillRect(br, c)

        ow = int(max(0, round(float(self.style.outline_width))))
        if ow > 0:
            outline_col = qcolor_from_hex(self.style.outline)
            # Rasterizar el texto una vez con el color de contorno y luego dibujar esa imagen
            # desplazada en los offsets necesarios. Esto evita llamar a super().paint muchas veces
            # (costoso) y suele ser mucho más rápido.
            br = super().boundingRect()
            pad = ow
            img_w = max(1, int(math.ceil(br.width())) + pad * 2)
            img_h = max(1, int(math.ceil(br.height())) + pad * 2)
            img = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
            img.fill(Qt.GlobalColor.transparent)

            img_p = QPainter(img)
            img_p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            # Preparar contexto para que super().paint dibuje en la posición correcta dentro de la imagen
            img_p.translate(pad - br.left(), pad - br.top())
            # Poner color de contorno temporalmente
            prev_color = self.defaultTextColor()
            self.setDefaultTextColor(outline_col)
            super().paint(img_p, option, widget)
            self.setDefaultTextColor(prev_color)
            img_p.end()

            # Dibujar la imagen de contorno muestreada en offsets (densidad limitada)
            max_samples = 11
            if ow <= max_samples:
                step = 1
            else:
                step = max(1, ow // max_samples)

            base_x = br.left() - pad
            base_y = br.top() - pad
            for dx in range(-ow, ow + 1, step):
                for dy in range(-ow, ow + 1, step):
                    if dx == 0 and dy == 0:
                        continue
                    painter.drawImage(QPointF(base_x + dx, base_y + dy), img)

        # Relleno (puede ser sólido, degradado o textura)
        try:
            if getattr(self.style, 'fill_type', 'solid') == 'solid':
                self.setDefaultTextColor(qcolor_from_hex(self.style.fill)); super().paint(painter, option, widget)
            else:
                # Obtener rect y dimensiones
                br = super().boundingRect()
                pad = 2
                w = max(1, int(math.ceil(br.width())))
                h = max(1, int(math.ceil(br.height())))

                mask_img = QImage(w + pad*2, h + pad*2, QImage.Format.Format_ARGB32_Premultiplied)
                mask_img.fill(Qt.GlobalColor.transparent)
                mp = QPainter(mask_img)
                mp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                mp.translate(pad - br.left(), pad - br.top())
                # Dibujar texto en blanco para crear máscara alfa
                prev_col = self.defaultTextColor()
                self.setDefaultTextColor(QColor('white'))
                super().paint(mp, option, widget)
                self.setDefaultTextColor(prev_col)
                mp.end()

                # Crear imagen de relleno
                fill_img = QImage(mask_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
                fill_img.fill(Qt.GlobalColor.transparent)
                fp = QPainter(fill_img)
                fp.setRenderHint(QPainter.RenderHint.Antialiasing, True)

                if self.style.fill_type == 'linear_gradient' and self.style.gradient_stops:
                    # Crear gradiente lineal simple
                    angle = float(getattr(self.style, 'gradient_angle', 0))
                    # Coordenadas para gradiente: de izquierda a derecha por defecto
                    x1 = 0; y1 = 0; x2 = fill_img.width(); y2 = 0
                    # Rotar vector por angle
                    import math as _math
                    rad = _math.radians(angle)
                    cx = fill_img.width()/2; cy = fill_img.height()/2
                    dx = _math.cos(rad) * fill_img.width()/2
                    dy = _math.sin(rad) * fill_img.height()/2
                    x1 = cx - dx; y1 = cy - dy; x2 = cx + dx; y2 = cy + dy
                    grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))
                    stops = getattr(self.style, 'gradient_stops', []) or []
                    # stops expected as list of (pos, hex)
                    for pos, col in stops:
                        try: grad.setColorAt(float(pos), qcolor_from_hex(col))
                        except Exception: pass
                    fp.fillRect(fill_img.rect(), grad)

                elif self.style.fill_type == 'texture' and getattr(self.style, 'texture_path', ''):
                    tp = getattr(self.style, 'texture_path', '')
                    pm = QPixmap(tp) if tp else QPixmap()
                    if not pm.isNull():
                        if getattr(self.style, 'texture_tile', True):
                            brush = QBrush(pm)
                            fp.fillRect(fill_img.rect(), brush)
                        else:
                            # escalar para cubrir
                            s = pm.scaled(fill_img.width(), fill_img.height(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            fp.drawPixmap(0, 0, s)
                    else:
                        fp.fillRect(fill_img.rect(), qcolor_from_hex(self.style.fill))
                else:
                    fp.fillRect(fill_img.rect(), qcolor_from_hex(self.style.fill))

                fp.end()

                # Aplicar máscara alfa: conservar sólo las áreas donde mask_img tiene alfa
                result = QImage(fill_img.size(), QImage.Format.Format_ARGB32_Premultiplied)
                result.fill(Qt.GlobalColor.transparent)
                rp = QPainter(result)
                rp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                rp.drawImage(0, 0, fill_img)
                rp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                rp.drawImage(0, 0, mask_img)
                rp.end()

                # Dibujar resultado en el painter principal
                painter.drawImage(QPointF(br.left()-pad, br.top()-pad), result)
        except Exception:
            # Fallback a comportamiento simple si algo falla
            try:
                self.setDefaultTextColor(qcolor_from_hex(self.style.fill)); super().paint(painter, option, widget)
            except Exception:
                pass

        try:
            if getattr(self, 'ordinal', -1) >= 0 and not getattr(self, '_suppress_overlays', False):
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
                # ===== HANDLES MÁS VISIBLES CON COLORES BRILLANTES =====
                # Color brillante para los handles (amarillo/naranja)
                handle_color = QColor('#FFA500')  # Naranja brillante
                border_color = QColor('white')
                
                # Handle de redimensionamiento (esquina inferior derecha)
                painter.setPen(QPen(border_color, 2))  # Borde blanco
                painter.setBrush(handle_color)
                painter.drawRect(self._handle_rect())
                
                # Handle de rotación (círculo superior)
                c = self._rot_handle_center()
                painter.setPen(QPen(border_color, 2))  # Línea blanca
                painter.drawLine(QPointF((br.left()+br.right())/2.0, br.top()),
                                 QPointF(c.x(), c.y()+self.ROT_HANDLE_R))
                painter.setPen(QPen(border_color, 2))  # Borde blanco del círculo
                painter.setBrush(handle_color)
                painter.drawEllipse(c, self.ROT_HANDLE_R, self.ROT_HANDLE_R)

    def hoverMoveEvent(self, event):
        if self.locked:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor)); super().hoverMoveEvent(event); return
        if self._handle_rect().contains(event.pos()):
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
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
        if self._handle_rect().contains(event.pos()):
            self._resizing = True; self._resize_start_width = self.textWidth()
            self._resize_start_pos = event.pos()
            self._resize_alt_scale = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
            self._start_font_pt = float(self.style.font_point_size); self._start_outline = float(self.style.outline_width)
            event.accept(); return
        c = self._rot_handle_center()
        if (event.pos() - c).manhattanLength() <= self.ROT_HANDLE_R + 3:
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
            cur_angle = math.degrees(math.atan2(
                pos_scene.y()-center_scene.y(), pos_scene.x()-center_scene.x()))
            delta = cur_angle - self._rot_start_angle; new = self._rot_base + delta
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
            if self._handle_rect().contains(event.pos()): event.accept(); return
            c = self._rot_handle_center()
            if (event.pos() - c).manhattanLength() <= self.ROT_HANDLE_R + 3: event.accept(); return
        self._old_text = self.toPlainText()
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        cursor = self.textCursor(); cursor.movePosition(QTextCursor.MoveOperation.End); self.setTextCursor(cursor)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        scene = self.scene()
        if scene and hasattr(scene, 'undo_stack'):
            new = self.toPlainText()
            if new != self._old_text:
                item = self; old = self._old_text; stack = scene.undo_stack
                push_cmd(stack, "Editar texto",
                         lambda: (item.setPlainText(old), item._apply_paragraph_to_doc()),
                         lambda: (item.setPlainText(new), item._apply_paragraph_to_doc()))

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
            'text': self.toPlainText(),
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
        item.setPos(QPointF(*d.get('pos', [0, 0])))
        item.setRotation(float(d.get('rotation', 0.0)))
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

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            acc = accent_qcolor(); br = super().boundingRect()
            painter.setPen(QPen(acc, 1, Qt.PenStyle.DashLine)); painter.drawRect(br)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(acc)
            painter.drawRect(self._handle_rect())

    def hoverMoveEvent(self, event):
        if self._handle_rect().contains(event.pos()):
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor if self.isSelected() else Qt.CursorShape.ArrowCursor))
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if self._handle_rect().contains(event.pos()):
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
        if item.scene() is None: self.scene.addItem(item)
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

    def remove_item_from_list(self, item: StrokeTextItem):
        for i in range(self.layer_list.count()):
            it = self.layer_list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) is item:
                self.layer_list.takeItem(i); break

    def on_layer_selected(self, cur: QListWidgetItem, prev: QListWidgetItem):
        item = self.current_item()
        if not item: return
        for i in range(self.layer_list.count()):
            itw = self.layer_list.item(i); obj: StrokeTextItem = itw.data(Qt.ItemDataRole.UserRole)
            obj.setSelected(obj is item)
        try:
            win = self.window()
            if hasattr(win, "_sync_props_from_item"): win._sync_props_from_item(item)
        except Exception: pass

    def on_scene_selection_changed(self):
        sel = self.scene.selectedItems()
        if not sel: return
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

# ---------------- Ventana principal ----------------
class MangaTextTool(QMainWindow):
    def __init__(self, username: str = ""):
        super().__init__()
        self.currentUser = username
        
        # Obtener factor de escala para UI responsiva
        scale = get_ui_scale_factor()

        self.setWindowTitle("EditorTyperTool – Animebbg")
        self.setWindowIcon(icon('app.ico'))
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

        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self._dark_theme = True

        # Ventana emergente "Nosotros"
        self.about_dialog = AboutDialog(self)

        # Crear UI
        self._build_toolbar()
        self._build_right_panel()
        self._build_raw_dock()
        self.tabs.currentChanged.connect(self._on_tab_changed)

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
        ctx = PageContext(pix, path); idx = self.tabs.addTab(ctx, path.name); self.tabs.setCurrentIndex(idx)
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
        
        # Proceder a cerrar
        self.tabs.removeTab(idx)
        ctx.deleteLater()

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
        lock_sel    = self.add_act(tb, 'pin.png', "Fijar seleccionados • Ctrl+L", self.lock_selected_items, "Ctrl+L")
        lock_all    = self.add_act(tb, 'pin-all.png', "Fijar TODOS en pestaña • Ctrl+Shift+L", self.lock_all_items_current_tab, "Ctrl+Shift+L")
        unlock_sel  = self.add_act(tb, 'unlock.png', "Desbloquear seleccionados • Ctrl+U", self.unlock_selected_items_confirm, "Ctrl+U")

        info = self.add_act(tb, 'help.png', "Ayuda: atajos y consejos", lambda: QMessageBox.information(self, "Ayuda",
            "Workflow Automático (Ctrl+W) → automatiza RAW → Traducción → Imágenes Limpias → Colocación de textos.\n"
            "Ctrl+esquina: escala; círculo superior: rotar.\n"
            "Fijar seleccionados: bloquea movimiento, rotación y resize (sigue seleccionable)."))

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

        subtitle = QLabel("© 2025 – versión 5.3.7.3.1")
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
        self.prop_dock = QDockWidget("Propiedades", self)
        w = QWidget(); layout = QFormLayout(w)
        self.prop_dock.setObjectName("PropDock")

        # Etiqueta del panel
        self.symb_combo = QComboBox(); self.symb_combo.addItems(list(PRESETS.keys())); self.symb_combo.currentIndexChanged.connect(self.on_symbol_changed)
        layout.addRow("Simbología", self.symb_combo)

        self.width_spin = QSpinBox(); self.width_spin.setRange(50, 2000); self.width_spin.valueChanged.connect(self.on_width_changed); layout.addRow("Ancho caja", self.width_spin)

        # Negrita
        self.bold_chk = QCheckBox("Negrita (toda la caja)")
        self.bold_chk.setToolTip("Aplica negrita a toda la caja de texto")
        self.bold_chk.stateChanged.connect(self.on_bold_toggle)
        layout.addRow(self.bold_chk)
        
        # Botón para negrita selectiva
        self.bold_sel_btn = QPushButton("Negrita selectiva (Ctrl+B)")
        self.bold_sel_btn.setToolTip("Haz doble clic en la caja de texto, selecciona el texto que quieres en negrita y presiona este botón o Ctrl+B")
        self.bold_sel_btn.clicked.connect(self.apply_bold_to_current_selection)
        layout.addRow(self.bold_sel_btn)
        
        self.font_btn = QPushButton("Elegir fuente…"); self.font_btn.clicked.connect(self.choose_font); layout.addRow("Fuente (caja)", self.font_btn)
        self.fill_btn = QPushButton("Color texto…"); self.fill_btn.clicked.connect(lambda: self.choose_color('fill')); layout.addRow("Color", self.fill_btn)
        self.out_btn = QPushButton("Color trazo…"); self.out_btn.clicked.connect(lambda: self.choose_color('outline')); layout.addRow("Trazo", self.out_btn)


        self.no_stroke_chk = QCheckBox("Sin trazo"); self.no_stroke_chk.stateChanged.connect(self.on_no_stroke_toggle); layout.addRow(self.no_stroke_chk)
        
        # Grosor trazo con slider
        outw_layout = QHBoxLayout()
        self.outw_slider = QSlider(Qt.Orientation.Horizontal)
        self.outw_slider.setRange(0, 40)
        self.outw_slider.setValue(3)
        self.outw_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.outw_slider.setTickInterval(5)
        self.outw_label = QLabel("3")
        self.outw_label.setMinimumWidth(40)
        self.outw_slider.valueChanged.connect(lambda v: (self.outw_label.setText(str(v)), self.on_outline_width(v)))
        outw_layout.addWidget(self.outw_slider)
        outw_layout.addWidget(self.outw_label)
        layout.addRow("Grosor trazo", outw_layout)


        self.shadow_chk = QCheckBox("Sombra"); self.shadow_chk.stateChanged.connect(self.on_shadow_toggle); layout.addRow(self.shadow_chk)

        self.bg_chk = QCheckBox("Fondo caja"); self.bg_chk.stateChanged.connect(self.on_bg_toggle); layout.addRow(self.bg_chk)
        self.bg_btn = QPushButton("Color fondo…"); self.bg_btn.clicked.connect(lambda: self.choose_color('background_color')); layout.addRow("Color fondo", self.bg_btn)
        self.bg_op = QSlider(Qt.Orientation.Horizontal); self.bg_op.setRange(0,100); self.bg_op.valueChanged.connect(self.on_bg_op); layout.addRow("Opacidad fondo", self.bg_op)

        self.align_combo = QComboBox(); self.align_combo.addItems(["Izquierda", "Centro", "Derecha", "Justificar"]); self.align_combo.setCurrentIndex(1)
        self.align_combo.currentIndexChanged.connect(self.on_alignment_changed); layout.addRow("Alineación", self.align_combo)

        # Interlineado con slider
        linespace_layout = QHBoxLayout()
        self.linespace_slider = QSlider(Qt.Orientation.Horizontal)
        self.linespace_slider.setRange(80, 300)  # 0.8 a 3.0 multiplicado por 100
        self.linespace_slider.setValue(120)  # 1.2 por defecto
        self.linespace_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.linespace_slider.setTickInterval(20)
        self.linespace_label = QLabel("1.20")
        self.linespace_label.setMinimumWidth(40)
        self.linespace_slider.valueChanged.connect(lambda v: (self.linespace_label.setText(f"{v/100:.2f}"), self.on_linespacing_changed(v/100)))
        linespace_layout.addWidget(self.linespace_slider)
        linespace_layout.addWidget(self.linespace_label)
        layout.addRow("Interlineado", linespace_layout)

        # Rotación con slider
        rotate_layout = QHBoxLayout()
        self.rotate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotate_slider.setRange(-180, 180)
        self.rotate_slider.setValue(0)
        self.rotate_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.rotate_slider.setTickInterval(45)
        self.rotate_label = QLabel("0°")
        self.rotate_label.setMinimumWidth(40)
        self.rotate_slider.valueChanged.connect(lambda v: (self.rotate_label.setText(f"{v}°"), self.on_rotation_changed(float(v))))
        rotate_layout.addWidget(self.rotate_slider)
        rotate_layout.addWidget(self.rotate_label)
        layout.addRow("Rotación", rotate_layout)

        self.cap_combo = QComboBox(); self.cap_combo.addItems(["Normal", "MAYÚSCULAS", "minúsculas"])
        self.cap_combo.currentIndexChanged.connect(self.on_capitalization_changed); layout.addRow("Cambiar letras", self.cap_combo)

        # ---- Marca de agua (opcional y persistente) ----
        self.wm_enable_chk = QCheckBox("Usar marca de agua")
        self.wm_enable_chk.toggled.connect(self.on_wm_enable_toggled)
        layout.addRow(self.wm_enable_chk)

        self.wm_pick_btn = QPushButton("Elegir imagen…")
        self.wm_pick_btn.clicked.connect(self.choose_wm_image)
        layout.addRow("Marca de agua", self.wm_pick_btn)

        self.wm_op_slider = QSlider(Qt.Orientation.Horizontal); self.wm_op_slider.setRange(0, 100)
        self.wm_op_slider.valueChanged.connect(self.on_wm_opacity_changed)
        layout.addRow("Opacidad marca", self.wm_op_slider)

        self.prop_dock.setWidget(w); self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.prop_dock)
        try:
            self.prop_dock.visibilityChanged.connect(self._on_prop_visibility_changed)
            for tb in self.findChildren(QToolBar):
                tb.addAction(self.toggle_props_act); break
        except Exception:
            pass
        self._apply_bg_controls_state()

    def _on_prop_visibility_changed(self, visible: bool):
        """Sincroniza la acción del toolbar con el dock de propiedades,
        ignorando cambios cuando la ventana está minimizada.
        """
        if self.isMinimized():
            return
        self.toggle_props_act.blockSignals(True)
        self.toggle_props_act.setChecked(visible)
        self.toggle_props_act.blockSignals(False)

    # ---------------- Acciones principales ----------------
    def open_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Abrir imagen(es) o proyecto(s)", 
            "", 
            "Todos los archivos soportados (*.png *.jpg *.jpeg *.webp *.bbg);;Imágenes (*.png *.jpg *.jpeg *.webp);;Proyectos (*.bbg)"
        )
        if not files: 
            return
        
        # Procesar cada archivo según su extensión
        for f in files:
            file_path = Path(f)
            if file_path.suffix.lower() == '.bbg':
                # Es un archivo .bbg, usar la función de abrir proyecto
                self._open_single_project_bbg(str(file_path))
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
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("Identificadores (opcionales): Globo 1:, N/T:, *:, ():, (texto), []:, [texto].\n`//` crea ANIDADO inline. (Se quita el identificador)."))
        te = QTextEdit(); te.setPlaceholderText("Globo 1: Texto...\n(): Pensamiento\n[Nota en cuadro]")
        te.setPlainText(QGuiApplication.clipboard().text()); v.addWidget(te)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); v.addWidget(bb)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        lines = [ln for ln in te.toPlainText().splitlines() if ln.strip()]
        if not lines: return
        y = 50
        for line in lines:
            preset_key, clean = parse_identifier(line)
            parts = [p.strip() for p in clean.split('//') if p.strip()] or [clean.strip()]
            for idx, seg in enumerate(parts):
                if not seg: continue
                use_preset = preset_key if idx == 0 else 'ANIDADO'
                style = PRESETS.get(use_preset, PRESETS['GLOBO'])
                item = StrokeTextItem(seg, replace(style), name=use_preset)
                item.setFont(item.style.to_qfont()); self._push_add_command(ctx, item, QPointF(50, y)); y += 70

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
            wizard = WorkflowWizard(self)
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
            
            # Store workflow data in context for persistence
            ctx.workflow_data = workflow_data.to_dict()
            
            # Apply watermark if enabled
            self._apply_wm_to_ctx(ctx)
            
            # Place text boxes according to detections
            for detection in workflow_data.detections:
                self._place_text_from_detection(ctx, detection)
            
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
    
    def _place_text_from_detection(self, ctx: 'PageContext', detection: 'TextBoxDetection'):
        """Coloca una caja de texto en el contexto según una detección"""
        # Get the preset style
        style = PRESETS.get(detection.preset, PRESETS['GLOBO'])
        
        # Create the text item
        item = StrokeTextItem(detection.text, replace(style), name=detection.preset)
        item.ordinal = detection.id
        
        # Set position from detection
        rect = detection.get_qrectf()
        item.setPos(QPointF(rect.x(), rect.y()))
        
        # Set width from detection
        item.setTextWidth(rect.width())
        
        # Add to scene and list
        ctx.add_item_and_list(item)
        
        # Apply font
        item.setFont(item.style.to_qfont())
        item._apply_paragraph_to_doc()
        item.apply_shadow()

    # ---------------- Propiedades ----------------
    def _sync_props_from_item(self, item: StrokeTextItem):
        bs = [self.width_spin, self.outw_slider, self.align_combo, self.linespace_slider,
              self.rotate_slider, self.symb_combo, self.no_stroke_chk,
              self.shadow_chk, self.bg_chk, self.bg_op, self.cap_combo, self.bold_chk]
        for w in bs: w.blockSignals(True)

        self.width_spin.setValue(int(item.textWidth()))
        
        # Actualizar slider de grosor trazo
        outw_value = item.style.outline_width
        self.outw_slider.setValue(outw_value)
        self.outw_label.setText(str(outw_value))
        
        self.no_stroke_chk.setChecked(item.style.outline_width == 0); self._apply_no_stroke_enabled_state()

        self.bold_chk.setChecked(bool(item.style.bold))

        align_map = {'left': 0, 'center': 1, 'right': 2, 'justify': 3}
        self.align_combo.setCurrentIndex(align_map.get(item.style.alignment, 1))
        
        # Actualizar sliders
        linespace_value = int(float(item.style.line_spacing) * 100)
        self.linespace_slider.setValue(linespace_value)
        self.linespace_label.setText(f"{linespace_value/100:.2f}")
        
        rotate_value = int(float(item.rotation()))
        self.rotate_slider.setValue(rotate_value)
        self.rotate_label.setText(f"{rotate_value}°")
        self.shadow_chk.setChecked(bool(item.style.shadow_enabled))
        self.bg_chk.setChecked(bool(item.style.background_enabled))
        try: self.bg_op.setValue(int(clamp(item.style.background_opacity, 0, 1)*100))
        except Exception: self.bg_op.setValue(0)

        try: idx = list(PRESETS.keys()).index(item.name)
        except ValueError: idx = 0
        self.symb_combo.setCurrentIndex(idx)

        cap_map_to_idx = {'mixed':0, 'uppercase':1, 'lowercase':2, 'capitalize':3, 'smallcaps':4}
        self.cap_combo.setCurrentIndex(cap_map_to_idx.get(getattr(item.style, 'capitalization', 'mixed'), 0))

        self._apply_bg_controls_state()
        for w in bs: w.blockSignals(False)

    def _apply_no_stroke_enabled_state(self):
        no_stroke = self.no_stroke_chk.isChecked()
        self.outw_slider.setEnabled(not no_stroke)
        self.outw_label.setEnabled(not no_stroke)
        self.out_btn.setEnabled(not no_stroke)

    def _apply_bg_controls_state(self):
        enabled = self.bg_chk.isChecked()
        self.bg_btn.setEnabled(enabled); self.bg_op.setEnabled(enabled)

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
        if not items: return
        base = items[0].style.to_qfont()
        font, ok = QFontDialog.getFont(base, self, "Elegir fuente")
        if not ok: return
        new_family, new_pt, new_bold, new_italic = font.family(), font.pointSize(), font.bold(), font.italic()
        apply_to_selected(ctx, items, "Cambiar fuente (varias)", lambda: [
            setattr(it.style, 'font_family', new_family) or setattr(it.style, 'font_point_size', new_pt) or
            setattr(it.style, 'bold', new_bold) or setattr(it.style, 'italic', new_italic) or
            it.setFont(it.style.to_qfont()) or it._apply_paragraph_to_doc()
            for it in items
        ])
        self._sync_props_from_item(items[0])

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
                else:
                    old = item.style.background_color
                    def undo(): item.style.background_color = old; item.update()
                    def redo(): item.style.background_color = final_color; item.update()
                    push_cmd(ctx.undo_stack, "Cambiar color fondo", undo, redo)
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
                item.update()
                if ctx and ctx.scene:
                    ctx.scene.update()
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
            item.update(); ctx and ctx.scene.update()

        def redo():
            item.style.fill_type = new_spec.get('fill_type', 'solid')
            item.style.fill = new_spec.get('fill', item.style.fill)
            item.style.gradient_stops = new_spec.get('gradient_stops')
            item.style.gradient_angle = int(new_spec.get('gradient_angle', 0))
            item.style.texture_path = new_spec.get('texture_path', '')
            item.style.texture_tile = bool(new_spec.get('texture_tile', True))
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

        self._raw_per_tab: Dict[int, Optional[QPixmap]] = {}

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
        pix = self._raw_per_tab.get(idx); self._set_raw_pixmap(pix)
        # aplica marca de agua al cambiar de pestaña
        ctx = self.tabs.widget(idx)
        if isinstance(ctx, PageContext):
            self._apply_wm_to_ctx(ctx)

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
        idx = self.tabs.currentIndex(); self._raw_per_tab[idx] = pix; self._set_raw_pixmap(pix); self.raw_dock.show()
        self.statusBar().showMessage(f"Referencia RAW cargada: {Path(path).name}")

    def clear_raw_image(self):
        idx = self.tabs.currentIndex()
        if idx in self._raw_per_tab: self._raw_per_tab[idx] = None
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
        self.statusBar().showMessage(f"Proyecto cargado: {Path(fname).name}")
        
        # Guardar la ruta del proyecto para auto-guardar
        self.last_saved_project_path = fname
        
        # Inicializar el tracking de cambios (el proyecto recién abierto no tiene cambios)
        ctx.has_unsaved_changes = False
        ctx.saved_file_path = fname

        # aplica marca de agua si procede
        self._apply_wm_to_ctx(ctx)
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
        prev = [it.toPlainText() for it in items]; new = [sentence_case(t) for t in prev]
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

# ---------------- Diálogo de fuentes por simbología ----------------
class FontsPerPresetDialog(QDialog):
    def __init__(self, parent, presets: Dict[str, TextStyle]):
        super().__init__(parent); self.setWindowTitle("Definir fuentes por simbología"); self.presets = presets
        lay = QVBoxLayout(self); grid = QGridLayout(); lay.addLayout(grid)
        self.font_btns = {}; self.size_spins = {}; row = 0
        for key in presets.keys():
            grid.addWidget(QLabel(key), row, 0)
            btn = QPushButton("Elegir fuente…"); btn.clicked.connect(lambda _, k=key: self.pick_font(k))
            grid.addWidget(btn, row, 1); self.font_btns[key] = btn
            sp = QSpinBox(); sp.setRange(6, 200); sp.setValue(presets[key].font_point_size)
            grid.addWidget(sp, row, 2); self.size_spins[key] = sp; row += 1
        self.apply_chk = QCheckBox("Aplicar a elementos existentes de cada tipo"); lay.addWidget(self.apply_chk)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); lay.addWidget(bb)
    def pick_font(self, k: str):
        cur = self.presets[k].to_qfont(); font, ok = QFontDialog.getFont(cur, self, f"Fuente para {k}")
        if ok: self.presets[k].font_family = font.family()
    def apply_changes(self):
        for k, sp in self.size_spins.items(): self.presets[k].font_point_size = int(sp.value())
        return self.apply_chk.isChecked()


class FillChooserDialog(QDialog):
    """Diálogo sencillo con tres pestañas: Sólido, Degradado (2 stops) y Textura.
    Actualiza la caja de texto en vivo mientras cambias valores (preview en tiempo real).
    """
    def __init__(self, parent, style: TextStyle, on_update_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar relleno")
        self.resize(420, 320)
        self.style = style
        self.on_update_callback = on_update_callback  # Función para notificar cambios
        
        lay = QVBoxLayout(self)
        tabs = QTabWidget()
        lay.addWidget(tabs)

        # -- Solid
        solid_w = QWidget(); solid_l = QVBoxLayout(solid_w)
        solid_info = QLabel("💡 Haz clic en 'Elegir color…' para ver los cambios en tiempo real")
        solid_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        solid_l.addWidget(solid_info)
        self.solid_btn = QPushButton("Elegir color…")
        solid_l.addWidget(self.solid_btn); self.solid_preview = QLabel(); solid_l.addWidget(self.solid_preview)
        solid_l.addStretch()
        tabs.addTab(solid_w, "Sólido")

        # -- Gradient
        grad_w = QWidget(); gl = QFormLayout(grad_w)
        grad_info = QLabel("💡 Haz clic en los botones de color para ver los cambios en tiempo real")
        grad_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        gl.addRow(grad_info)
        self.grad_c1 = QPushButton("Color 1…")
        self.grad_c2 = QPushButton("Color 2…")
        self.grad_angle = QSpinBox(); self.grad_angle.setRange(0, 359); self.grad_angle.setValue(getattr(style, 'gradient_angle', 0))
        gl.addRow("Color inicio", self.grad_c1); gl.addRow("Color fin", self.grad_c2); gl.addRow("Ángulo", self.grad_angle)
        self.grad_preview = QLabel(); gl.addRow(self.grad_preview)
        tabs.addTab(grad_w, "Degradado")

        # -- Texture
        tex_w = QWidget(); tl = QVBoxLayout(tex_w)
        self.tex_pick = QPushButton("Elegir imagen…")
        self.tex_path_lbl = QLabel(getattr(style, 'texture_path', '') or "(ninguna)")
        self.tex_tile_chk = QCheckBox("Repetir (tile)"); self.tex_tile_chk.setChecked(getattr(style, 'texture_tile', True))
        tl.addWidget(self.tex_pick); tl.addWidget(self.tex_path_lbl); tl.addWidget(self.tex_tile_chk)
        self.tex_preview = QLabel(); tl.addWidget(self.tex_preview)
        tl.addStretch()
        tabs.addTab(tex_w, "Textura")

        # Buttons
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); lay.addWidget(bb)

        # Conexiones: actualizar en tiempo real
        self.solid_btn.clicked.connect(self._pick_solid)
        self.grad_c1.clicked.connect(lambda: self._pick_grad_color(1))
        self.grad_c2.clicked.connect(lambda: self._pick_grad_color(2))
        self.grad_angle.valueChanged.connect(lambda: self._notify_update())
        self.tex_pick.clicked.connect(self._pick_texture)
        self.tex_tile_chk.stateChanged.connect(lambda: self._notify_update())

        # estado inicial
        self._solid_color = getattr(style, 'fill', '#000000')
        gs = getattr(style, 'gradient_stops', None) or [(0.0, getattr(style, 'fill', '#000000')), (1.0, getattr(style, 'fill', '#ffffff'))]
        self._grad_stops = gs
        self._grad_angle = int(getattr(style, 'gradient_angle', 0))
        self._tex_path = getattr(style, 'texture_path', '')
        self._tex_tile = bool(getattr(style, 'texture_tile', True))
        self._update_previews()

    def _pick_solid(self):
        dlg = QColorDialog(qcolor_from_hex(self._solid_color), self)
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        
        # Timer para actualizar en vivo mientras el diálogo está abierto
        timer = QTimer()
        def on_color_change():
            cur = dlg.currentColor()
            if cur.isValid():
                self._solid_color = cur.name(QColor.NameFormat.HexRgb)
                self._update_previews()
                self._notify_update()
        
        dlg.currentColorChanged.connect(on_color_change)
        timer.timeout.connect(on_color_change)
        timer.start(50)
        
        result = dlg.exec()
        timer.stop()
        
        if result == QColorDialog.DialogCode.Accepted:
            self._solid_color = dlg.selectedColor().name(QColor.NameFormat.HexRgb)
            self._update_previews()
            self._notify_update()

    def _pick_grad_color(self, which: int):
        cur = qcolor_from_hex(self._grad_stops[0][1] if which == 1 else self._grad_stops[1][1])
        dlg = QColorDialog(cur, self)
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        
        # Timer para actualizar en vivo
        timer = QTimer()
        def on_color_change():
            c = dlg.currentColor()
            if c.isValid():
                col = c.name(QColor.NameFormat.HexRgb)
                if which == 1:
                    self._grad_stops[0] = (0.0, col)
                else:
                    self._grad_stops[1] = (1.0, col)
                self._update_previews()
                self._notify_update()
        
        dlg.currentColorChanged.connect(on_color_change)
        timer.timeout.connect(on_color_change)
        timer.start(50)
        
        result = dlg.exec()
        timer.stop()
        
        if result == QColorDialog.DialogCode.Accepted:
            col = dlg.selectedColor().name(QColor.NameFormat.HexRgb)
            if which == 1:
                self._grad_stops[0] = (0.0, col)
            else:
                self._grad_stops[1] = (1.0, col)
            self._update_previews()
            self._notify_update()

    def _pick_texture(self):
        f, _ = QFileDialog.getOpenFileName(self, "Seleccionar textura", "", "Imágenes (*.png *.jpg *.jpeg *.webp)")
        if not f: return
        self._tex_path = f; self.tex_path_lbl.setText(f)
        self._update_previews()
        self._notify_update()

    def _update_previews(self):
        # Sólido preview
        pm = QPixmap(120, 32); pm.fill(qcolor_from_hex(self._solid_color)); self.solid_preview.setPixmap(pm)
        # Grad preview
        gpm = QPixmap(120, 32); gp = QPainter(gpm); grad = QLinearGradient(0,0,120,0)
        try:
            grad.setColorAt(0.0, qcolor_from_hex(self._grad_stops[0][1])); grad.setColorAt(1.0, qcolor_from_hex(self._grad_stops[1][1]))
        except Exception:
            pass
        gp.fillRect(gpm.rect(), grad); gp.end(); self.grad_preview.setPixmap(gpm)
        # Texture preview
        tpm = QPixmap(120, 32); tpm.fill(Qt.GlobalColor.transparent)
        if self._tex_path:
            pix = QPixmap(self._tex_path)
            if not pix.isNull():
                if self._tex_tile:
                    brush = QBrush(pix)
                    tp = QPainter(tpm); tp.fillRect(tpm.rect(), brush); tp.end()
                else:
                    s = pix.scaled(120, 32, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    tp = QPainter(tpm); tp.drawPixmap(0,0,s); tp.end()
        self.tex_preview.setPixmap(tpm)

    def _notify_update(self):
        """Notifica al callback para actualizar la caja de texto en vivo."""
        if callable(self.on_update_callback):
            try:
                spec = self.get_current_spec()
                self.on_update_callback(spec)
            except Exception:
                pass

    def get_current_spec(self):
        """Devuelve la especificación actual sin cerrar el diálogo."""
        cur_tab = self.findChild(QTabWidget).currentIndex()
        if cur_tab == 0:
            return {'fill_type': 'solid', 'fill': self._solid_color}
        elif cur_tab == 1:
            return {'fill_type': 'linear_gradient', 'gradient_stops': self._grad_stops, 'gradient_angle': int(self.grad_angle.value())}
        else:
            return {'fill_type': 'texture', 'texture_path': self._tex_path, 'texture_tile': bool(self.tex_tile_chk.isChecked())}

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
    
    # Abrir archivos .bbg pasados como argumentos iniciales
    if bbg_files:
        for file_path in bbg_files:
            win._open_single_project_bbg(file_path)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
