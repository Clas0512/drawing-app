"""
Style module - Defines drawing and text styles for the application.

Styles control the appearance of drawing elements including
pen colors, widths, text formatting, and more.
"""

from typing import Dict, Any, List
from PyQt5.QtGui import QColor


class DrawingStyle:
    """
    Manages drawing styles including pen, brush, and line properties.
    
    Provides presets for common drawing styles and allows customization.
    """
    
    # Default color palette
    COLORS = {
        'black': '#000000',
        'white': '#FFFFFF',
        'red': '#FF0000',
        'green': '#00FF00',
        'blue': '#0000FF',
        'yellow': '#FFFF00',
        'cyan': '#00FFFF',
        'magenta': '#FF00FF',
        'orange': '#FFA500',
        'purple': '#800080',
        'pink': '#FFC0CB',
        'brown': '#A52A2A',
        'gray': '#808080',
        'dark_gray': '#404040',
        'light_gray': '#C0C0C0',
    }
    
    # Pen width presets
    PEN_WIDTHS = {
        'thin': 1,
        'normal': 2,
        'medium': 4,
        'thick': 8,
        'bold': 12,
        'extra_bold': 20,
    }
    
    def __init__(self):
        self.pen_color = QColor('#000000')
        self.brush_color = QColor(0, 0, 0, 0)  # Transparent
        self.pen_width = 2
        self.fill_color = QColor('#FFFFFF')
        self.fill_alpha = 200
        self.line_style = 'solid'  # solid, dashed, dotted
        self.cap_style = 'round'  # round, square, flat
        self.join_style = 'round'  # round, bevel, miter
    
    def set_pen_color(self, color: QColor):
        """Set the pen color."""
        self.pen_color = color
    
    def set_pen_color_by_name(self, name: str):
        """Set pen color by name from palette."""
        if name in self.COLORS:
            self.pen_color = QColor(self.COLORS[name])
        else:
            self.pen_color = QColor(name)
    
    def set_pen_width(self, width: int):
        """Set the pen width."""
        self.pen_width = max(1, width)
    
    def set_pen_width_preset(self, preset: str):
        """Set pen width by preset name."""
        if preset in self.PEN_WIDTHS:
            self.pen_width = self.PEN_WIDTHS[preset]
    
    def set_brush_color(self, color: QColor):
        """Set the brush color."""
        self.brush_color = color
    
    def set_fill_color(self, color: QColor, alpha: int = 200):
        """Set the fill color for shapes."""
        self.fill_color = color
        self.fill_alpha = max(0, min(255, alpha))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert style to dictionary."""
        return {
            'pen_color': self.pen_color.name(),
            'pen_color_alpha': self.pen_color.alpha(),
            'brush_color': self.brush_color.name(),
            'brush_color_alpha': self.brush_color.alpha(),
            'pen_width': self.pen_width,
            'fill_color': self.fill_color.name(),
            'fill_alpha': self.fill_alpha,
            'line_style': self.line_style,
            'cap_style': self.cap_style,
            'join_style': self.join_style,
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load style from dictionary."""
        self.pen_color = QColor(data.get('pen_color', '#000000'))
        self.pen_color.setAlpha(data.get('pen_color_alpha', 255))
        self.brush_color = QColor(data.get('brush_color', 'transparent'))
        self.brush_color.setAlpha(data.get('brush_color_alpha', 0))
        self.pen_width = data.get('pen_width', 2)
        self.fill_color = QColor(data.get('fill_color', '#FFFFFF'))
        self.fill_alpha = data.get('fill_alpha', 200)
        self.line_style = data.get('line_style', 'solid')
        self.cap_style = data.get('cap_style', 'round')
        self.join_style = data.get('join_style', 'round')
    
    def get_style_dict(self) -> Dict[str, Any]:
        """Get style as a dictionary for elements."""
        return {
            'pen_color': self.pen_color.name(),
            'pen_color_alpha': self.pen_color.alpha(),
            'brush_color': self.brush_color.name(),
            'pen_width': self.pen_width,
            'fill_color': self.fill_color.name(),
            'fill_alpha': self.fill_alpha,
            'line_style': self.line_style,
        }


class TextStyle:
    """
    Manages text styles including font properties and formatting.
    
    Provides presets for headings, titles, normal text, and lists.
    """
    
    # Font size presets
    FONT_SIZES = {
        'small': 10,
        'normal': 14,
        'medium': 18,
        'large': 24,
        'title': 32,
        'heading': 24,
        'subtitle': 18,
    }
    
    # Text style presets
    TEXT_STYLES = ['normal', 'heading', 'title', 'subtitle', 'quote', 'code']
    
    # List types
    LIST_TYPES = ['bullet', 'numbered', 'plain']
    
    def __init__(self):
        self.font_size = 14
        self.font_family = 'Arial'
        self.bold = False
        self.italic = False
        self.underline = False
        self.strikethrough = False
        self.text_style = 'normal'  # normal, heading, title, subtitle
        self.list_type = 'bullet'  # bullet, numbered, plain
        self.color = QColor('#000000')
        self.alignment = 'left'  # left, center, right, justify
    
    def set_font_size(self, size: int):
        """Set font size."""
        self.font_size = max(6, size)
    
    def set_font_size_preset(self, preset: str):
        """Set font size by preset name."""
        if preset in self.FONT_SIZES:
            self.font_size = self.FONT_SIZES[preset]
    
    def set_bold(self, bold: bool):
        """Set bold state."""
        self.bold = bold
    
    def set_italic(self, italic: bool):
        """Set italic state."""
        self.italic = italic
    
    def set_underline(self, underline: bool):
        """Set underline state."""
        self.underline = underline
    
    def set_text_style(self, style: str):
        """Set text style preset."""
        if style in self.TEXT_STYLES:
            self.text_style = style
            # Apply associated formatting
            if style == 'heading':
                self.font_size = 24
                self.bold = True
                self.italic = False
            elif style == 'title':
                self.font_size = 32
                self.bold = True
                self.italic = False
            elif style == 'subtitle':
                self.font_size = 18
                self.bold = True
                self.italic = False
            elif style == 'quote':
                self.font_size = 14
                self.italic = True
                self.bold = False
            elif style == 'code':
                self.font_family = 'Courier New'
                self.bold = False
                self.italic = False
    
    def set_list_type(self, list_type: str):
        """Set list type."""
        if list_type in self.LIST_TYPES:
            self.list_type = list_type
    
    def set_color(self, color: QColor):
        """Set text color."""
        self.color = color
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert style to dictionary."""
        return {
            'font_size': self.font_size,
            'font_family': self.font_family,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
            'strikethrough': self.strikethrough,
            'text_style': self.text_style,
            'list_type': self.list_type,
            'color': self.color.name(),
            'alignment': self.alignment,
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load style from dictionary."""
        self.font_size = data.get('font_size', 14)
        self.font_family = data.get('font_family', 'Arial')
        self.bold = data.get('bold', False)
        self.italic = data.get('italic', False)
        self.underline = data.get('underline', False)
        self.strikethrough = data.get('strikethrough', False)
        self.text_style = data.get('text_style', 'normal')
        self.list_type = data.get('list_type', 'bullet')
        self.color = QColor(data.get('color', '#000000'))
        self.alignment = data.get('alignment', 'left')
    
    def get_style_dict(self) -> Dict[str, Any]:
        """Get style as a dictionary for elements."""
        return {
            'font_size': self.font_size,
            'font_family': self.font_family,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
            'text_style': self.text_style,
            'list_type': self.list_type,
            'color': self.color.name(),
            'alignment': self.alignment,
        }


class CombinedStyle:
    """
    Combines drawing and text styles for unified style management.
    
    Used by the tool manager to maintain current style state.
    """
    
    def __init__(self):
        self.drawing = DrawingStyle()
        self.text = TextStyle()
        self.current_color = QColor('#000000')
    
    def set_color(self, color: QColor):
        """Set both pen and text color."""
        self.current_color = color
        self.drawing.set_pen_color(color)
        self.text.set_color(color)
    
    def set_pen_width(self, width: int):
        """Set pen width."""
        self.drawing.set_pen_width(width)
    
    def get_pen_width(self) -> int:
        """Get current pen width."""
        return self.drawing.pen_width
    
    def get_style_dict(self) -> Dict[str, Any]:
        """Get style as a dictionary for elements - combines drawing and text styles."""
        # Start with drawing style
        style = self.drawing.get_style_dict()
        # Add text style
        style.update(self.text.get_style_dict())
        # Add current color
        style['current_color'] = self.current_color.name()
        return style
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'drawing': self.drawing.to_dict(),
            'text': self.text.to_dict(),
            'current_color': self.current_color.name(),
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load from dictionary."""
        if 'drawing' in data:
            self.drawing.from_dict(data['drawing'])
        if 'text' in data:
            self.text.from_dict(data['text'])
        self.current_color = QColor(data.get('current_color', '#000000'))
