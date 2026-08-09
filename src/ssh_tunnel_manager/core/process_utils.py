#!/usr/bin/env python3
"""
SSH Tunnel Manager - Cross-platform process introspection

Uses psutil (rather than shelling out to lsof/ps on Unix or netstat/tasklist on
Windows) to find ssh/autossh tunnel processes left running from a previous
session - there's no visible terminal window for a user to notice these anymore.
"""

from typing import Iterable

import psutil

from .constants import TUNNEL_CONTROL_DIR

_TUNNEL_PROCESS_NAMES = {'ssh', 'ssh.exe', 'autossh', 'autossh.exe'}


def find_orphaned_tunnel_processes(known_pids: Iterable[int]) -> list[dict]:
    """Find ssh/autossh processes that belong to this app but aren't tracked in this session.

    Matches on the app's control-socket directory appearing in the process's command
    line (every tunnel launched by this app passes -o ControlPath=<TUNNEL_CONTROL_DIR>/%C),
    so unrelated ssh processes on the system are not flagged.
    """
    known_pids = set(known_pids)
    control_dir_marker = str(TUNNEL_CONTROL_DIR)
    orphans = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            info = proc.info
            if info['pid'] in known_pids:
                continue
            if info['name'] not in _TUNNEL_PROCESS_NAMES:
                continue

            cmdline = info.get('cmdline') or []
            if not any(control_dir_marker in arg for arg in cmdline):
                continue

            orphans.append({
                'pid': info['pid'],
                'name': info['name'],
                'cmdline': ' '.join(cmdline),
                'create_time': info.get('create_time'),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return orphans


def kill_orphaned_tunnel_processes(pids: Iterable[int]) -> tuple[int, int]:
    """Best-effort terminate the given PIDs. Returns (succeeded, failed) counts."""
    succeeded = 0
    failed = 0

    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()
            succeeded += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            failed += 1

    return succeeded, failed
