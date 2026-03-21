"""
Layer module - Defines Layer and LayerGroup classes for the drawing application.

Layers are the fundamental building blocks for organizing drawing content.
Each layer can contain multiple drawing elements and can be independently
managed (visibility, locking, grouping).
"""

import uuid
from typing import List, Optional, Any, Dict
from datetime import datetime
from PyQt5.QtGui import QImage, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QPointF, QRectF, QSize


class DrawingElement:
    """Base class for all drawing elements on a layer."""
    
    def __init__(self, element_type: str, style: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.element_type = element_type
        self.style = style.copy()
        self.points: List[QPointF] = []
        self.text: str = ""
        self.bounding_rect: QRectF = QRectF()
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
    
    def add_point(self, point: QPointF):
        """Add a point to the element (for paths, lines, etc.)."""
        self.points.append(point)
        self.modified_at = datetime.now()
        self._update_bounding_rect()
    
    def set_points(self, points: List[QPointF]):
        """Set all points at once."""
        self.points = points.copy()
        self.modified_at = datetime.now()
        self._update_bounding_rect()
    
    def set_text(self, text: str):
        """Set text content for text elements."""
        self.text = text
        self.modified_at = datetime.now()
    
    def _update_bounding_rect(self):
        """Update the bounding rectangle based on points."""
        if not self.points:
            self.bounding_rect = QRectF()
            return
        
        min_x = min(p.x() for p in self.points)
        max_x = max(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_y = max(p.y() for p in self.points)
        
        # Add padding for line width
        padding = self.style.get('pen_width', 2) / 2
        self.bounding_rect = QRectF(min_x - padding, min_y - padding,
                                     max_x - min_x + padding * 2,
                                     max_y - min_y + padding * 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.element_type,
            'style': self.style,
            'points': [{'x': p.x(), 'y': p.y()} for p in self.points],
            'text': self.text,
            'bounding_rect': {
                'x': self.bounding_rect.x(),
                'y': self.bounding_rect.y(),
                'width': self.bounding_rect.width(),
                'height': self.bounding_rect.height()
            },
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DrawingElement':
        """Create element from dictionary."""
        element = cls(data['type'], data.get('style', {}))
        element.id = data['id']
        element.points = [QPointF(p['x'], p['y']) for p in data.get('points', [])]
        element.text = data.get('text', '')
        rect = data.get('bounding_rect', {})
        element.bounding_rect = QRectF(rect.get('x', 0), rect.get('y', 0),
                                        rect.get('width', 0), rect.get('height', 0))
        element.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        element.modified_at = datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat()))
        return element


class Layer:
    """
    Represents a single layer in the drawing application.
    
    Each layer can contain multiple drawing elements and has properties
    for visibility, locking, opacity, and naming.
    """
    
    def __init__(self, name: str = "Layer", color: QColor = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.color = color if color else QColor(0, 0, 0)
        self.visible = True
        self.locked = False
        self.opacity = 1.0
        self.elements: List[DrawingElement] = []
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self._thumbnail: Optional[QImage] = None
    
    def add_element(self, element: DrawingElement):
        """Add a drawing element to the layer."""
        if not self.locked:
            self.elements.append(element)
            self.modified_at = datetime.now()
            self._thumbnail = None  # Invalidate thumbnail
    
    def remove_element(self, element_id: str) -> bool:
        """Remove an element by ID. Returns True if removed."""
        if self.locked:
            return False
        for i, element in enumerate(self.elements):
            if element.id == element_id:
                self.elements.pop(i)
                self.modified_at = datetime.now()
                self._thumbnail = None
                return True
        return False
    
    def get_element(self, element_id: str) -> Optional[DrawingElement]:
        """Get an element by ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None
    
    def clear(self):
        """Clear all elements from the layer."""
        if not self.locked:
            self.elements.clear()
            self.modified_at = datetime.now()
            self._thumbnail = None
    
    def set_visible(self, visible: bool):
        """Set layer visibility."""
        self.visible = visible
        self.modified_at = datetime.now()
    
    def set_locked(self, locked: bool):
        """Set layer lock state."""
        self.locked = locked
        self.modified_at = datetime.now()
    
    def set_opacity(self, opacity: float):
        """Set layer opacity (0.0 to 1.0)."""
        self.opacity = max(0.0, min(1.0, opacity))
        self.modified_at = datetime.now()
    
    def set_name(self, name: str):
        """Set layer name."""
        self.name = name
        self.modified_at = datetime.now()
    
    def set_color(self, color: QColor):
        """Set layer color (used for identification)."""
        self.color = color
        self.modified_at = datetime.now()
    
    def get_bounding_rect(self) -> QRectF:
        """Get the bounding rectangle of all elements."""
        if not self.elements:
            return QRectF()
        
        min_x = min(e.bounding_rect.left() for e in self.elements if not e.bounding_rect.isEmpty())
        max_x = max(e.bounding_rect.right() for e in self.elements if not e.bounding_rect.isEmpty())
        min_y = min(e.bounding_rect.top() for e in self.elements if not e.bounding_rect.isEmpty())
        max_y = max(e.bounding_rect.bottom() for e in self.elements if not e.bounding_rect.isEmpty())
        
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def render(self, painter: QPainter, scale: float = 1.0):
        """Render the layer to a QPainter."""
        if not self.visible:
            return
        
        painter.save()
        painter.setOpacity(self.opacity)
        
        for element in self.elements:
            self._render_element(painter, element, scale)
        
        painter.restore()
    
    def _render_element(self, painter: QPainter, element: DrawingElement, scale: float = 1.0):
        """Render a single drawing element."""
        style = element.style
        pen_color = QColor(style.get('pen_color', '#000000'))
        brush_color = QColor(style.get('brush_color', 'transparent'))
        pen_width = style.get('pen_width', 2)
        
        pen = QPen(pen_color, pen_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        
        brush = QBrush(Qt.NoBrush)
        if brush_color.isValid() and brush_color.alpha() > 0:
            brush = QBrush(brush_color)
        
        painter.setPen(pen)
        painter.setBrush(brush)
        
        if element.element_type == 'pen':
            if len(element.points) > 1:
                for i in range(1, len(element.points)):
                    painter.drawLine(element.points[i-1], element.points[i])
        
        elif element.element_type == 'line':
            if len(element.points) >= 2:
                painter.drawLine(element.points[0], element.points[1])
        
        elif element.element_type == 'rectangle':
            if len(element.points) >= 2:
                rect = QRectF(element.points[0], element.points[1])
                painter.drawRect(rect)
        
        elif element.element_type == 'ellipse':
            if len(element.points) >= 2:
                rect = QRectF(element.points[0], element.points[1])
                painter.drawEllipse(rect)
        
        elif element.element_type == 'arrow':
            if len(element.points) >= 2:
                self._draw_arrow(painter, element.points[0], element.points[1], pen_width)
        
        elif element.element_type == 'box':
            if len(element.points) >= 2:
                rect = QRectF(element.points[0], element.points[1])
                # Draw filled box with border
                fill_color = QColor(style.get('fill_color', '#ffffff'))
                fill_color.setAlpha(style.get('fill_alpha', 200))
                painter.fillRect(rect, fill_color)
                painter.drawRect(rect)
        
        elif element.element_type == 'text':
            font = painter.font()
            font_size = style.get('font_size', 14)
            font.setPointSize(font_size)
            
            # Apply text styles
            if style.get('bold', False):
                font.setBold(True)
            if style.get('italic', False):
                font.setItalic(True)
            if style.get('underline', False):
                font.setUnderline(True)
            
            # Apply heading/title styles
            style_type = style.get('text_style', 'normal')
            if style_type == 'heading':
                font.setPointSize(24)
                font.setBold(True)
            elif style_type == 'title':
                font.setPointSize(32)
                font.setBold(True)
            elif style_type == 'subtitle':
                font.setPointSize(18)
                font.setBold(True)
            
            painter.setFont(font)
            
            if element.points:
                painter.drawText(element.points[0], element.text)
            else:
                painter.drawText(0, 0, element.text)
        
        elif element.element_type == 'list':
            font = painter.font()
            font_size = style.get('font_size', 14)
            font.setPointSize(font_size)
            painter.setFont(font)
            
            list_type = style.get('list_type', 'bullet')
            y_offset = 0
            line_height = font_size + 8
            
            if element.points:
                start_pos = element.points[0]
                for i, line in enumerate(element.text.split('\n')):
                    if list_type == 'bullet':
                        painter.drawText(start_pos.x(), start_pos.y() + y_offset, "• " + line)
                    elif list_type == 'numbered':
                        painter.drawText(start_pos.x(), start_pos.y() + y_offset, f"{i+1}. {line}")
                    else:
                        painter.drawText(start_pos.x(), start_pos.y() + y_offset, line)
                    y_offset += line_height
    
    def _draw_arrow(self, painter: QPainter, start: QPointF, end: QPointF, pen_width: int):
        """Draw an arrow from start to end point."""
        import math
        
        painter.drawLine(start, end)
        
        # Calculate arrow head
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        arrow_length = 15 + pen_width * 2
        arrow_angle = math.pi / 6
        
        x1 = end.x() - arrow_length * math.cos(angle - arrow_angle)
        y1 = end.y() - arrow_length * math.sin(angle - arrow_angle)
        x2 = end.x() - arrow_length * math.cos(angle + arrow_angle)
        y2 = end.y() - arrow_length * math.sin(angle + arrow_angle)
        
        painter.drawLine(end, QPointF(x1, y1))
        painter.drawLine(end, QPointF(x2, y2))
    
    def get_thumbnail(self, size: QSize = QSize(100, 100)) -> QImage:
        """Generate and return a thumbnail of the layer."""
        if self._thumbnail is not None:
            return self._thumbnail
        
        thumbnail = QImage(size, QImage.Format_ARGB32_Premultiplied)
        thumbnail.fill(Qt.transparent)
        
        painter = QPainter(thumbnail)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Scale to fit
        bounds = self.get_bounding_rect()
        if not bounds.isEmpty():
            scale_x = size.width() / bounds.width() if bounds.width() > 0 else 1
            scale_y = size.height() / bounds.height() if bounds.height() > 0 else 1
            scale = min(scale_x, scale_y) * 0.9
            
            painter.translate(size.width() / 2, size.height() / 2)
            painter.scale(scale, scale)
            painter.translate(-bounds.center())
        
        self.render(painter)
        painter.end()
        
        self._thumbnail = thumbnail
        return thumbnail
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert layer to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color.name(),
            'visible': self.visible,
            'locked': self.locked,
            'opacity': self.opacity,
            'elements': [e.to_dict() for e in self.elements],
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Layer':
        """Create layer from dictionary."""
        layer = cls(data.get('name', 'Layer'), QColor(data.get('color', '#000000')))
        layer.id = data['id']
        layer.visible = data.get('visible', True)
        layer.locked = data.get('locked', False)
        layer.opacity = data.get('opacity', 1.0)
        layer.elements = [DrawingElement.from_dict(e) for e in data.get('elements', [])]
        layer.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        layer.modified_at = datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat()))
        return layer


class LayerGroup:
    """
    Represents a group of layers that can be managed together.
    
    Layer groups allow organizing layers hierarchically and
    applying operations to multiple layers at once.
    """
    
    def __init__(self, name: str = "Group"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.layers: List[Layer] = []
        self.visible = True
        self.locked = False
        self.expanded = True
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
    
    def add_layer(self, layer: Layer):
        """Add a layer to the group."""
        if layer not in self.layers:
            self.layers.append(layer)
            self.modified_at = datetime.now()
    
    def remove_layer(self, layer: Layer) -> bool:
        """Remove a layer from the group."""
        if layer in self.layers:
            self.layers.remove(layer)
            self.modified_at = datetime.now()
            return True
        return False
    
    def set_visible(self, visible: bool):
        """Set visibility for all layers in group."""
        self.visible = visible
        for layer in self.layers:
            layer.set_visible(visible)
        self.modified_at = datetime.now()
    
    def set_locked(self, locked: bool):
        """Set lock state for all layers in group."""
        self.locked = locked
        for layer in self.layers:
            layer.set_locked(locked)
        self.modified_at = datetime.now()
    
    def set_expanded(self, expanded: bool):
        """Set expanded state in layer tree."""
        self.expanded = expanded
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'type': 'group',
            'visible': self.visible,
            'locked': self.locked,
            'expanded': self.expanded,
            'layers': [l.to_dict() for l in self.layers],
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerGroup':
        """Create group from dictionary."""
        group = cls(data.get('name', 'Group'))
        group.id = data['id']
        group.visible = data.get('visible', True)
        group.locked = data.get('locked', False)
        group.expanded = data.get('expanded', True)
        group.layers = [Layer.from_dict(l) for l in data.get('layers', [])]
        group.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        group.modified_at = datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat()))
        return group
