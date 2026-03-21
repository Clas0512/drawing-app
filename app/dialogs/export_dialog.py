"""
Export Dialog module - Dialog for configuring export options.

Allows users to set export format, dimensions, and background options.
"""

from typing import Tuple, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QSpinBox, QCheckBox, QPushButton, QComboBox, QColorDialog,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class ExportDialog(QDialog):
    """
    Dialog for configuring export settings.
    
    Allows users to choose:
    - Export format (PNG, JPEG, SVG)
    - Image dimensions
    - Background color/transparency
    - Quality settings
    """
    
    def __init__(self, parent=None, default_width: int = 1920, default_height: int = 1080):
        super().__init__(parent)
        self.setWindowTitle("Export Image")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.default_width = default_width
        self.default_height = default_height
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QHBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "SVG"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addWidget(format_group)
        
        # Dimensions
        dims_group = QGroupBox("Dimensions")
        dims_layout = QVBoxLayout(dims_group)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 10000)
        self.width_spin.setValue(self.default_width)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 10000)
        self.height_spin.setValue(self.default_height)
        size_layout.addWidget(self.height_spin)
        
        size_layout.addStretch()
        dims_layout.addLayout(size_layout)
        
        # Presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))
        
        for name, w, h in [
            ("HD", 1920, 1080),
            ("4K", 3840, 2160),
            ("A4", 2480, 3508),
            ("Square", 2000, 2000),
        ]:
            btn = QPushButton(name)
            btn.setFixedWidth(60)
            btn.clicked.connect(lambda checked, w=w, h=h: self._set_size(w, h))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        dims_layout.addLayout(presets_layout)
        
        layout.addWidget(dims_group)
        
        # Background options
        bg_group = QGroupBox("Background")
        bg_layout = QVBoxLayout(bg_group)
        
        self.bg_group = QButtonGroup(self)
        
        self.transparent_btn = QRadioButton("Transparent (PNG/SVG only)")
        self.transparent_btn.setChecked(True)
        self.bg_group.addButton(self.transparent_btn)
        bg_layout.addWidget(self.transparent_btn)
        
        white_layout = QHBoxLayout()
        self.white_btn = QRadioButton("White")
        self.bg_group.addButton(self.white_btn)
        white_layout.addWidget(self.white_btn)
        
        self.custom_btn = QRadioButton("Custom:")
        self.bg_group.addButton(self.custom_btn)
        white_layout.addWidget(self.custom_btn)
        
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(30, 30)
        self.bg_color = QColor('#FFFFFF')
        self.bg_color_btn.setStyleSheet(
            f"background-color: {self.bg_color.name()}; border: 1px solid #333;"
        )
        self.bg_color_btn.clicked.connect(self._choose_bg_color)
        white_layout.addWidget(self.bg_color_btn)
        
        white_layout.addStretch()
        bg_layout.addLayout(white_layout)
        
        layout.addWidget(bg_group)
        
        # JPEG quality
        self.quality_group = QGroupBox("Quality")
        quality_layout = QHBoxLayout(self.quality_group)
        quality_layout.addWidget(QLabel("JPEG Quality:"))
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        quality_layout.addWidget(self.quality_spin)
        quality_layout.addStretch()
        
        layout.addWidget(self.quality_group)
        self.quality_group.setVisible(False)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
    
    def _on_format_changed(self, format: str):
        """Handle format change."""
        self.quality_group.setVisible(format == "JPEG")
        self.transparent_btn.setEnabled(format in ["PNG", "SVG"])
        if format == "JPEG":
            self.white_btn.setChecked(True)
    
    def _set_size(self, width: int, height: int):
        """Set image dimensions."""
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
    
    def _choose_bg_color(self):
        """Open color dialog for background."""
        color = QColorDialog.getColor(self.bg_color, self, "Background Color")
        if color.isValid():
            self.bg_color = color
            self.bg_color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #333;"
            )
            self.custom_btn.setChecked(True)
    
    def get_settings(self) -> dict:
        """Get export settings."""
        return {
            'format': self.format_combo.currentText(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'transparent': self.transparent_btn.isChecked(),
            'background_color': self.bg_color,
            'quality': self.quality_spin.value(),
        }
