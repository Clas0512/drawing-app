"""
File Model Module

Defines the File, FileCollaborator, and FileOperation database models
for file management and real-time collaboration.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.server.models.user import db


class FilePermission(PyEnum):
    """File permission levels for collaborators."""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class File(db.Model):
    """
    File model for storing drawing project files.
    
    Attributes:
        id: Unique file identifier
        name: File name
        owner_id: ID of the file owner
        content: JSON content of the drawing file
        size: File size in bytes
        version: Current version number for conflict detection
        is_public: Whether the file is publicly accessible
        created_at: File creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'files'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # File content (stored as JSON)
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    
    # Version control for collaboration
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Access control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="files")
    collaborators: Mapped[List["FileCollaborator"]] = relationship(
        "FileCollaborator", back_populates="file", cascade="all, delete-orphan"
    )
    operations: Mapped[List["FileOperation"]] = relationship(
        "FileOperation", back_populates="file", cascade="all, delete-orphan"
    )
    
    def update_content(self, content: dict) -> None:
        """Update file content and increment version."""
        self.content = content
        self.size = len(str(content).encode('utf-8'))
        self.version += 1
        self.updated_at = datetime.utcnow()
    
    def get_collaborator_permission(self, user_id: int) -> Optional[FilePermission]:
        """Get permission level for a user."""
        if self.owner_id == user_id:
            return FilePermission.ADMIN
        
        for collab in self.collaborators:
            if collab.user_id == user_id:
                return collab.permission
        
        return None
    
    def can_view(self, user_id: int) -> bool:
        """Check if user can view the file."""
        return self.is_public or self.get_collaborator_permission(user_id) is not None
    
    def can_edit(self, user_id: int) -> bool:
        """Check if user can edit the file."""
        permission = self.get_collaborator_permission(user_id)
        return permission in (FilePermission.EDIT, FilePermission.ADMIN)
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is the owner."""
        return self.owner_id == user_id
    
    def to_dict(self, include_content: bool = False) -> dict:
        """
        Convert file to dictionary representation.
        
        Args:
            include_content: Whether to include file content
            
        Returns:
            Dictionary representation of file
        """
        result = {
            'id': self.id,
            'name': self.name,
            'owner_id': self.owner_id,
            'owner_username': self.owner.username if self.owner else None,
            'size': self.size,
            'version': self.version,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'collaborators': [
                {
                    'user_id': c.user_id,
                    'username': c.user.username if c.user else None,
                    'permission': c.permission.value if c.permission else None
                }
                for c in self.collaborators
            ]
        }
        
        if include_content:
            result['content'] = self.content
        
        return result
    
    def __repr__(self) -> str:
        return f"<File {self.name}>"


class FileCollaborator(db.Model):
    """
    FileCollaborator model for managing file sharing and permissions.
    
    Attributes:
        id: Unique identifier
        file_id: ID of the shared file
        user_id: ID of the collaborator
        permission: Permission level (view, edit, admin)
        added_at: When the collaborator was added
    """
    
    __tablename__ = 'file_collaborators'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey('files.id'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    permission: Mapped[FilePermission] = mapped_column(Enum(FilePermission), default=FilePermission.VIEW)
    
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file: Mapped["File"] = relationship("File", back_populates="collaborators")
    user: Mapped["User"] = relationship("User", back_populates="collaborations")
    
    def to_dict(self) -> dict:
        """Convert collaborator to dictionary representation."""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'permission': self.permission.value if self.permission else None,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }
    
    def __repr__(self) -> str:
        return f"<FileCollaborator user={self.user_id} file={self.file_id}>"


class FileOperation(db.Model):
    """
    FileOperation model for tracking changes in real-time collaboration.
    
    Used for operational transformation and conflict resolution.
    
    Attributes:
        id: Unique identifier
        file_id: ID of the file
        user_id: ID of the user who made the operation
        operation_type: Type of operation (create, update, delete)
        operation_data: JSON data describing the operation
        version: File version after this operation
        created_at: When the operation was performed
    """
    
    __tablename__ = 'file_operations'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey('files.id'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    operation_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file: Mapped["File"] = relationship("File", back_populates="operations")
    
    def to_dict(self) -> dict:
        """Convert operation to dictionary representation."""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'operation_type': self.operation_type,
            'operation_data': self.operation_data,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<FileOperation file={self.file_id} type={self.operation_type}>"
