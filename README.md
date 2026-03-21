# Drawing Application

A modular Qt-based drawing application with layer support, multiple drawing tools, text styles, and file management.

## Features

### Drawing Tools
- **Pen** - Freehand drawing with smooth strokes
- **Line** - Straight lines between two points
- **Rectangle** - Rectangle shapes with optional fill
- **Ellipse** - Oval/circle shapes
- **Arrow** - Lines with arrow heads
- **Box** - Filled rectangular containers
- **Text** - Text input with various styles
- **List** - Bullet or numbered lists
- **Select** - Select and move elements
- **Eraser** - Remove drawing elements

### Text Styles
- **Normal** - Standard text
- **Heading** - Larger bold text
- **Title** - Extra large bold text
- **Subtitle** - Medium bold text
- **Quote** - Italic text
- **Code** - Monospace font
- **Bold/Italic/Underline** - Text formatting
- **Font sizes** - 6-72pt

### Layer Management
- Create, delete, and rename layers
- Layer groups for organization
- Visibility toggle per layer
- Lock layers to prevent editing
- Opacity control
- Layer reordering (up/down)
- Overlay view to see all layers
- Custom layer colors for identification

### File Operations
- **Save/Open** - Custom `.draw` project format
- **Export** - PNG, JPEG, SVG formats
- **Auto-save** - Optional background saving

## Project Structure

```
├── main.py                 # Application entry point
├── app/
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   ├── canvas.py           # Drawing canvas widget
│   ├── layer_panel.py      # Layer management panel
│   ├── toolbar.py          # Tools and styles toolbar
│   ├── dialogs/
│   │   ├── __init__.py
│   │   └── export_dialog.py
│   └── core/
│       ├── __init__.py
│       ├── layer.py        # Layer and LayerGroup classes
│       ├── layer_manager.py
│       ├── tool.py         # Drawing tool classes
│       ├── tool_manager.py
│       ├── style.py        # Style definitions
│       └── file_handler.py # Save/Open/Export
├── pyproject.toml
└── poetry.lock
```

## Installation

```bash
# Using Poetry
poetry install

# Or using pip
pip install PyQt5 Pillow
```

## Usage

```bash
# Run the application
python main.py
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| P | Pen tool |
| L | Line tool |
| R | Rectangle tool |
| E | Ellipse tool |
| A | Arrow tool |
| T | Text tool |
| B | Box tool |
| I | List tool |
| S | Select tool |
| Ctrl+N | New project |
| Ctrl+O | Open project |
| Ctrl+S | Save project |
| Ctrl+Shift+N | New layer |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+0 | Reset zoom |
| Delete | Clear current layer |

## Architecture

The application follows a modular architecture:

1. **Core Module** (`app/core/`) - Contains the business logic:
   - `layer.py` - Layer and DrawingElement classes
   - `layer_manager.py` - Layer management and organization
   - `tool.py` - All drawing tool implementations
   - `tool_manager.py` - Tool state and style management
   - `style.py` - Drawing and text style definitions
   - `file_handler.py` - File operations

2. **UI Module** (`app/`) - Contains the user interface:
   - `canvas.py` - Interactive drawing area
   - `toolbar.py` - Tools and style controls
   - `layer_panel.py` - Layer management UI
   - `main_window.py` - Main application window

## Extending the Application

### Adding New Tools

1. Create a new tool class in `app/core/tool.py`:
```python
class MyTool(Tool):
    def __init__(self):
        super().__init__("MyTool", "🎨")
    
    def mouse_press(self, point, layer):
        # Handle mouse press
        pass
    
    def mouse_move(self, point, layer):
        # Handle mouse move
        pass
    
    def mouse_release(self, point, layer):
        # Handle mouse release
        pass
```

2. Register in `ToolManager._initialize_tools()`:
```python
tools.append(MyTool())
```

### Adding New File Formats

Extend `FileHandler` in `app/core/file_handler.py` to support additional formats.

## License

MIT License
