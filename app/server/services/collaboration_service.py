"""
Collaboration Service Module

Handles real-time collaboration features including WebSocket events,
operational transformation, and conflict resolution.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from flask_socketio import emit, join_room, leave_room, rooms
from flask import request

from app.server.models.user import db, User
from app.server.models.file import File, FileOperation, FilePermission
from app.server.services.file_service import FileService


class CollaborationService:
    """
    Service class for real-time collaboration.
    
    Provides methods for:
    - WebSocket room management
    - Real-time file updates
    - Operation broadcasting
    - Conflict resolution
    """
    
    # Store active editing sessions
    _active_sessions: Dict[int, List[Dict[str, Any]]] = {}
    
    @staticmethod
    def join_file_room(file_id: int, user: User) -> Dict[str, Any]:
        """
        Join a file's collaboration room.
        
        Args:
            file_id: File ID to join
            user: User joining the room
            
        Returns:
            Dictionary with room info and current file state
        """
        # Verify user has access
        file, error = FileService.get_file(file_id, user, include_content=True)
        if error:
            return {'error': error}
        
        room_name = f"file_{file_id}"
        join_room(room_name)
        
        # Track active user
        session_info = {
            'user_id': user.id,
            'username': user.username,
            'joined_at': datetime.utcnow().isoformat(),
            'sid': request.sid
        }
        
        if file_id not in CollaborationService._active_sessions:
            CollaborationService._active_sessions[file_id] = []
        
        CollaborationService._active_sessions[file_id].append(session_info)
        
        # Notify others in the room
        emit('user_joined', {
            'user_id': user.id,
            'username': user.username,
            'active_users': CollaborationService.get_active_users(file_id)
        }, room=room_name, include_self=False)
        
        return {
            'file': file.to_dict(include_content=True),
            'active_users': CollaborationService.get_active_users(file_id),
            'permission': file.get_collaborator_permission(user.id).value if file.get_collaborator_permission(user.id) else None
        }
    
    @staticmethod
    def leave_file_room(file_id: int, user: User) -> None:
        """
        Leave a file's collaboration room.
        
        Args:
            file_id: File ID to leave
            user: User leaving the room
        """
        room_name = f"file_{file_id}"
        leave_room(room_name)
        
        # Remove from active sessions
        if file_id in CollaborationService._active_sessions:
            CollaborationService._active_sessions[file_id] = [
                s for s in CollaborationService._active_sessions[file_id]
                if s['user_id'] != user.id
            ]
            
            if not CollaborationService._active_sessions[file_id]:
                del CollaborationService._active_sessions[file_id]
        
        # Notify others in the room
        emit('user_left', {
            'user_id': user.id,
            'username': user.username,
            'active_users': CollaborationService.get_active_users(file_id)
        }, room=room_name)
    
    @staticmethod
    def get_active_users(file_id: int) -> List[Dict[str, Any]]:
        """
        Get list of active users in a file room.
        
        Args:
            file_id: File ID to check
            
        Returns:
            List of active user info
        """
        sessions = CollaborationService._active_sessions.get(file_id, [])
        return [
            {
                'user_id': s['user_id'],
                'username': s['username'],
                'joined_at': s['joined_at']
            }
            for s in sessions
        ]
    
    @staticmethod
    def broadcast_operation(file_id: int, user: User, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Broadcast an operation to all users in the file room.
        
        Args:
            file_id: File ID
            user: User making the operation
            operation: Operation data
            
        Returns:
            Dictionary with result or error
        """
        # Get file and verify permission
        file, error = FileService.get_file(file_id, user)
        if error:
            return {'error': error}
        
        if not file.can_edit(user.id):
            return {'error': 'You do not have permission to edit this file'}
        
        room_name = f"file_{file_id}"
        
        # Apply operation to file
        operation_type = operation.get('type')
        operation_data = operation.get('data', {})
        
        if operation_type == 'element_add':
            result = CollaborationService._handle_element_add(file, user, operation_data)
        elif operation_type == 'element_update':
            result = CollaborationService._handle_element_update(file, user, operation_data)
        elif operation_type == 'element_delete':
            result = CollaborationService._handle_element_delete(file, user, operation_data)
        elif operation_type == 'layer_change':
            result = CollaborationService._handle_layer_change(file, user, operation_data)
        elif operation_type == 'full_sync':
            result = CollaborationService._handle_full_sync(file, user, operation_data)
        else:
            return {'error': f'Unknown operation type: {operation_type}'}
        
        if 'error' in result:
            return result
        
        # Broadcast to all users in room (including sender for confirmation)
        emit('operation', {
            'type': operation_type,
            'data': operation_data,
            'user_id': user.id,
            'username': user.username,
            'version': file.version,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_name)
        
        return result
    
    @staticmethod
    def _handle_element_add(file: File, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adding an element to the file."""
        content = file.content or {'layers': []}
        
        if 'elements' not in content:
            content['elements'] = []
        
        content['elements'].append(data.get('element', {}))
        
        success, error = FileService.update_file(file, user, content)
        if error:
            return {'error': error}
        
        return {'success': True, 'version': file.version}
    
    @staticmethod
    def _handle_element_update(file: File, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle updating an element in the file."""
        content = file.content or {'layers': []}
        element_id = data.get('element_id')
        
        if 'elements' in content:
            for i, element in enumerate(content['elements']):
                if element.get('id') == element_id:
                    content['elements'][i] = data.get('element', element)
                    break
        
        success, error = FileService.update_file(file, user, content)
        if error:
            return {'error': error}
        
        return {'success': True, 'version': file.version}
    
    @staticmethod
    def _handle_element_delete(file: File, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deleting an element from the file."""
        content = file.content or {'layers': []}
        element_id = data.get('element_id')
        
        if 'elements' in content:
            content['elements'] = [
                e for e in content['elements']
                if e.get('id') != element_id
            ]
        
        success, error = FileService.update_file(file, user, content)
        if error:
            return {'error': error}
        
        return {'success': True, 'version': file.version}
    
    @staticmethod
    def _handle_layer_change(file: File, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle layer changes in the file."""
        content = file.content or {}
        content['layers'] = data.get('layers', content.get('layers', []))
        
        success, error = FileService.update_file(file, user, content)
        if error:
            return {'error': error}
        
        return {'success': True, 'version': file.version}
    
    @staticmethod
    def _handle_full_sync(file: File, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a full file sync."""
        content = data.get('content', {})
        
        success, error = FileService.update_file(file, user, content)
        if error:
            return {'error': error}
        
        return {'success': True, 'version': file.version}
    
    @staticmethod
    def request_sync(file_id: int, user: User, since_version: int) -> Dict[str, Any]:
        """
        Request synchronization for missed operations.
        
        Args:
            file_id: File ID
            user: User requesting sync
            since_version: Version to sync from
            
        Returns:
            Dictionary with operations or error
        """
        file, error = FileService.get_file(file_id, user)
        if error:
            return {'error': error}
        
        operations = FileService.get_file_operations(file, since_version)
        
        return {
            'operations': [op.to_dict() for op in operations],
            'current_version': file.version,
            'file_content': file.content if file.version > since_version else None
        }
    
    @staticmethod
    def send_cursor_position(file_id: int, user: User, position: Dict[str, Any]) -> None:
        """
        Broadcast cursor position to other users.
        
        Args:
            file_id: File ID
            user: User sending cursor position
            position: Cursor position data
        """
        room_name = f"file_{file_id}"
        
        emit('cursor_update', {
            'user_id': user.id,
            'username': user.username,
            'position': position,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_name, include_self=False)
    
    @staticmethod
    def send_selection(file_id: int, user: User, selection: Dict[str, Any]) -> None:
        """
        Broadcast selection to other users.
        
        Args:
            file_id: File ID
            user: User sending selection
            selection: Selection data (element IDs)
        """
        room_name = f"file_{file_id}"
        
        emit('selection_update', {
            'user_id': user.id,
            'username': user.username,
            'selection': selection,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_name, include_self=False)
