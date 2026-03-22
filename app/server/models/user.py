"""
User Model Module

Defines the User database model for authentication and user management.
"""

from datetime import datetime
from typing import List, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """
    User model for authentication and user management.
    
    Attributes:
        id: Unique user identifier
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password (never store plain text)
        storage_limit: Maximum storage in bytes (default 100MB)
        storage_used: Current storage used in bytes
        is_active: Whether the user account is active
        is_verified: Whether the email is verified
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last login timestamp
    """
    
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    
    # Storage management
    storage_limit: Mapped[int] = mapped_column(Integer, default=100 * 1024 * 1024)  # 100MB default
    storage_used: Mapped[int] = mapped_column(Integer, default=0)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    files: Mapped[List["File"]] = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    collaborations: Mapped[List["FileCollaborator"]] = relationship(
        "FileCollaborator", back_populates="user", cascade="all, delete-orphan"
    )
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
        self.updated_at = datetime.utcnow()
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def update_storage_used(self, delta: int) -> bool:
        """
        Update storage used by delta bytes.
        
        Args:
            delta: Change in storage (positive to add, negative to remove)
            
        Returns:
            True if update successful, False if would exceed limit
        """
        new_used = self.storage_used + delta
        if new_used < 0:
            new_used = 0
        if new_used > self.storage_limit:
            return False
        self.storage_used = new_used
        self.updated_at = datetime.utcnow()
        return True
    
    def get_storage_remaining(self) -> int:
        """Get remaining storage in bytes."""
        return max(0, self.storage_limit - self.storage_used)
    
    def get_storage_percentage(self) -> float:
        """Get storage usage as percentage."""
        if self.storage_limit == 0:
            return 0.0
        return (self.storage_used / self.storage_limit) * 100
    
    def can_store(self, size: int) -> bool:
        """Check if user can store a file of given size."""
        return self.storage_used + size <= self.storage_limit
    
    def to_dict(self, include_private: bool = False) -> dict:
        """
        Convert user to dictionary representation.
        
        Args:
            include_private: Whether to include private fields
            
        Returns:
            Dictionary representation of user
        """
        result = {
            'id': self.id,
            'username': self.username,
            'email': self.email if include_private else None,
            'storage_limit': self.storage_limit,
            'storage_used': self.storage_used,
            'storage_remaining': self.get_storage_remaining(),
            'storage_percentage': round(self.get_storage_percentage(), 2),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_private:
            result.update({
                'is_verified': self.is_verified,
                'last_login': self.last_login.isoformat() if self.last_login else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            })
        
        return result
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"
