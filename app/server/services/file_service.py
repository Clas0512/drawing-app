"""
File Service Module

Handles file operations including CRUD, storage management, and sharing.
"""

from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.server.models.user import db, User
from app.server.models.file import File, FileCollaborator, FileOperation, FilePermission


class FileService:
    """
    Service class for file operations.
    
    Provides methods for:
    - File CRUD operations
    - Storage management
    - File sharing and permissions
    - Version control
    """
    
    @staticmethod
    def create_file(user: User, name: str, content: dict = None) -> Tuple[Optional[File], Optional[str]]:
        """
        Create a new file for a user.
        
        Args:
            user: User creating the file
            name: File name
            content: Initial file content (optional)
            
        Returns:
            Tuple of (File, None) on success or (None, error_message) on failure
        """
        if not name or len(name) > 255:
            return None, "File name must be between 1 and 255 characters"
        
        # Calculate file size
        content = content or {}
        file_size = len(str(content).encode('utf-8'))
        
        # Check storage limit
        if not user.can_store(file_size):
            return None, "Insufficient storage space"
        
        # Create file
        file = File(name=name, owner_id=user.id, content=content, size=file_size)
        
        try:
            db.session.add(file)
            
            # Update user's storage
            user.update_storage_used(file_size)
            
            # Create initial operation record
            operation = FileOperation(
                file=file,
                user_id=user.id,
                operation_type='create',
                operation_data={'name': name},
                version=1
            )
            db.session.add(operation)
            
            db.session.commit()
            return file, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to create file: {str(e)}"
    
    @staticmethod
    def get_file(file_id: int, user: User, include_content: bool = False) -> Tuple[Optional[File], Optional[str]]:
        """
        Get a file by ID with permission check.
        
        Args:
            file_id: File ID
            user: User requesting the file
            include_content: Whether to include file content
            
        Returns:
            Tuple of (File, None) on success or (None, error_message) on failure
        """
        file = File.query.get(file_id)
        
        if not file:
            return None, "File not found"
        
        if not file.can_view(user.id):
            return None, "You don't have permission to view this file"
        
        return file, None
    
    @staticmethod
    def update_file(file: File, user: User, content: dict, version: int = None) -> Tuple[bool, Optional[str]]:
        """
        Update file content with version control.
        
        Args:
            file: File to update
            user: User making the update
            content: New file content
            version: Expected current version (for conflict detection)
            
        Returns:
            Tuple of (success, error_message)
        """
        if not file.can_edit(user.id):
            return False, "You don't have permission to edit this file"
        
        # Version conflict check
        if version is not None and file.version != version:
            return False, f"Version conflict: file has been modified (current version: {file.version})"
        
        # Calculate size difference
        old_size = file.size
        new_size = len(str(content).encode('utf-8'))
        size_diff = new_size - old_size
        
        # Check storage limit for owner
        owner = file.owner
        if size_diff > 0 and not owner.can_store(size_diff):
            return False, "Insufficient storage space"
        
        try:
            # Update file
            old_version = file.version
            file.update_content(content)
            
            # Update owner's storage
            owner.update_storage_used(size_diff)
            
            # Create operation record
            operation = FileOperation(
                file_id=file.id,
                user_id=user.id,
                operation_type='update',
                operation_data={'size_change': size_diff},
                version=file.version
            )
            db.session.add(operation)
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update file: {str(e)}"
    
    @staticmethod
    def delete_file(file: File, user: User) -> Tuple[bool, Optional[str]]:
        """
        Delete a file.
        
        Args:
            file: File to delete
            user: User requesting deletion
            
        Returns:
            Tuple of (success, error_message)
        """
        if not file.is_owner(user.id):
            return False, "Only the file owner can delete the file"
        
        try:
            # Update owner's storage
            user.update_storage_used(-file.size)
            
            # Delete file (cascade will handle related records)
            db.session.delete(file)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete file: {str(e)}"
    
    @staticmethod
    def rename_file(file: File, user: User, new_name: str) -> Tuple[bool, Optional[str]]:
        """
        Rename a file.
        
        Args:
            file: File to rename
            user: User requesting rename
            new_name: New file name
            
        Returns:
            Tuple of (success, error_message)
        """
        if not file.can_edit(user.id):
            return False, "You don't have permission to rename this file"
        
        if not new_name or len(new_name) > 255:
            return False, "File name must be between 1 and 255 characters"
        
        try:
            old_name = file.name
            file.name = new_name
            file.updated_at = datetime.utcnow()
            
            # Create operation record
            operation = FileOperation(
                file_id=file.id,
                user_id=user.id,
                operation_type='rename',
                operation_data={'old_name': old_name, 'new_name': new_name},
                version=file.version
            )
            db.session.add(operation)
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to rename file: {str(e)}"
    
    @staticmethod
    def share_file(file: File, owner: User, user_id: int, permission: FilePermission) -> Tuple[bool, Optional[str]]:
        """
        Share a file with another user.
        
        Args:
            file: File to share
            owner: File owner
            user_id: ID of user to share with
            permission: Permission level to grant
            
        Returns:
            Tuple of (success, error_message)
        """
        if not file.is_owner(owner.id):
            return False, "Only the file owner can share the file"
        
        if user_id == owner.id:
            return False, "Cannot share file with yourself"
        
        # Check if target user exists
        target_user = User.query.get(user_id)
        if not target_user:
            return False, "User not found"
        
        # Check if already shared
        existing = FileCollaborator.query.filter_by(
            file_id=file.id, user_id=user_id
        ).first()
        
        try:
            if existing:
                existing.permission = permission
            else:
                collaborator = FileCollaborator(
                    file_id=file.id,
                    user_id=user_id,
                    permission=permission
                )
                db.session.add(collaborator)
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to share file: {str(e)}"
    
    @staticmethod
    def unshare_file(file: File, owner: User, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Remove a user's access to a file.
        
        Args:
            file: File to unshare
            owner: File owner
            user_id: ID of user to remove
            
        Returns:
            Tuple of (success, error_message)
        """
        if not file.is_owner(owner.id):
            return False, "Only the file owner can unshare the file"
        
        collaborator = FileCollaborator.query.filter_by(
            file_id=file.id, user_id=user_id
        ).first()
        
        if not collaborator:
            return False, "User does not have access to this file"
        
        try:
            db.session.delete(collaborator)
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to unshare file: {str(e)}"
    
    @staticmethod
    def get_user_files(user: User, include_shared: bool = True) -> List[File]:
        """
        Get all files accessible by a user.
        
        Args:
            user: User to get files for
            include_shared: Whether to include shared files
            
        Returns:
            List of files
        """
        # Get owned files
        files = File.query.filter_by(owner_id=user.id).all()
        
        if include_shared:
            # Get shared files
            shared_ids = [c.file_id for c in user.collaborations]
            if shared_ids:
                shared_files = File.query.filter(File.id.in_(shared_ids)).all()
                files.extend(shared_files)
        
        return files
    
    @staticmethod
    def get_file_operations(file: File, since_version: int = 0) -> List[FileOperation]:
        """
        Get file operations for synchronization.
        
        Args:
            file: File to get operations for
            since_version: Get operations after this version
            
        Returns:
            List of operations
        """
        return FileOperation.query.filter(
            FileOperation.file_id == file.id,
            FileOperation.version > since_version
        ).order_by(FileOperation.version).all()
    
    @staticmethod
    def set_file_public(file: File, user: User, is_public: bool) -> Tuple[bool, Optional[str]]:
        """
        Set file public visibility.
        
        Args:
            file: File to modify
            user: User making the request
            is_public: Whether file should be public
            
        Returns:
            Tuple of (success, error_message)
        """
        if not file.is_owner(user.id):
            return False, "Only the file owner can change visibility"
        
        try:
            file.is_public = is_public
            file.updated_at = datetime.utcnow()
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update visibility: {str(e)}"
