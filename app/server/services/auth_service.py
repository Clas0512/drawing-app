"""
Authentication Service Module

Handles user authentication, registration, and token management.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.server.models.user import db, User
from app.server.models.file import File


class AuthService:
    """
    Service class for authentication operations.
    
    Provides methods for:
    - User registration
    - User login
    - Token generation and validation
    - Password management
    """
    
    @staticmethod
    def register_user(username: str, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new user.
        
        Args:
            username: Desired username
            email: User's email address
            password: Plain text password
            
        Returns:
            Tuple of (User, None) on success or (None, error_message) on failure
        """
        # Validate input
        if not username or len(username) < 3:
            return None, "Username must be at least 3 characters long"
        
        if not email or '@' not in email:
            return None, "Invalid email address"
        
        if not password or len(password) < 6:
            return None, "Password must be at least 6 characters long"
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return None, "Username already exists"
            return None, "Email already registered"
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            return user, None
        except IntegrityError:
            db.session.rollback()
            return None, "Failed to create user account"
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            Tuple of (User, None) on success or (None, error_message) on failure
        """
        if not username or not password:
            return None, "Username and password are required"
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None, "Invalid username or password"
        
        if not user.is_active:
            return None, "Account is disabled"
        
        if not user.check_password(password):
            return None, "Invalid username or password"
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return user, None
    
    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with 'access_token' and 'refresh_token'
        """
        now = datetime.utcnow()
        
        # Access token
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
        }
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Refresh token
        refresh_payload = {
            'user_id': user.id,
            'type': 'refresh',
            'iat': now,
            'exp': now + timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES'])
        }
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }
    
    @staticmethod
    def validate_token(token: str, token_type: str = 'access') -> Tuple[Optional[int], Optional[str]]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Tuple of (user_id, None) on success or (None, error_message) on failure
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            if payload.get('type') != token_type:
                return None, "Invalid token type"
            
            user_id = payload.get('user_id')
            if not user_id:
                return None, "Invalid token payload"
            
            return user_id, None
            
        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.InvalidTokenError:
            return None, "Invalid token"
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Tuple of (token_dict, None) on success or (None, error_message) on failure
        """
        user_id, error = AuthService.validate_token(refresh_token, 'refresh')
        
        if error:
            return None, error
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return None, "User not found or inactive"
        
        # Generate new tokens
        tokens = AuthService.generate_tokens(user)
        return tokens, None
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Change a user's password.
        
        Args:
            user: User instance
            old_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, error_message)
        """
        if not user.check_password(old_password):
            return False, "Current password is incorrect"
        
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long"
        
        user.set_password(new_password)
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID."""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username."""
        return User.query.filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        return User.query.filter(User.email == email).first()
