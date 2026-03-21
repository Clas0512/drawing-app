"""
Tool Manager module - Manages available tools and current tool state.

Handles tool switching, style management, and tool interactions.
"""

from typing import Dict, Optional, List, Callable
from PyQt5.QtCore import QObject, pyqtSignal

from app.core.tool import (
    Tool, PenTool, LineTool, RectangleTool, EllipseTool,
    ArrowTool, TextTool, BoxTool, ListTool, EraserTool, SelectTool
)
from app.core.style import CombinedStyle


class ToolManager(QObject):
    """
    Manages all available tools and the current active tool.
    
    Emits signals when tools change or styles are modified.
    """
    
    tool_changed = pyqtSignal(str)  # Tool name
    style_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.tools: Dict[str, Tool] = {}
        self.current_tool: Optional[Tool] = None
        self.style = CombinedStyle()
        
        # Initialize all tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools."""
        tools = [
            PenTool(),
            LineTool(),
            RectangleTool(),
            EllipseTool(),
            ArrowTool(),
            BoxTool(),
            TextTool(),
            ListTool(),
            EraserTool(),
            SelectTool(),
        ]
        
        for tool in tools:
            self.tools[tool.name] = tool
            tool.set_style(self.style)
        
        # Set default tool
        self.set_tool("Pen")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[Tool]:
        """Get list of all tools."""
        return list(self.tools.values())
    
    def get_tool_names(self) -> List[str]:
        """Get list of all tool names."""
        return list(self.tools.keys())
    
    def set_tool(self, name: str) -> bool:
        """Set the current active tool by name."""
        tool = self.tools.get(name)
        if tool is None:
            return False
        
        # Deactivate current tool
        if self.current_tool:
            self.current_tool.deactivate()
        
        # Activate new tool
        self.current_tool = tool
        tool.activate()
        
        # Update tool style
        tool.set_style(self.style)
        
        self.tool_changed.emit(name)
        return True
    
    def get_current_tool(self) -> Optional[Tool]:
        """Get the current active tool."""
        return self.current_tool
    
    def set_color(self, color):
        """Set the current color for drawing and text."""
        self.style.set_color(color)
        if self.current_tool:
            self.current_tool.set_style(self.style)
        self.style_changed.emit()
    
    def set_fill_color(self, color):
        """Set the fill color for shapes."""
        self.style.drawing.set_fill_color(color)
        if self.current_tool:
            self.current_tool.set_style(self.style)
        self.style_changed.emit()
    
    def set_pen_width(self, width: int):
        """Set the current pen width."""
        self.style.set_pen_width(width)
        if self.current_tool:
            self.current_tool.set_style(self.style)
        self.style_changed.emit()
    
    def set_text_style(self, style: str):
        """Set text style preset."""
        self.style.text.set_text_style(style)
        if self.current_tool and isinstance(self.current_tool, TextTool):
            self.current_tool.set_text_style(style)
        self.style_changed.emit()
    
    def set_list_type(self, list_type: str):
        """Set list type."""
        self.style.text.set_list_type(list_type)
        if self.current_tool and isinstance(self.current_tool, ListTool):
            self.current_tool.set_list_type(list_type)
        self.style_changed.emit()
    
    def set_bold(self, bold: bool):
        """Set bold text."""
        self.style.text.set_bold(bold)
        self.style_changed.emit()
    
    def set_italic(self, italic: bool):
        """Set italic text."""
        self.style.text.set_italic(italic)
        self.style_changed.emit()
    
    def set_font_size(self, size: int):
        """Set font size."""
        self.style.text.set_font_size(size)
        self.style_changed.emit()
    
    def get_current_style(self) -> CombinedStyle:
        """Get current combined style."""
        return self.style
    
    def to_dict(self) -> dict:
        """Convert tool manager state to dictionary."""
        return {
            'current_tool': self.current_tool.name if self.current_tool else 'Pen',
            'style': self.style.to_dict(),
        }
    
    def from_dict(self, data: dict):
        """Load tool manager state from dictionary."""
        if 'style' in data:
            self.style.from_dict(data['style'])
        
        if 'current_tool' in data:
            self.set_tool(data['current_tool'])
