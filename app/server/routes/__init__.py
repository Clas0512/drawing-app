"""
Routes Module

Contains Flask blueprints for API endpoints.
"""

from app.server.routes.auth_routes import auth_bp
from app.server.routes.user_routes import user_bp
from app.server.routes.file_routes import file_bp
from app.server.routes.collaboration_routes import collaboration_bp

__all__ = ['auth_bp', 'user_bp', 'file_bp', 'collaboration_bp']
