#!/usr/bin/env python3
"""
SSH Tunnel Manager - SSH Options Help Dialog
Quick reference for the "Extra SSH Options" advanced field.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
from PySide6.QtGui import QFont

_HELP_TEXT = """\
SSH OPTIONS QUICK REFERENCE
============================

The "Extra SSH Options" field accepts additional ssh command-line flags and
"-o Key=Value" options, exactly as you'd type them on an ssh command line, e.g.:

    -o ProxyJump=bastion.example.com -o Compression=yes

Options you specify here are appended AFTER this app's own required options
(BatchMode, ControlMaster, etc.), so if you specify a conflicting "-o" key, your
value is ignored in favor of the app's - ssh uses the first occurrence of a
repeated "-o Key=value" option. This field is for ADDING options, not overriding
the ones the app needs to keep tunnels working headlessly.

This field is for flags/options only - not a remote command to run.

Commonly useful ssh_config options for tunnels:

  ProxyJump=host            Connect through a bastion/jump host first.
  IdentitiesOnly=yes        Only try the key(s) explicitly configured for this
                            tunnel, skip any others offered by an ssh-agent.
  Compression=yes           Compress the connection - helps on slow links,
                            rarely helps (or can hurt) on fast ones.
  ConnectTimeout=<secs>     How long to wait for the initial connection.
  ServerAliveInterval=<s>   Seconds between keepalive probes (already set by
                            this app to 30; override here if you need tighter
                            or looser detection of a dead connection).
  ServerAliveCountMax=<n>   How many missed keepalives before giving up.
  LogLevel=<level>          QUIET, ERROR, INFO, VERBOSE, DEBUG1-3. The
                            dedicated "Verbosity" dropdown above is usually
                            easier for troubleshooting than setting this
                            directly.
  ExitOnForwardFailure=yes  Already set by this app - fail fast instead of
                            connecting but silently not forwarding.
  ForwardAgent=yes          Forward your local ssh-agent to the remote host.
                            Only enable this for hosts you trust.
  StrictHostKeyChecking=no  Already set by this app (tunnels use ephemeral
                            control sockets, not long-lived known_hosts
                            entries) - listed here for reference only.
  PubkeyAuthentication=yes  Explicitly require public-key auth (this app
                            already requires a resolvable key to start any
                            tunnel at all).

Verbosity:
  The "Verbosity" dropdown above maps directly to ssh's -v/-vv/-vvv flags
  (1 to 3 repeats of -v) - useful for diagnosing connection/auth problems.
  Higher is more detailed. This is equivalent to adding "-v" here manually,
  just easier to toggle.

Full reference:
  man ssh_config
  man ssh
  https://man.openbsd.org/ssh_config
"""


class SSHOptionsHelpDialog(QDialog):
    """Read-only reference for the Extra SSH Options field."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Options Reference")
        self.setGeometry(250, 250, 640, 560)

        layout = QVBoxLayout(self)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 9))
        text_edit.setPlainText(_HELP_TEXT)
        layout.addWidget(text_edit)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)
