#!/usr/bin/env python3
"""
SSH Tunnel Manager Application
==============================

A professional, comprehensive application for managing SSH tunnels and connections.

Usage:
    python ssh_tunnel_manager_app.py

Features:
- SSH tunnel creation and management
- Connection monitoring and status tracking
- Port forwarding configuration
- Tunnel persistence and auto-reconnection
- Professional GUI interface
- System tray integration
- Comprehensive logging and error handling

This is the main entry point for the SSH Tunnel Manager application.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
except ImportError:
    print("PySide6 not installed. Please install with: pip install PySide6")
    sys.exit(1)

from ssh_tunnel_manager.gui import SSHTunnelManager
from ssh_tunnel_manager.gui.main_window_actions import MainWindowActions
from ssh_tunnel_manager.core.single_instance import SingleInstanceGuard


class SSHTunnelManagerApp(SSHTunnelManager, MainWindowActions):
    """Complete SSH Tunnel Manager application with all functionality.

    Multiple inheritance (matching ssh_tunnel_manager/__main__.py, the pip-installed
    entry point) rather than composition: SSHTunnelManager.__init__ calls
    self.auto_start_tunnels(), a MainWindowActions method, so MainWindowActions must
    actually be a base class for that call to resolve at all.
    """
    pass


def main():
    """Main application entry point."""
    # Note: High DPI scaling is automatically enabled in Qt6
    # No need to set AA_EnableHighDpiScaling or AA_UseHighDpiPixmaps
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Allow running in system tray

    guard = SingleInstanceGuard()
    if not guard.try_acquire():
        QMessageBox.warning(
            None, "SSH Tunnel Manager",
            "SSH Tunnel Manager is already running.\n\n"
            "Check your system tray for the existing window."
        )
        sys.exit(1)

    # Create and show main window
    window = SSHTunnelManagerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
