"""
File Handler module - Handles save, open, and export operations.

Supports custom project files (.draw) and various export formats.
"""

import json
import os
from typing import Optional, Tuple
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import Qt

from app.core.layer_manager import LayerManager
from app.core.tool_manager import ToolManager


class FileHandler(QObject):
    """
    Handles all file operations for the drawing application.
    
    Supports:
    - Save/Load project files (.draw format - JSON based)
    - Export to PNG, JPEG, SVG
    - Auto-save functionality
    """
    
    file_saved = pyqtSignal(str)  # File path
    file_opened = pyqtSignal(str)  # File path
    file_error = pyqtSignal(str)  # Error message
    
    # File extension for project files
    PROJECT_EXTENSION = ".draw"
    
    def __init__(self):
        super().__init__()
        self.current_file: Optional[str] = None
        self.modified = False
        self.auto_save_enabled = True
        self.auto_save_interval = 5 * 60 * 1000  # 5 minutes in ms
    
    def get_project_filter(self) -> str:
        """Get file filter for project files."""
        ext = self.PROJECT_EXTENSION
        return f"Drawing Project (*{ext});;All Files (*)"
    
    def get_export_filter(self) -> str:
        """Get file filter for export formats."""
        return "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;SVG Image (*.svg);;All Files (*)"
    
    def new_project(self, layer_manager: LayerManager, tool_manager: ToolManager):
        """Create a new project."""
        layer_manager.layers.clear()
        layer_manager._layer_counter = 0
        layer_manager._create_default_layer()
        
        tool_manager.set_tool("Pen")
        tool_manager.style.set_color(QColor('#000000'))
        tool_manager.style.set_pen_width(2)
        
        self.current_file = None
        self.modified = False
    
    def save_project(self, file_path: str, layer_manager: LayerManager,
                     tool_manager: ToolManager) -> bool:
        """Save project to file."""
        try:
            project_data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'modified_at': datetime.now().isoformat(),
                'layer_manager': layer_manager.to_dict(),
                'tool_manager': tool_manager.to_dict(),
            }
            
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            self.current_file = file_path
            self.modified = False
            self.file_saved.emit(file_path)
            return True
            
        except Exception as e:
            self.file_error.emit(f"Error saving file: {str(e)}")
            return False
    
    def open_project(self, file_path: str, layer_manager: LayerManager,
                     tool_manager: ToolManager) -> bool:
        """Open project from file."""
        try:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
            
            # Check version
            version = project_data.get('version', '1.0')
            if version != '1.0':
                self.file_error.emit(f"Unsupported file version: {version}")
                return False
            
            # Load layer manager
            if 'layer_manager' in project_data:
                layer_manager.from_dict(project_data['layer_manager'])
            
            # Load tool manager
            if 'tool_manager' in project_data:
                tool_manager.from_dict(project_data['tool_manager'])
            
            self.current_file = file_path
            self.modified = False
            self.file_opened.emit(file_path)
            return True
            
        except json.JSONDecodeError as e:
            self.file_error.emit(f"Invalid file format: {str(e)}")
            return False
        except Exception as e:
            self.file_error.emit(f"Error opening file: {str(e)}")
            return False
    
    def export_image(self, file_path: str, layer_manager: LayerManager,
                     width: int = 1920, height: int = 1080,
                     background_color: QColor = None) -> bool:
        """Export current drawing to an image file."""
        try:
            # Create image
            if background_color is None:
                background_color = QColor('#FFFFFF')
            
            image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
            image.fill(background_color)
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Render all layers
            layer_manager.render_all(painter)
            
            painter.end()
            
            # Save based on extension
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.svg':
                return self._export_svg(file_path, layer_manager, width, height)
            
            # PNG and JPEG
            quality = -1 if ext == '.png' else 95
            if not image.save(file_path, quality=quality):
                self.file_error.emit(f"Failed to save image: {file_path}")
                return False
            
            self.file_saved.emit(file_path)
            return True
            
        except Exception as e:
            self.file_error.emit(f"Error exporting image: {str(e)}")
            return False
    
    def _export_svg(self, file_path: str, layer_manager: LayerManager,
                    width: int, height: int) -> bool:
        """Export to SVG format."""
        try:
            from PyQt5.QtSvg import QSvgGenerator
            from PyQt5.QtCore import QRect
            
            generator = QSvgGenerator()
            generator.setFileName(file_path)
            generator.setSize(QSize(width, height))
            generator.setViewBox(QRect(0, 0, width, height))
            generator.setTitle("Drawing Export")
            generator.setDescription("Exported from Drawing Application")
            
            painter = QPainter(generator)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Render all layers
            layer_manager.render_all(painter)
            
            painter.end()
            
            self.file_saved.emit(file_path)
            return True
            
        except ImportError:
            self.file_error.emit("SVG export requires PyQt5.QtSvg module")
            return False
        except Exception as e:
            self.file_error.emit(f"Error exporting SVG: {str(e)}")
            return False
    
    def export_layer(self, file_path: str, layer, width: int = 1920,
                     height: int = 1080, background_color: QColor = None) -> bool:
        """Export a single layer to an image file."""
        try:
            if background_color is None:
                background_color = QColor(255, 255, 255, 0)  # Transparent
            
            image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
            image.fill(background_color)
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            
            layer.render(painter)
            
            painter.end()
            
            if not image.save(file_path):
                self.file_error.emit(f"Failed to save layer image: {file_path}")
                return False
            
            self.file_saved.emit(file_path)
            return True
            
        except Exception as e:
            self.file_error.emit(f"Error exporting layer: {str(e)}")
            return False
    
    def auto_save(self, layer_manager: LayerManager, tool_manager: ToolManager):
        """Perform auto-save if enabled."""
        if not self.auto_save_enabled or not self.current_file:
            return False
        
        auto_save_path = self.current_file + ".autosave"
        return self.save_project(auto_save_path, layer_manager, tool_manager)
    
    def set_modified(self):
        """Mark project as modified."""
        self.modified = True
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self.modified
    
    def get_recent_files(self, max_count: int = 10) -> list:
        """Get list of recently opened files."""
        # In a full implementation, this would read from settings
        return []
    
    def add_recent_file(self, file_path: str):
        """Add file to recent files list."""
        # In a full implementation, this would update settings
        pass
