# Drawing Application

A modular Qt-based drawing application with layer support, multiple drawing tools, text styles, file management, user authentication, and real-time collaboration.

## Quick Start

```bash
# 1. Install dependencies
pip install PyQt5 Pillow Flask Flask-SQLAlchemy Flask-Login Flask-SocketIO \
            Flask-CORS psycopg[binary] alembic PyJWT passlib python-dotenv \
            httpx python-socketio email-validator authlib

# 2. Setup database (interactive)
python setup_database.py

# 3. Start the server
python run_server.py

# 4. In another terminal, start the client
python main.py
```

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
├── setup_database.py       # Database setup script
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
│   ├── env.py             # Alembic environment
│   ├── script.py.mako     # Migration template
│   └── versions/          # Migration versions
│       └── 001_initial.py # Initial schema
└── pyproject.toml
```

## Installation

### Prerequisites

1. **Python 3.13+** - Make sure Python is installed
2. **PostgreSQL 12+** - Database server

### Installing Dependencies

```bash
# Using Poetry
poetry install

# Or using pip
pip install PyQt5 Pillow Flask Flask-SQLAlchemy Flask-Login Flask-SocketIO \
            Flask-CORS psycopg[binary] alembic PyJWT passlib python-dotenv \
            httpx python-socketio email-validator authlib
```

## Database Setup

### Step 1: Install and Start PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from https://www.postgresql.org/download/windows/

### Step 2: Configure Database Connection

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/drawing_app
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
```

### Step 3: Initialize the Database

**Option A: Using the setup script (Recommended)**

The setup script handles everything automatically - creating the database, running migrations, and optionally creating an admin user:

```bash
# Interactive setup (recommended for first-time setup)
python setup_database.py

# Or non-interactive full initialization
python setup_database.py --init --admin-user admin --admin-password yourpassword

# Other options:
python setup_database.py --create-db        # Create database only
python setup_database.py --migrate          # Run migrations only
python setup_database.py --reset            # Reset database (drop and recreate)
```

**Option B: Manual setup**

If you prefer manual setup:

```bash
# 1. Create the database (using psql or createdb)
sudo -u postgres psql -c "CREATE DATABASE drawing_app;"

# 2. Run migrations using Alembic
alembic upgrade head

# 3. Or create tables directly using Flask CLI
flask init-db

# 4. Create an admin user (optional)
flask create-admin admin admin@example.com yourpassword
```

**Option C: Using SQLAlchemy directly**

If migrations fail, you can create tables directly:

```python
# Run this in Python shell
from app.server.app_factory import create_app
from app.server.models.user import db

app = create_app('development')
with app.app_context():
    db.create_all()
    print("Tables created!")
```

### Step 4: Verify Database Setup

```bash
# Check database connection
python setup_database.py --migrate

# Or manually verify
psql -d drawing_app -c "\dt"  # List all tables
```

### Troubleshooting Database Issues

**Connection refused error:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                 # macOS

# Start if not running
sudo systemctl start postgresql   # Linux
brew services start postgresql    # macOS
```

**Authentication failed:**
```bash
# Reset PostgreSQL password
sudo -u postgres psql
ALTER USER postgres PASSWORD 'your_password';
```

**Database doesn't exist:**
```bash
# Create database manually
sudo -u postgres createdb drawing_app
# Or
python setup_database.py --create-db
```

**Permission denied:**
```bash
# Grant permissions to user
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE drawing_app TO postgres;
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
