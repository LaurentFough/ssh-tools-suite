#!/usr/bin/env python3
"""
Third Party Installer Entry Point
"""

import argparse
import sys
import os
from importlib.metadata import version, PackageNotFoundError


def _get_version() -> str:
    try:
        return version("ssh-tools-suite")
    except PackageNotFoundError:
        return "unknown"


def main():
    """Main entry point for the third-party installer."""
    parser = argparse.ArgumentParser(prog="ssh-tools-installer", description="SSH Tools Suite - Third-Party Installer")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_get_version()}")
    parser.parse_args()

    try:
        from .gui.main_window import ThirdPartyInstallerGUI
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Third Party Installer")
        app.setApplicationDisplayName("SSH Tools Suite - Third Party Installer")
        app.setApplicationVersion(_get_version())
        
        # Create and show the installer window
        installer = ThirdPartyInstallerGUI()
        installer.show()
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Please ensure PySide6 is installed: pip install PySide6")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
