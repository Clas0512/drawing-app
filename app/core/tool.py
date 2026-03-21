"""
Tool module - Defines drawing tools for the application.

Tools include pen, line, shapes, text, arrows, boxes, and lists.
Each tool handles user input and creates appropriate drawing elements.
"""

from typing import Optional, Dict, Any, List, Callable
from abc import ABC, abstractmethod
from PyQt5.QtCore import QPointF, Qt
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
        self.fill_color = QColor('#FFFFFF')
        self.fill_alpha = 200
    
    def set_fill_color(self, color: QColor, alpha: int = 200):
        """Set the fill color."""
        self.fill_color = color
        self.fill_alpha = alpha
    
    def get_style_dict(self) -> Dict[str, Any]:
        style = super().get_style_dict()
        style['fill_color'] = self.fill_color.name()
        style['fill_alpha'] = self.fill_alpha
        return style
    
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
    
    def set_text_style(self, style: str):
        """Set text style preset."""
        self.text_style = style
    
    def get_style_dict(self) -> Dict[str, Any]:
        style = super().get_style_dict()
        style['text_style'] = self.text_style
        style['font_size'] = 14
        style['bold'] = self.text_style in ['heading', 'title']
        return style
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('text', self.get_style_dict())
        self.current_element.add_point(point)
        self.current_element.set_text(self.pending_text or "Text")
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
    
    def set_list_type(self, list_type: str):
        """Set list type (bullet or numbered)."""
        self.list_type = list_type
    
    def get_style_dict(self) -> Dict[str, Any]:
        style = super().get_style_dict()
        style['list_type'] = self.list_type
        style['font_size'] = 14
        return style
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        if layer.locked:
            return False
        
        self.start_point = point
        self.current_element = DrawingElement('list', self.get_style_dict())
        self.current_element.add_point(point)
        
        # Join items with newlines
        text = '\n'.join(self.pending_items) if self.pending_items else "List item"
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
    
    def mouse_press(self, point: QPointF, layer: Layer) -> bool:
        self.start_point = point
        
        # Find element at point
        for element in reversed(layer.elements):
            for p in element.points:
                if abs(p.x() - point.x()) < 10 and abs(p.y() - point.y()) < 10:
                    self.selected_element = element
                    self.selection_offset = QPointF(point.x() - p.x(), point.y() - p.y())
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
