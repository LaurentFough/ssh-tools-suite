#!/usr/bin/env python3
"""
SSH Tunnel Manager - Single Instance Guard
Prevents multiple copies of the GUI from running at once.
"""

from PySide6.QtCore import QSharedMemory

# Same key used by every entry point (ssh_tunnel_manager/__main__.py,
# ssh_tunnel_manager_app.py, gui/__main__.py) so they all guard against each other,
# not just against copies of themselves.
_GUARD_KEY = "ssh-tools-suite.ssh-tunnel-manager.single-instance-guard"


class SingleInstanceGuard:
    """Cross-platform single-instance guard using QSharedMemory.

    QSharedMemory (rather than a lock file) is used because it's genuinely
    cross-platform via Qt itself - no separate POSIX/Windows lock-file code paths -
    and self-heals from a segment left behind by a process that crashed without
    cleaning up, which is a real risk for a GUI app: attaching to an existing segment
    and immediately detaching releases it if no other process is actually holding it,
    but is a harmless no-op if another instance genuinely still has it attached. This
    is the standard documented pattern for QSharedMemory-based single-instance guards.
    """

    def __init__(self):
        self._shared_memory = QSharedMemory(_GUARD_KEY)
        if self._shared_memory.attach():
            self._shared_memory.detach()

    def try_acquire(self) -> bool:
        """Returns True if this is the only instance, False if another is running."""
        return self._shared_memory.create(1)
