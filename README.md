# Drawing Application

A modular Qt-based drawing application with layer support, multiple drawing tools, text styles, file management, user authentication, and real-time collaboration.

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
- **Cloud Storage** - Save to cloud with user account

### User Authentication
- **Sign Up** - Create new user account
- **Login/Logout** - Session management
- **User Profile** - View and manage profile
- **Storage Quota** - 100MB default storage limit

### Real-time Collaboration
- **File Sharing** - Share files with other users
- **Permission Levels** - View, Edit, Admin permissions
- **Live Editing** - Multiple users edit simultaneously
- **Cursor Sharing** - See other users' cursors
- **Operation Sync** - Real-time operation broadcasting

## Project Structure

```
drawing-app/
├── main.py                 # Application entry point
├── run_server.py           # Flask server entry point
├── alembic.ini             # Database migration config
├── .env.example            # Environment variables template
├── app/
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   ├── canvas.py           # Drawing canvas widget
│   ├── layer_panel.py      # Layer management panel
│   ├── toolbar.py          # Tools and styles toolbar
│   ├── client/             # Client-side API services
│   │   ├── api_client.py   # HTTP API client
│   │   ├── auth_manager.py # Authentication manager
│   │   └── collaboration_client.py # WebSocket client
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── element_edit_dialog.py
│   │   ├── export_dialog.py
│   │   └── auth_dialog.py  # Login/Signup dialogs
│   ├── server/             # Flask server components
│   │   ├── config.py       # Server configuration
│   │   ├── app_factory.py  # Flask app factory
│   │   ├── models/         # Database models
│   │   │   ├── user.py     # User model
│   │   │   └── file.py     # File, Collaborator, Operation models
│   │   ├── routes/         # API routes
│   │   │   ├── auth_routes.py
│   │   │   ├── user_routes.py
│   │   │   ├── file_routes.py
│   │   │   └── collaboration_routes.py
│   │   └── services/       # Business logic services
│   │       ├── auth_service.py
│   │       ├── file_service.py
│   │       └── collaboration_service.py
│   └── core/
│       ├── __init__.py
│       ├── layer.py        # Layer and LayerGroup classes
│       ├── layer_manager.py
│       ├── tool.py         # Drawing tool classes
│       ├── tool_manager.py
│       ├── style.py        # Style definitions
│       └── file_handler.py # Save/Open/Export
├── migrations/             # Database migrations
└── pyproject.toml
```

## Installation

```bash
# Using Poetry
poetry install

# Or using pip
pip install PyQt5 Pillow Flask Flask-SQLAlchemy Flask-Login Flask-SocketIO \
            Flask-CORS psycopg[binary] alembic PyJWT passlib python-dotenv \
            httpx python-socketio email-validator authlib
```

## Database Setup

```bash
# Create PostgreSQL database
createdb drawing_app

# Run migrations
alembic upgrade head

# Or initialize database directly
flask init-db
```

## Usage

### Running the Client Application

```bash
# Run the Qt application
python main.py
```

### Running the Server

```bash
# Run the Flask API server
python run_server.py

# Or with specific options
python run_server.py --host 0.0.0.0 --port 5000 --debug
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

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Users
- `GET /api/users/<id>` - Get user profile
- `PUT /api/users/<id>` - Update user profile
- `DELETE /api/users/<id>` - Delete user account
- `GET /api/users/<id>/storage` - Get storage info
- `GET /api/users/search` - Search users

### Files
- `GET /api/files` - List accessible files
- `POST /api/files` - Create new file
- `GET /api/files/<id>` - Get file by ID
- `PUT /api/files/<id>` - Update file content
- `DELETE /api/files/<id>` - Delete file
- `POST /api/files/<id>/rename` - Rename file
- `POST /api/files/<id>/share` - Share file with user
- `POST /api/files/<id>/unshare` - Remove user access
- `POST /api/files/<id>/visibility` - Set public visibility

### Collaboration (WebSocket)
- `join_file` - Join a file's collaboration room
- `leave_file` - Leave collaboration room
- `operation` - Send drawing operation
- `request_sync` - Request missed operations
- `cursor_move` - Send cursor position
- `selection_change` - Send selection update

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

3. **Server Module** (`app/server/`) - Flask API server:
   - `models/` - SQLAlchemy database models
   - `routes/` - API endpoint handlers
   - `services/` - Business logic services

4. **Client Module** (`app/client/`) - Qt client services:
   - `api_client.py` - HTTP API client
   - `auth_manager.py` - Authentication state management
   - `collaboration_client.py` - WebSocket client

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://user:pass@localhost:5432/drawing_app
```

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
