"""
Profile Page Module

Provides a full-page widget for viewing and editing user profile.
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QProgressBar, QMessageBox,
    QLineEdit, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from app.client.auth_manager import AuthManager
from app.client.api_client import APIClient


class ProfilePage(QWidget):
    """
    Full-page widget for user profile management.
    
    Provides:
    - User information display and editing
    - Storage usage visualization
    - Account management options
    """
    
    # Signals
    back_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    
    def __init__(self, auth_manager: AuthManager, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.api_client = api_client
        
        self._setup_ui()
        self._load_user_data()
    
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
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel("Profile")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # User info group
        info_group = QGroupBox("Account Information")
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(15, 25, 15, 15)
        
        self.username_label = QLabel()
        self.username_label.setStyleSheet("font-size: 14px;")
        info_layout.addRow("Username:", self.username_label)
        
        self.email_label = QLabel()
        self.email_label.setStyleSheet("font-size: 14px;")
        info_layout.addRow("Email:", self.email_label)
        
        # Edit profile section
        edit_layout = QHBoxLayout()
        self.edit_username_input = QLineEdit()
        self.edit_username_input.setPlaceholderText("New username")
        self.edit_username_input.setMinimumHeight(35)
        edit_layout.addWidget(self.edit_username_input)
        
        self.edit_email_input = QLineEdit()
        self.edit_email_input.setPlaceholderText("New email")
        self.edit_email_input.setMinimumHeight(35)
        edit_layout.addWidget(self.edit_email_input)
        
        info_layout.addRow("Edit:", edit_layout)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setMinimumHeight(35)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_btn.clicked.connect(self._save_profile)
        info_layout.addRow("", save_btn)
        
        scroll_layout.addWidget(info_group)
        
        # Storage group
        storage_group = QGroupBox("Storage")
        storage_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        storage_layout = QVBoxLayout(storage_group)
        storage_layout.setContentsMargins(15, 25, 15, 15)
        storage_layout.setSpacing(10)
        
        self.storage_bar = QProgressBar()
        self.storage_bar.setRange(0, 100)
        self.storage_bar.setFormat("%p% used")
        self.storage_bar.setMinimumHeight(25)
        self.storage_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        storage_layout.addWidget(self.storage_bar)
        
        self.storage_label = QLabel()
        self.storage_label.setStyleSheet("color: #666; font-size: 12px;")
        storage_layout.addWidget(self.storage_label)
        
        scroll_layout.addWidget(storage_group)
        
        # Account actions group
        actions_group = QGroupBox("Account Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(15, 25, 15, 15)
        actions_layout.setSpacing(10)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setMinimumHeight(40)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_btn.clicked.connect(self._handle_logout)
        actions_layout.addWidget(logout_btn)
        
        scroll_layout.addWidget(actions_group)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def _load_user_data(self):
        """Load user data into the page."""
        user = self.auth_manager.current_user
        if user:
            self.username_label.setText(user.get('username', ''))
            self.email_label.setText(user.get('email', ''))
            self.edit_username_input.setPlaceholderText(f"Current: {user.get('username', '')}")
            self.edit_email_input.setPlaceholderText(f"Current: {user.get('email', '')}")
            
            storage_info = self.auth_manager.get_storage_info()
            if storage_info:
                percentage = storage_info.get('percentage', 0)
                self.storage_bar.setValue(int(percentage))
                
                # Change color based on usage
                if percentage > 80:
                    self.storage_bar.setStyleSheet("""
                        QProgressBar {
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            text-align: center;
                        }
                        QProgressBar::chunk {
                            background-color: #e74c3c;
                            border-radius: 4px;
                        }
                    """)
                elif percentage > 60:
                    self.storage_bar.setStyleSheet("""
                        QProgressBar {
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            text-align: center;
                        }
                        QProgressBar::chunk {
                            background-color: #f39c12;
                            border-radius: 4px;
                        }
                    """)
                
                used = storage_info.get('used', 0)
                limit = storage_info.get('limit', 0)
                remaining = storage_info.get('remaining', 0)
                
                used_mb = used / (1024 * 1024)
                limit_mb = limit / (1024 * 1024)
                remaining_mb = remaining / (1024 * 1024)
                
                self.storage_label.setText(
                    f"{used_mb:.2f} MB used of {limit_mb:.0f} MB "
                    f"({remaining_mb:.2f} MB remaining)"
                )
    
    def refresh(self):
        """Refresh the page data."""
        self._load_user_data()
    
    def _save_profile(self):
        """Save profile changes."""
        user = self.auth_manager.current_user
        if not user:
            return
        
        new_username = self.edit_username_input.text().strip()
        new_email = self.edit_email_input.text().strip()
        
        if not new_username and not new_email:
            QMessageBox.information(self, "No Changes", "No changes to save.")
            return
        
        data, error = self.api_client.update_user(
            user.get('id'),
            username=new_username if new_username else None,
            email=new_email if new_email else None
        )
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to update profile: {error}")
        else:
            QMessageBox.information(self, "Success", "Profile updated successfully!")
            self.edit_username_input.clear()
            self.edit_email_input.clear()
            self._load_user_data()
    
    def _handle_logout(self):
        """Handle logout button click."""
        reply = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()
