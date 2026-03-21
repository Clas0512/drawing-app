"""
Toolbar module - Main toolbar with tools, styles, and options.

Provides UI for:
- Drawing tool selection
- Color selection
- Pen width selection
- Text styles (bold, italic, heading, etc.)
- List types
- Grid toggle
- Zoom controls
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QToolButton, QButtonGroup,
    QLabel, QSpinBox, QSlider, QPushButton, QColorDialog,
    QGroupBox, QFrame, QComboBox, QCheckBox, QToolBar, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QIcon, QPainter, QBrush, QPen, QPixmap

from app.core.tool_manager import ToolManager
from app.core.style import DrawingStyle, TextStyle


class ColorButton(QToolButton):
    """Button that displays and allows selecting a color."""
    
    color_changed = pyqtSignal(QColor)
    
    def __init__(self, color: QColor = None, parent=None):
        super().__init__(parent)
        self._color = color if color else QColor('#000000')
        self.setFixedSize(40, 40)
        self.clicked.connect(self._choose_color)
        self._update_style()
    
    def _update_style(self):
        """Update button style to show color."""
        self.setStyleSheet(
            f"QToolButton {{ background-color: {self._color.name()}; "
            "border: 2px solid #333; border-radius: 4px; }}"
            "QToolButton:hover { border-color: #666; }"
        )
    
    def _choose_color(self):
        """Open color dialog."""
        color = QColorDialog.getColor(self._color, self, "Choose Color")
        if color.isValid():
            self.set_color(color)
    
    def set_color(self, color: QColor):
        """Set the current color."""
        self._color = color
        self._update_style()
        self.color_changed.emit(color)
    
    def get_color(self) -> QColor:
        """Get current color."""
        return self._color


class PenWidthWidget(QWidget):
    """Widget for selecting pen width."""
    
    width_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Width:"))
        
        self.spinbox = QSpinBox()
        self.spinbox.setRange(1, 100)
        self.spinbox.setValue(2)
        self.spinbox.valueChanged.connect(self.width_changed.emit)
        layout.addWidget(self.spinbox)
        
        # Quick width buttons
        for width in [1, 2, 4, 8]:
            btn = QToolButton()
            btn.setText(f"{width}")
            btn.setFixedSize(30, 30)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, w=width: self.spinbox.setValue(w))
            layout.addWidget(btn)
    
    def set_width(self, width: int):
        """Set current width."""
        self.spinbox.setValue(width)
    
    def get_width(self) -> int:
        """Get current width."""
        return self.spinbox.value()


class ToolToolbar(QWidget):
    """
    Main toolbar widget with all drawing tools and style options.
    
    Provides:
    - Tool selection buttons
    - Color picker
    - Pen width control
    - Text style options
    - List type options
    - View options (grid, zoom)
    """
    
    def __init__(self, tool_manager: ToolManager):
        super().__init__()
        self.tool_manager = tool_manager
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Tools section
        tools_group = QGroupBox("Tools")
        tools_layout = QHBoxLayout(tools_group)
        tools_layout.setSpacing(2)
        
        self.tool_buttons = {}
        self.tool_button_group = QButtonGroup()
        self.tool_button_group.setExclusive(True)
        
        # Tool definitions with icons
        tools = [
            ("Pen", "✏️", "P"),
            ("Line", "📏", "L"),
            ("Rectangle", "⬜", "R"),
            ("Ellipse", "⬭", "E"),
            ("Arrow", "➡️", "A"),
            ("Box", "📦", "B"),
            ("Text", "T", "T"),
            ("List", "☰", "I"),
            ("Select", "🖐️", "S"),
            ("Eraser", "🧹", "E"),
        ]
        
        for name, icon, shortcut in tools:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(f"{name} ({shortcut})")
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            btn.setFont(btn.font())
            # Store tool name on button for identification
            btn.setProperty("tool_name", name)
            btn.clicked.connect(self._on_tool_button_clicked)
            
            self.tool_buttons[name] = btn
            self.tool_button_group.addButton(btn)
            tools_layout.addWidget(btn)
        
        # Set default tool
        if "Pen" in self.tool_buttons:
            self.tool_buttons["Pen"].setChecked(True)
        
        layout.addWidget(tools_group)
        
        # Colors section
        colors_group = QGroupBox("Colors")
        colors_layout = QHBoxLayout(colors_group)
        
        self.color_button = ColorButton(QColor('#000000'))
        self.color_button.color_changed.connect(self.tool_manager.set_color)
        colors_layout.addWidget(self.color_button)
        
        # Quick color palette
        palette_colors = [
            '#000000', '#FFFFFF', '#FF0000', '#00FF00',
            '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
            '#FFA500', '#800080', '#808080', '#A52A2A',
        ]
        
        for hex_color in palette_colors:
            btn = QToolButton()
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(
                f"QToolButton {{ background-color: {hex_color}; "
                "border: 1px solid #333; border-radius: 2px; }}"
            )
            btn.setProperty("color", hex_color)
            btn.clicked.connect(self._on_color_button_clicked)
            colors_layout.addWidget(btn)
        
        colors_layout.addStretch()
        layout.addWidget(colors_group)
        
        # Pen width section
        width_group = QGroupBox("Pen Width")
        width_layout = QHBoxLayout(width_group)
        
        self.width_widget = PenWidthWidget()
        self.width_widget.width_changed.connect(self.tool_manager.set_pen_width)
        width_layout.addWidget(self.width_widget)
        
        layout.addWidget(width_group)
        
        # Text styles section
        text_group = QGroupBox("Text Styles")
        text_layout = QVBoxLayout(text_group)
        
        # Style preset combo
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))
        self.text_style_combo = QComboBox()
        self.text_style_combo.addItems([
            "Normal", "Heading", "Title", "Subtitle", "Quote", "Code"
        ])
        self.text_style_combo.currentTextChanged.connect(self._on_text_style_changed)
        style_layout.addWidget(self.text_style_combo)
        style_layout.addStretch()
        text_layout.addLayout(style_layout)
        
        # Formatting buttons
        format_layout = QHBoxLayout()
        
        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setToolTip("Bold (Ctrl+B)")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(30, 30)
        self.bold_btn.setFont(self.bold_btn.font())
        self.bold_btn.font().setBold(True)
        self.bold_btn.clicked.connect(self._on_bold_toggled)
        format_layout.addWidget(self.bold_btn)
        
        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setToolTip("Italic (Ctrl+I)")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(30, 30)
        self.italic_btn.clicked.connect(self._on_italic_toggled)
        format_layout.addWidget(self.italic_btn)
        
        self.underline_btn = QToolButton()
        self.underline_btn.setText("U")
        self.underline_btn.setToolTip("Underline (Ctrl+U)")
        self.underline_btn.setCheckable(True)
        self.underline_btn.setFixedSize(30, 30)
        self.underline_btn.clicked.connect(self._on_underline_toggled)
        format_layout.addWidget(self.underline_btn)
        
        format_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(14)
        self.font_size_spin.valueChanged.connect(self.tool_manager.set_font_size)
        format_layout.addWidget(self.font_size_spin)
        
        format_layout.addStretch()
        text_layout.addLayout(format_layout)
        
        layout.addWidget(text_group)
        
        # List options section
        list_group = QGroupBox("List Options")
        list_layout = QHBoxLayout(list_group)
        
        list_layout.addWidget(QLabel("Type:"))
        self.list_type_combo = QComboBox()
        self.list_type_combo.addItems(["Bullet", "Numbered", "Plain"])
        self.list_type_combo.currentTextChanged.connect(self._on_list_type_changed)
        list_layout.addWidget(self.list_type_combo)
        list_layout.addStretch()
        
        layout.addWidget(list_group)
        
        # View options section
        view_group = QGroupBox("View")
        view_layout = QHBoxLayout(view_group)
        
        self.grid_btn = QToolButton()
        self.grid_btn.setText("Grid")
        self.grid_btn.setToolTip("Toggle grid")
        self.grid_btn.setCheckable(True)
        self.grid_btn.clicked.connect(self._on_grid_toggled)
        view_layout.addWidget(self.grid_btn)
        
        view_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        view_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        view_layout.addWidget(self.zoom_label)
        
        view_layout.addStretch()
        layout.addWidget(view_group)
        
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect tool manager signals."""
        self.tool_manager.tool_changed.connect(self._on_tool_changed)
    
    def _on_tool_button_clicked(self, checked=False):
        """Handle tool button click by getting tool name from button property."""
        sender = self.sender()
        if sender:
            tool_name = sender.property("tool_name")
            if tool_name:
                self.tool_manager.set_tool(tool_name)
    
    def _on_color_button_clicked(self, checked=False):
        """Handle color button click by getting color from button property."""
        sender = self.sender()
        if sender:
            color_hex = sender.property("color")
            if color_hex:
                self.color_button.set_color(QColor(color_hex))
    
    def _on_tool_changed(self, tool_name: str):
        """Handle tool change."""
        for name, btn in self.tool_buttons.items():
            btn.setChecked(name == tool_name)
    
    def _on_text_style_changed(self, style: str):
        """Handle text style change."""
        self.tool_manager.set_text_style(style.lower())
    
    def _on_bold_toggled(self, checked: bool):
        """Handle bold toggle."""
        self.tool_manager.set_bold(checked)
    
    def _on_italic_toggled(self, checked: bool):
        """Handle italic toggle."""
        self.tool_manager.set_italic(checked)
    
    def _on_underline_toggled(self, checked: bool):
        """Handle underline toggle."""
        pass  # Could add underline support
    
    def _on_list_type_changed(self, list_type: str):
        """Handle list type change."""
        self.tool_manager.set_list_type(list_type.lower())
    
    def _on_grid_toggled(self, checked: bool):
        """Handle grid toggle."""
        # This should be connected to canvas in main window
        pass
    
    def _on_zoom_changed(self, value: int):
        """Handle zoom change."""
        self.zoom_label.setText(f"{value}%")
        # This should be connected to canvas in main window
    
    def get_zoom_factor(self) -> float:
        """Get current zoom factor."""
        return self.zoom_slider.value() / 100.0
    
    def set_zoom(self, factor: float):
        """Set zoom factor."""
        self.zoom_slider.setValue(int(factor * 100))
