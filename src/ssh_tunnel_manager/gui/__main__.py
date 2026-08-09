#!/usr/bin/env python3
"""
SSH Tunnel Manager GUI entry point
"""

import sys
from pathlib import Path

# Add the parent directory to Python path for relative imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

def main():
    """Main entry point for SSH Tunnel Manager GUI."""
    # Check if required third-party tools are installed
    try:
        from ssh_tools_common.install_check import ensure_third_party_tools_installed
        if not ensure_third_party_tools_installed("SSH Tunnel Manager"):
            return 1
    except ImportError:
        print("Warning: Could not verify third-party tools installation")
    
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import Qt
    except ImportError:
        print("PySide6 not installed. Please install with: pip install ssh-tools-suite[gui]")
        sys.exit(1)

    # Import the main application. SSHTunnelManager.__init__ calls
    # self.auto_start_tunnels(), a MainWindowActions method, so MainWindowActions must
    # actually be a base class (not just the bare SSHTunnelManager) for that call to
    # resolve at all - both import paths need the same multiple-inheritance class.
    try:
        # Try importing from the installed package first
        from ssh_tunnel_manager.gui import SSHTunnelManager
        from ssh_tunnel_manager.gui.main_window_actions import MainWindowActions
    except ImportError:
        # Fall back to relative import for development
        sys.path.insert(0, str(src_dir.parent))
        from ssh_tunnel_manager_app import SSHTunnelManagerApp
        SSHTunnelManager = None

    from ssh_tunnel_manager.core.single_instance import SingleInstanceGuard

    if SSHTunnelManager is not None:
        class SSHTunnelManagerApp(SSHTunnelManager, MainWindowActions):
            """Complete SSH Tunnel Manager application with all functionality."""
            pass

    # Create and run the application
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
