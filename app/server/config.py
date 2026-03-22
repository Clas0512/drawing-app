"""
Configuration Module

Contains configuration classes for different environments.
"""

import os
from typing import Optional


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database settings
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/drawing_app'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    
    # JWT settings
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES: int = 60 * 60 * 24  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRES: int = 60 * 60 * 24 * 30  # 30 days
    
    # Storage settings
    DEFAULT_USER_STORAGE_LIMIT: int = 100 * 1024 * 1024  # 100MB
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # CORS settings
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', '*')
    
    # WebSocket settings
    SOCKETIO_MESSAGE_QUEUE: Optional[str] = os.environ.get('SOCKETIO_MESSAGE_QUEUE', None)
    SOCKETIO_ASYNC_MODE: str = 'threading'


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES: int = 60 * 5  # 5 minutes for testing


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG: bool = False
    
    # In production, these must be set via environment variables
    @property
    def SECRET_KEY(self) -> str:
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("SECRET_KEY must be set in production")
        return key
    
    @property
    def JWT_SECRET_KEY(self) -> str:
        key = os.environ.get('JWT_SECRET_KEY')
        if not key:
            raise ValueError("JWT_SECRET_KEY must be set in production")
        return key


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)()
