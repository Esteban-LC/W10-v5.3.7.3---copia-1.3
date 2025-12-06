# -*- coding: utf-8 -*-
"""
Automated Workflow Module for Manga Translation
Provides a wizard-based workflow for:
1. Scanning RAW images to detect text areas
2. Loading clean images
3. Automatically placing translated text in detected positions
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

from PyQt6.QtCore import Qt, QPointF, QRectF, QSize
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QPixmap, QImage, 
    QFont, QCursor, QKeySequence, QShortcut
)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsTextItem, QFileDialog, QMessageBox,
    QTextEdit, QComboBox, QFormLayout, QWidget, QSplitter,
    QGroupBox, QScrollArea, QFrame, QStackedWidget, QProgressBar
)

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class TextBoxDetection:
    """Represents a detected text box area in the RAW image"""
    id: int
    rect: Dict[str, float]  # {"x": float, "y": float, "width": float, "height": float}
    preset: str = "GLOBO"
    text: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(d: Dict) -> 'TextBoxDetection':
        return TextBoxDetection(**d)
    
    def get_qrectf(self) -> QRectF:
        """Convert to QRectF for Qt graphics"""
        return QRectF(
            self.rect["x"],
            self.rect["y"],
            self.rect["width"],
            self.rect["height"]
        )
    
    def set_from_qrectf(self, rect: QRectF):
        """Update from QRectF"""
        self.rect = {
            "x": rect.x(),
            "y": rect.y(),
            "width": rect.width(),
            "height": rect.height()
        }


@dataclass
class WorkflowData:
    """Complete workflow data"""
    raw_image_path: str = ""
    clean_image_paths: List[str] = None
    detections: List[TextBoxDetection] = None
    
    def __post_init__(self):
        if self.clean_image_paths is None:
            self.clean_image_paths = []
        if self.detections is None:
            self.detections = []
    
    def to_dict(self) -> Dict:
        return {
            "raw_image_path": self.raw_image_path,
            "clean_image_paths": self.clean_image_paths,
            "detections": [d.to_dict() for d in self.detections]
        }
    
    @staticmethod
    def from_dict(d: Dict) -> 'WorkflowData':
        return WorkflowData(
            raw_image_path=d.get("raw_image_path", ""),
            clean_image_paths=d.get("clean_image_paths", []),
            detections=[TextBoxDetection.from_dict(det) for det in d.get("detections", [])]
        )


# ============================================================================
# Graphics Items for Text Area Detection
# ============================================================================

class DetectionBoxItem(QGraphicsRectItem):
    """Interactive rectangle for marking text areas in RAW image"""
    
    def __init__(self, rect: QRectF, detection_id: int, parent=None):
        super().__init__(rect, parent)
        self.detection_id = detection_id
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Visual style
        self.setPen(QPen(QColor("#E11D48"), 2, Qt.PenStyle.SolidLine))
        self.setBrush(QBrush(QColor(225, 29, 72, 50)))  # Semi-transparent red
        
        # Resizing
        self._resizing = False
        self._resize_handle_size = 10
        
    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        
        # Draw ID number
        rect = self.rect()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Circle background
        radius = 15
        center = QPointF(rect.left() + radius + 5, rect.top() + radius + 5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#E11D48'))
        painter.drawEllipse(center, radius, radius)
        
        # Number text
        painter.setPen(QPen(QColor('white')))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius),
            int(Qt.AlignmentFlag.AlignCenter),
            str(self.detection_id)
        )
        
        # Draw resize handle if selected
        if self.isSelected():
            handle_rect = QRectF(
                rect.right() - self._resize_handle_size,
                rect.bottom() - self._resize_handle_size,
                self._resize_handle_size,
                self._resize_handle_size
            )
            painter.setBrush(QColor('#FFA500'))
            painter.setPen(QPen(QColor('white'), 2))
            painter.drawRect(handle_rect)
        
        painter.restore()


# ============================================================================
# Step 1: RAW Image Scanning Dialog
# ============================================================================

class RawScanDialog(QDialog):
    """Dialog for scanning RAW image and marking text areas"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paso 1: Escanear Imagen RAW")
        self.resize(1200, 800)
        
        self.raw_image_path: Optional[str] = None
        self.raw_pixmap: Optional[QPixmap] = None
        self.detections: List[TextBoxDetection] = []
        self._next_id = 1
        self._drawing = False
        self._draw_start = QPointF()
        self._current_box: Optional[DetectionBoxItem] = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📸 Marca las áreas de texto en la imagen RAW")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Main content: Controls (left) + Image viewer (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Controls and list
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        
        # Instructions
        instructions = QLabel(
            "• Haz clic en 'Cargar RAW' para abrir la imagen original\n"
            "• Haz clic y arrastra para marcar cada área de texto\n"
            "• Las áreas se numerarán automáticamente (01, 02, 03...)\n"
            "• Puedes mover y redimensionar las cajas\n"
            "• Asigna el tipo de texto (GLOBO, N/T, etc.) en la lista"
        )
        instructions.setStyleSheet("color: #9ca3af; padding: 5px; font-size: 11px;")
        controls_layout.addWidget(instructions)
        
        # Detected areas label
        areas_label = QLabel("Áreas Detectadas")
        areas_label.setStyleSheet("font-weight: bold; font-size: 13px; padding-top: 10px;")
        controls_layout.addWidget(areas_label)
        
        # Detection list
        self.detection_list = QListWidget()
        self.detection_list.currentRowChanged.connect(self._on_detection_selected)
        controls_layout.addWidget(self.detection_list)
        
        # Preset selector for current detection
        preset_group = QGroupBox("Tipo de Texto")
        preset_layout = QFormLayout(preset_group)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "GLOBO", "N/T", "FUERA_GLOBO", "PENSAMIENTO", "CUADRO",
            "TITULO", "GRITOS", "GEMIDOS", "ONOMATOPEYAS", "TEXTO_NERVIOSO", "ANIDADO"
        ])
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addRow("Preset:", self.preset_combo)
        controls_layout.addWidget(preset_group)
        
        # Action buttons
        btn_layout = QVBoxLayout()
        delete_btn = QPushButton("🗑️ Eliminar Seleccionada")
        delete_btn.clicked.connect(self._delete_selected)
        clear_btn = QPushButton("🧹 Limpiar Todo")
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(clear_btn)
        controls_layout.addLayout(btn_layout)
        
        controls_layout.addStretch()
        splitter.addWidget(controls_widget)
        
        # Right: Image viewer
        viewer_widget = QWidget()
        viewer_layout = QVBoxLayout(viewer_widget)
        viewer_layout.setContentsMargins(10, 10, 10, 10)
        
        # Load button at top - centered
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        load_btn = QPushButton("📂 Cargar imagen RAW")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #F97316;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #EA580C;
            }
        """)
        load_btn.clicked.connect(self._load_raw_image)
        btn_container.addWidget(load_btn)
        btn_container.addStretch()
        viewer_layout.addLayout(btn_container)
        
        # Graphics view - much larger
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setMinimumHeight(600)  # Minimum height for image viewer
        viewer_layout.addWidget(self.view)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_in_btn = QPushButton("🔍 Zoom +")
        zoom_in_btn.clicked.connect(lambda: self.view.scale(1.2, 1.2))
        zoom_out_btn = QPushButton("🔍 Zoom -")
        zoom_out_btn.clicked.connect(lambda: self.view.scale(1/1.2, 1/1.2))
        zoom_reset_btn = QPushButton("🔄 Reset")
        zoom_reset_btn.clicked.connect(lambda: self.view.resetTransform())
        zoom_layout.addWidget(zoom_in_btn)
        zoom_layout.addWidget(zoom_out_btn)
        zoom_layout.addWidget(zoom_reset_btn)
        zoom_layout.addStretch()
        viewer_layout.addLayout(zoom_layout)
        
        splitter.addWidget(viewer_widget)
        
        # Set splitter sizes: left panel much smaller (300px), right panel much larger (900px)
        splitter.setSizes([300, 900])
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        self.next_btn = QPushButton("Siguiente →")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.accept)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #E11D48;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #BE123C;
            }
            QPushButton:disabled {
                background-color: #6B7280;
            }
        """)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.next_btn)
        layout.addLayout(button_layout)
        
        # Install event filter for drawing
        self.view.viewport().installEventFilter(self)
        
    def _load_raw_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Imagen RAW",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.webp)"
        )
        
        if not file_path:
            return
        
        self.raw_image_path = file_path
        self.raw_pixmap = QPixmap(file_path)
        
        if self.raw_pixmap.isNull():
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen")
            return
        
        # Clear scene and add image
        self.scene.clear()
        self.scene.addPixmap(self.raw_pixmap)
        self.scene.setSceneRect(QRectF(self.raw_pixmap.rect()))
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        self.next_btn.setEnabled(False)
        
    def eventFilter(self, obj, event):
        """Handle mouse events for drawing detection boxes"""
        if obj == self.view.viewport() and self.raw_pixmap is not None:
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    scene_pos = self.view.mapToScene(event.pos())
                    if self.scene.sceneRect().contains(scene_pos):
                        self._drawing = True
                        self._draw_start = scene_pos
                        return True
                        
            elif event.type() == event.Type.MouseMove:
                if self._drawing:
                    scene_pos = self.view.mapToScene(event.pos())
                    rect = QRectF(self._draw_start, scene_pos).normalized()
                    
                    # Remove temporary box if exists
                    if self._current_box and self._current_box.scene():
                        self.scene.removeItem(self._current_box)
                    
                    # Create temporary box
                    self._current_box = DetectionBoxItem(rect, self._next_id)
                    self.scene.addItem(self._current_box)
                    return True
                    
            elif event.type() == event.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton and self._drawing:
                    self._drawing = False
                    
                    if self._current_box:
                        rect = self._current_box.rect()
                        
                        # Only create if box is large enough
                        if rect.width() > 20 and rect.height() > 20:
                            self._add_detection(rect)
                        else:
                            self.scene.removeItem(self._current_box)
                        
                        self._current_box = None
                    return True
        
        return super().eventFilter(obj, event)
    
    def _add_detection(self, rect: QRectF):
        """Add a new detection"""
        detection = TextBoxDetection(
            id=self._next_id,
            rect={
                "x": rect.x(),
                "y": rect.y(),
                "width": rect.width(),
                "height": rect.height()
            },
            preset="GLOBO"
        )
        
        self.detections.append(detection)
        self._next_id += 1
        
        # Add to list
        item = QListWidgetItem(f"{detection.id:02d} · {detection.preset}")
        item.setData(Qt.ItemDataRole.UserRole, detection)
        self.detection_list.addItem(item)
        
        self.next_btn.setEnabled(len(self.detections) > 0)
        
    def _on_detection_selected(self, row: int):
        """Handle detection selection from list"""
        if row < 0:
            return
        
        item = self.detection_list.item(row)
        detection = item.data(Qt.ItemDataRole.UserRole)
        
        # Update preset combo
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentText(detection.preset)
        self.preset_combo.blockSignals(False)
        
        # Highlight in scene
        for scene_item in self.scene.items():
            if isinstance(scene_item, DetectionBoxItem):
                scene_item.setSelected(scene_item.detection_id == detection.id)
    
    def _on_preset_changed(self, preset: str):
        """Update preset for current detection"""
        row = self.detection_list.currentRow()
        if row < 0:
            return
        
        item = self.detection_list.item(row)
        detection = item.data(Qt.ItemDataRole.UserRole)
        detection.preset = preset
        
        # Update list item text
        item.setText(f"{detection.id:02d} · {detection.preset}")
    
    def _delete_selected(self):
        """Delete selected detection"""
        row = self.detection_list.currentRow()
        if row < 0:
            return
        
        item = self.detection_list.takeItem(row)
        detection = item.data(Qt.ItemDataRole.UserRole)
        
        # Remove from detections list
        self.detections = [d for d in self.detections if d.id != detection.id]
        
        # Remove from scene
        for scene_item in self.scene.items():
            if isinstance(scene_item, DetectionBoxItem) and scene_item.detection_id == detection.id:
                self.scene.removeItem(scene_item)
                break
        
        self.next_btn.setEnabled(len(self.detections) > 0)
    
    def _clear_all(self):
        """Clear all detections"""
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Eliminar todas las áreas detectadas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.detections.clear()
            self.detection_list.clear()
            
            # Remove all boxes from scene
            for item in list(self.scene.items()):
                if isinstance(item, DetectionBoxItem):
                    self.scene.removeItem(item)
            
            self._next_id = 1
            self.next_btn.setEnabled(False)
    
    def get_data(self) -> Tuple[str, List[TextBoxDetection]]:
        """Return RAW image path and detections"""
        return self.raw_image_path, self.detections


# ============================================================================
# Step 2: Translation Input Dialog
# ============================================================================

class TranslationInputDialog(QDialog):
    """Dialog for inputting translations"""
    
    def __init__(self, detections: List[TextBoxDetection], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paso 2: Ingresar Traducciones")
        self.resize(800, 600)
        
        self.detections = detections
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("✍️ Ingresa los textos traducidos")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "• Pega un texto por línea, en orden numérico (01, 02, 03...)\n"
            "• Puedes usar identificadores opcionales: 'Globo 1:', 'N/T:', etc.\n"
            "• El preview muestra cómo se asignarán los textos"
        )
        instructions.setStyleSheet("color: #9ca3af; padding: 5px 10px;")
        layout.addWidget(instructions)
        
        # Splitter: Input + Preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Text input
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        input_label = QLabel("Textos Traducidos:")
        input_label.setStyleSheet("font-weight: bold;")
        input_layout.addWidget(input_label)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Línea 1 para área 01\n"
            "Línea 2 para área 02\n"
            "Línea 3 para área 03\n"
            "..."
        )
        self.text_input.textChanged.connect(self._update_preview)
        input_layout.addWidget(self.text_input)
        
        splitter.addWidget(input_widget)
        
        # Right: Preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(preview_label)
        
        self.preview_list = QListWidget()
        preview_layout.addWidget(self.preview_list)
        
        splitter.addWidget(preview_widget)
        splitter.setSizes([450, 450])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        back_btn = QPushButton("← Atrás")
        back_btn.clicked.connect(self.reject)
        
        self.apply_btn = QPushButton("Siguiente →")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.accept)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #E11D48;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #BE123C;
            }
            QPushButton:disabled {
                background-color: #6B7280;
            }
        """)
        
        button_layout.addWidget(back_btn)
        button_layout.addWidget(self.apply_btn)
        layout.addLayout(button_layout)
        
        # Initial preview
        self._update_preview()
    
    def _update_preview(self):
        """Update preview list"""
        self.preview_list.clear()
        
        lines = [line.strip() for line in self.text_input.toPlainText().splitlines() if line.strip()]
        
        for i, detection in enumerate(self.detections):
            text = lines[i] if i < len(lines) else ""
            detection.text = text
            
            # Create preview item
            status = "✅" if text else "⚠️"
            item_text = f"{status} {detection.id:02d} · {detection.preset} → {text[:50]}{'...' if len(text) > 50 else ''}"
            
            item = QListWidgetItem(item_text)
            if not text:
                item.setForeground(QColor("#EF4444"))
            
            self.preview_list.addItem(item)
        
        # Enable apply button if all detections have text
        all_filled = all(d.text for d in self.detections)
        self.apply_btn.setEnabled(all_filled)
    
    def get_detections(self) -> List[TextBoxDetection]:
        """Return detections with assigned texts"""
        return self.detections


# ============================================================================
# Step 3: Clean Images Selection Dialog
# ============================================================================

class CleanImagesDialog(QDialog):
    """Dialog for selecting clean images"""
    
    def __init__(self, raw_image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paso 3: Cargar Imágenes Limpias")
        self.resize(800, 600)
        
        self.raw_image_path = raw_image_path
        self.clean_image_paths: List[str] = []
        
        # Get RAW image dimensions for validation
        raw_pixmap = QPixmap(raw_image_path)
        self.raw_size = raw_pixmap.size() if not raw_pixmap.isNull() else QSize(0, 0)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🖼️ Selecciona las imágenes limpias (sin texto)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Info
        info = QLabel(
            f"Imagen RAW: {Path(self.raw_image_path).name}\n"
            f"Dimensiones: {self.raw_size.width()} x {self.raw_size.height()} px"
        )
        info.setStyleSheet("color: #9ca3af; padding: 5px 10px;")
        layout.addWidget(info)
        
        # Add button
        add_btn = QPushButton("➕ Agregar Imágenes Limpias")
        add_btn.clicked.connect(self._add_images)
        layout.addWidget(add_btn)
        
        # Image list
        self.image_list = QListWidget()
        layout.addWidget(self.image_list)
        
        # Remove button
        remove_btn = QPushButton("🗑️ Eliminar Seleccionada")
        remove_btn.clicked.connect(self._remove_selected)
        layout.addWidget(remove_btn)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        back_btn = QPushButton("← Atrás")
        back_btn.clicked.connect(self.reject)
        
        self.next_btn = QPushButton("✅ Aplicar y Finalizar")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.accept)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #6B7280;
            }
        """)
        
        button_layout.addWidget(back_btn)
        button_layout.addWidget(self.next_btn)
        layout.addLayout(button_layout)
    
    def _add_images(self):
        """Add clean images"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Imágenes Limpias",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.webp)"
        )
        
        if not files:
            return
        
        for file_path in files:
            # Validate dimensions
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                continue
            
            # Optional: warn if dimensions don't match
            if pixmap.size() != self.raw_size:
                reply = QMessageBox.question(
                    self,
                    "Dimensiones diferentes",
                    f"La imagen {Path(file_path).name} tiene dimensiones diferentes a la RAW.\n"
                    f"RAW: {self.raw_size.width()}x{self.raw_size.height()}\n"
                    f"Esta: {pixmap.width()}x{pixmap.height()}\n\n"
                    "¿Continuar de todas formas?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    continue
            
            self.clean_image_paths.append(file_path)
            item = QListWidgetItem(f"📄 {Path(file_path).name}")
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.image_list.addItem(item)
        
        self.next_btn.setEnabled(len(self.clean_image_paths) > 0)
    
    def _remove_selected(self):
        """Remove selected image"""
        row = self.image_list.currentRow()
        if row < 0:
            return
        
        item = self.image_list.takeItem(row)
        file_path = item.data(Qt.ItemDataRole.UserRole)
        self.clean_image_paths.remove(file_path)
        
        self.next_btn.setEnabled(len(self.clean_image_paths) > 0)
    
    def get_clean_paths(self) -> List[str]:
        """Return list of clean image paths"""
        return self.clean_image_paths


# ============================================================================
# Main Workflow Wizard
# ============================================================================

class WorkflowWizard(QDialog):
    """Main wizard that orchestrates the 3-step workflow"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Workflow Automático de Traducción")
        self.setModal(True)
        
        self.workflow_data = WorkflowData()
        
    def run(self) -> Optional[WorkflowData]:
        """Run the complete workflow, returns WorkflowData if successful"""
        
        # Step 1: RAW Scan
        raw_dialog = RawScanDialog(self.parent())
        if raw_dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        
        raw_path, detections = raw_dialog.get_data()
        if not raw_path or not detections:
            return None
        
        self.workflow_data.raw_image_path = raw_path
        self.workflow_data.detections = detections
        
        # Step 2: Translations
        trans_dialog = TranslationInputDialog(detections, self.parent())
        if trans_dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        
        final_detections = trans_dialog.get_detections()
        self.workflow_data.detections = final_detections
        
        # Step 3: Clean Images
        clean_dialog = CleanImagesDialog(raw_path, self.parent())
        if clean_dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        
        clean_paths = clean_dialog.get_clean_paths()
        if not clean_paths:
            return None
        
        self.workflow_data.clean_image_paths = clean_paths
        
        return self.workflow_data
