"""
File Management and Sharing Dialog Module

Provides dialogs for:
- Browsing owned and shared files
- Sharing files with other users
- Managing file permissions
- Setting file visibility
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QInputDialog, QCheckBox, QGroupBox,
    QFormLayout, QListWidget, QListWidgetItem, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from app.client.api_client import APIClient
from app.client.auth_manager import AuthManager


class FileListDialog(QDialog):
    """
    Dialog for browsing and managing files (owned and shared).
    
    Provides:
    - List of owned files
    - List of shared files
    - Open, rename, delete, share actions
    - File sharing management
    """
    
    # Signals
    file_opened = pyqtSignal(dict)  # File data
    file_selected = pyqtSignal(dict)  # File data for current selection
    
    def __init__(self, api_client: APIClient, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.auth_manager = auth_manager
        
        self.setWindowTitle("My Files")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setModal(True)
        
        self._files: List[Dict[str, Any]] = []
        self._shared_files: List[Dict[str, Any]] = []
        self._current_file: Optional[Dict[str, Any]] = None
        
        self._setup_ui()
        self._load_files()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("File Manager")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Tab widget for owned vs shared files
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Owned files tab
        owned_tab = self._create_owned_tab()
        self.tab_widget.addTab(owned_tab, "My Files")
        
        # Shared with me tab
        shared_tab = self._create_shared_tab()
        self.tab_widget.addTab(shared_tab, "Shared with Me")
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_files)
        action_layout.addWidget(self.refresh_btn)
        
        action_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        action_layout.addWidget(self.close_btn)
        
        layout.addLayout(action_layout)
    
    def _create_owned_tab(self) -> QWidget:
        """Create the owned files tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Files table
        self.owned_table = QTableWidget()
        self.owned_table.setColumnCount(5)
        self.owned_table.setHorizontalHeaderLabels(["Name", "Size", "Version", "Shared", "Actions"])
        self.owned_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.owned_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.owned_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.owned_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.owned_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.owned_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.owned_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.owned_table.itemSelectionChanged.connect(self._on_owned_selection_changed)
        layout.addWidget(self.owned_table)
        
        # Action buttons for owned files
        btn_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self._open_selected_file)
        self.open_btn.setEnabled(False)
        btn_layout.addWidget(self.open_btn)
        
        self.share_btn = QPushButton("Share...")
        self.share_btn.clicked.connect(self._share_selected_file)
        self.share_btn.setEnabled(False)
        btn_layout.addWidget(self.share_btn)
        
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._rename_selected_file)
        self.rename_btn.setEnabled(False)
        btn_layout.addWidget(self.rename_btn)
        
        self.visibility_btn = QPushButton("Set Public")
        self.visibility_btn.clicked.connect(self._toggle_visibility)
        self.visibility_btn.setEnabled(False)
        btn_layout.addWidget(self.visibility_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_selected_file)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("color: red;")
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_shared_tab(self) -> QWidget:
        """Create the shared files tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info label
        info_label = QLabel("Files shared with you by other users:")
        layout.addWidget(info_label)
        
        # Shared files table
        self.shared_table = QTableWidget()
        self.shared_table.setColumnCount(5)
        self.shared_table.setHorizontalHeaderLabels(["Name", "Owner", "Permission", "Size", "Actions"])
        self.shared_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.shared_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.shared_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.shared_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.shared_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.shared_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.shared_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.shared_table.itemSelectionChanged.connect(self._on_shared_selection_changed)
        layout.addWidget(self.shared_table)
        
        # Action buttons for shared files
        btn_layout = QHBoxLayout()
        
        self.open_shared_btn = QPushButton("Open")
        self.open_shared_btn.clicked.connect(self._open_selected_shared_file)
        self.open_shared_btn.setEnabled(False)
        btn_layout.addWidget(self.open_shared_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
    
    def _load_files(self):
        """Load files from the server."""
        if not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "Not Logged In", "Please login to view files.")
            return
        
        # Load owned and shared files
        data, error = self.api_client.list_files(include_shared=True)
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to load files: {error}")
            return
        
        self._files = data.get('files', [])
        
        # Separate owned vs shared
        current_user_id = self.auth_manager.current_user.get('id') if self.auth_manager.current_user else None
        self._owned_files = [f for f in self._files if f.get('owner_id') == current_user_id]
        self._shared_files = [f for f in self._files if f.get('owner_id') != current_user_id]
        
        self._populate_owned_table()
        self._populate_shared_table()
    
    def _populate_owned_table(self):
        """Populate the owned files table."""
        self.owned_table.setRowCount(len(self._owned_files))
        
        for row, file in enumerate(self._owned_files):
            # Name
            name_item = QTableWidgetItem(file.get('name', 'Untitled'))
            name_item.setData(Qt.UserRole, file)
            self.owned_table.setItem(row, 0, name_item)
            
            # Size
            size = file.get('size', 0)
            size_str = self._format_size(size)
            self.owned_table.setItem(row, 1, QTableWidgetItem(size_str))
            
            # Version
            version = file.get('version', 1)
            self.owned_table.setItem(row, 2, QTableWidgetItem(f"v{version}"))
            
            # Shared count
            collaborators = file.get('collaborators', [])
            shared_count = len(collaborators)
            shared_text = f"{shared_count} user(s)" if shared_count else "No"
            if file.get('is_public'):
                shared_text += " + Public"
            self.owned_table.setItem(row, 3, QTableWidgetItem(shared_text))
            
            # Actions column (placeholder, actual actions via buttons)
            self.owned_table.setItem(row, 4, QTableWidgetItem(""))
        
        self.owned_table.resizeRowsToContents()
    
    def _populate_shared_table(self):
        """Populate the shared files table."""
        self.shared_table.setRowCount(len(self._shared_files))
        
        for row, file in enumerate(self._shared_files):
            # Name
            name_item = QTableWidgetItem(file.get('name', 'Untitled'))
            name_item.setData(Qt.UserRole, file)
            self.shared_table.setItem(row, 0, name_item)
            
            # Owner
            owner = file.get('owner_username', 'Unknown')
            self.shared_table.setItem(row, 1, QTableWidgetItem(owner))
            
            # Permission
            # Find my permission level
            current_user_id = self.auth_manager.current_user.get('id') if self.auth_manager.current_user else None
            permission = "View"
            for collab in file.get('collaborators', []):
                if collab.get('user_id') == current_user_id:
                    permission = collab.get('permission', 'view').capitalize()
                    break
            self.shared_table.setItem(row, 2, QTableWidgetItem(permission))
            
            # Size
            size = file.get('size', 0)
            size_str = self._format_size(size)
            self.shared_table.setItem(row, 3, QTableWidgetItem(size_str))
            
            # Actions column
            self.shared_table.setItem(row, 4, QTableWidgetItem(""))
        
        self.shared_table.resizeRowsToContents()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _on_owned_selection_changed(self):
        """Handle owned file selection."""
        row = self.owned_table.currentRow()
        if row >= 0:
            item = self.owned_table.item(row, 0)
            if item:
                self._current_file = item.data(Qt.UserRole)
                self.file_selected.emit(self._current_file)
                self.open_btn.setEnabled(True)
                self.share_btn.setEnabled(True)
                self.rename_btn.setEnabled(True)
                self.visibility_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                
                # Update visibility button text
                if self._current_file and self._current_file.get('is_public'):
                    self.visibility_btn.setText("Make Private")
                else:
                    self.visibility_btn.setText("Make Public")
                return
        
        self._current_file = None
        self.open_btn.setEnabled(False)
        self.share_btn.setEnabled(False)
        self.rename_btn.setEnabled(False)
        self.visibility_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
    
    def _on_shared_selection_changed(self):
        """Handle shared file selection."""
        row = self.shared_table.currentRow()
        if row >= 0:
            item = self.shared_table.item(row, 0)
            if item:
                self._current_file = item.data(Qt.UserRole)
                self.file_selected.emit(self._current_file)
                self.open_shared_btn.setEnabled(True)
                return
        
        self._current_file = None
        self.open_shared_btn.setEnabled(False)
    
    def _open_selected_file(self):
        """Open the selected owned file."""
        if self._current_file:
            self.file_opened.emit(self._current_file)
            self.accept()
    
    def _open_selected_shared_file(self):
        """Open the selected shared file."""
        if self._current_file:
            self.file_opened.emit(self._current_file)
            self.accept()
    
    def _share_selected_file(self):
        """Open share dialog for selected file."""
        if self._current_file:
            dialog = FileShareDialog(
                self._current_file,
                self.api_client,
                self.auth_manager,
                self
            )
            dialog.exec_()
            # Refresh files after sharing
            self._load_files()
    
    def _rename_selected_file(self):
        """Rename the selected file."""
        if not self._current_file:
            return
        
        new_name, ok = QInputDialog.getText(
            self, "Rename File",
            "New name:",
            QLineEdit.Normal,
            self._current_file.get('name', '')
        )
        
        if ok and new_name and new_name != self._current_file.get('name'):
            data, error = self.api_client.rename_file(self._current_file['id'], new_name)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to rename: {error}")
            else:
                self._load_files()
    
    def _toggle_visibility(self):
        """Toggle public visibility of selected file."""
        if not self._current_file:
            return
        
        current_public = self._current_file.get('is_public', False)
        new_public = not current_public
        
        data, error = self.api_client.set_file_visibility(self._current_file['id'], new_public)
        if error:
            QMessageBox.critical(self, "Error", f"Failed to update visibility: {error}")
        else:
            self._load_files()
    
    def _delete_selected_file(self):
        """Delete the selected file."""
        if not self._current_file:
            return
        
        reply = QMessageBox.question(
            self, "Delete File",
            f"Are you sure you want to delete '{self._current_file.get('name')}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            data, error = self.api_client.delete_file(self._current_file['id'])
            if error:
                QMessageBox.critical(self, "Error", f"Failed to delete: {error}")
            else:
                self._load_files()


class FileShareDialog(QDialog):
    """
    Dialog for sharing a file with other users.
    
    Allows:
    - Searching for users
    - Setting permission levels (View, Edit, Admin)
    - Managing existing collaborators
    - Making file public/private
    """
    
    def __init__(self, file_data: Dict[str, Any], api_client: APIClient, 
                 auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.file_data = file_data
        self.api_client = api_client
        self.auth_manager = auth_manager
        
        self.setWindowTitle(f"Share: {file_data.get('name', 'File')}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        self._collaborators: List[Dict[str, Any]] = file_data.get('collaborators', [])
        
        self._setup_ui()
        self._load_collaborators()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # File info
        info_group = QGroupBox("File Information")
        info_layout = QFormLayout(info_group)
        
        name_label = QLabel(self.file_data.get('name', 'Untitled'))
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Name:", name_label)
        
        owner_label = QLabel(self.file_data.get('owner_username', 'You'))
        info_layout.addRow("Owner:", owner_label)
        
        layout.addWidget(info_group)
        
        # Public visibility
        visibility_layout = QHBoxLayout()
        self.public_checkbox = QCheckBox("Make file public (anyone with link can view)")
        self.public_checkbox.setChecked(self.file_data.get('is_public', False))
        self.public_checkbox.stateChanged.connect(self._on_visibility_changed)
        visibility_layout.addWidget(self.public_checkbox)
        visibility_layout.addStretch()
        layout.addLayout(visibility_layout)
        
        # Current collaborators
        collab_group = QGroupBox("Current Collaborators")
        collab_layout = QVBoxLayout(collab_group)
        
        self.collab_list = QListWidget()
        self.collab_list.setMaximumHeight(150)
        collab_layout.addWidget(self.collab_list)
        
        # Remove collaborator button
        remove_layout = QHBoxLayout()
        remove_layout.addStretch()
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._remove_collaborator)
        self.remove_btn.setEnabled(False)
        remove_layout.addWidget(self.remove_btn)
        collab_layout.addLayout(remove_layout)
        
        layout.addWidget(collab_group)
        
        # Add new collaborator
        add_group = QGroupBox("Share with User")
        add_layout = QFormLayout(add_group)
        
        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText("Search by username or email...")
        self.user_search.textChanged.connect(self._on_search_changed)
        add_layout.addRow("User:", self.user_search)
        
        self.search_results = QListWidget()
        self.search_results.setMaximumHeight(100)
        self.search_results.itemClicked.connect(self._on_user_selected)
        add_layout.addRow("Results:", self.search_results)
        
        perm_layout = QHBoxLayout()
        self.permission_combo = QComboBox()
        self.permission_combo.addItems(["View", "Edit", "Admin"])
        perm_layout.addWidget(QLabel("Permission:"))
        perm_layout.addWidget(self.permission_combo)
        perm_layout.addStretch()
        
        self.add_btn = QPushButton("Share")
        self.add_btn.clicked.connect(self._add_collaborator)
        self.add_btn.setEnabled(False)
        perm_layout.addWidget(self.add_btn)
        
        add_layout.addRow("", perm_layout)
        layout.addWidget(add_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
        
        # Timer for search debounce
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._selected_user_id: Optional[int] = None
    
    def _load_collaborators(self):
        """Load current collaborators."""
        self.collab_list.clear()
        
        for collab in self._collaborators:
            username = collab.get('username', 'Unknown')
            permission = collab.get('permission', 'view').capitalize()
            item_text = f"{username} - {permission}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, collab)
            self.collab_list.addItem(item)
        
        if not self._collaborators:
            item = QListWidgetItem("(No collaborators yet)")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.collab_list.addItem(item)
        
        self.collab_list.itemSelectionChanged.connect(
            lambda: self.remove_btn.setEnabled(self.collab_list.currentRow() >= 0)
        )
    
    def _on_visibility_changed(self, state):
        """Handle public visibility toggle."""
        is_public = state == Qt.Checked
        data, error = self.api_client.set_file_visibility(self.file_data['id'], is_public)
        if error:
            QMessageBox.critical(self, "Error", f"Failed to update visibility: {error}")
            self.public_checkbox.setChecked(not is_public)
        else:
            self.file_data['is_public'] = is_public
    
    def _on_search_changed(self, text: str):
        """Handle search text change with debounce."""
        self._selected_user_id = None
        self.add_btn.setEnabled(False)
        self.search_results.clear()
        
        if len(text) >= 2:
            self._search_timer.start(300)  # 300ms debounce
    
    def _perform_search(self):
        """Perform user search."""
        query = self.user_search.text().strip()
        if len(query) < 2:
            return
        
        data, error = self.api_client.search_users(query, limit=10)
        
        if error:
            return
        
        self.search_results.clear()
        users = data.get('users', [])
        
        for user in users:
            # Skip self
            if user.get('id') == self.auth_manager.current_user.get('id'):
                continue
            item_text = f"{user.get('username', '')} ({user.get('email', '')})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, user)
            self.search_results.addItem(item)
        
        if not users:
            item = QListWidgetItem("(No users found)")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.search_results.addItem(item)
    
    def _on_user_selected(self, item: QListWidgetItem):
        """Handle user selection from search results."""
        user_data = item.data(Qt.UserRole)
        if user_data:
            self._selected_user_id = user_data.get('id')
            self.add_btn.setEnabled(True)
        else:
            self._selected_user_id = None
            self.add_btn.setEnabled(False)
    
    def _add_collaborator(self):
        """Share file with selected user."""
        if not self._selected_user_id:
            return
        
        permission = self.permission_combo.currentText().lower()
        
        data, error = self.api_client.share_file(
            self.file_data['id'],
            self._selected_user_id,
            permission
        )
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to share: {error}")
        else:
            QMessageBox.information(self, "Success", "File shared successfully!")
            self.user_search.clear()
            self.search_results.clear()
            self._selected_user_id = None
            self.add_btn.setEnabled(False)
            self._load_collaborators()
    
    def _remove_collaborator(self):
        """Remove selected collaborator."""
        item = self.collab_list.currentItem()
        if not item:
            return
        
        collab = item.data(Qt.UserRole)
        if not collab:
            return
        
        username = collab.get('username', 'Unknown')
        reply = QMessageBox.question(
            self, "Remove Collaborator",
            f"Remove {username} from this file?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            data, error = self.api_client.unshare_file(
                self.file_data['id'],
                collab.get('user_id')
            )
            
            if error:
                QMessageBox.critical(self, "Error", f"Failed to remove: {error}")
            else:
                self._load_collaborators()


class FileShareButton(QPushButton):
    """A button that opens the file sharing dialog."""
    
    def __init__(self, api_client: APIClient, auth_manager: AuthManager, 
                 get_current_file_id=None, parent=None):
        super().__init__("Share", parent)
        self.api_client = api_client
        self.auth_manager = auth_manager
        self.get_current_file_id = get_current_file_id
        
        self.setToolTip("Share current file with other users")
        self.clicked.connect(self._open_share_dialog)
    
    def _open_share_dialog(self):
        """Open share dialog for current file."""
        file_id = self.get_current_file_id() if self.get_current_file_id else None
        
        if not file_id:
            QMessageBox.information(
                self, "No File",
                "Please save the file to cloud first, then share it."
            )
            return
        
        # Load file data
        data, error = self.api_client.get_file(file_id, include_content=False)
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to load file: {error}")
            return
        
        file_data = data.get('file', {})
        
        dialog = FileShareDialog(file_data, self.api_client, self.auth_manager, self)
        dialog.exec_()
