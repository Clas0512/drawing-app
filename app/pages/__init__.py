"""
Pages module - Contains page widgets for the application.

Pages are full-view widgets that replace the main canvas view,
providing dedicated interfaces for specific features.
"""

from app.pages.profile_page import ProfilePage
from app.pages.shared_files_page import SharedFilesPage

__all__ = ['ProfilePage', 'SharedFilesPage']
