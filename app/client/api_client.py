"""
API Client Module

Provides a client for communicating with the Flask server API.
"""

import json
from typing import Optional, Dict, Any, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
import httpx


class APIClient(QObject):
    """
    HTTP client for the drawing application API.
    
    Handles authentication, request formatting, and error handling.
    """
    
    # Signals
    request_failed = pyqtSignal(str)  # Error message
    token_expired = pyqtSignal()
    
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        super().__init__()
        self.base_url = base_url
        self.settings = QSettings("DrawingApp", "DrawingApp")
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        
        # Load tokens from settings
        self._load_tokens()
        
        # Create HTTP client
        self.client = httpx.Client(timeout=30.0)
    
    def _load_tokens(self):
        """Load tokens from settings."""
        self._access_token = self.settings.value("access_token")
        self._refresh_token = self.settings.value("refresh_token")
    
    def _save_tokens(self, access_token: str, refresh_token: str):
        """Save tokens to settings."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self.settings.setValue("access_token", access_token)
        self.settings.setValue("refresh_token", refresh_token)
    
    def _clear_tokens(self):
        """Clear tokens from settings."""
        self._access_token = None
        self._refresh_token = None
        self.settings.remove("access_token")
        self.settings.remove("refresh_token")
    
    def get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if include_auth and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        
        return headers
    
    def set_tokens(self, access_token: str, refresh_token: str):
        """Set authentication tokens."""
        self._save_tokens(access_token, refresh_token)
    
    def clear_tokens(self):
        """Clear authentication tokens."""
        self._clear_tokens()
    
    def is_authenticated(self) -> bool:
        """Check if client has valid tokens."""
        return self._access_token is not None
    
    def _handle_response(self, response: httpx.Response) -> Tuple[Dict[str, Any], Optional[str]]:
        """Handle HTTP response and return (data, error)."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            return {}, f"Invalid response: {response.text}"
        
        if response.status_code >= 400:
            error_msg = data.get('error', f"HTTP {response.status_code}")
            
            # Handle token expiration
            if response.status_code == 401:
                self.token_expired.emit()
            
            return {}, error_msg
        
        return data, None
    
    def request(self, method: str, endpoint: str, 
                data: Dict[str, Any] = None, 
                params: Dict[str, Any] = None,
                include_auth: bool = True) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Make an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            include_auth: Whether to include authentication header
            
        Returns:
            Tuple of (response_data, error_message)
        """
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers(include_auth)
        
        try:
            if method.upper() == "GET":
                response = self.client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.client.put(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.client.delete(url, headers=headers, params=params)
            else:
                return {}, f"Unsupported method: {method}"
            
            return self._handle_response(response)
            
        except httpx.RequestError as e:
            return {}, f"Request failed: {str(e)}"
        except Exception as e:
            return {}, f"Unexpected error: {str(e)}"
    
    # Authentication endpoints
    
    def register(self, username: str, email: str, password: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """Register a new user."""
        data, error = self.request("POST", "/auth/register", {
            "username": username,
            "email": email,
            "password": password
        }, include_auth=False)
        
        if not error and data.get("access_token"):
            self.set_tokens(data["access_token"], data["refresh_token"])
        
        return data, error
    
    def login(self, username: str, password: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """Login with credentials."""
        data, error = self.request("POST", "/auth/login", {
            "username": username,
            "password": password
        }, include_auth=False)
        
        if not error and data.get("access_token"):
            self.set_tokens(data["access_token"], data["refresh_token"])
        
        return data, error
    
    def logout(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """Logout the current user."""
        data, error = self.request("POST", "/auth/logout")
        self.clear_tokens()
        return data, error
    
    def refresh_token(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """Refresh the access token."""
        if not self._refresh_token:
            return {}, "No refresh token available"
        
        data, error = self.request("POST", "/auth/refresh", {
            "refresh_token": self._refresh_token
        }, include_auth=False)
        
        if not error and data.get("access_token"):
            self.set_tokens(data["access_token"], data.get("refresh_token", self._refresh_token))
        
        return data, error
    
    def get_current_user(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """Get current user info."""
        return self.request("GET", "/auth/me")
    
    # User endpoints
    
    def get_user(self, user_id: int) -> Tuple[Dict[str, Any], Optional[str]]:
        """Get user by ID."""
        return self.request("GET", f"/users/{user_id}")
    
    def update_user(self, user_id: int, username: str = None, email: str = None) -> Tuple[Dict[str, Any], Optional[str]]:
        """Update user profile."""
        data = {}
        if username:
            data["username"] = username
        if email:
            data["email"] = email
        return self.request("PUT", f"/users/{user_id}", data)
    
    def get_storage_info(self, user_id: int) -> Tuple[Dict[str, Any], Optional[str]]:
        """Get user storage info."""
        return self.request("GET", f"/users/{user_id}/storage")
    
    def search_users(self, query: str, limit: int = 10) -> Tuple[Dict[str, Any], Optional[str]]:
        """Search for users."""
        return self.request("GET", "/users/search", params={"q": query, "limit": limit})
    
    # File endpoints
    
    def list_files(self, include_shared: bool = True) -> Tuple[Dict[str, Any], Optional[str]]:
        """List all accessible files."""
        return self.request("GET", "/files", params={"include_shared": str(include_shared).lower()})
    
    def create_file(self, name: str, content: dict = None) -> Tuple[Dict[str, Any], Optional[str]]:
        """Create a new file."""
        return self.request("POST", "/files", {"name": name, "content": content})
    
    def get_file(self, file_id: int, include_content: bool = True) -> Tuple[Dict[str, Any], Optional[str]]:
        """Get file by ID."""
        return self.request("GET", f"/files/{file_id}", params={"include_content": str(include_content).lower()})
    
    def update_file(self, file_id: int, content: dict, version: int = None) -> Tuple[Dict[str, Any], Optional[str]]:
        """Update file content."""
        data = {"content": content}
        if version is not None:
            data["version"] = version
        return self.request("PUT", f"/files/{file_id}", data)
    
    def delete_file(self, file_id: int) -> Tuple[Dict[str, Any], Optional[str]]:
        """Delete a file."""
        return self.request("DELETE", f"/files/{file_id}")
    
    def rename_file(self, file_id: int, name: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """Rename a file."""
        return self.request("POST", f"/files/{file_id}/rename", {"name": name})
    
    def share_file(self, file_id: int, user_id: int, permission: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """Share a file with another user."""
        return self.request("POST", f"/files/{file_id}/share", {
            "user_id": user_id,
            "permission": permission
        })
    
    def unshare_file(self, file_id: int, user_id: int) -> Tuple[Dict[str, Any], Optional[str]]:
        """Remove user's access to a file."""
        return self.request("POST", f"/files/{file_id}/unshare", {"user_id": user_id})
    
    def set_file_visibility(self, file_id: int, is_public: bool) -> Tuple[Dict[str, Any], Optional[str]]:
        """Set file public visibility."""
        return self.request("POST", f"/files/{file_id}/visibility", {"is_public": is_public})
    
    def get_file_operations(self, file_id: int, since_version: int = 0) -> Tuple[Dict[str, Any], Optional[str]]:
        """Get file operations for sync."""
        return self.request("GET", f"/files/{file_id}/operations", params={"since_version": since_version})
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
