#!/usr/bin/env python3
"""
Drawing Application - Main Entry Point

A modular Qt-based drawing application with:
- Multiple drawing tools (pen, line, shapes, text, arrows, etc.)
- Layer management with grouping and overlay
- Text styles (headings, titles, bold, italic, lists)
- File save/open with custom .draw format
- Export to PNG, JPEG, SVG
- User authentication and cloud storage
- Real-time collaboration

Run with: python main.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Import the main window
from app.main_window import MainWindow


def main():
    """Main application entry point."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Drawing Application")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("DrawingApp")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
