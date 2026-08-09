#!/usr/bin/env python3
"""
Third Party Installer Package

This package handles installation of third-party tools required by the SSH Tools Suite:
- PsExec (PsTools)
- VLC Media Player 
- FFmpeg
- PX (Corporate Proxy Tool)
"""

__version__ = "2.1.0"
__author__ = "SSH Tools Team"

from .core.installer import ThirdPartyInstaller
from .gui.main_window import ThirdPartyInstallerGUI

__all__ = ["ThirdPartyInstaller", "ThirdPartyInstallerGUI"]
