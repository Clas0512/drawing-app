"""
Authentication Dialog Module

Provides login and signup dialogs for user authentication.
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout,
    QGroupBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from app.client.auth_manager import AuthManager


class AuthDialog(QDialog):
    """
    Dialog for user authentication (login and signup).
    
    Provides a tabbed interface for login and registration.
    """
    
    # Signals
    authenticated = pyqtSignal(dict)  # User data
    
    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        
        self.setWindowTitle("Drawing Application - Login")
        self.setMinimumWidth(400)
        self.setMinimumHeight(450)
        self.setModal(True)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Drawing Application")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Sign in to save and collaborate on drawings")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: gray;")
        layout.addWidget(subtitle_label)
        
        # Tab widget for login/signup
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Login tab
        login_widget = self._create_login_tab()
        self.tab_widget.addTab(login_widget, "Login")
        
        # Signup tab
        signup_widget = self._create_signup_tab()
        self.tab_widget.addTab(signup_widget, "Sign Up")
        
        # Skip login button (for offline mode)
        skip_layout = QHBoxLayout()
        skip_layout.addStretch()
        skip_btn = QPushButton("Continue Offline")
        skip_btn.setFlat(True)
        skip_btn.setStyleSheet("color: gray;")
        skip_btn.clicked.connect(self.reject)
        skip_layout.addWidget(skip_btn)
        layout.addLayout(skip_layout)
    
    def _create_login_tab(self) -> QWidget:
        """Create the login tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Username or email")
        self.login_username.setMinimumHeight(35)
        form_layout.addRow("Username:", self.login_username)
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setMinimumHeight(35)
        form_layout.addRow("Password:", self.login_password)
        
        layout.addLayout(form_layout)
        
        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.login_btn.clicked.connect(self._handle_login)
        layout.addWidget(self.login_btn)
        
        # Error label
        self.login_error = QLabel()
        self.login_error.setStyleSheet("color: red;")
        self.login_error.setWordWrap(True)
        self.login_error.hide()
        layout.addWidget(self.login_error)
        
        layout.addStretch()
        
        return widget
    
    def _create_signup_tab(self) -> QWidget:
        """Create the signup tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.signup_username = QLineEdit()
        self.signup_username.setPlaceholderText("Choose a username")
        self.signup_username.setMinimumHeight(35)
        form_layout.addRow("Username:", self.signup_username)
        
        self.signup_email = QLineEdit()
        self.signup_email.setPlaceholderText("Enter your email")
        self.signup_email.setMinimumHeight(35)
        form_layout.addRow("Email:", self.signup_email)
        
        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Choose a password (min 6 characters)")
        self.signup_password.setEchoMode(QLineEdit.Password)
        self.signup_password.setMinimumHeight(35)
        form_layout.addRow("Password:", self.signup_password)
        
        self.signup_confirm = QLineEdit()
        self.signup_confirm.setPlaceholderText("Confirm password")
        self.signup_confirm.setEchoMode(QLineEdit.Password)
        self.signup_confirm.setMinimumHeight(35)
        form_layout.addRow("Confirm:", self.signup_confirm)
        
        layout.addLayout(form_layout)
        
        # Storage info
        storage_label = QLabel("Free account includes 100MB storage")
        storage_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(storage_label)
        
        # Signup button
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setMinimumHeight(40)
        self.signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.signup_btn.clicked.connect(self._handle_signup)
        layout.addWidget(self.signup_btn)
        
        # Error label
        self.signup_error = QLabel()
        self.signup_error.setStyleSheet("color: red;")
        self.signup_error.setWordWrap(True)
        self.signup_error.hide()
        layout.addWidget(self.signup_error)
        
        layout.addStretch()
        
        return widget
    
    def _connect_signals(self):
        """Connect signals to handlers."""
        # Connect auth manager signals
        self.auth_manager.login_failed.connect(self._on_login_failed)
        self.auth_manager.registration_failed.connect(self._on_signup_failed)
        self.auth_manager.logged_in.connect(self._on_authenticated)
        
        # Enter key handling
        self.login_password.returnPressed.connect(self._handle_login)
        self.signup_confirm.returnPressed.connect(self._handle_signup)
    
    def _handle_login(self):
        """Handle login button click."""
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username:
            self._show_login_error("Please enter your username")
            return
        
        if not password:
            self._show_login_error("Please enter your password")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in...")
        self.login_error.hide()
        
        success = self.auth_manager.login(username, password)
        
        if not success:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Login")
    
    def _handle_signup(self):
        """Handle signup button click."""
        username = self.signup_username.text().strip()
        email = self.signup_email.text().strip()
        password = self.signup_password.text()
        confirm = self.signup_confirm.text()
        
        # Validation
        if not username:
            self._show_signup_error("Please enter a username")
            return
        
        if len(username) < 3:
            self._show_signup_error("Username must be at least 3 characters")
            return
        
        if not email:
            self._show_signup_error("Please enter your email")
            return
        
        if '@' not in email:
            self._show_signup_error("Please enter a valid email address")
            return
        
        if not password:
            self._show_signup_error("Please enter a password")
            return
        
        if len(password) < 6:
            self._show_signup_error("Password must be at least 6 characters")
            return
        
        if password != confirm:
            self._show_signup_error("Passwords do not match")
            return
        
        self.signup_btn.setEnabled(False)
        self.signup_btn.setText("Creating account...")
        self.signup_error.hide()
        
        success = self.auth_manager.register(username, email, password)
        
        if not success:
            self.signup_btn.setEnabled(True)
            self.signup_btn.setText("Create Account")
    
    def _show_login_error(self, message: str):
        """Show login error message."""
        self.login_error.setText(message)
        self.login_error.show()
    
    def _show_signup_error(self, message: str):
        """Show signup error message."""
        self.signup_error.setText(message)
        self.signup_error.show()
    
    def _on_login_failed(self, error: str):
        """Handle login failure."""
        self._show_login_error(error)
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Login")
    
    def _on_signup_failed(self, error: str):
        """Handle signup failure."""
        self._show_signup_error(error)
        self.signup_btn.setEnabled(True)
        self.signup_btn.setText("Create Account")
    
    def _on_authenticated(self, user: dict):
        """Handle successful authentication."""
        self.authenticated.emit(user)
        self.accept()
    
    def clear_forms(self):
        """Clear all form fields."""
        self.login_username.clear()
        self.login_password.clear()
        self.signup_username.clear()
        self.signup_email.clear()
        self.signup_password.clear()
        self.signup_confirm.clear()
        self.login_error.hide()
        self.signup_error.hide()
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Login")
        self.signup_btn.setEnabled(True)
        self.signup_btn.setText("Create Account")


class UserProfileDialog(QDialog):
    """
    Dialog for viewing and editing user profile.
    """
    
    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        
        self.setWindowTitle("User Profile")
        self.setMinimumWidth(400)
        
        self._setup_ui()
        self._load_user_data()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # User info group
        info_group = QGroupBox("Account Information")
        info_layout = QFormLayout(info_group)
        
        self.username_label = QLabel()
        info_layout.addRow("Username:", self.username_label)
        
        self.email_label = QLabel()
        info_layout.addRow("Email:", self.email_label)
        
        layout.addWidget(info_group)
        
        # Storage group
        storage_group = QGroupBox("Storage")
        storage_layout = QVBoxLayout(storage_group)
        
        self.storage_bar = QProgressBar()
        self.storage_bar.setRange(0, 100)
        self.storage_bar.setFormat("%p% used")
        storage_layout.addWidget(self.storage_bar)
        
        self.storage_label = QLabel()
        storage_layout.addWidget(self.storage_label)
        
        layout.addWidget(storage_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self._handle_logout)
        btn_layout.addWidget(logout_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_user_data(self):
        """Load user data into the dialog."""
        user = self.auth_manager.current_user
        if user:
            self.username_label.setText(user.get('username', ''))
            self.email_label.setText(user.get('email', ''))
            
            storage_info = self.auth_manager.get_storage_info()
            if storage_info:
                percentage = storage_info.get('percentage', 0)
                self.storage_bar.setValue(int(percentage))
                
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
            self.accept()
