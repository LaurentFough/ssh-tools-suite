#!/usr/bin/env python3
"""
SSH Tunnel Manager - Constants and Configuration
"""

import os
import sys
import tempfile
from pathlib import Path


def _default_control_dir() -> Path:
    """Short-as-possible directory for SSH ControlMaster sockets.

    AF_UNIX socket paths are limited to ~104-108 bytes total, and a user's home
    directory path length is not under our control (verified in testing: even a
    moderately nested $HOME can blow the limit once "/.ssh/.stm/control/<hash>" is
    appended) - so this deliberately does NOT live under the home directory.
    Prefers XDG_RUNTIME_DIR (short, per-user, tmpfs-backed) when available.
    """
    xdg_runtime = os.environ.get('XDG_RUNTIME_DIR')
    if xdg_runtime:
        return Path(xdg_runtime) / 'stm'
    if sys.platform == 'win32':
        return Path(tempfile.gettempdir()) / 'stm'
    return Path(tempfile.gettempdir()) / f'.stm-{os.getuid()}'


# Per-tunnel log files: kept under the home directory since these are meant to be
# human-discoverable for debugging and aren't subject to any socket path length limit.
TUNNEL_LOG_DIR = Path.home() / ".ssh" / ".stm" / "logs"

# SSH ControlMaster socket directory - see _default_control_dir() docstring.
TUNNEL_CONTROL_DIR = _default_control_dir()

# SSH prompt detection patterns
SSH_PASSWORD_PROMPTS = [
    'password:', 'password for', "'s password:", 
    'enter password', 'password required', 'authentication',
    'passphrase', 'login:', 'user:', 'username:',
    'please enter password', 'password authentication'
]

SSH_STDERR_PASSWORD_PROMPTS = SSH_PASSWORD_PROMPTS + [
    '@', 'permission denied', 'access denied',
    'enter passphrase', 'ssh key passphrase'
]

SSH_CONFIRMATION_PROMPTS = [
    'yes/no', 'fingerprint', 'continue connecting', 'are you sure',
    'host key verification', 'authenticity', 'accept'
]

SSH_ERROR_PATTERNS = [
    'connection refused', 'connection timed out', 'host unreachable',
    'no route to host', 'permission denied (publickey)',
    'authentication failed', 'too many authentication failures'
]

# Application constants
APP_NAME = "SSH Tunnel Manager"
APP_VERSION = "1.0"
ORGANIZATION_NAME = "SSHTunnelManager"
CONFIG_NAME = "Config"

# Default ports for services
DEFAULT_SSH_PORT = 22
DEFAULT_RTSP_PORT = 554
DEFAULT_LOCAL_RTSP_PORT = 8554

# Common service ports for testing
HTTP_PORTS = [80, 8080, 3000, 5000, 8000, 9000]
HTTPS_PORTS = [443, 8443]
RTSP_PORTS = [554, 8554]

# UI Constants
CONSOLE_FONT = "Consolas"
CONSOLE_FONT_SIZE = 10
LOG_FONT_SIZE = 9

# Terminal styling
TERMINAL_STYLE = """
    QPlainTextEdit {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #555;
        padding: 5px;
    }
"""

# Timeouts and intervals
SSH_TIMEOUT = 30
PROCESS_START_DELAY = 1
PROCESS_ESTABLISH_DELAY = 2
MONITOR_INTERVAL = 2
INPUT_HIDE_DELAY = 2000

# File extensions
CONFIG_FILE_EXTENSION = ".json"
BACKUP_FILE_EXTENSION = ".bak"
