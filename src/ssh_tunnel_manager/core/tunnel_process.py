#!/usr/bin/env python3
"""
SSH Tunnel Manager - SSH Process Management
"""

import logging
import logging.handlers
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Callable, Optional

# Cap per-tunnel log files at 2MB with 3 rotated backups, rather than growing forever.
_LOG_MAX_BYTES = 2 * 1024 * 1024
_LOG_BACKUP_COUNT = 3

from .models import TunnelConfig
from .constants import PROCESS_ESTABLISH_DELAY, TUNNEL_LOG_DIR

_SAFE_NAME_RE = re.compile(r'[^A-Za-z0-9_.-]+')


class TunnelProcess:
    """Manages an SSH tunnel process, launched headlessly in the background."""

    # Status constants
    STATUS_STOPPED = "stopped"
    STATUS_STARTING = "starting"
    STATUS_RUNNING = "running"
    STATUS_ERROR = "error"

    def __init__(self, config: TunnelConfig, log_callback: Optional[Callable[[str, str], None]] = None):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.status = self.STATUS_STOPPED
        self.log_callback = log_callback
        self.connection_lost_count = 0  # Track connection lost messages
        self._reader_thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Start the SSH tunnel as a headless background process (no terminal window)."""
        if self.is_running:
            return True

        try:
            # Set status to starting and reset connection lost counter
            self.status = self.STATUS_STARTING
            self.connection_lost_count = 0

            TUNNEL_LOG_DIR.mkdir(parents=True, exist_ok=True)

            ssh_args = self.config.get_ssh_command_args()

            # ssh_args[0] is always 'ssh' (see TunnelConfig.get_ssh_command_args); autossh
            # substitutes itself for that invocation, so it takes ssh's *arguments* only.
            autossh = shutil.which('autossh')
            cmd = [autossh, '-M', '0'] + ssh_args[1:] if autossh else ssh_args

            self.process = self._start_headless_process(cmd)

            # Give SSH time to establish the tunnel
            time.sleep(PROCESS_ESTABLISH_DELAY)

            if self.process.poll() is None:
                # Process is running, but keep in STARTING state until health check passes
                # The monitor thread will transition it to RUNNING when it's actually connected
                return True
            else:
                return_code = self.process.returncode
                error_message = self._get_error_message(return_code)
                self.status = self.STATUS_ERROR
                raise Exception(error_message)

        except Exception as e:
            self.is_running = False
            self.status = self.STATUS_ERROR
            raise e

    def _start_headless_process(self, cmd: list[str]) -> subprocess.Popen:
        """Start the ssh/autossh process with no visible console window, capturing output."""
        popen_kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if sys.platform == "win32":
            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(cmd, **popen_kwargs)

        log_path = TUNNEL_LOG_DIR / f"{self._safe_log_name()}.log"
        self._reader_thread = threading.Thread(
            target=self._pump_output, args=(process, log_path), daemon=True
        )
        self._reader_thread.start()

        return process

    def _safe_log_name(self) -> str:
        """Sanitize the tunnel name for use as a log filename."""
        return _SAFE_NAME_RE.sub('_', self.config.name) or "tunnel"

    def _get_file_logger(self, log_path) -> logging.Logger:
        """A rotating, timestamped logger for this tunnel's log file.

        logging.getLogger() returns the *same* Logger object for the same name across
        the whole process, so a fresh handler must not be added on every start() of a
        same-named tunnel - that would pile up duplicate handlers (and duplicate log
        lines) across repeated start/stop cycles. Clear any existing handlers first.
        """
        logger = logging.getLogger(f"ssh_tunnel_manager.tunnel.{self._safe_log_name()}")
        logger.setLevel(logging.INFO)
        logger.propagate = False  # don't bubble up to the root logger

        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()

        handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=_LOG_MAX_BYTES, backupCount=_LOG_BACKUP_COUNT, encoding='utf-8'
        )
        # Same "hh:mm:ss" timestamp format as the in-app log widget
        # (gui/widgets/professional_log.py), so file and UI timestamps line up.
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
        logger.addHandler(handler)

        return logger

    def _pump_output(self, process: subprocess.Popen, log_path) -> None:
        """Read the subprocess's merged stdout/stderr, tee to a log file and the log callback."""
        try:
            file_logger = self._get_file_logger(log_path)
            file_logger.info("=== Tunnel '%s' started ===", self.config.name)

            for line in process.stdout:
                line = line.rstrip('\n')
                if not line:
                    continue

                file_logger.info(line)

                if self.log_callback:
                    try:
                        self.log_callback(f"[{self.config.name}] {line}", "info")
                    except Exception:
                        pass
        except Exception:
            pass

    def _get_error_message(self, return_code: int) -> str:
        """Get error message based on SSH return code."""
        error_messages = {
            255: "SSH connection failed - most likely authentication failure, network issue, or server unreachable",
            1: "SSH connection failed - check host/port configuration",
            130: "SSH connection interrupted by user",
            2: "SSH protocol error or invalid command line arguments",
            65: "Host key verification failed",
            67: "Authentication method not supported"
        }

        base_message = error_messages.get(
            return_code,
            f"SSH tunnel failed to start (exit code: {return_code})"
        )

        # Add specific guidance for common issues
        if return_code == 255:
            base_message += "\n\nTroubleshooting steps:"
            base_message += "\n1. Verify SSH server is reachable: ssh user@host"
            base_message += "\n2. Ensure your SSH key is deployed to the server (Tools -> SSH Keys)"
            base_message += "\n3. Verify network connectivity and firewall settings"

        return base_message

    def stop(self):
        """Stop the SSH tunnel."""
        if not self.process:
            return

        if self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                # Force kill if graceful termination fails
                try:
                    self.process.kill()
                    self.process.wait()
                except Exception:
                    pass

        self.is_running = False
        self.status = self.STATUS_STOPPED
        self.connection_lost_count = 0  # Reset counter when manually stopped
        self.process = None

    def is_alive(self) -> bool:
        """Check if the tunnel process is alive."""
        if not self.process:
            self.is_running = False
            self.status = self.STATUS_STOPPED
            return False

        poll_result = self.process.poll()
        if poll_result is not None:
            self.is_running = False
            self.status = self.STATUS_STOPPED
            return False

        return True

    def get_status(self) -> str:
        """Get human-readable status."""
        if self.status == self.STATUS_STARTING:
            return "🟡 Starting"
        elif self.status == self.STATUS_RUNNING and self.is_alive():
            return "🟢 Running"
        elif self.status == self.STATUS_ERROR:
            return "🔴 Error"
        else:
            return "🔴 Stopped"

    def health_check(self) -> bool:
        """Perform a health check to see if the tunnel is actually working."""
        if not self.process or self.process.poll() is not None:
            return False

        # For local and dynamic (SOCKS) tunnels, verify the local port is actually listening.
        if self.config.tunnel_type in ('local', 'dynamic'):
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)  # 2 second timeout
                result = sock.connect_ex(('localhost', self.config.local_port))
                sock.close()
                return result == 0
            except Exception:
                return False

        # For remote tunnels, we can only check if the process is running
        else:
            return True

    def transition_to_running_if_healthy(self):
        """Transition from STARTING to RUNNING if health check passes."""
        if self.status == self.STATUS_STARTING and self.health_check():
            self.status = self.STATUS_RUNNING
            self.is_running = True
            return True
        return False
