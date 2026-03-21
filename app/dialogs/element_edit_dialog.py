"""
Element Edit Dialog - Dialog for editing drawing elements.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QColorDialog,
    QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from app.core.layer import DrawingElement


class ElementEditDialog(QDialog):
    """
    Dialog for editing drawing element properties.
    
    Supports editing:
    - Text: content, font size, color, bold, italic
    - Shapes: border color, fill color
    - All: general properties
    """
    
    def __init__(self, element: DrawingElement, parent=None):
        super().__init__(parent)
        self.element = element
        self.setWindowTitle(f"Edit {element.element_type.capitalize()}")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._init_ui()
        self._load_element_properties()
    
    def _init_ui(self):
        """Initialize the UI based on element type."""
        layout = QVBoxLayout(self)
        
        if self.element.element_type in ['text', 'list']:
            self._init_text_ui(layout)
        elif self.element.element_type in ['rectangle', 'box', 'ellipse']:
            self._init_shape_ui(layout)
        else:
            self._init_generic_ui(layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
    
    def _init_text_ui(self, layout):
        """Initialize UI for text elements."""
        text_group = QGroupBox("Text Properties")
        text_layout = QVBoxLayout(text_group)
        
        # Content
        content_layout = QHBoxLayout()
        content_layout.addWidget(QLabel("Content:"))
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(80)
        content_layout.addWidget(self.content_edit)
        text_layout.addLayout(content_layout)
        
        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Font Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(14)
        size_layout.addWidget(self.font_size_spin)
        size_layout.addStretch()
        text_layout.addLayout(size_layout)
        
        # Style presets
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Normal", "Heading", "Title", "Subtitle", "Quote", "Code"])
        style_layout.addWidget(self.style_combo)
        style_layout.addStretch()
        text_layout.addLayout(style_layout)
        
        # Formatting
        format_layout = QHBoxLayout()
        self.bold_cb = QCheckBox("Bold")
        self.italic_cb = QCheckBox("Italic")
        self.underline_cb = QCheckBox("Underline")
        format_layout.addWidget(self.bold_cb)
        format_layout.addWidget(self.italic_cb)
        format_layout.addWidget(self.underline_cb)
        format_layout.addStretch()
        text_layout.addLayout(format_layout)
        
        # Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(40, 25)
        self.color_btn.clicked.connect(self._choose_text_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        text_layout.addLayout(color_layout)
        
        layout.addWidget(text_group)
    
    def _init_shape_ui(self, layout):
        """Initialize UI for shape elements."""
        shape_group = QGroupBox("Shape Properties")
        shape_layout = QVBoxLayout(shape_group)
        
        # Border color
        border_layout = QHBoxLayout()
        border_layout.addWidget(QLabel("Border Color:"))
        self.border_color_btn = QPushButton()
        self.border_color_btn.setFixedSize(40, 25)
        self.border_color_btn.clicked.connect(self._choose_border_color)
        border_layout.addWidget(self.border_color_btn)
        border_layout.addStretch()
        shape_layout.addLayout(border_layout)
        
        # Fill color
        fill_layout = QHBoxLayout()
        fill_layout.addWidget(QLabel("Fill Color:"))
        self.fill_color_btn = QPushButton()
        self.fill_color_btn.setFixedSize(40, 25)
        self.fill_color_btn.clicked.connect(self._choose_fill_color)
        fill_layout.addWidget(self.fill_color_btn)
        
        self.no_fill_cb = QCheckBox("No Fill")
        self.no_fill_cb.stateChanged.connect(self._on_no_fill)
        fill_layout.addWidget(self.no_fill_cb)
        fill_layout.addStretch()
        shape_layout.addLayout(fill_layout)
        
        # Border width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Border Width:"))
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(1, 20)
        self.border_width_spin.setValue(2)
        width_layout.addWidget(self.border_width_spin)
        width_layout.addStretch()
        shape_layout.addLayout(width_layout)
        
        layout.addWidget(shape_group)
    
    def _init_generic_ui(self, layout):
        """Initialize UI for other elements."""
        info = QLabel(f"Element type: {self.element.element_type}")
        layout.addWidget(info)
    
    def _load_element_properties(self):
        """Load current element properties into UI."""
        style = self.element.style
        
        if self.element.element_type in ['text', 'list']:
            self.content_edit.setText(self.element.text)
            self.font_size_spin.setValue(style.get('font_size', 14))
            
            style_preset = style.get('text_style', 'normal')
            idx = self.style_combo.findText(style_preset.capitalize())
            if idx >= 0:
                self.style_combo.setCurrentIndex(idx)
            
            self.bold_cb.setChecked(style.get('bold', False))
            self.italic_cb.setChecked(style.get('italic', False))
            self.underline_cb.setChecked(style.get('underline', False))
            
            color = QColor(style.get('color', style.get('pen_color', '#000000')))
            self.text_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #333;")
        
        elif self.element.element_type in ['rectangle', 'box', 'ellipse']:
            border_color = QColor(style.get('pen_color', '#000000'))
            self.border_color = border_color
            self.border_color_btn.setStyleSheet(f"background-color: {border_color.name()}; border: 1px solid #333;")
            
            fill_color = QColor(style.get('fill_color', '#FFFFFF'))
            self.fill_color = fill_color
            fill_alpha = style.get('fill_alpha', 200)
            self.fill_color_btn.setStyleSheet(f"background-color: {fill_color.name()}; border: 1px solid #333;")
            
            self.no_fill_cb.setChecked(fill_alpha == 0)
            self.border_width_spin.setValue(style.get('pen_width', 2))
    
    def _choose_text_color(self):
        """Open color dialog for text color."""
        color = QColorDialog.getColor(getattr(self, 'text_color', QColor('#000000')), self)
        if color.isValid():
            self.text_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #333;")
    
    def _choose_border_color(self):
        """Open color dialog for border color."""
        color = QColorDialog.getColor(getattr(self, 'border_color', QColor('#000000')), self)
        if color.isValid():
            self.border_color = color
            self.border_color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #333;")
    
    def _choose_fill_color(self):
        """Open color dialog for fill color."""
        color = QColorDialog.getColor(getattr(self, 'fill_color', QColor('#FFFFFF')), self)
        if color.isValid():
            self.fill_color = color
            self.fill_color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #333;")
            self.no_fill_cb.setChecked(False)
    
    def _on_no_fill(self, state):
        """Handle no fill checkbox."""
        self.fill_color_btn.setEnabled(state != Qt.Checked)
    
    def apply_changes(self):
        """Apply dialog changes to the element."""
        style = self.element.style.copy()
        
        if self.element.element_type in ['text', 'list']:
            self.element.set_text(self.content_edit.toPlainText())
            style['font_size'] = self.font_size_spin.value()
            style['text_style'] = self.style_combo.currentText().lower()
            style['bold'] = self.bold_cb.isChecked()
            style['italic'] = self.italic_cb.isChecked()
            style['underline'] = self.underline_cb.isChecked()
            style['color'] = self.text_color.name()
        
        elif self.element.element_type in ['rectangle', 'box', 'ellipse']:
            style['pen_color'] = self.border_color.name()
            style['fill_color'] = self.fill_color.name()
            style['fill_alpha'] = 0 if self.no_fill_cb.isChecked() else 200
            style['pen_width'] = self.border_width_spin.value()
        
        self.element.style = style
