"""
Shared Files Page Module

Provides a full-page widget for browsing and managing shared files.
Includes auto-save functionality for shared files.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QInputDialog, QLineEdit, QFrame, QSplitter, QListWidget,
    QListWidgetItem, QComboBox, QGroupBox, QFormLayout, QDialog,
    QDialogButtonBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from app.client.api_client import APIClient
from app.client.auth_manager import AuthManager


class SharedFilesPage(QWidget):
    """
    Full-page widget for managing shared files.
    
    Provides:
    - List of owned files with sharing options
    - List of shared files from other users
    - File sharing management
    - Auto-save functionality
    """
    
    # Signals
    back_requested = pyqtSignal()
    file_opened = pyqtSignal(dict)  # File data
    auto_save_triggered = pyqtSignal(int, dict)  # file_id, content
    
    def __init__(self, auth_manager: AuthManager, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.api_client = api_client
        
        self._files: List[Dict[str, Any]] = []
        self._owned_files: List[Dict[str, Any]] = []
        self._shared_files: List[Dict[str, Any]] = []
        self._current_file: Optional[Dict[str, Any]] = None
        
        # Auto-save timer (saves every 30 seconds when file is modified)
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setInterval(30000)  # 30 seconds
        self._auto_save_timer.timeout.connect(self._auto_save)
        
        self._pending_auto_save = False
        self._auto_save_content: Optional[dict] = None
        
        self._setup_ui()
        self._load_files()
    
    def _setup_ui(self):
        """Set up the page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header with back button
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back to Canvas")
        back_btn.clicked.connect(self.back_requested.emit)
        back_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: #3498db;
                font-size: 14px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        
        # Auto-save indicator
        self.auto_save_label = QLabel("Auto-save: Enabled")
        self.auto_save_label.setStyleSheet("color: #27ae60; font-size: 12px;")
        header_layout.addWidget(self.auto_save_label)
        
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel("Shared Files")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Splitter for owned and shared files
        splitter = QSplitter(Qt.Vertical)
        
        # Owned files section
        owned_widget = QWidget()
        owned_layout = QVBoxLayout(owned_widget)
        owned_layout.setContentsMargins(0, 0, 0, 0)
        
        owned_label = QLabel("My Files")
        owned_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        owned_layout.addWidget(owned_label)
        
        self.owned_table = QTableWidget()
        self.owned_table.setColumnCount(5)
        self.owned_table.setHorizontalHeaderLabels(["Name", "Size", "Version", "Shared", "Actions"])
        self.owned_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.owned_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.owned_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.owned_table.itemSelectionChanged.connect(self._on_owned_selection_changed)
        owned_layout.addWidget(self.owned_table)
        
        # Action buttons for owned files
        owned_btn_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self._open_selected_file)
        self.open_btn.setEnabled(False)
        owned_btn_layout.addWidget(self.open_btn)
        
        self.share_btn = QPushButton("Share...")
        self.share_btn.clicked.connect(self._share_selected_file)
        self.share_btn.setEnabled(False)
        owned_btn_layout.addWidget(self.share_btn)
        
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._rename_selected_file)
        self.rename_btn.setEnabled(False)
        owned_btn_layout.addWidget(self.rename_btn)
        
        self.visibility_btn = QPushButton("Set Public")
        self.visibility_btn.clicked.connect(self._toggle_visibility)
        self.visibility_btn.setEnabled(False)
        owned_btn_layout.addWidget(self.visibility_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_selected_file)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("color: red;")
        owned_btn_layout.addWidget(self.delete_btn)
        
        owned_btn_layout.addStretch()
        owned_layout.addLayout(owned_btn_layout)
        
        splitter.addWidget(owned_widget)
        
        # Shared files section
        shared_widget = QWidget()
        shared_layout = QVBoxLayout(shared_widget)
        shared_layout.setContentsMargins(0, 0, 0, 0)
        
        shared_label = QLabel("Shared with Me")
        shared_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        shared_layout.addWidget(shared_label)
        
        self.shared_table = QTableWidget()
        self.shared_table.setColumnCount(5)
        self.shared_table.setHorizontalHeaderLabels(["Name", "Owner", "Permission", "Size", "Actions"])
        self.shared_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.shared_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.shared_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.shared_table.itemSelectionChanged.connect(self._on_shared_selection_changed)
        shared_layout.addWidget(self.shared_table)
        
        # Action buttons for shared files
        shared_btn_layout = QHBoxLayout()
        
        self.open_shared_btn = QPushButton("Open")
        self.open_shared_btn.clicked.connect(self._open_selected_shared_file)
        self.open_shared_btn.setEnabled(False)
        shared_btn_layout.addWidget(self.open_shared_btn)
        
        shared_btn_layout.addStretch()
        shared_layout.addLayout(shared_btn_layout)
        
        splitter.addWidget(shared_widget)
        
        splitter.setSizes([300, 200])
        layout.addWidget(splitter)
        
        # Refresh button
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_files)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_files(self):
        """Load files from the server."""
        if not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "Not Logged In", "Please login to view files.")
            return
        
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
            name_item = QTableWidgetItem(file.get('name', 'Untitled'))
            name_item.setData(Qt.UserRole, file)
            self.owned_table.setItem(row, 0, name_item)
            
            size = file.get('size', 0)
            size_str = self._format_size(size)
            self.owned_table.setItem(row, 1, QTableWidgetItem(size_str))
            
            version = file.get('version', 1)
            self.owned_table.setItem(row, 2, QTableWidgetItem(f"v{version}"))
            
            collaborators = file.get('collaborators', [])
            shared_count = len(collaborators)
            shared_text = f"{shared_count} user(s)" if shared_count else "No"
            if file.get('is_public'):
                shared_text += " + Public"
            self.owned_table.setItem(row, 3, QTableWidgetItem(shared_text))
            
            self.owned_table.setItem(row, 4, QTableWidgetItem(""))
        
        self.owned_table.resizeRowsToContents()
    
    def _populate_shared_table(self):
        """Populate the shared files table."""
        self.shared_table.setRowCount(len(self._shared_files))
        
        for row, file in enumerate(self._shared_files):
            name_item = QTableWidgetItem(file.get('name', 'Untitled'))
            name_item.setData(Qt.UserRole, file)
            self.shared_table.setItem(row, 0, name_item)
            
            owner = file.get('owner_username', 'Unknown')
            self.shared_table.setItem(row, 1, QTableWidgetItem(owner))
            
            current_user_id = self.auth_manager.current_user.get('id') if self.auth_manager.current_user else None
            permission = "View"
            for collab in file.get('collaborators', []):
                if collab.get('user_id') == current_user_id:
                    permission = collab.get('permission', 'view').capitalize()
                    break
            self.shared_table.setItem(row, 2, QTableWidgetItem(permission))
            
            size = file.get('size', 0)
            size_str = self._format_size(size)
            self.shared_table.setItem(row, 3, QTableWidgetItem(size_str))
            
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
                self.open_btn.setEnabled(True)
                self.share_btn.setEnabled(True)
                self.rename_btn.setEnabled(True)
                self.visibility_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                
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
                self.open_shared_btn.setEnabled(True)
                return
        
        self._current_file = None
        self.open_shared_btn.setEnabled(False)
    
    def _open_selected_file(self):
        """Open the selected owned file."""
        if self._current_file:
            self.file_opened.emit(self._current_file)
            self.back_requested.emit()
    
    def _open_selected_shared_file(self):
        """Open the selected shared file."""
        if self._current_file:
            self.file_opened.emit(self._current_file)
            self.back_requested.emit()
    
    def _share_selected_file(self):
        """Open share dialog for selected file."""
        if self._current_file:
            from app.dialogs.file_sharing_dialog import FileShareDialog
            dialog = FileShareDialog(
                self._current_file,
                self.api_client,
                self.auth_manager,
                self
            )
            dialog.exec_()
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
    
    def schedule_auto_save(self, file_id: int, content: dict):
        """Schedule an auto-save for a shared file."""
        self._pending_auto_save = True
        self._auto_save_file_id = file_id
        self._auto_save_content = content
        
        if not self._auto_save_timer.isActive():
            self._auto_save_timer.start()
            self.auto_save_label.setText("Auto-save: Pending...")
            self.auto_save_label.setStyleSheet("color: #f39c12; font-size: 12px;")
    
    def _auto_save(self):
        """Perform auto-save if there are pending changes."""
        if self._pending_auto_save and self._auto_save_content:
            self.auto_save_label.setText("Auto-save: Saving...")
            self.auto_save_label.setStyleSheet("color: #3498db; font-size: 12px;")
            
            self.auto_save_triggered.emit(self._auto_save_file_id, self._auto_save_content)
            
            self._pending_auto_save = False
            self.auto_save_label.setText("Auto-save: Saved")
            self.auto_save_label.setStyleSheet("color: #27ae60; font-size: 12px;")
            
            # Reset label after a moment
            QTimer.singleShot(2000, lambda: self.auto_save_label.setText("Auto-save: Enabled"))
    
    def stop_auto_save(self):
        """Stop the auto-save timer."""
        self._auto_save_timer.stop()
        self._pending_auto_save = False
    
    def refresh(self):
        """Refresh the page data."""
        self._load_files()
