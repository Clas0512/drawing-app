#!/usr/bin/env python3
"""
Flask Server Entry Point

Run the Flask server for the drawing application API.

Usage:
    python run_server.py [--host HOST] [--port PORT] [--debug]
"""

import os
import sys
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.server.app_factory import create_app, socketio


def init_database(app):
    """
    Initialize database tables if they don't exist.
    This provides automatic database setup on server startup.
    """
    from app.server.models.user import db
    
    with app.app_context():
        try:
            # Try to check if tables exist
            db.session.execute(db.text('SELECT 1 FROM users LIMIT 1'))
            print("Database tables already exist.")
        except Exception:
            # Tables don't exist, create them
            print("Initializing database tables...")
            try:
                db.create_all()
                print("Database tables created successfully!")
            except Exception as e:
                print(f"Warning: Could not create database tables: {e}")
                print("Please run 'python setup_database.py' to initialize the database.")


def main():
    """Run the Flask server."""
    parser = argparse.ArgumentParser(description='Run the Drawing Application API server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', default='development', help='Configuration to use')
    parser.add_argument('--skip-db-init', action='store_true', help='Skip automatic database initialization')
    
    args = parser.parse_args()
    
    # Set environment
    os.environ['FLASK_ENV'] = args.config
    
    # Create app
    app = create_app(args.config)
    
    # Auto-initialize database unless skipped
    if not args.skip_db_init:
        init_database(app)
    
    print(f"\nStarting Drawing Application API server...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug: {args.debug}")
    print(f"Config: {args.config}")
    print(f"API URL: http://{args.host}:{args.port}/api")
    print(f"\nPress Ctrl+C to stop the server.\n")
    
    # Run with SocketIO
    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug or args.config == 'development',
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    main()
