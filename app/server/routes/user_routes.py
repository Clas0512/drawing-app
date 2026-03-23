"""
User Routes Module

Contains API endpoints for user management.
"""

from flask import Blueprint, request, jsonify

from app.server.models.user import db, User
from app.server.services.auth_service import AuthService
from app.server.routes.auth_routes import token_required


user_bp = Blueprint('users', __name__)


@user_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """
    Get a user's public profile.
    
    Path Parameters:
        user_id: User ID to retrieve
    
    Returns:
        200: User profile
        404: User not found
    """
    user = AuthService.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """
    Update a user's profile.
    
    Only the user themselves can update their profile.
    
    Path Parameters:
        user_id: User ID to update
    
    Request Body:
        username: New username (optional)
        email: New email (optional)
    
    Returns:
        200: Updated user profile
        400: Validation error
        403: Not authorized
    """
    if current_user.id != user_id:
        return jsonify({'error': 'Not authorized to update this user'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update username if provided
    if 'username' in data:
        new_username = data['username'].strip()
        
        if len(new_username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        # Check if username is taken
        existing = AuthService.get_user_by_username(new_username)
        if existing and existing.id != current_user.id:
            return jsonify({'error': 'Username already taken'}), 400
        
        current_user.username = new_username
    
    # Update email if provided
    if 'email' in data:
        new_email = data['email'].strip()
        
        if '@' not in new_email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        # Check if email is taken
        existing = AuthService.get_user_by_email(new_email)
        if existing and existing.id != current_user.id:
            return jsonify({'error': 'Email already in use'}), 400
        
        current_user.email = new_email
        current_user.is_verified = False  # Reset verification on email change
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': current_user.to_dict(include_private=True)
    }), 200


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    """
    Delete a user account.
    
    Only the user themselves can delete their account.
    
    Path Parameters:
        user_id: User ID to delete
    
    Returns:
        200: Account deleted
        403: Not authorized
    """
    if current_user.id != user_id:
        return jsonify({'error': 'Not authorized to delete this user'}), 403
    
    try:
        db.session.delete(current_user)
        db.session.commit()
        return jsonify({'message': 'Account deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete account'}), 500


@user_bp.route('/<int:user_id>/storage', methods=['GET'])
@token_required
def get_storage_info(current_user, user_id):
    """
    Get a user's storage information.
    
    Path Parameters:
        user_id: User ID
    
    Returns:
        200: Storage info
        403: Not authorized
    """
    if current_user.id != user_id:
        return jsonify({'error': 'Not authorized'}), 403
    
    return jsonify({
        'storage': {
            'limit': current_user.storage_limit,
            'used': current_user.storage_used,
            'remaining': current_user.get_storage_remaining(),
            'percentage': round(current_user.get_storage_percentage(), 2)
        }
    }), 200


@user_bp.route('/search', methods=['GET'])
@token_required
def search_users(current_user):
    """
    Search for users by username.
    
    Query Parameters:
        q: Search query (min 1 character)
        limit: Maximum results (default 10, max 50)
    
    Returns:
        200: List of matching users
    """
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if len(query) < 1:
        return jsonify({'error': 'Query must be at least 1 character'}), 400
    
    users = User.query.filter(
        User.username.ilike(f'%{query}%'),
        User.id != current_user.id
    ).limit(limit).all()
    
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200
