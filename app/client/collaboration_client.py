"""
Collaboration Client Module

Provides WebSocket client for real-time collaboration.
"""

from typing import Optional, Dict, Any, List, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

try:
    from socketio import Client as SocketIOClient
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False


class CollaborationClient(QObject):
    """
    WebSocket client for real-time collaboration.
    
    Provides signals for collaboration events and methods
    for joining/leaving files and sending operations.
    """
    
    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    connection_error = pyqtSignal(str)
    
    # File collaboration signals
    joined_file = pyqtSignal(dict)  # File data
    left_file = pyqtSignal(int)  # File ID
    user_joined = pyqtSignal(dict)  # User info
    user_left = pyqtSignal(dict)  # User info
    
    # Operation signals
    operation_received = pyqtSignal(dict)  # Operation data
    operation_ack = pyqtSignal(dict)  # Acknowledgment
    sync_received = pyqtSignal(dict)  # Sync data
    
    # Cursor/selection signals
    cursor_update = pyqtSignal(dict)  # Cursor position
    selection_update = pyqtSignal(dict)  # Selection
    
    # Error signal
    error = pyqtSignal(str)
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        super().__init__()
        self.base_url = base_url
        self._access_token: Optional[str] = None
        self._current_file_id: Optional[int] = None
        self._active_users: List[Dict[str, Any]] = []
        
        if SOCKETIO_AVAILABLE:
            self._socket = SocketIOClient()
            self._setup_socket_handlers()
        else:
            self._socket = None
        
        # Reconnection timer
        self._reconnect_timer = QTimer()
        self._reconnect_timer.timeout.connect(self._try_reconnect)
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
    
    def set_token(self, token: str):
        """Set the authentication token."""
        self._access_token = token
    
    def clear_token(self):
        """Clear the authentication token."""
        self._access_token = None
    
    def _setup_socket_handlers(self):
        """Set up Socket.IO event handlers."""
        if not self._socket:
            return
        
        @self._socket.on('connect')
        def on_connect():
            self._reconnect_attempts = 0
            self._reconnect_timer.stop()
            self.connected.emit()
        
        @self._socket.on('disconnect')
        def on_disconnect():
            self.disconnected.emit()
            self._start_reconnect()
        
        @self._socket.on('connect_error')
        def on_connect_error(error):
            self.connection_error.emit(str(error))
            self._start_reconnect()
        
        @self._socket.on('error')
        def on_error(data):
            self.error.emit(data.get('message', 'Unknown error'))
        
        @self._socket.on('joined_file')
        def on_joined_file(data):
            self._current_file_id = data.get('file', {}).get('id')
            self._active_users = data.get('active_users', [])
            self.joined_file.emit(data)
        
        @self._socket.on('user_joined')
        def on_user_joined(data):
            self._active_users = data.get('active_users', [])
            self.user_joined.emit(data)
        
        @self._socket.on('user_left')
        def on_user_left(data):
            self._active_users = data.get('active_users', [])
            self.user_left.emit(data)
        
        @self._socket.on('operation')
        def on_operation(data):
            self.operation_received.emit(data)
        
        @self._socket.on('operation_ack')
        def on_operation_ack(data):
            self.operation_ack.emit(data)
        
        @self._socket.on('sync')
        def on_sync(data):
            self.sync_received.emit(data)
        
        @self._socket.on('cursor_update')
        def on_cursor_update(data):
            self.cursor_update.emit(data)
        
        @self._socket.on('selection_update')
        def on_selection_update(data):
            self.selection_update.emit(data)
    
    def connect(self) -> bool:
        """
        Connect to the collaboration server.
        
        Returns:
            True if connection initiated successfully
        """
        if not self._socket:
            self.error.emit("Socket.IO not available")
            return False
        
        if not self._access_token:
            self.error.emit("Authentication required")
            return False
        
        try:
            self._socket.connect(
                self.base_url,
                headers={"Authorization": f"Bearer {self._access_token}"},
                wait=False
            )
            return True
        except Exception as e:
            self.connection_error.emit(str(e))
            return False
    
    def disconnect(self):
        """Disconnect from the collaboration server."""
        if self._socket and self._socket.connected:
            self._socket.disconnect()
        
        self._current_file_id = None
        self._active_users = []
        self._reconnect_timer.stop()
    
    def _start_reconnect(self):
        """Start reconnection attempts."""
        if self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            self._reconnect_timer.start(5000)  # Try every 5 seconds
    
    def _try_reconnect(self):
        """Try to reconnect to the server."""
        if self._access_token:
            self.connect()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to the server."""
        return self._socket is not None and self._socket.connected
    
    @property
    def current_file_id(self) -> Optional[int]:
        """Get the current file ID being collaborated on."""
        return self._current_file_id
    
    @property
    def active_users(self) -> List[Dict[str, Any]]:
        """Get list of active users in the current file."""
        return self._active_users.copy()
    
    def join_file(self, file_id: int) -> bool:
        """
        Join a file's collaboration room.
        
        Args:
            file_id: File ID to join
            
        Returns:
            True if join request sent successfully
        """
        if not self.is_connected:
            self.error.emit("Not connected to server")
            return False
        
        self._socket.emit('join_file', {'file_id': file_id})
        return True
    
    def leave_file(self, file_id: int = None):
        """
        Leave the current file's collaboration room.
        
        Args:
            file_id: File ID to leave (defaults to current file)
        """
        if not self.is_connected:
            return
        
        file_id = file_id or self._current_file_id
        if file_id:
            self._socket.emit('leave_file', {'file_id': file_id})
            self._current_file_id = None
            self._active_users = []
            self.left_file.emit(file_id)
    
    def send_operation(self, operation_type: str, data: Dict[str, Any], file_id: int = None) -> bool:
        """
        Send an operation to the server.
        
        Args:
            operation_type: Type of operation
            data: Operation data
            file_id: Target file ID (defaults to current file)
            
        Returns:
            True if operation sent successfully
        """
        if not self.is_connected:
            return False
        
        file_id = file_id or self._current_file_id
        if not file_id:
            return False
        
        self._socket.emit('operation', {
            'file_id': file_id,
            'operation': {
                'type': operation_type,
                'data': data
            }
        })
        return True
    
    def request_sync(self, since_version: int = 0, file_id: int = None):
        """
        Request synchronization of missed operations.
        
        Args:
            since_version: Version to sync from
            file_id: Target file ID (defaults to current file)
        """
        if not self.is_connected:
            return
        
        file_id = file_id or self._current_file_id
        if not file_id:
            return
        
        self._socket.emit('request_sync', {
            'file_id': file_id,
            'since_version': since_version
        })
    
    def send_cursor_position(self, position: Dict[str, Any], file_id: int = None):
        """
        Send cursor position to other users.
        
        Args:
            position: Cursor position data
            file_id: Target file ID (defaults to current file)
        """
        if not self.is_connected:
            return
        
        file_id = file_id or self._current_file_id
        if not file_id:
            return
        
        self._socket.emit('cursor_move', {
            'file_id': file_id,
            'position': position
        })
    
    def send_selection(self, selection: Dict[str, Any], file_id: int = None):
        """
        Send selection to other users.
        
        Args:
            selection: Selection data (element IDs)
            file_id: Target file ID (defaults to current file)
        """
        if not self.is_connected:
            return
        
        file_id = file_id or self._current_file_id
        if not file_id:
            return
        
        self._socket.emit('selection_change', {
            'file_id': file_id,
            'selection': selection
        })
