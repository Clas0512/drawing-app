"""
Authentication Manager Module

Manages user authentication state and session.
"""

from typing import Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal

from app.client.api_client import APIClient


class AuthManager(QObject):
    """
    Manages authentication state for the Qt application.
    
    Provides signals for authentication state changes and
    methods for login, logout, and registration.
    """
    
    # Signals
    logged_in = pyqtSignal(dict)  # User data
    logged_out = pyqtSignal()
    login_failed = pyqtSignal(str)  # Error message
    registration_failed = pyqtSignal(str)  # Error message
    user_updated = pyqtSignal(dict)  # Updated user data
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self._current_user: Optional[Dict[str, Any]] = None
        
        # Connect to API client signals
        self.api_client.token_expired.connect(self._on_token_expired)
    
    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current logged-in user."""
        return self._current_user
    
    @property
    def is_authenticated(self) -> bool:
        """Check if a user is authenticated."""
        return self._current_user is not None and self.api_client.is_authenticated()
    
    @property
    def user_id(self) -> Optional[int]:
        """Get the current user's ID."""
        return self._current_user.get('id') if self._current_user else None
    
    @property
    def username(self) -> Optional[str]:
        """Get the current user's username."""
        return self._current_user.get('username') if self._current_user else None
    
    def login(self, username: str, password: str) -> bool:
        """
        Login with credentials.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            True if login successful
        """
        data, error = self.api_client.login(username, password)
        
        if error:
            self.login_failed.emit(error)
            return False
        
        self._current_user = data.get('user')
        self.logged_in.emit(self._current_user)
        return True
    
    def register(self, username: str, email: str, password: str) -> bool:
        """
        Register a new user.
        
        Args:
            username: Desired username
            email: Email address
            password: Password
            
        Returns:
            True if registration successful
        """
        data, error = self.api_client.register(username, email, password)
        
        if error:
            self.registration_failed.emit(error)
            return False
        
        self._current_user = data.get('user')
        self.logged_in.emit(self._current_user)
        return True
    
    def logout(self):
        """Logout the current user."""
        if self.is_authenticated:
            self.api_client.logout()
        
        self._current_user = None
        self.logged_out.emit()
    
    def refresh_user(self) -> bool:
        """
        Refresh current user data from server.
        
        Returns:
            True if refresh successful
        """
        if not self.is_authenticated:
            return False
        
        data, error = self.api_client.get_current_user()
        
        if error:
            return False
        
        self._current_user = data.get('user')
        self.user_updated.emit(self._current_user)
        return True
    
    def try_auto_login(self) -> bool:
        """
        Try to auto-login using saved tokens.
        
        Returns:
            True if auto-login successful
        """
        if not self.api_client.is_authenticated():
            return False
        
        data, error = self.api_client.get_current_user()
        
        if error:
            # Try to refresh token
            refresh_data, refresh_error = self.api_client.refresh_token()
            
            if refresh_error:
                self.logout()
                return False
            
            data, error = self.api_client.get_current_user()
            
            if error:
                self.logout()
                return False
        
        self._current_user = data.get('user')
        self.logged_in.emit(self._current_user)
        return True
    
    def _on_token_expired(self):
        """Handle token expiration."""
        # Try to refresh the token
        data, error = self.api_client.refresh_token()
        
        if error:
            self.logout()
    
    def get_storage_info(self) -> Optional[Dict[str, Any]]:
        """Get storage info for current user."""
        if not self.is_authenticated:
            return None
        
        data, error = self.api_client.get_storage_info(self.user_id)
        
        if error:
            return None
        
        return data.get('storage')
