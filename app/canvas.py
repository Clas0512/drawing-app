"""
Canvas module - The main drawing canvas widget.

Provides the interactive drawing area with support for all tools,
layer rendering, and user interactions.
"""

from typing import Optional
from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QTimer, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QImage,
    QMouseEvent, QPaintEvent, QResizeEvent, QKeyEvent, QFont, QCursor
)

from app.core.layer_manager import LayerManager
from app.core.tool_manager import ToolManager
from app.core.layer import Layer


class InlineTextEditor(QLineEdit):
    """Inline text editor widget for creating text directly on canvas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                border-bottom: 2px solid #3498db;
                padding: 2px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #2980b9;
            }
        """)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumWidth(200)
        self.setPlaceholderText("Type here...")
        
        self._canvas_point = QPointF()
        self._current_layer = None
        self._tool_manager = None
    
    def set_position(self, canvas_point: QPointF, widget_pos: QPointF, layer, tool_manager):
        """Set the editor position and context."""
        self._canvas_point = canvas_point
        self._current_layer = layer
        self._tool_manager = tool_manager
        
        # Position in widget coordinates
        self.move(int(widget_pos.x()), int(widget_pos.y()))
        self.clear()
        self.show()
        self.setFocus()
    
    def get_canvas_point(self) -> QPointF:
        """Get the canvas point where text should be created."""
        return self._canvas_point
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.hide()
            return
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Don't hide on Enter, allow multiline-style editing
            self.setText(self.text() + '\n')
            return
        
        super().keyPressEvent(event)
    
    def focusOutEvent(self, event):
        """Handle focus out - create text element if there's content."""
        text = self.text().strip()
        if text and self._current_layer and self._canvas_point:
            from app.core.layer import DrawingElement
            
            # Get current style from tool manager
            style = {}
            if self._tool_manager:
                style = self._tool_manager.get_current_style().get_style_dict()
            style['font_size'] = 14
            
            element = DrawingElement('text', style)
            element.add_point(self._canvas_point)
            element.set_text(text)
            self._current_layer.add_element(element)
        
        self.hide()
        self.clear()


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
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Connect signals
        self.layer_manager.layer_changed.connect(self._on_layer_changed)
        self.layer_manager.layers_reordered.connect(self.update)
        self.tool_manager.style_changed.connect(self.update)
        
        # Create off-screen buffer for performance
        self._buffer = QImage(self.canvas_width, self.canvas_height,
                              QImage.Format_ARGB32_Premultiplied)
        self._buffer_valid = False
        
        # Create inline text editor
        self._inline_text_editor = InlineTextEditor(self)
        self._inline_text_editor.hide()
        self._inline_text_editor.textChanged.connect(self._on_inline_text_changed)
        self._inline_text_editor.editingFinished.connect(self._on_inline_text_finished)
    
    def _on_inline_text_changed(self):
        """Handle inline text changes."""
        pass  # Could add live preview here
    
    def _on_inline_text_finished(self):
        """Handle inline text editing finished."""
        text = self._inline_text_editor.text().strip()
        if text:
            self._buffer_valid = False
            self.update()
            self.drawing_changed.emit()
    
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
    
    def _get_canvas_point(self, widget_point) -> QPointF:
        """Convert widget coordinates to canvas coordinates."""
        # Handle both QPoint and QPointF
        if hasattr(widget_point, 'x'):
            wx = widget_point.x()
            wy = widget_point.y()
        else:
            wx = widget_point[0]
            wy = widget_point[1]
        
        x = (wx - self.width() / 2) / self.zoom_factor + self.canvas_width / 2 - self.offset.x()
        y = (wy - self.height() / 2) / self.zoom_factor + self.canvas_height / 2 - self.offset.y()
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
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click for editing elements or creating text."""
        if event.button() == Qt.LeftButton:
            point = self._get_canvas_point(event.pos())
            widget_point = event.pos()
            
            # Check if we're in Text tool mode
            current_tool = self.tool_manager.get_current_tool()
            tool_name = current_tool.name if current_tool else ""
            
            if tool_name == "Text":
                # Create inline text editor at the click position
                self._create_inline_text_at(point, widget_point)
            else:
                # Try to edit existing element
                self._open_edit_dialog_at(point)
    
    def _create_inline_text_at(self, canvas_point: QPointF, widget_point):
        """Create an inline text editor at the given position."""
        current_layer = self.layer_manager.get_current_layer()
        if not current_layer or current_layer.locked:
            return
        
        # Position the inline editor
        self._inline_text_editor.set_position(
            canvas_point, 
            QPointF(widget_point),
            current_layer,
            self.tool_manager
        )
        self._inline_text_editor.show()
        self._inline_text_editor.setFocus()
    
    def _open_edit_dialog_at(self, point):
        """Open edit dialog for element at point."""
        current_layer = self.layer_manager.get_current_layer()
        if not current_layer or current_layer.locked:
            return
        
        # Try to find existing element to edit (check full bounding area for shapes)
        tol = 15
        for element in reversed(current_layer.elements):
            found = False
            if not element.points:
                continue
            
            if element.element_type in ['rectangle', 'ellipse', 'box'] and len(element.points) >= 2:
                # Check if point is inside bounding rect
                x1, y1 = element.points[0].x(), element.points[0].y()
                x2, y2 = element.points[1].x(), element.points[1].y()
                left, right = min(x1, x2), max(x1, x2)
                top, bottom = min(y1, y2), max(y1, y2)
                found = (left - tol <= point.x() <= right + tol) and (top - tol <= point.y() <= bottom + tol)
            elif element.element_type in ['line', 'arrow'] and len(element.points) >= 2:
                # Check distance to line
                found = self._point_near_line(point, element.points[0], element.points[1], tol)
            elif element.element_type == 'pen':
                # Check distance to any segment
                for i in range(1, len(element.points)):
                    if self._point_near_line(point, element.points[i-1], element.points[i], tol):
                        found = True
                        break
            else:
                # Text, list, etc - check near first point
                for p in element.points:
                    if abs(p.x() - point.x()) < tol and abs(p.y() - point.y()) < tol:
                        found = True
                        break
            
            if found:
                try:
                    from app.dialogs.element_edit_dialog import ElementEditDialog
                    dialog = ElementEditDialog(element, self)
                    if dialog.exec_() == dialog.Accepted:
                        dialog.apply_changes()
                        self._buffer_valid = False
                        self.update()
                        self.drawing_changed.emit()
                except Exception:
                    pass
                return
    
    def _point_near_line(self, point, p1, p2, tol=15):
        """Check if point is near a line segment."""
        x0, y0 = point.x(), point.y()
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return abs(x0 - x1) < tol and abs(y0 - y1) < tol
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / length_sq))
        nearest_x, nearest_y = x1 + t * dx, y1 + t * dy
        dist = ((x0 - nearest_x) ** 2 + (y0 - nearest_y) ** 2) ** 0.5
        return dist < tol
    
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
            # Zoom focused on cursor position
            cursor_widget = event.pos()
            
            # Get cursor position in canvas coordinates before zoom
            cx = (cursor_widget.x() - self.width() / 2) / self.zoom_factor + self.canvas_width / 2 - self.offset.x()
            cy = (cursor_widget.y() - self.height() / 2) / self.zoom_factor + self.canvas_height / 2 - self.offset.y()
            
            old_zoom = self.zoom_factor
            if delta > 0:
                new_zoom = min(5.0, self.zoom_factor * 1.2)
            else:
                new_zoom = max(0.1, self.zoom_factor / 1.2)
            
            # Calculate new offset so (cx, cy) stays at cursor position
            self.zoom_factor = new_zoom
            
            # New offset needed: (cx, cy) should map to cursor_widget position
            # screen_x = (cx - canvas_w/2 + offset_x) * zoom + w/2
            # cursor_widget.x() = (cx - canvas_w/2 + new_offset_x) * new_zoom + w/2
            # new_offset_x = (cursor_widget.x() - w/2) / new_zoom - cx + canvas_w/2
            new_offset_x = (cursor_widget.x() - self.width() / 2) / new_zoom - cx + self.canvas_width / 2
            new_offset_y = (cursor_widget.y() - self.height() / 2) / new_zoom - cy + self.canvas_height / 2
            
            self.offset = QPointF(new_offset_x, new_offset_y)
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
    
    # Drag and drop support
    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move event."""
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event - import files to canvas."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    self._import_file(file_path, event.pos())
            event.acceptProposedAction()
        elif event.mimeData().hasImage():
            # Handle raw image data
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def _import_file(self, file_path, drop_pos):
        """Import a file to the canvas."""
        import os
        from app.core.layer import DrawingElement
        
        ext = os.path.splitext(file_path)[1].lower()
        point = self._get_canvas_point(drop_pos)
        
        current_layer = self.layer_manager.get_current_layer()
        if not current_layer or current_layer.locked:
            return
        
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']:
            # Image file - create a box with image info
            element = DrawingElement('box', {
                'pen_color': '#333333',
                'fill_color': '#EEEEEE',
                'fill_alpha': 255,
                'pen_width': 2,
                'image_path': file_path
            })
            element.add_point(point)
            element.add_point(QPointF(point.x() + 200, point.y() + 150))
            current_layer.add_element(element)
            
            # Also add filename text
            text_el = DrawingElement('text', {
                'text_style': 'normal',
                'font_size': 12,
                'color': '#333333'
            })
            text_el.add_point(QPointF(point.x() + 5, point.y() + 20))
            text_el.set_text(os.path.basename(file_path))
            current_layer.add_element(text_el)
            
        elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
            # Sound file - create a note
            element = DrawingElement('box', {
                'pen_color': '#FF6600',
                'fill_color': '#FFF0E0',
                'fill_alpha': 200,
                'pen_width': 2
            })
            element.add_point(point)
            element.add_point(QPointF(point.x() + 180, point.y() + 60))
            current_layer.add_element(element)
            
            text_el = DrawingElement('text', {
                'text_style': 'normal',
                'font_size': 12,
                'color': '#FF6600'
            })
            text_el.add_point(QPointF(point.x() + 5, point.y() + 20))
            text_el.set_text(f"♪ {os.path.basename(file_path)}")
            current_layer.add_element(text_el)
            
        else:
            # Other file - just show filename
            element = DrawingElement('text', {
                'text_style': 'normal',
                'font_size': 14,
                'color': '#0066CC'
            })
            element.add_point(point)
            element.set_text(f"📎 {os.path.basename(file_path)}")
            current_layer.add_element(element)
        
        self._buffer_valid = False
        self.update()
        self.drawing_changed.emit()
    
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
