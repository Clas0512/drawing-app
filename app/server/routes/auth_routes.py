"""
Authentication Routes Module

Contains API endpoints for user authentication.
"""

from flask import Blueprint, request, jsonify
from functools import wraps

from app.server.models.user import db, User
from app.server.services.auth_service import AuthService


auth_bp = Blueprint('auth', __name__)


def token_required(f):
    """
    Decorator to require valid JWT token for an endpoint.
    
    Adds current_user to the function kwargs.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        user_id, error = AuthService.validate_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        current_user = AuthService.get_user_by_id(user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request Body:
        username: Desired username (min 3 characters)
        email: User's email address
        password: Password (min 6 characters)
    
    Returns:
        201: User created successfully with tokens
        400: Validation error
        409: Username or email already exists
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    user, error = AuthService.register_user(username, email, password)
    
    if error:
        return jsonify({'error': error}), 400
    
    # Generate tokens for auto-login
    tokens = AuthService.generate_tokens(user)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(include_private=True),
        **tokens
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user.
    
    Request Body:
        username: Username or email
        password: Password
    
    Returns:
        200: Authentication successful with tokens
        401: Invalid credentials
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user, error = AuthService.authenticate_user(username, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    tokens = AuthService.generate_tokens(user)
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(include_private=True),
        **tokens
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """
    Logout the current user.
    
    In a stateless JWT system, the client should discard the tokens.
    This endpoint can be used for logging or token blacklisting if implemented.
    
    Returns:
        200: Logout successful
    """
    # In a more complex system, you might add the token to a blacklist
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token.
    
    Request Body:
        refresh_token: Valid refresh token
    
    Returns:
        200: New tokens
        401: Invalid or expired refresh token
    """
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Refresh token is required'}), 400
    
    tokens, error = AuthService.refresh_access_token(data['refresh_token'])
    
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify(tokens), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    Get the current authenticated user's info.
    
    Returns:
        200: User info
    """
    return jsonify({
        'user': current_user.to_dict(include_private=True)
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """
    Change the current user's password.
    
    Request Body:
        old_password: Current password
        new_password: New password (min 6 characters)
    
    Returns:
        200: Password changed successfully
        400: Invalid old password or new password
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    success, error = AuthService.change_password(current_user, old_password, new_password)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Password changed successfully'}), 200
