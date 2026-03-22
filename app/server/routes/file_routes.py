"""
File Routes Module

Contains API endpoints for file management.
"""

from flask import Blueprint, request, jsonify

from app.server.models.file import FilePermission
from app.server.services.file_service import FileService
from app.server.routes.auth_routes import token_required


file_bp = Blueprint('files', __name__)


@file_bp.route('', methods=['GET'])
@token_required
def list_files(current_user):
    """
    List all files accessible by the current user.
    
    Query Parameters:
        include_shared: Include shared files (default: true)
    
    Returns:
        200: List of files
    """
    include_shared = request.args.get('include_shared', 'true').lower() == 'true'
    files = FileService.get_user_files(current_user, include_shared)
    
    return jsonify({
        'files': [f.to_dict() for f in files]
    }), 200


@file_bp.route('', methods=['POST'])
@token_required
def create_file(current_user):
    """
    Create a new file.
    
    Request Body:
        name: File name
        content: Initial file content (optional)
    
    Returns:
        201: File created
        400: Validation error or storage limit exceeded
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name', 'Untitled').strip()
    content = data.get('content')
    
    file, error = FileService.create_file(current_user, name, content)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'File created successfully',
        'file': file.to_dict(include_content=True)
    }), 201


@file_bp.route('/<int:file_id>', methods=['GET'])
@token_required
def get_file(current_user, file_id):
    """
    Get a file by ID.
    
    Path Parameters:
        file_id: File ID
    
    Query Parameters:
        include_content: Include file content (default: true)
    
    Returns:
        200: File info
        404: File not found
        403: No permission
    """
    include_content = request.args.get('include_content', 'true').lower() == 'true'
    
    file, error = FileService.get_file(file_id, current_user, include_content)
    
    if error:
        return jsonify({'error': error}), 404 if 'not found' in error.lower() else 403
    
    return jsonify({
        'file': file.to_dict(include_content=include_content)
    }), 200


@file_bp.route('/<int:file_id>', methods=['PUT'])
@token_required
def update_file(current_user, file_id):
    """
    Update file content.
    
    Path Parameters:
        file_id: File ID
    
    Request Body:
        content: New file content
        version: Expected current version (for conflict detection)
    
    Returns:
        200: File updated
        400: Validation error or version conflict
        403: No permission
        404: File not found
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    content = data.get('content')
    version = data.get('version')
    
    if content is None:
        return jsonify({'error': 'Content is required'}), 400
    
    file, error = FileService.get_file(file_id, current_user)
    if error:
        return jsonify({'error': error}), 404 if 'not found' in error.lower() else 403
    
    success, error = FileService.update_file(file, current_user, content, version)
    
    if error:
        if 'conflict' in error.lower():
            return jsonify({'error': error, 'current_version': file.version}), 409
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'File updated successfully',
        'file': file.to_dict(include_content=True)
    }), 200


@file_bp.route('/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file(current_user, file_id):
    """
    Delete a file.
    
    Path Parameters:
        file_id: File ID
    
    Returns:
        200: File deleted
        403: Not the owner
        404: File not found
    """
    file, error = FileService.get_file(file_id, current_user)
    if error:
        return jsonify({'error': error}), 404
    
    success, error = FileService.delete_file(file, current_user)
    
    if error:
        return jsonify({'error': error}), 403
    
    return jsonify({'message': 'File deleted successfully'}), 200


@file_bp.route('/<int:file_id>/rename', methods=['POST'])
@token_required
def rename_file(current_user, file_id):
    """
    Rename a file.
    
    Path Parameters:
        file_id: File ID
    
    Request Body:
        name: New file name
    
    Returns:
        200: File renamed
        400: Validation error
        403: No permission
        404: File not found
    """
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    file, error = FileService.get_file(file_id, current_user)
    if error:
        return jsonify({'error': error}), 404
    
    success, error = FileService.rename_file(file, current_user, data['name'].strip())
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'File renamed successfully',
        'file': file.to_dict()
    }), 200


@file_bp.route('/<int:file_id>/share', methods=['POST'])
@token_required
def share_file(current_user, file_id):
    """
    Share a file with another user.
    
    Path Parameters:
        file_id: File ID
    
    Request Body:
        user_id: User ID to share with
        permission: Permission level (view, edit, admin)
    
    Returns:
        200: File shared
        400: Validation error
        403: Not the owner
        404: File or user not found
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    user_id = data.get('user_id')
    permission_str = data.get('permission', 'view')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    try:
        permission = FilePermission(permission_str.lower())
    except ValueError:
        return jsonify({'error': 'Invalid permission level'}), 400
    
    file, error = FileService.get_file(file_id, current_user)
    if error:
        return jsonify({'error': error}), 404
    
    success, error = FileService.share_file(file, current_user, user_id, permission)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'File shared successfully',
        'file': file.to_dict()
    }), 200


@file_bp.route('/<int:file_id>/unshare', methods=['POST'])
@token_required
def unshare_file(current_user, file_id):
    """
    Remove a user's access to a file.
    
    Path Parameters:
        file_id: File ID
    
    Request Body:
        user_id: User ID to remove
    
    Returns:
        200: Access removed
        400: Validation error
        403: Not the owner
        404: File not found
    """
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': 'User ID is required'}), 400
    
    file, error = FileService.get_file(file_id, current_user)
    if error:
        return jsonify({'error': error}), 404
    
    success, error = FileService.unshare_file(file, current_user, data['user_id'])
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Access removed successfully',
        'file': file.to_dict()
    }), 200


@file_bp.route('/<int:file_id>/visibility', methods=['POST'])
@token_required
def set_file_visibility(current_user, file_id):
    """
    Set file public visibility.
    
    Path Parameters:
        file_id: File ID
    
    Request Body:
        is_public: Whether file should be public
    
    Returns:
        200: Visibility updated
        403: Not the owner
        404: File not found
    """
    data = request.get_json()
    
    if data is None:
        return jsonify({'error': 'No data provided'}), 400
    
    is_public = data.get('is_public', False)
    
    file, error = FileService.get_file(file_id, current_user)
    if error:
        return jsonify({'error': error}), 404
    
    success, error = FileService.set_file_public(file, current_user, is_public)
    
    if error:
        return jsonify({'error': error}), 403
    
    return jsonify({
        'message': 'Visibility updated successfully',
        'file': file.to_dict()
    }), 200


@file_bp.route('/<int:file_id>/operations', methods=['GET'])
@token_required
def get_file_operations(current_user, file_id):
    """
    Get file operations for synchronization.
    
    Path Parameters:
        file_id: File ID
    
    Query Parameters:
        since_version: Get operations after this version (default: 0)
    
    Returns:
        200: List of operations
        403: No permission
        404: File not found
    """
    since_version = int(request.args.get('since_version', 0))
    
    file, error = FileService.get_file(file_id, current_user)
    if error:
        return jsonify({'error': error}), 404
    
    operations = FileService.get_file_operations(file, since_version)
    
    return jsonify({
        'operations': [op.to_dict() for op in operations],
        'current_version': file.version
    }), 200
