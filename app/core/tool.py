"""
Tool module - Defines drawing tools for the application.

Tools include pen, line, shapes, text, arrows, boxes, and lists.
Each tool handles user input and creates appropriate drawing elements.
"""

from typing import Optional, Dict, Any, List, Callable
from abc import ABC, abstractmethod
from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QColor

from app.core.layer import Layer, DrawingElement
from app.core.style import CombinedStyle


class Tool(ABC):
    """
    Abstract base class for all drawing tools.
    
    Each tool handles mouse events and creates drawing elements
    on the current layer.
    """
    
    def __init__(self, name: str, icon: str = ""):
        self.name = name
        self.icon = icon
        self.active = False
        self.style: Optional[CombinedStyle] = None
        self.current_element: Optional[DrawingElement] = None
        self.start_point: Optional[QPointF] = None
    
    def set_style(self, style: CombinedStyle):
        """Set the current style for this tool."""
        self.style = style
    
    def activate(self):
        """Activate the tool."""
        self.active = True
    
    def deactivate(self):
        """Deactivate the tool."""
        self.active = False
        self.current_element = None
        self.start_point = None
    
    @abstractmethod
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        """Handle mouse press event. Returns True if drawing started."""
        pass
    
    @abstractmethod
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        """Handle mouse move event. Returns True if element updated."""
        pass
    
    @abstractmethod
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        """Handle mouse release event. Returns the completed element."""
        pass
    
    def get_style_dict(self) -> Dict[str, Any]:
        """Get current style as dictionary."""
        if self.style:
            return self.style.get_style_dict()
        return {'pen_color': '#000000', 'pen_width': 2}


class PenTool(Tool):
    """Freehand drawing tool (pen/pencil)."""
    
    def __init__(self):
        super().__init__("Pen", "✏️")
        self.smoothing = True
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('pen', self.get_style_dict())
        self.current_element.add_point(point)
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if self.current_element is None or layer.locked:
            return False
        
        self.current_element.add_point(point)
        return True
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element


class LineTool(Tool):
    """Straight line drawing tool."""
    
    def __init__(self):
        super().__init__("Line", "📏")
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('line', self.get_style_dict())
        self.current_element.add_point(point)
        self.current_element.add_point(point)  # End point, updated on move
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if self.current_element is None or layer.locked:
            return False
        
        # Update end point
        if len(self.current_element.points) >= 2:
            self.current_element.points[1] = point
            self.current_element._update_bounding_rect()
        return True
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element


class RectangleTool(Tool):
    """Rectangle drawing tool."""
    
    def __init__(self):
        super().__init__("Rectangle", "⬜")
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('rectangle', self.get_style_dict())
        self.current_element.add_point(point)
        self.current_element.add_point(point)
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if self.current_element is None or layer.locked:
            return False
        
        if len(self.current_element.points) >= 2:
            self.current_element.points[1] = point
            self.current_element._update_bounding_rect()
        return True
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element


class EllipseTool(Tool):
    """Ellipse/Oval drawing tool."""
    
    def __init__(self):
        super().__init__("Ellipse", "⬭")
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('ellipse', self.get_style_dict())
        self.current_element.add_point(point)
        self.current_element.add_point(point)
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if self.current_element is None or layer.locked:
            return False
        
        if len(self.current_element.points) >= 2:
            self.current_element.points[1] = point
            self.current_element._update_bounding_rect()
        return True
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element


class ArrowTool(Tool):
    """Arrow drawing tool."""
    
    def __init__(self):
        super().__init__("Arrow", "➡️")
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('arrow', self.get_style_dict())
        self.current_element.add_point(point)
        self.current_element.add_point(point)
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if self.current_element is None or layer.locked:
            return False
        
        if len(self.current_element.points) >= 2:
            self.current_element.points[1] = point
            self.current_element._update_bounding_rect()
        return True
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element


class BoxTool(Tool):
    """Filled box/container drawing tool."""
    
    def __init__(self):
        super().__init__("Box", "📦")
        self.fill_alpha = 200  # Default fill alpha (transparency)
    
    def get_style_dict(self) -> Dict[str, Any]:
        style = super().get_style_dict()
        # Preserve fill_color from style (set by fill color button)
        # If not set, use white with default alpha
        if 'fill_color' not in style or not style.get('fill_color'):
            style['fill_color'] = '#FFFFFF'
        if 'fill_alpha' not in style:
            style['fill_alpha'] = self.fill_alpha
        return style
    
    def set_fill_alpha(self, alpha: int):
        """Set the fill transparency (0-255)."""
        self.fill_alpha = max(0, min(255, alpha))
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('box', self.get_style_dict())
        self.current_element.add_point(point)
        self.current_element.add_point(point)
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if self.current_element is None or layer.locked:
            return False
        
        if len(self.current_element.points) >= 2:
            self.current_element.points[1] = point
            self.current_element._update_bounding_rect()
        return True
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element


class TextTool(Tool):
    """Text input tool."""
    
    def __init__(self):
        super().__init__("Text", "T")
        self.text_style = 'normal'
        self.pending_text: Optional[str] = None
        self.text_input_callback = None  # Callback to get text from UI
    
    def set_text_style(self, style: str):
        """Set text style preset."""
        self.text_style = style
    
    def get_style_dict(self) -> Dict[str, Any]:
        style = super().get_style_dict()
        style['text_style'] = self.text_style
        style['font_size'] = 14
        style['bold'] = self.text_style in ['heading', 'title']
        return style
    
    def set_text_input_callback(self, callback):
        """Set callback to get text input from user."""
        self.text_input_callback = callback
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        # Get text from callback if available
        text = "Text"
        if self.text_input_callback:
            try:
                result = self.text_input_callback()
                if result:
                    text = result
            except Exception:
                pass
        elif self.pending_text:
            text = self.pending_text
        
        self.start_point = point
        self.current_element = DrawingElement('text', self.get_style_dict())
        self.current_element.add_point(point)
        self.current_element.set_text(text)
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        # Text doesn't update on move
        return False
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element
    
    def set_pending_text(self, text: str):
        """Set text to be used for next text element."""
        self.pending_text = text


class ListTool(Tool):
    """List creation tool (bullet or numbered)."""
    
    def __init__(self):
        super().__init__("List", "☰")
        self.list_type = 'bullet'
        self.pending_items: List[str] = []
        self.items_input_callback = None  # Callback to get list items from UI
    
    def set_list_type(self, list_type: str):
        """Set list type (bullet or numbered)."""
        self.list_type = list_type
    
    def get_style_dict(self) -> Dict[str, Any]:
        style = super().get_style_dict()
        style['list_type'] = self.list_type
        style['font_size'] = 14
        return style
    
    def set_pending_items_callback(self, callback):
        """Set callback to get list items from user."""
        self.items_input_callback = callback
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        # Get items from callback if available
        items = self.pending_items if self.pending_items else ["List item"]
        if self.items_input_callback:
            try:
                result = self.items_input_callback()
                if result:
                    items = result
            except Exception:
                pass
        
        self.start_point = point
        self.current_element = DrawingElement('list', self.get_style_dict())
        self.current_element.add_point(point)
        
        # Join items with newlines
        text = '\n'.join(items) if items else "List item"
        self.current_element.set_text(text)
        layer.add_element(self.current_element)
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        return False
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        if self.current_element is None:
            return None
        
        element = self.current_element
        self.current_element = None
        self.start_point = None
        return element
    
    def set_pending_items(self, items: List[str]):
        """Set list items to be used for next list element."""
        self.pending_items = items


class EraserTool(Tool):
    """Eraser tool for removing content."""
    
    def __init__(self):
        super().__init__("Eraser", "🧹")
        self.erased_elements: List[DrawingElement] = []
    
    def get_style_dict(self) -> Dict[str, Any]:
        # Eraser uses white pen with larger width
        return {
            'pen_color': '#FFFFFF',
            'pen_width': 20,
        }
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.erased_elements.clear()
        return True
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        # Find and remove elements near the eraser point
        eraser_radius = 15
        to_remove = []
        
        for element in layer.elements:
            for p in element.points:
                if (p.x() - point.x()) ** 2 + (p.y() - point.y()) ** 2 < eraser_radius ** 2:
                    to_remove.append(element)
                    break
        
        for element in to_remove:
            if element in layer.elements:
                layer.elements.remove(element)
                self.erased_elements.append(element)
        
        if to_remove:
            layer.modified_at = layer.modified_at.__class__.now()
            layer._thumbnail = None
            return True
        
        return False
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        self.start_point = None
        self.erased_elements.clear()
        return None


class SelectTool(Tool):
    """Selection tool for selecting and moving elements."""
    
    def __init__(self):
        super().__init__("Select", "🖐️")
        self.selected_element: Optional[DrawingElement] = None
        self.selection_offset = QPointF(0, 0)
        self.hit_tolerance = 10  # Pixels tolerance for hit detection
    
    def _point_in_element(self, point: QPointF, element: DrawingElement) -> bool:
        """Check if point is inside or near an element."""
        if not element.points:
            return False
        
        # For elements with bounding rect (shapes), check if point is inside
        if element.element_type in ['rectangle', 'ellipse', 'box']:
            if len(element.points) >= 2:
                rect = QRectF(element.points[0], element.points[1])
                # Expand rect by tolerance
                expanded = rect.adjusted(-self.hit_tolerance, -self.hit_tolerance,
                                        self.hit_tolerance, self.hit_tolerance)
                return expanded.contains(point)
        
        # For lines and arrows, check distance to line segment
        if element.element_type in ['line', 'arrow']:
            if len(element.points) >= 2:
                return self._point_near_line(point, element.points[0], element.points[1])
        
        # For pen paths, check distance to any point
        if element.element_type == 'pen':
            for p in element.points:
                if abs(p.x() - point.x()) < self.hit_tolerance and \
                   abs(p.y() - point.y()) < self.hit_tolerance:
                    return True
            # Also check distance to line segments
            for i in range(1, len(element.points)):
                if self._point_near_line(point, element.points[i-1], element.points[i]):
                    return True
        
        # For text and lists, check if near the start point
        if element.element_type in ['text', 'list']:
            if element.points:
                p = element.points[0]
                # Estimate text bounds (rough)
                return abs(p.x() - point.x()) < 100 and abs(p.y() - point.y()) < 50
        
        # Fallback: check any point
        for p in element.points:
            if abs(p.x() - point.x()) < self.hit_tolerance and \
               abs(p.y() - point.y()) < self.hit_tolerance:
                return True
        
        return False
    
    def _point_near_line(self, point: QPointF, p1: QPointF, p2: QPointF) -> bool:
        """Check if point is near a line segment."""
        # Calculate distance from point to line segment
        x0, y0 = point.x(), point.y()
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        
        # Line segment length squared
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy
        
        if length_sq == 0:
            # Point is the same
            return abs(x0 - x1) < self.hit_tolerance and abs(y0 - y1) < self.hit_tolerance
        
        # Calculate projection parameter
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / length_sq))
        
        # Nearest point on line
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        
        # Distance to nearest point
        dist = ((x0 - nearest_x) ** 2 + (y0 - nearest_y) ** 2) ** 0.5
        
        return dist < self.hit_tolerance
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        self.start_point = point
        
        # Find element at point (check from top to bottom)
        for element in reversed(layer.elements):
            if self._point_in_element(point, element):
                self.selected_element = element
                # Calculate offset from first point
                if element.points:
                    self.selection_offset = QPointF(point.x() - element.points[0].x(),
                                                    point.y() - element.points[0].y())
                return True
        
        self.selected_element = None
        return False
    
    def mouse_move(self, point: QPointF, layer: Layer) -> bool:
        if self.selected_element is None or layer.locked:
            return False
        
        # Move all points by delta
        delta = QPointF(
            point.x() - self.start_point.x(),
            point.y() - self.start_point.y()
        )
        
        for p in self.selected_element.points:
            p.setX(p.x() + delta.x())
            p.setY(p.y() + delta.y())
        
        self.selected_element._update_bounding_rect()
        self.start_point = point
        layer.modified_at = layer.modified_at.__class__.now()
        layer._thumbnail = None
        return True
    
    def mouse_release(self, point: QPointF, layer: Layer) -> Optional[DrawingElement]:
        element = self.selected_element
        self.selected_element = None
        self.start_point = None
        return element
