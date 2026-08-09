#!/usr/bin/env python3
"""
SSH Tunnel Manager - Module Entry Point
"""

import argparse
import sys
from importlib.metadata import version, PackageNotFoundError


def _get_version() -> str:
    try:
        return version("ssh-tools-suite")
    except PackageNotFoundError:
        return "unknown"


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(prog="ssh-tunnel-manager", description="SSH Tunnel Manager")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_get_version()}")
    parser.parse_args()

    from .gui import SSHTunnelManager
    from .gui.main_window_actions import MainWindowActions
    from .core.single_instance import SingleInstanceGuard

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import Qt
    except ImportError:
        print("PySide6 not installed. Please install with: pip install PySide6")
        sys.exit(1)

    class SSHTunnelManagerApp(SSHTunnelManager, MainWindowActions):
        """Complete SSH Tunnel Manager application with all functionality."""
        pass

    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

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
