"""
Main Window module - The main application window.

Integrates all components: canvas, toolbar, layer panel,
and provides menu bar with file operations.
"""

import os
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QAction, QStatusBar, QLabel, QMessageBox,
    QFileDialog, QToolBar, QDockWidget, QApplication
)
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QCloseEvent

from app.canvas import Canvas
from app.toolbar import ToolToolbar
from app.layer_panel import LayerPanel
from app.core.layer_manager import LayerManager
from app.core.tool_manager import ToolManager
from app.core.file_handler import FileHandler


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Provides the complete drawing application interface with:
    - Menu bar for file operations
    - Toolbar for tools and styles
    - Canvas for drawing
    - Layer panel for layer management
    - Status bar for feedback
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Drawing Application")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize core components
        self.layer_manager = LayerManager()
        self.tool_manager = ToolManager()
        self.file_handler = FileHandler()
        
        # Initialize UI
        self._init_ui()
        self._create_menus()
        self._create_status_bar()
        self._connect_signals()
        
        # Settings
        self.settings = QSettings("DrawingApp", "DrawingApp")
        self._load_settings()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel: Toolbar
        self.toolbar_widget = ToolToolbar(self.tool_manager)
        self.toolbar_widget.setMinimumWidth(280)
        self.toolbar_widget.setMaximumWidth(350)
        splitter.addWidget(self.toolbar_widget)
        
        # Center: Canvas
        self.canvas = Canvas(self.layer_manager, self.tool_manager)
        self.canvas.drawing_changed.connect(self._on_drawing_changed)
        self.canvas.cursor_position_changed.connect(self._on_cursor_position_changed)
        
        # Connect toolbar zoom to canvas
        self.toolbar_widget.zoom_slider.valueChanged.connect(
            lambda v: self.canvas.set_zoom(v / 100.0)
        )
        self.toolbar_widget.grid_btn.clicked.connect(
            lambda checked: self.canvas.set_show_grid(checked)
        )
        
        splitter.addWidget(self.canvas)
        
        # Right panel: Layer panel
        self.layer_panel = LayerPanel(self.layer_manager)
        splitter.addWidget(self.layer_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 800, 300])
        
        # Connect toolbar to canvas for some features
        self.toolbar_widget.grid_btn.clicked.connect(
            lambda checked: self.canvas.set_show_grid(checked)
        )
    
    def _create_menus(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu("&Export")
        
        export_png_action = QAction("Export as &PNG...", self)
        export_png_action.triggered.connect(lambda: self._export_image("png"))
        export_menu.addAction(export_png_action)
        
        export_jpg_action = QAction("Export as &JPEG...", self)
        export_jpg_action.triggered.connect(lambda: self._export_image("jpg"))
        export_menu.addAction(export_jpg_action)
        
        export_svg_action = QAction("Export as &SVG...", self)
        export_svg_action.triggered.connect(lambda: self._export_image("svg"))
        export_menu.addAction(export_svg_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        clear_action = QAction("&Clear Canvas", self)
        clear_action.triggered.connect(self.canvas.clear_canvas)
        edit_menu.addAction(clear_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        grid_action = QAction("Show &Grid", self)
        grid_action.setCheckable(True)
        grid_action.toggled.connect(self.canvas.set_show_grid)
        view_menu.addAction(grid_action)
        
        # Layer menu
        layer_menu = menubar.addMenu("&Layer")
        
        new_layer_action = QAction("&New Layer", self)
        new_layer_action.setShortcut("Ctrl+Shift+N")
        new_layer_action.triggered.connect(self.layer_panel._add_layer)
        layer_menu.addAction(new_layer_action)
        
        new_group_action = QAction("New &Group", self)
        new_group_action.triggered.connect(self.layer_panel._add_group)
        layer_menu.addAction(new_group_action)
        
        layer_menu.addSeparator()
        
        toggle_overlay_action = QAction("Toggle &Overlay", self)
        toggle_overlay_action.setCheckable(True)
        toggle_overlay_action.setChecked(True)
        toggle_overlay_action.toggled.connect(self.layer_manager.set_overlay_visible)
        layer_menu.addAction(toggle_overlay_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = self.statusBar()
        
        # Position label
        self.position_label = QLabel("X: 0, Y: 0")
        self.status_bar.addPermanentWidget(self.position_label)
        
        # Tool label
        self.tool_label = QLabel("Tool: Pen")
        self.status_bar.addWidget(self.tool_label)
        
        # Layer label
        self.layer_label = QLabel("Layer: Background")
        self.status_bar.addWidget(self.layer_label)
        
        # Modified indicator
        self.modified_label = QLabel("")
        self.status_bar.addWidget(self.modified_label)
    
    def _connect_signals(self):
        """Connect all signals."""
        self.tool_manager.tool_changed.connect(
            lambda name: self.tool_label.setText(f"Tool: {name}")
        )
        
        self.layer_manager.current_layer_changed.connect(
            lambda layer: self.layer_label.setText(f"Layer: {layer.name}")
        )
        
        self.file_handler.file_saved.connect(self._on_file_saved)
        self.file_handler.file_opened.connect(self._on_file_opened)
        self.file_handler.file_error.connect(self._on_file_error)
    
    def _on_drawing_changed(self):
        """Handle drawing changes."""
        self.file_handler.set_modified()
        self.modified_label.setText("*")
    
    def _on_cursor_position_changed(self, pos):
        """Handle cursor position change."""
        self.position_label.setText(f"X: {int(pos.x())}, Y: {int(pos.y())}")
    
    def _on_file_saved(self, path: str):
        """Handle file saved."""
        self.setWindowTitle(f"Drawing Application - {os.path.basename(path)}")
        self.modified_label.setText("")
    
    def _on_file_opened(self, path: str):
        """Handle file opened."""
        self.setWindowTitle(f"Drawing Application - {os.path.basename(path)}")
        self.modified_label.setText("")
        self.canvas._buffer_valid = False
        self.canvas.update()
    
    def _on_file_error(self, error: str):
        """Handle file error."""
        QMessageBox.critical(self, "File Error", error)
    
    def _new_project(self):
        """Create a new project."""
        if self.file_handler.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "New Project",
                "Save current project before creating new?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                self._save_project()
        
        self.file_handler.new_project(self.layer_manager, self.tool_manager)
        self.canvas._buffer_valid = False
        self.canvas.update()
        self.setWindowTitle("Drawing Application - Untitled")
    
    def _open_project(self):
        """Open a project file."""
        if self.file_handler.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Open Project",
                "Save current project before opening?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                self._save_project()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project",
            "", self.file_handler.get_project_filter()
        )
        
        if file_path:
            self.file_handler.open_project(
                file_path, self.layer_manager, self.tool_manager
            )
    
    def _save_project(self):
        """Save the current project."""
        if self.file_handler.current_file:
            self.file_handler.save_project(
                self.file_handler.current_file,
                self.layer_manager, self.tool_manager
            )
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        """Save project with new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project",
            "", self.file_handler.get_project_filter()
        )
        
        if file_path:
            if not file_path.endswith(self.file_handler.PROJECT_EXTENSION):
                file_path += self.file_handler.PROJECT_EXTENSION
            
            self.file_handler.save_project(
                file_path, self.layer_manager, self.tool_manager
            )
    
    def _export_image(self, format: str):
        """Export current drawing to image."""
        filters = {
            'png': "PNG Image (*.png)",
            'jpg': "JPEG Image (*.jpg *.jpeg)",
            'svg': "SVG Image (*.svg)",
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Image",
            "", filters.get(format, "All Files (*)")
        )
        
        if file_path:
            self.file_handler.export_image(
                file_path, self.layer_manager,
                width=self.canvas.canvas_width,
                height=self.canvas.canvas_height
            )
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Drawing Application",
            "Drawing Application v1.0\n\n"
            "A modular Qt-based drawing application with:\n"
            "• Multiple drawing tools\n"
            "• Layer management\n"
            "• Text styles (headings, titles, lists)\n"
            "• Export to various formats\n"
            "• Project save/load"
        )
    
    def _load_settings(self):
        """Load application settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        if self.file_handler.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Quit",
                "Save changes before quitting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.Yes:
                self._save_project()
        
        # Save settings
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()
