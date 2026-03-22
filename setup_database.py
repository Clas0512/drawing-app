#!/usr/bin/env python3
"""
Database Setup Script

This script handles database creation and initialization for the Drawing Application.
It can create the database, run migrations, and optionally create an admin user.

Usage:
    python setup_database.py                    # Interactive setup
    python setup_database.py --create-db        # Create database only
    python setup_database.py --migrate          # Run migrations only
    python setup_database.py --init             # Full initialization
    python setup_database.py --reset            # Reset database (drop and recreate)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import psycopg
    from psycopg import sql
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False
    print("Warning: psycopg not available. Database creation will be skipped.")


def get_database_config():
    """Get database configuration from environment or defaults."""
    database_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/drawing_app'
    )
    
    # Parse database URL
    # Format: postgresql://user:password@host:port/database
    import re
    match = re.match(
        r'postgresql://(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:]+):(?P<port>\d+)/(?P<database>.+)',
        database_url
    )
    
    if match:
        return {
            'user': match.group('user'),
            'password': match.group('password'),
            'host': match.group('host'),
            'port': int(match.group('port')),
            'database': match.group('database'),
            'url': database_url
        }
    else:
        # Default configuration
        return {
            'user': 'postgres',
            'password': 'postgres',
            'host': 'localhost',
            'port': 5432,
            'database': 'drawing_app',
            'url': database_url
        }


def create_database(config: dict, drop_if_exists: bool = False) -> bool:
    """
    Create the database if it doesn't exist.
    
    Args:
        config: Database configuration dictionary
        drop_if_exists: Whether to drop the database if it exists
        
    Returns:
        True if successful, False otherwise
    """
    if not PSYCOPG_AVAILABLE:
        print("Cannot create database: psycopg package not installed.")
        print("Please install it with: pip install psycopg[binary]")
        return False
    
    try:
        # Connect to postgres database (default database)
        conn_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/postgres"
        
        print(f"Connecting to PostgreSQL server at {config['host']}:{config['port']}...")
        
        with psycopg.connect(conn_string, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (config['database'],)
                )
                exists = cur.fetchone() is not None
                
                if exists:
                    if drop_if_exists:
                        print(f"Dropping existing database '{config['database']}'...")
                        cur.execute(
                            sql.SQL("DROP DATABASE {}").format(
                                sql.Identifier(config['database'])
                            )
                        )
                        exists = False
                    else:
                        print(f"Database '{config['database']}' already exists.")
                        return True
                
                if not exists:
                    print(f"Creating database '{config['database']}'...")
                    cur.execute(
                        sql.SQL("CREATE DATABASE {}").format(
                            sql.Identifier(config['database'])
                        )
                    )
                    print(f"Database '{config['database']}' created successfully!")
                
                return True
                
    except psycopg.OperationalError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("\nPlease ensure PostgreSQL is running and accessible.")
        print("You may need to:")
        print("  1. Start PostgreSQL service")
        print("  2. Check your DATABASE_URL environment variable")
        print("  3. Verify the username and password")
        return False
    except Exception as e:
        print(f"Error creating database: {e}")
        return False


def run_migrations() -> bool:
    """
    Run database migrations using Alembic.
    
    Returns:
        True if successful, False otherwise
    """
    print("\nRunning database migrations...")
    
    try:
        # Check if alembic is available
        result = subprocess.run(
            ['alembic', 'current'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Alembic not properly configured. Trying direct migration...")
            return run_direct_migration()
        
        # Run alembic upgrade head
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Migrations completed successfully!")
            print(result.stdout)
            return True
        else:
            print(f"Migration failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("Alembic not found. Trying direct migration...")
        return run_direct_migration()
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


def run_direct_migration() -> bool:
    """
    Run migrations directly using Python imports.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from alembic.config import Config
        from alembic import command
        
        # Get the project root directory
        project_root = Path(__file__).parent
        
        # Create Alembic configuration
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        
        # Override SQLAlchemy URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            alembic_cfg.set_main_option('sqlalchemy.url', database_url)
        
        # Run upgrade
        command.upgrade(alembic_cfg, 'head')
        
        print("Direct migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Direct migration failed: {e}")
        return False


def create_tables_directly() -> bool:
    """
    Create tables directly using SQLAlchemy models.
    This is a fallback if Alembic migrations fail.
    
    Returns:
        True if successful, False otherwise
    """
    print("\nCreating tables directly using SQLAlchemy...")
    
    try:
        from app.server.app_factory import create_app
        from app.server.models.user import db
        
        # Create Flask app
        app = create_app('development')
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("Tables created successfully!")
            return True
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


def create_admin_user(username: str, email: str, password: str) -> bool:
    """
    Create an admin user.
    
    Args:
        username: Admin username
        email: Admin email
        password: Admin password
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\nCreating admin user '{username}'...")
    
    try:
        from app.server.app_factory import create_app
        from app.server.models.user import db, User
        
        # Create Flask app
        app = create_app('development')
        
        with app.app_context():
            # Check if user already exists
            existing = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing:
                print(f"User '{username}' or email '{email}' already exists.")
                return False
            
            # Create admin user
            user = User(username=username, email=email)
            user.set_password(password)
            user.is_verified = True
            user.storage_limit = 1024 * 1024 * 1024  # 1GB for admin
            
            db.session.add(user)
            db.session.commit()
            
            print(f"Admin user '{username}' created successfully!")
            return True
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        True if connection successful, False otherwise
    """
    print("\nChecking database connection...")
    
    try:
        from app.server.app_factory import create_app
        from app.server.models.user import db
        
        # Create Flask app
        app = create_app('development')
        
        with app.app_context():
            # Try to execute a simple query
            db.session.execute(db.text('SELECT 1'))
            print("Database connection successful!")
            return True
            
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def interactive_setup():
    """Run interactive database setup."""
    print("=" * 60)
    print("Drawing Application - Database Setup")
    print("=" * 60)
    
    config = get_database_config()
    print(f"\nDatabase Configuration:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  User: {config['user']}")
    
    # Step 1: Create database
    print("\n[Step 1/4] Creating database...")
    if not create_database(config):
        print("\nDatabase creation failed. Please check your PostgreSQL configuration.")
        return False
    
    # Step 2: Run migrations
    print("\n[Step 2/4] Running migrations...")
    if not run_migrations():
        print("\nMigration failed. Trying direct table creation...")
        if not create_tables_directly():
            print("\nTable creation failed. Please check the error messages.")
            return False
    
    # Step 3: Verify connection
    print("\n[Step 3/4] Verifying database connection...")
    if not check_database_connection():
        print("\nDatabase verification failed.")
        return False
    
    # Step 4: Ask about admin user
    print("\n[Step 4/4] Admin user setup...")
    response = input("Do you want to create an admin user? (y/n): ").strip().lower()
    
    if response == 'y':
        username = input("Admin username [admin]: ").strip() or "admin"
        email = input("Admin email [admin@example.com]: ").strip() or "admin@example.com"
        password = input("Admin password [admin123]: ").strip() or "admin123"
        
        create_admin_user(username, email, password)
    
    print("\n" + "=" * 60)
    print("Database setup completed successfully!")
    print("=" * 60)
    print("\nYou can now start the server with:")
    print("  python run_server.py")
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Database setup script for Drawing Application'
    )
    parser.add_argument(
        '--create-db',
        action='store_true',
        help='Create database only'
    )
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Run migrations only'
    )
    parser.add_argument(
        '--init',
        action='store_true',
        help='Full initialization (create DB + migrate)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database (drop and recreate)'
    )
    parser.add_argument(
        '--admin-user',
        type=str,
        help='Create admin user with username'
    )
    parser.add_argument(
        '--admin-email',
        type=str,
        default='admin@example.com',
        help='Admin user email'
    )
    parser.add_argument(
        '--admin-password',
        type=str,
        default='admin123',
        help='Admin user password'
    )
    
    args = parser.parse_args()
    
    config = get_database_config()
    
    if args.reset:
        print("Resetting database...")
        create_database(config, drop_if_exists=True)
        run_migrations()
        if args.admin_user:
            create_admin_user(args.admin_user, args.admin_email, args.admin_password)
        return
    
    if args.create_db:
        create_database(config)
        return
    
    if args.migrate:
        run_migrations()
        return
    
    if args.init:
        create_database(config)
        run_migrations()
        if args.admin_user:
            create_admin_user(args.admin_user, args.admin_email, args.admin_password)
        return
    
    if args.admin_user:
        create_admin_user(args.admin_user, args.admin_email, args.admin_password)
        return
    
    # Default: interactive setup
    interactive_setup()


if __name__ == '__main__':
    main()
