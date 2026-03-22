"""
Collaboration Routes Module

Contains API endpoints and WebSocket event handlers for real-time collaboration.
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit

from app.server.services.collaboration_service import CollaborationService
from app.server.services.auth_service import AuthService
from app.server.routes.auth_routes import token_required
from app.server.app_factory import socketio


collaboration_bp = Blueprint('collaboration', __name__)


# REST endpoints
@collaboration_bp.route('/<int:file_id>/active-users', methods=['GET'])
@token_required
def get_active_users(current_user, file_id):
    """
    Get list of users currently editing a file.
    
    Path Parameters:
        file_id: File ID
    
    Returns:
        200: List of active users
    """
    active_users = CollaborationService.get_active_users(file_id)
    return jsonify({'active_users': active_users}), 200


# WebSocket event handlers
def get_user_from_socket():
    """Extract user from socket authentication."""
    # Get token from auth data
    auth = request.args.get('token') or request.headers.get('Authorization', '')
    
    if auth.startswith('Bearer '):
        token = auth[7:]
    else:
        token = auth
    
    if not token:
        return None
    
    user_id, error = AuthService.validate_token(token)
    if error:
        return None
    
    return AuthService.get_user_by_id(user_id)


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    user = get_user_from_socket()
    if not user:
        return False  # Reject connection
    
    emit('connected', {'message': 'Connected successfully', 'user_id': user.id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    # Clean up any active sessions
    user = get_user_from_socket()
    if user:
        # Leave all file rooms
        for file_id in list(CollaborationService._active_sessions.keys()):
            sessions = CollaborationService._active_sessions.get(file_id, [])
            if any(s['user_id'] == user.id for s in sessions):
                CollaborationService.leave_file_room(file_id, user)


@socketio.on('join_file')
def handle_join_file(data):
    """Handle joining a file's collaboration room."""
    user = get_user_from_socket()
    if not user:
        emit('error', {'message': 'Authentication required'})
        return
    
    file_id = data.get('file_id')
    if not file_id:
        emit('error', {'message': 'File ID is required'})
        return
    
    result = CollaborationService.join_file_room(file_id, user)
    
    if 'error' in result:
        emit('error', {'message': result['error']})
    else:
        emit('joined_file', result)


@socketio.on('leave_file')
def handle_leave_file(data):
    """Handle leaving a file's collaboration room."""
    user = get_user_from_socket()
    if not user:
        return
    
    file_id = data.get('file_id')
    if file_id:
        CollaborationService.leave_file_room(file_id, user)


@socketio.on('operation')
def handle_operation(data):
    """Handle a real-time operation on a file."""
    user = get_user_from_socket()
    if not user:
        emit('error', {'message': 'Authentication required'})
        return
    
    file_id = data.get('file_id')
    operation = data.get('operation', {})
    
    if not file_id:
        emit('error', {'message': 'File ID is required'})
        return
    
    result = CollaborationService.broadcast_operation(file_id, user, operation)
    
    if 'error' in result:
        emit('error', {'message': result['error']})
    else:
        emit('operation_ack', result)


@socketio.on('request_sync')
def handle_request_sync(data):
    """Handle a request to sync missed operations."""
    user = get_user_from_socket()
    if not user:
        emit('error', {'message': 'Authentication required'})
        return
    
    file_id = data.get('file_id')
    since_version = data.get('since_version', 0)
    
    if not file_id:
        emit('error', {'message': 'File ID is required'})
        return
    
    result = CollaborationService.request_sync(file_id, user, since_version)
    
    if 'error' in result:
        emit('error', {'message': result['error']})
    else:
        emit('sync', result)


@socketio.on('cursor_move')
def handle_cursor_move(data):
    """Handle cursor position updates."""
    user = get_user_from_socket()
    if not user:
        return
    
    file_id = data.get('file_id')
    position = data.get('position', {})
    
    if file_id:
        CollaborationService.send_cursor_position(file_id, user, position)


@socketio.on('selection_change')
def handle_selection_change(data):
    """Handle selection updates."""
    user = get_user_from_socket()
    if not user:
        return
    
    file_id = data.get('file_id')
    selection = data.get('selection', {})
    
    if file_id:
        CollaborationService.send_selection(file_id, user, selection)
