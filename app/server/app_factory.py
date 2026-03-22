"""
Flask Application Factory Module

Creates and configures the Flask application instance.
"""

from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS

from app.server.config import get_config
from app.server.models.user import db
from app.server.models import User


# Initialize extensions
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*")


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory for creating Flask app instances.
    
    Args:
        config_name: Configuration name (development, testing, production)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name:
        from app.server.config import config_by_name
        app.config.from_object(config_by_name[config_name])
    else:
        config = get_config()
        app.config.from_object(config)
    
    # Initialize extensions
    _init_extensions(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register CLI commands
    _register_cli_commands(app)
    
    return app


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        """Load user by ID for Flask-Login."""
        return User.query.get(int(user_id))
    
    # Initialize SocketIO
    socketio.init_app(app, async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading'))


def _register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    from app.server.routes.auth_routes import auth_bp
    from app.server.routes.user_routes import user_bp
    from app.server.routes.file_routes import file_bp
    from app.server.routes.collaboration_routes import collaboration_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(file_bp, url_prefix='/api/files')
    app.register_blueprint(collaboration_bp, url_prefix='/api/collaboration')


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    from flask import jsonify
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


def _register_cli_commands(app: Flask) -> None:
    """Register custom CLI commands."""
    import click
    
    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        db.create_all()
        click.echo('Database initialized.')
    
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    def create_admin(username: str, email: str, password: str):
        """Create an admin user."""
        user = User(username=username, email=email)
        user.set_password(password)
        user.is_verified = True
        user.storage_limit = 1024 * 1024 * 1024  # 1GB for admin
        
        db.session.add(user)
        db.session.commit()
        
        click.echo(f'Admin user "{username}" created successfully.')


def create_socketio(app: Flask):
    """Create SocketIO server with the app."""
    socketio.init_app(app)
    return socketio
