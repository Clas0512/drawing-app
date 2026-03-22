"""
Client Module

Contains client-side services for communicating with the server.
"""

from app.client.api_client import APIClient
from app.client.auth_manager import AuthManager
from app.client.collaboration_client import CollaborationClient

__all__ = ['APIClient', 'AuthManager', 'CollaborationClient']
