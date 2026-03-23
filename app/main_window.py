"""
Main Window module - The main application window.

Integrates all components: canvas, toolbar, layer panel,
and provides menu bar with file operations.
"""

import os
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QAction, QStatusBar, QLabel, QMessageBox,
    QFileDialog, QToolBar, QDockWidget, QApplication, QStackedWidget
)
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QCloseEvent

from app.canvas import Canvas
from app.toolbar import ToolToolbar
from app.layer_panel import LayerPanel
from app.core.layer_manager import LayerManager
from app.core.tool_manager import ToolManager
from app.core.file_handler import FileHandler
from app.core.tool import TextTool, ListTool
from PyQt5.QtWidgets import QInputDialog, QLineEdit

# Import client components
from app.client.api_client import APIClient
from app.client.auth_manager import AuthManager
from app.client.collaboration_client import CollaborationClient
from app.dialogs.auth_dialog import AuthDialog, UserProfileDialog
from app.dialogs.file_sharing_dialog import FileListDialog, FileShareDialog

# Import pages
from app.pages.profile_page import ProfilePage
from app.pages.shared_files_page import SharedFilesPage


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Provides the complete drawing application interface with:
    - Menu bar for file operations
    - Toolbar for tools and styles
    - Canvas for drawing
    - Layer panel for layer management
    - Status bar for feedback
    - User authentication and cloud storage
    - Real-time collaboration
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Drawing Application")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize core components
        self.layer_manager = LayerManager()
        self.tool_manager = ToolManager()
        self.file_handler = FileHandler()
        
        # Initialize client components
        self._init_client_components()
        
        # Initialize UI
        self._init_ui()
        self._create_menus()
        self._create_status_bar()
        self._connect_signals()
        
        # Settings
        self.settings = QSettings("DrawingApp", "DrawingApp")
        self._load_settings()
        
        # Try auto-login
        self._try_auto_login()
        
        # Current cloud file ID
        self._cloud_file_id: Optional[int] = None
        self._file_version: int = 0
    
    def _init_client_components(self):
        """Initialize API client and authentication components."""
        # API client
        self.api_client = APIClient()
        
        # Auth manager
        self.auth_manager = AuthManager(self.api_client)
        
        # Collaboration client
        self.collaboration_client = CollaborationClient()
    
    def _try_auto_login(self):
        """Try to auto-login with saved credentials."""
        if self.auth_manager.try_auto_login():
            self._on_logged_in(self.auth_manager.current_user)
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Central widget with stacked layout for pages
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        
        # Main drawing view (canvas with panels)
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel: Toolbar
        self.toolbar_widget = ToolToolbar(self.tool_manager)
        self.toolbar_widget.setMinimumWidth(280)
        self.toolbar_widget.setMaximumWidth(350)
        splitter.addWidget(self.toolbar_widget)
        
        # Center: Canvas
        self.canvas = Canvas(self.layer_manager, self.tool_manager)
        self.canvas.drawing_changed.connect(self._on_drawing_changed)
        self.canvas.cursor_position_changed.connect(self._on_cursor_position_changed)
        
        # Connect toolbar zoom to canvas
        self.toolbar_widget.zoom_slider.valueChanged.connect(
            lambda v: self.canvas.set_zoom(v / 100.0)
        )
        self.toolbar_widget.grid_btn.clicked.connect(
            lambda checked: self.canvas.set_show_grid(checked)
        )
        
        splitter.addWidget(self.canvas)
        
        # Right panel: Layer panel
        self.layer_panel = LayerPanel(self.layer_manager)
        splitter.addWidget(self.layer_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 800, 300])
        
        # Connect toolbar to canvas for some features
        self.toolbar_widget.grid_btn.clicked.connect(
            lambda checked: self.canvas.set_show_grid(checked)
        )
        
        # Set up text input callback for Text tool
        text_tool = self.tool_manager.get_tool("Text")
        if text_tool and isinstance(text_tool, TextTool):
            text_tool.set_text_input_callback(self._get_text_input)
        
        # Set up list input callback for List tool
        list_tool = self.tool_manager.get_tool("List")
        if list_tool and isinstance(list_tool, ListTool):
            list_tool.set_pending_items_callback(self._get_list_input)
        
        # Connect layer panel changes to canvas update
        self.layer_panel.layer_changed.connect(lambda: self.canvas.update())
        
        # Add main widget to stack
        self.central_stack.addWidget(main_widget)
        
        # Create pages
        self._create_pages()
    
    def _create_pages(self):
        """Create page widgets for navigation."""
        # Profile page
        self.profile_page = ProfilePage(self.auth_manager, self.api_client, self)
        self.profile_page.back_requested.connect(self._show_canvas_view)
        self.profile_page.logout_requested.connect(self._handle_logout)
        self.central_stack.addWidget(self.profile_page)
        
        # Shared files page
        self.shared_files_page = SharedFilesPage(self.auth_manager, self.api_client, self)
        self.shared_files_page.back_requested.connect(self._show_canvas_view)
        self.shared_files_page.file_opened.connect(self._on_file_manager_open)
        self.shared_files_page.auto_save_triggered.connect(self._perform_auto_save)
        self.central_stack.addWidget(self.shared_files_page)
    
    def _show_canvas_view(self):
        """Show the main canvas view."""
        self.central_stack.setCurrentIndex(0)
    
    def _show_profile_page(self):
        """Show the profile page."""
        if self.auth_manager.is_authenticated:
            self.profile_page.refresh()
            self.central_stack.setCurrentWidget(self.profile_page)
    
    def _show_shared_files_page(self):
        """Show the shared files page."""
        if self.auth_manager.is_authenticated:
            self.shared_files_page.refresh()
            self.central_stack.setCurrentWidget(self.shared_files_page)
    
    def _create_menus(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        # Open from Cloud action
        self.open_cloud_action = QAction("Open from &Cloud...", self)
        self.open_cloud_action.triggered.connect(self._open_from_cloud)
        self.open_cloud_action.setEnabled(False)
        file_menu.addAction(self.open_cloud_action)
        
        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        # Save to Cloud action
        self.save_cloud_action = QAction("Save to Clou&d...", self)
        self.save_cloud_action.triggered.connect(self._save_to_cloud)
        self.save_cloud_action.setEnabled(False)
        file_menu.addAction(self.save_cloud_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu("&Export")
        
        export_png_action = QAction("Export as &PNG...", self)
        export_png_action.triggered.connect(lambda: self._export_image("png"))
        export_menu.addAction(export_png_action)
        
        export_jpg_action = QAction("Export as &JPEG...", self)
        export_jpg_action.triggered.connect(lambda: self._export_image("jpg"))
        export_menu.addAction(export_jpg_action)
        
        export_svg_action = QAction("Export as &SVG...", self)
        export_svg_action.triggered.connect(lambda: self._export_image("svg"))
        export_menu.addAction(export_svg_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        clear_action = QAction("&Clear Canvas", self)
        clear_action.triggered.connect(self.canvas.clear_canvas)
        edit_menu.addAction(clear_action)
        
        # Store history
        self._history = []
        self._history_index = -1
        self._max_history = 50
        
        # Connect drawing changes to history
        self.canvas.drawing_changed.connect(self._save_to_history)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        grid_action = QAction("Show &Grid", self)
        grid_action.setCheckable(True)
        grid_action.toggled.connect(self.canvas.set_show_grid)
        view_menu.addAction(grid_action)
        
        # Layer menu
        layer_menu = menubar.addMenu("&Layer")
        
        new_layer_action = QAction("&New Layer", self)
        new_layer_action.setShortcut("Ctrl+Shift+N")
        new_layer_action.triggered.connect(self.layer_panel._add_layer)
        layer_menu.addAction(new_layer_action)
        
        new_group_action = QAction("New &Group", self)
        new_group_action.triggered.connect(self.layer_panel._add_group)
        layer_menu.addAction(new_group_action)
        
        layer_menu.addSeparator()
        
        toggle_overlay_action = QAction("Toggle &Overlay", self)
        toggle_overlay_action.setCheckable(True)
        toggle_overlay_action.setChecked(True)
        toggle_overlay_action.toggled.connect(self.layer_manager.set_overlay_visible)
        layer_menu.addAction(toggle_overlay_action)
        
        # Account menu
        account_menu = menubar.addMenu("&Account")
        
        self.login_action = QAction("&Login...", self)
        self.login_action.triggered.connect(self._show_login_dialog)
        account_menu.addAction(self.login_action)
        
        self.profile_action = QAction("&Profile...", self)
        self.profile_action.triggered.connect(self._show_profile_page)
        self.profile_action.setEnabled(False)
        account_menu.addAction(self.profile_action)
        
        self.logout_action = QAction("&Logout", self)
        self.logout_action.triggered.connect(self._handle_logout)
        self.logout_action.setEnabled(False)
        account_menu.addAction(self.logout_action)
        
        # Files menu (cloud file management)
        files_menu = menubar.addMenu("&Files")
        
        self.my_files_action = QAction("&My Files...", self)
        self.my_files_action.setShortcut("Ctrl+Shift+F")
        self.my_files_action.triggered.connect(self._show_shared_files_page)
        self.my_files_action.setEnabled(False)
        files_menu.addAction(self.my_files_action)
        
        files_menu.addSeparator()
        
        self.share_file_action = QAction("&Share Current File...", self)
        self.share_file_action.triggered.connect(self._share_current_file)
        self.share_file_action.setEnabled(False)
        files_menu.addAction(self.share_file_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = self.statusBar()
        
        # Position label
        self.position_label = QLabel("X: 0, Y: 0")
        self.status_bar.addPermanentWidget(self.position_label)
        
        # Tool label
        self.tool_label = QLabel("Tool: Pen")
        self.status_bar.addWidget(self.tool_label)
        
        # Layer label
        self.layer_label = QLabel("Layer: Background")
        self.status_bar.addWidget(self.layer_label)
        
        # User label
        self.user_label = QLabel("Not logged in")
        self.status_bar.addWidget(self.user_label)
        
        # Modified indicator
        self.modified_label = QLabel("")
        self.status_bar.addWidget(self.modified_label)
    
    def _connect_signals(self):
        """Connect all signals."""
        self.tool_manager.tool_changed.connect(
            lambda name: self.tool_label.setText(f"Tool: {name}")
        )
        
        self.layer_manager.current_layer_changed.connect(
            lambda layer: self.layer_label.setText(f"Layer: {layer.name}")
        )
        
        self.file_handler.file_saved.connect(self._on_file_saved)
        self.file_handler.file_opened.connect(self._on_file_opened)
        self.file_handler.file_error.connect(self._on_file_error)
        
        # Auth signals
        self.auth_manager.logged_in.connect(self._on_logged_in)
        self.auth_manager.logged_out.connect(self._on_logged_out)
        
        # Collaboration signals
        self.collaboration_client.operation_received.connect(self._on_operation_received)
        self.collaboration_client.user_joined.connect(self._on_user_joined)
        self.collaboration_client.user_left.connect(self._on_user_left)
    
    def _on_logged_in(self, user: dict):
        """Handle successful login."""
        self.user_label.setText(f"User: {user.get('username', 'Unknown')}")
        self.login_action.setEnabled(False)
        self.profile_action.setEnabled(True)
        self.logout_action.setEnabled(True)
        self.open_cloud_action.setEnabled(True)
        self.save_cloud_action.setEnabled(True)
        self.my_files_action.setEnabled(True)
        self.share_file_action.setEnabled(True)
        
        # Connect collaboration client
        self.collaboration_client.set_token(self.api_client._access_token)
    
    def _on_logged_out(self):
        """Handle logout."""
        self.user_label.setText("Not logged in")
        self.login_action.setEnabled(True)
        self.profile_action.setEnabled(False)
        self.logout_action.setEnabled(False)
        self.open_cloud_action.setEnabled(False)
        self.save_cloud_action.setEnabled(False)
        self.my_files_action.setEnabled(False)
        self.share_file_action.setEnabled(False)
        
        # Disconnect collaboration client
        self.collaboration_client.clear_token()
        self.collaboration_client.disconnect()
        self._cloud_file_id = None
    
    def _show_login_dialog(self):
        """Show the login dialog."""
        dialog = AuthDialog(self.auth_manager, self)
        dialog.exec_()
    
    def _handle_logout(self):
        """Handle logout button click."""
        reply = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_manager.logout()
    
    def _open_from_cloud(self):
        """Open a file from cloud storage."""
        if not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "Not Logged In", "Please login to access cloud files.")
            return
        
        # Get list of files
        data, error = self.api_client.list_files()
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to load files: {error}")
            return
        
        files = data.get('files', [])
        
        if not files:
            QMessageBox.information(self, "No Files", "No files found in your cloud storage.")
            return
        
        # Show file selection dialog
        from PyQt5.QtWidgets import QDialog, QListWidget, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Open from Cloud")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Select a file to open:")
        layout.addWidget(label)
        
        file_list = QListWidget()
        for f in files:
            file_list.addItem(f"{f['name']} (v{f['version']})")
        file_list.setProperty('files', files)
        layout.addWidget(file_list)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Open | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted and file_list.currentRow() >= 0:
            selected_file = files[file_list.currentRow()]
            self._load_cloud_file(selected_file['id'])
    
    def _on_file_manager_open(self, file_data: dict):
        """Handle file opened from file manager."""
        file_id = file_data.get('id')
        if file_id:
            self._load_cloud_file(file_id)
    
    def _share_current_file(self):
        """Open share dialog for current cloud file."""
        if not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "Not Logged In", "Please login to share files.")
            return
        
        if not self._cloud_file_id:
            QMessageBox.information(
                self, "No Cloud File",
                "Please save this file to cloud first, then share it.\n\n"
                "Use File > Save to Cloud..."
            )
            return
        
        # Load file data
        data, error = self.api_client.get_file(self._cloud_file_id, include_content=False)
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to load file: {error}")
            return
        
        file_data = data.get('file', {})
        
        dialog = FileShareDialog(file_data, self.api_client, self.auth_manager, self)
        dialog.exec_()
    
    def _load_cloud_file(self, file_id: int):
        """Load a file from cloud storage."""
        data, error = self.api_client.get_file(file_id, include_content=True)
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to load file: {error}")
            return
        
        file_data = data.get('file', {})
        content = file_data.get('content', {})
        
        # Leave previous collaboration room if any
        if self._cloud_file_id and self.collaboration_client.is_connected:
            self.collaboration_client.leave_file(self._cloud_file_id)
        
        if content:
            self.layer_manager.from_dict(content.get('layer_manager', {}))
            self._cloud_file_id = file_id
            self._file_version = file_data.get('version', 0)
            self.canvas._buffer_valid = False
            self.canvas.update()
            self.setWindowTitle(f"Drawing Application - {file_data['name']} (Cloud)")
            
            # Join collaboration room for real-time sync with other users
            if self.collaboration_client.is_connected:
                self.collaboration_client.join_file(file_id)
    
    def _save_to_cloud(self):
        """Save current project to cloud storage."""
        if not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "Not Logged In", "Please login to save to cloud.")
            return
        
        # Get file name
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, "Save to Cloud", "File name:",
            QLineEdit.Normal,
            os.path.basename(self.file_handler.current_file) if self.file_handler.current_file else "Untitled"
        )
        
        if not ok or not name:
            return
        
        # Prepare content
        content = {
            'layer_manager': self.layer_manager.to_dict(),
            'tool_manager': self.tool_manager.to_dict()
        }
        
        if self._cloud_file_id:
            # Update existing file
            data, error = self.api_client.update_file(
                self._cloud_file_id, content, self._file_version
            )
        else:
            # Create new file
            data, error = self.api_client.create_file(name, content)
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to save file: {error}")
            return
        
        file_data = data.get('file', {})
        new_file_id = file_data.get('id')
        
        # If this is a new file (not an update), join collaboration room
        if self._cloud_file_id != new_file_id:
            if self._cloud_file_id and self.collaboration_client.is_connected:
                self.collaboration_client.leave_file(self._cloud_file_id)
            self._cloud_file_id = new_file_id
            if self.collaboration_client.is_connected:
                self.collaboration_client.join_file(new_file_id)
        
        self._file_version = file_data.get('version', 1)
        
        QMessageBox.information(self, "Success", f"File saved to cloud as '{name}'")
        self.setWindowTitle(f"Drawing Application - {name} (Cloud)")
    
    def _on_operation_received(self, operation: dict):
        """Handle received operation from collaboration."""
        # Apply operation to local state
        op_type = operation.get('type')
        op_data = operation.get('data', {})
        
        if op_type == 'full_sync':
            content = op_data.get('content', {})
            if content:
                self.layer_manager.from_dict(content.get('layer_manager', {}))
                self._file_version = operation.get('version', self._file_version)
                self.canvas._buffer_valid = False
                self.canvas.update()
    
    def _on_user_joined(self, data: dict):
        """Handle user joined collaboration."""
        username = data.get('username', 'Unknown')
        self.status_bar.showMessage(f"{username} joined the session")
    
    def _on_user_left(self, data: dict):
        """Handle user left collaboration."""
        username = data.get('username', 'Unknown')
        self.status_bar.showMessage(f"{username} left the session")
    
    def _on_drawing_changed(self):
        """Handle drawing changes."""
        self.file_handler.set_modified()
        self.modified_label.setText("*")
        
        # Send operation to collaboration if connected
        if self.collaboration_client.is_connected and self._cloud_file_id:
            content = {
                'layer_manager': self.layer_manager.to_dict(),
                'tool_manager': self.tool_manager.to_dict()
            }
            self.collaboration_client.send_operation('full_sync', {'content': content})
            
            # Schedule auto-save for shared files
            if self._cloud_file_id:
                self.shared_files_page.schedule_auto_save(self._cloud_file_id, content)
    
    def _on_cursor_position_changed(self, pos):
        """Handle cursor position change."""
        self.position_label.setText(f"X: {int(pos.x())}, Y: {int(pos.y())}")
        
        # Send cursor position to collaboration
        if self.collaboration_client.is_connected and self._cloud_file_id:
            self.collaboration_client.send_cursor_position({
                'x': pos.x(),
                'y': pos.y()
            })
    
    def _on_file_saved(self, path: str):
        """Handle file saved."""
        self.setWindowTitle(f"Drawing Application - {os.path.basename(path)}")
        self.modified_label.setText("")
    
    def _on_file_opened(self, path: str):
        """Handle file opened."""
        self.setWindowTitle(f"Drawing Application - {os.path.basename(path)}")
        self.modified_label.setText("")
        self.canvas._buffer_valid = False
        self.canvas.update()
    
    def _on_file_error(self, error: str):
        """Handle file error."""
        QMessageBox.critical(self, "File Error", error)
    
    def _new_project(self):
        """Create a new project."""
        if self.file_handler.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "New Project",
                "Save current project before creating new?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                self._save_project()
        
        # Leave collaboration room for previous file
        if self._cloud_file_id and self.collaboration_client.is_connected:
            self.collaboration_client.leave_file(self._cloud_file_id)
        
        self.file_handler.new_project(self.layer_manager, self.tool_manager)
        self.canvas._buffer_valid = False
        self.canvas.update()
        self.setWindowTitle("Drawing Application - Untitled")
        self._cloud_file_id = None
        self._file_version = 0
    
    def _open_project(self):
        """Open a project file."""
        if self.file_handler.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Open Project",
                "Save current project before opening?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                self._save_project()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project",
            "", self.file_handler.get_project_filter()
        )
        
        if file_path:
            self.file_handler.open_project(
                file_path, self.layer_manager, self.tool_manager
            )
    
    def _save_project(self):
        """Save the current project."""
        if self.file_handler.current_file:
            self.file_handler.save_project(
                self.file_handler.current_file,
                self.layer_manager, self.tool_manager
            )
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        """Save project with new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project",
            "", self.file_handler.get_project_filter()
        )
        
        if file_path:
            if not file_path.endswith(self.file_handler.PROJECT_EXTENSION):
                file_path += self.file_handler.PROJECT_EXTENSION
            
            self.file_handler.save_project(
                file_path, self.layer_manager, self.tool_manager
            )
    
    def _export_image(self, format: str):
        """Export current drawing to image."""
        filters = {
            'png': "PNG Image (*.png)",
            'jpg': "JPEG Image (*.jpg *.jpeg)",
            'svg': "SVG Image (*.svg)",
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Image",
            "", filters.get(format, "All Files (*)")
        )
        
        if file_path:
            # Ensure correct extension
            ext = 'jpg' if format == 'jpg' else format
            if not file_path.lower().endswith(f'.{ext}'):
                file_path += f'.{ext}'
            
            success = self.file_handler.export_image(
                file_path, self.layer_manager,
                width=self.canvas.canvas_width,
                height=self.canvas.canvas_height
            )
            
            if success:
                QMessageBox.information(self, "Export", f"Image exported to {file_path}")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Drawing Application",
            "Drawing Application v2.0\n\n"
            "A modular Qt-based drawing application with:\n"
            "• Multiple drawing tools\n"
            "• Layer management\n"
            "• Text styles (headings, titles, lists)\n"
            "• Export to various formats\n"
            "• Project save/load\n"
            "• Cloud storage\n"
            "• Real-time collaboration"
        )
    
    def _load_settings(self):
        """Load application settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
    
    def _get_text_input(self) -> Optional[str]:
        """Get text input from user via dialog."""
        text, ok = QInputDialog.getText(
            self, "Enter Text", "Text:",
            QLineEdit.Normal, ""
        )
        if ok and text:
            return text
        return None
    
    def _get_list_input(self) -> list:
        """Get list items from user via dialog."""
        text, ok = QInputDialog.getMultiLineText(
            self, "Enter List Items", "Enter one item per line:",
            ""
        )
        if ok and text:
            return [line.strip() for line in text.split('\n') if line.strip()]
        return ["List item"]
    
    def _save_to_history(self):
        """Save current state to history."""
        try:
            state = self.layer_manager.to_dict()
            # Remove future history if we're not at the end
            self._history = self._history[:self._history_index + 1]
            self._history.append(state)
            self._history_index = len(self._history) - 1
            
            # Limit history size
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
                self._history_index = len(self._history) - 1
        except Exception:
            pass
    
    def _undo(self):
        """Undo last action."""
        if self._history_index > 0:
            self._history_index -= 1
            self._restore_from_history(self._history[self._history_index])
    
    def _redo(self):
        """Redo last undone action."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_from_history(self._history[self._history_index])
    
    def _restore_from_history(self, state: dict):
        """Restore layer manager from history state."""
        try:
            self.layer_manager.from_dict(state)
            self.canvas._buffer_valid = False
            self.canvas.update()
        except Exception as e:
            pass
    
    def _perform_auto_save(self, file_id: int, content: dict):
        """Perform auto-save to cloud."""
        if not self.auth_manager.is_authenticated:
            return
        
        data, error = self.api_client.update_file(
            file_id, content, self._file_version
        )
        
        if not error:
            file_data = data.get('file', {})
            self._file_version = file_data.get('version', self._file_version + 1)
            self.status_bar.showMessage("Auto-saved", 3000)
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        if self.file_handler.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Quit",
                "Save changes before quitting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.Yes:
                self._save_project()
        
        # Leave collaboration room if in one
        if self._cloud_file_id and self.collaboration_client.is_connected:
            self.collaboration_client.leave_file(self._cloud_file_id)
        
        # Disconnect collaboration
        self.collaboration_client.disconnect()
        
        # Close API client
        self.api_client.close()
        
        # Save settings
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()
