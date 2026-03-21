"""
Canvas module - The main drawing canvas widget.

Provides the interactive drawing area with support for all tools,
layer rendering, and user interactions.
"""

from typing import Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QTimer
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QImage,
    QMouseEvent, QPaintEvent, QResizeEvent, QKeyEvent
)

from app.core.layer_manager import LayerManager
from app.core.tool_manager import ToolManager
from app.core.layer import Layer


class Canvas(QWidget):
    """
    Main drawing canvas widget.
    
    Handles all mouse events for drawing, renders layers,
    and provides interactive feedback.
    """
    
    # Signals
    drawing_changed = pyqtSignal()
    cursor_position_changed = pyqtSignal(QPointF)
    
    def __init__(self, layer_manager: LayerManager, tool_manager: ToolManager):
        super().__init__()
        
        self.layer_manager = layer_manager
        self.tool_manager = tool_manager
        
        # Canvas settings
        self.canvas_width = 3000
        self.canvas_height = 3000
        self.zoom_factor = 1.0
        self.offset = QPointF(0, 0)
        
        # Drawing state
        self.is_drawing = False
        self.last_point = QPointF()
        
        # Preview element (for shapes being drawn)
        self.preview_element = None
        
        # Background settings
        self.background_color = QColor('#FFFFFF')
        self.show_grid = False
        self.grid_size = 50
        self.grid_color = QColor('#E0E0E0')
        
        # Set up widget
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(800, 600)
        
        # Enable smooth rendering
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        # Connect signals
        self.layer_manager.layer_changed.connect(self._on_layer_changed)
        self.layer_manager.layers_reordered.connect(self.update)
        self.tool_manager.style_changed.connect(self.update)
        
        # Create off-screen buffer for performance
        self._buffer = QImage(self.canvas_width, self.canvas_height,
                              QImage.Format_ARGB32_Premultiplied)
        self._buffer_valid = False
    
    def _on_layer_changed(self, layer_id: str):
        """Handle layer content changes."""
        self._buffer_valid = False
        self.update()
    
    def set_zoom(self, factor: float):
        """Set zoom factor."""
        self.zoom_factor = max(0.1, min(5.0, factor))
        self.update()
    
    def zoom_in(self):
        """Increase zoom."""
        self.set_zoom(self.zoom_factor * 1.2)
    
    def zoom_out(self):
        """Decrease zoom."""
        self.set_zoom(self.zoom_factor / 1.2)
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.set_zoom(1.0)
    
    def set_offset(self, offset: QPointF):
        """Set view offset."""
        self.offset = offset
        self.update()
    
    def center_view(self):
        """Center the view on the canvas."""
        self.offset = QPointF(0, 0)
        self.update()
    
    def set_background_color(self, color: QColor):
        """Set canvas background color."""
        self.background_color = color
        self.update()
    
    def set_show_grid(self, show: bool):
        """Toggle grid display."""
        self.show_grid = show
        self.update()
    
    def _get_canvas_point(self, widget_point: QPointF) -> QPointF:
        """Convert widget coordinates to canvas coordinates."""
        x = (widget_point.x() - self.width() / 2) / self.zoom_factor + self.canvas_width / 2 - self.offset.x()
        y = (widget_point.y() - self.height() / 2) / self.zoom_factor + self.canvas_height / 2 - self.offset.y()
        return QPointF(x, y)
    
    def _get_widget_point(self, canvas_point: QPointF) -> QPointF:
        """Convert canvas coordinates to widget coordinates."""
        x = (canvas_point.x() - self.canvas_width / 2 + self.offset.x()) * self.zoom_factor + self.width() / 2
        y = (canvas_point.y() - self.canvas_height / 2 + self.offset.y()) * self.zoom_factor + self.height() / 2
        return QPointF(x, y)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            point = self._get_canvas_point(event.pos())
            
            current_layer = self.layer_manager.get_current_layer()
            if current_layer:
                tool = self.tool_manager.get_current_tool()
                if tool:
                    self.is_drawing = tool.mouse_press(point, current_layer)
                    self.last_point = point
                    
                    if self.is_drawing:
                        self.drawing_changed.emit()
        
        elif event.button() == Qt.MiddleButton:
            # Start panning
            self.setCursor(Qt.ClosedHandCursor)
            self._pan_start = event.pos()
            self._pan_offset_start = self.offset
        
        self.update()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""
        point = self._get_canvas_point(event.pos())
        self.cursor_position_changed.emit(point)
        
        if event.buttons() & Qt.LeftButton:
            if self.is_drawing:
                current_layer = self.layer_manager.get_current_layer()
                if current_layer:
                    tool = self.tool_manager.get_current_tool()
                    if tool:
                        tool.mouse_move(point, current_layer)
                        self.drawing_changed.emit()
        
        elif event.buttons() & Qt.MiddleButton:
            # Pan view
            delta = event.pos() - self._pan_start
            self.offset = QPointF(
                self._pan_offset_start.x() + delta.x() / self.zoom_factor,
                self._pan_offset_start.y() + delta.y() / self.zoom_factor
            )
        
        self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            if self.is_drawing:
                point = self._get_canvas_point(event.pos())
                current_layer = self.layer_manager.get_current_layer()
                
                if current_layer:
                    tool = self.tool_manager.get_current_tool()
                    if tool:
                        element = tool.mouse_release(point, current_layer)
                        if element:
                            self.drawing_changed.emit()
                
                self.is_drawing = False
        
        elif event.button() == Qt.MiddleButton:
            self.setCursor(Qt.ArrowCursor)
        
        self.update()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        
        if event.modifiers() & Qt.ControlModifier:
            # Zoom
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Scroll
            scroll_amount = 50
            if event.modifiers() & Qt.ShiftModifier:
                self.offset = QPointF(
                    self.offset.x() + (delta / 120) * scroll_amount,
                    self.offset.y()
                )
            else:
                self.offset = QPointF(
                    self.offset.x(),
                    self.offset.y() + (delta / 120) * scroll_amount
                )
        
        self.update()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Zoom shortcuts
        if event.key() == Qt.Key_Plus and event.modifiers() & Qt.ControlModifier:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus and event.modifiers() & Qt.ControlModifier:
            self.zoom_out()
        elif event.key() == Qt.Key_0 and event.modifiers() & Qt.ControlModifier:
            self.reset_zoom()
        
        # Tool shortcuts
        elif event.key() == Qt.Key_P:
            self.tool_manager.set_tool("Pen")
        elif event.key() == Qt.Key_L:
            self.tool_manager.set_tool("Line")
        elif event.key() == Qt.Key_R:
            self.tool_manager.set_tool("Rectangle")
        elif event.key() == Qt.Key_E:
            self.tool_manager.set_tool("Ellipse")
        elif event.key() == Qt.Key_A:
            self.tool_manager.set_tool("Arrow")
        elif event.key() == Qt.Key_T:
            self.tool_manager.set_tool("Text")
        elif event.key() == Qt.Key_B:
            self.tool_manager.set_tool("Box")
        elif event.key() == Qt.Key_I:
            self.tool_manager.set_tool("List")
        elif event.key() == Qt.Key_S:
            if event.modifiers() & Qt.ControlModifier:
                # Let main window handle save
                pass
            else:
                self.tool_manager.set_tool("Select")
        elif event.key() == Qt.Key_Delete:
            # Delete selected or clear current layer
            current = self.layer_manager.get_current_layer()
            if current and not current.locked:
                current.clear()
                self._buffer_valid = False
                self.update()
        
        self.update()
    
    def paintEvent(self, event: QPaintEvent):
        """Handle paint events."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Fill background
        painter.fillRect(self.rect(), self.background_color)
        
        # Apply transformations for zoom and offset
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self.zoom_factor, self.zoom_factor)
        painter.translate(-self.canvas_width / 2 + self.offset.x(),
                          -self.canvas_height / 2 + self.offset.y())
        
        # Draw grid if enabled
        if self.show_grid:
            self._draw_grid(painter)
        
        # Draw all layers
        self.layer_manager.render_all(painter)
        
        # Draw current preview element if drawing
        if self.is_drawing:
            current_layer = self.layer_manager.get_current_layer()
            if current_layer and self.tool_manager.current_tool:
                # The element is already in the layer, just re-render
                pass
        
        # Draw canvas boundary
        pen = QPen(QColor('#CCCCCC'))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, self.canvas_width, self.canvas_height)
        
        painter.end()
    
    def _draw_grid(self, painter: QPainter):
        """Draw grid lines."""
        pen = QPen(self.grid_color)
        pen.setWidthF(0.5)
        painter.setPen(pen)
        
        # Calculate visible area
        left = -self.offset.x()
        top = -self.offset.y()
        right = left + self.width() / self.zoom_factor
        bottom = top + self.height() / self.zoom_factor
        
        # Draw vertical lines
        start_x = int(left / self.grid_size) * self.grid_size
        for x in range(start_x, int(right) + self.grid_size, self.grid_size):
            painter.drawLine(x, int(top), x, int(bottom))
        
        # Draw horizontal lines
        start_y = int(top / self.grid_size) * self.grid_size
        for y in range(start_y, int(bottom) + self.grid_size, self.grid_size):
            painter.drawLine(int(left), y, int(right), y)
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle resize events."""
        super().resizeEvent(event)
    
    def get_canvas_image(self, width: int = None, height: int = None) -> QImage:
        """Get the current canvas as an image."""
        if width is None:
            width = self.canvas_width
        if height is None:
            height = self.canvas_height
        
        image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        image.fill(self.background_color)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        
        self.layer_manager.render_all(painter)
        
        painter.end()
        
        return image
    
    def clear_canvas(self):
        """Clear all layers."""
        for item in self.layer_manager.layers:
            if isinstance(item, Layer):
                item.clear()
            elif hasattr(item, 'layers'):
                for layer in item.layers:
                    layer.clear()
        
        self._buffer_valid = False
        self.drawing_changed.emit()
        self.update()
