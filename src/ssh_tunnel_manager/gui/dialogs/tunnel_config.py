#!/usr/bin/env python3
"""
SSH Tunnel Manager - Configuration Dialog
"""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit,
    QSpinBox, QComboBox, QCheckBox, QDialogButtonBox, QTextEdit, QLabel,
    QPushButton, QFileDialog, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ...core.models import TunnelConfig
from ...core.constants import DEFAULT_SSH_PORT, DEFAULT_LOCAL_RTSP_PORT
from .ssh_options_help import SSHOptionsHelpDialog


class TunnelConfigDialog(QDialog):
    """Dialog for creating/editing tunnel configurations."""
    
    def __init__(self, config: Optional[TunnelConfig] = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Tunnel Configuration")
        self.setMinimumWidth(600)
        self.setup_ui()
        self.resize(self.sizeHint())
        
        if config:
            self.load_config(config)
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        
        # Basic settings
        self.name_edit = QLineEdit()
        self.description_edit = QLineEdit()
        form.addRow("Name:", self.name_edit)
        form.addRow("Description:", self.description_edit)
        
        # SSH connection settings
        ssh_group = QGroupBox("SSH Connection")
        ssh_layout = QFormLayout(ssh_group)
        
        self.ssh_host_edit = QLineEdit()
        self.ssh_port_spin = QSpinBox()
        self.ssh_port_spin.setRange(1, 65535)
        self.ssh_port_spin.setValue(DEFAULT_SSH_PORT)
        self.ssh_user_edit = QLineEdit()
        self.ssh_key_edit = QLineEdit()
        self.ssh_key_edit.setPlaceholderText("Leave empty to use a default key in ~/.ssh")

        ssh_key_layout = QHBoxLayout()
        ssh_key_layout.addWidget(self.ssh_key_edit)
        ssh_key_browse_btn = QPushButton("Browse...")
        ssh_key_browse_btn.clicked.connect(self._browse_ssh_key)
        ssh_key_layout.addWidget(ssh_key_browse_btn)

        ssh_layout.addRow("SSH Host:", self.ssh_host_edit)
        ssh_layout.addRow("SSH Port:", self.ssh_port_spin)
        ssh_layout.addRow("SSH User:", self.ssh_user_edit)
        ssh_layout.addRow("SSH Key Path (optional):", ssh_key_layout)
        
        # Tunnel settings
        tunnel_group = QGroupBox("Tunnel Configuration")
        tunnel_layout = QFormLayout(tunnel_group)
        
        self.tunnel_type_combo = QComboBox()
        self.tunnel_type_combo.addItems(['local', 'remote', 'dynamic'])
        self.tunnel_type_combo.currentTextChanged.connect(self.on_tunnel_type_changed)
        
        self.local_port_spin = QSpinBox()
        self.local_port_spin.setRange(1024, 65535)
        self.local_port_spin.setValue(DEFAULT_LOCAL_RTSP_PORT)
        
        self.remote_host_edit = QLineEdit()
        self.remote_host_edit.setText("localhost")
        self.remote_host_edit.setPlaceholderText("Not used for dynamic (SOCKS) tunnels")
        
        self.remote_port_spin = QSpinBox()
        self.remote_port_spin.setRange(1, 65535)
        self.remote_port_spin.setValue(554)
        
        tunnel_layout.addRow("Tunnel Type:", self.tunnel_type_combo)
        tunnel_layout.addRow("Local Port:", self.local_port_spin)
        tunnel_layout.addRow("Remote Host:", self.remote_host_edit)
        tunnel_layout.addRow("Remote Port:", self.remote_port_spin)

        # Advanced settings
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout(advanced_group)

        self.verbosity_combo = QComboBox()
        self.verbosity_combo.addItems([
            "Normal", "Verbose (-v)", "More Verbose (-vv)", "Debug (-vvv)"
        ])
        advanced_layout.addRow("Verbosity:", self.verbosity_combo)

        extra_args_label_layout = QHBoxLayout()
        extra_args_label_layout.addWidget(QLabel("Extra SSH Options:"))
        extra_args_label_layout.addStretch()
        extra_args_help_btn = QPushButton("❓")
        extra_args_help_btn.setMinimumWidth(36)
        extra_args_help_btn.setMaximumWidth(44)
        extra_args_help_btn.setToolTip("SSH options reference")
        extra_args_help_btn.clicked.connect(self._show_ssh_options_help)
        extra_args_label_layout.addWidget(extra_args_help_btn)

        self.extra_ssh_args_edit = QTextEdit()
        self.extra_ssh_args_edit.setPlaceholderText(
            "Additional flags/options only, e.g. -o ProxyJump=bastion.example.com -o Compression=yes\n"
            "(not a remote command - validated when you save)"
        )
        self.extra_ssh_args_edit.setFont(QFont("Consolas", 9))
        self.extra_ssh_args_edit.setFixedHeight(50)

        advanced_layout.addRow(extra_args_label_layout)
        advanced_layout.addRow(self.extra_ssh_args_edit)

        self.test_target_edit = QLineEdit()
        advanced_layout.addRow("Test Target (optional):", self.test_target_edit)

        # RTSP Configuration
        rtsp_group = QGroupBox("RTSP Configuration (Optional)")
        rtsp_layout = QFormLayout(rtsp_group)
        
        self.rtsp_url_edit = QLineEdit()
        self.rtsp_url_edit.setPlaceholderText(f"rtsp://localhost:{DEFAULT_LOCAL_RTSP_PORT}/live/0")

        rtsp_help = QLabel("Leave empty to use default: rtsp://localhost:[local_port]/live/0")
        rtsp_help.setWordWrap(True)
        rtsp_help.setStyleSheet("color: gray; font-size: 10px;")
        
        rtsp_layout.addRow("RTSP URL:", self.rtsp_url_edit)
        rtsp_layout.addRow("", rtsp_help)
        
        # Options
        self.auto_start_check = QCheckBox("Auto-start on application launch")

        # Live preview of the actual ssh command this configuration would run
        command_header_layout = QHBoxLayout()
        command_header_layout.addWidget(QLabel("Resolved Command:"))
        command_header_layout.addStretch()
        copy_command_btn = QPushButton("Copy")
        copy_command_btn.setMaximumWidth(70)
        copy_command_btn.clicked.connect(self._copy_resolved_command)
        command_header_layout.addWidget(copy_command_btn)

        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setFont(QFont("Consolas", 9))
        self.command_preview.setFixedHeight(60)

        # Layout assembly
        layout.addLayout(form)
        layout.addWidget(ssh_group)
        layout.addWidget(tunnel_group)
        layout.addWidget(advanced_group)
        layout.addWidget(rtsp_group)
        layout.addWidget(self.auto_start_check)
        layout.addLayout(command_header_layout)
        layout.addWidget(self.command_preview)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Keep the command preview live as any relevant field changes
        for widget, signal_name in [
            (self.name_edit, "textChanged"), (self.ssh_host_edit, "textChanged"),
            (self.ssh_port_spin, "valueChanged"), (self.ssh_user_edit, "textChanged"),
            (self.ssh_key_edit, "textChanged"), (self.tunnel_type_combo, "currentTextChanged"),
            (self.local_port_spin, "valueChanged"), (self.remote_host_edit, "textChanged"),
            (self.remote_port_spin, "valueChanged"), (self.verbosity_combo, "currentIndexChanged"),
            (self.extra_ssh_args_edit, "textChanged"), (self.test_target_edit, "textChanged"),
        ]:
            getattr(widget, signal_name).connect(self._update_command_preview)

        self.local_port_spin.valueChanged.connect(self._update_rtsp_placeholder)
        self.ssh_host_edit.textChanged.connect(self._update_test_target_placeholder)
        self.ssh_port_spin.valueChanged.connect(self._update_test_target_placeholder)

        # Set initial state
        self.on_tunnel_type_changed()
        self._update_command_preview()

    def _update_rtsp_placeholder(self):
        """Keep the RTSP URL placeholder in sync with the current local port, matching
        the help text below it ('...rtsp://localhost:[local_port]/live/0')."""
        self.rtsp_url_edit.setPlaceholderText(f"rtsp://localhost:{self.local_port_spin.value()}/live/0")

    def _update_test_target_placeholder(self):
        """Explain what Test Tunnel checks by default for the current tunnel type,
        so the field's purpose is clear without needing the "?" reference dialog."""
        tunnel_type = self.tunnel_type_combo.currentText()
        ssh_host = self.ssh_host_edit.text().strip() or "ssh-host"
        ssh_port = self.ssh_port_spin.value()
        if tunnel_type == 'dynamic':
            self.test_target_edit.setPlaceholderText(
                f"host:port to connect to through the proxy (default: {ssh_host}:{ssh_port})"
            )
        elif tunnel_type == 'local':
            self.test_target_edit.setPlaceholderText(
                "URL or host:port to check instead of auto-detecting (default: auto-detect)"
            )
        else:  # remote
            self.test_target_edit.setPlaceholderText(
                f"host:port to check SSH reachability (default: {ssh_host}:{ssh_port})"
            )

    def _update_command_preview(self):
        """Refresh the read-only command preview from the current form values."""
        draft = self.get_config()
        self.command_preview.setPlainText(draft.get_resolved_command_string())

    def _copy_resolved_command(self):
        """Copy the resolved command preview to the clipboard, for testing/verification
        independently of the app (e.g. pasting into a terminal)."""
        QApplication.clipboard().setText(self.command_preview.toPlainText())

    def _show_ssh_options_help(self):
        """Show the SSH options quick reference."""
        dialog = SSHOptionsHelpDialog(self)
        dialog.exec()

    def _browse_ssh_key(self):
        """Browse for an SSH private key file - avoids users hand-typing a path (e.g. with
        an unexpanded '~') that then silently fails to resolve."""
        ssh_dir = os.path.expanduser("~/.ssh")
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select SSH Private Key", ssh_dir, "All Files (*)"
        )
        if not filename:
            return

        # A .pub file is a public key, never usable as an identity file - private and
        # public keys sit right next to each other with the same base name, so picking
        # the wrong one here is an easy mistake. Auto-correct rather than silently
        # accepting a key path that will never actually authenticate.
        if filename.endswith('.pub') and os.path.exists(filename[:-4]):
            filename = filename[:-4]

        self.ssh_key_edit.setText(filename)

    def on_tunnel_type_changed(self):
        """Handle tunnel type changes - enable/disable relevant fields.

        Dynamic (SOCKS) tunnels don't use remote_host/remote_port at all, but merely
        disabling those fields left whatever value happened to be sitting in them
        visible-but-grayed-out - looking like a real, active setting when it's
        actually ignored. Clear them when entering dynamic, and restore whatever was
        there before when leaving it, rather than losing the user's local/remote
        values or showing a stale/misleading number.
        """
        tunnel_type = self.tunnel_type_combo.currentText()
        previous_type = getattr(self, '_previous_tunnel_type', None)

        if tunnel_type == 'dynamic':
            if previous_type != 'dynamic':
                self._saved_remote_host = self.remote_host_edit.text()
                self._saved_remote_port = self.remote_port_spin.value()
                self.remote_host_edit.clear()
                self.remote_port_spin.setValue(self.remote_port_spin.minimum())
            self.remote_host_edit.setEnabled(False)
            self.remote_port_spin.setEnabled(False)
            self.local_port_spin.setEnabled(True)
        else:
            # Local or remote port forwarding - both use remote_host/remote_port
            if previous_type == 'dynamic':
                self.remote_host_edit.setText(getattr(self, '_saved_remote_host', '') or 'localhost')
                saved_port = getattr(self, '_saved_remote_port', None)
                self.remote_port_spin.setValue(saved_port if saved_port else 554)
            self.remote_host_edit.setEnabled(True)
            self.remote_port_spin.setEnabled(True)
            self.local_port_spin.setEnabled(True)

        self._previous_tunnel_type = tunnel_type
        self._update_test_target_placeholder()

    def load_config(self, config: TunnelConfig):
        """Load configuration into dialog fields."""
        self.name_edit.setText(config.name)
        self.description_edit.setText(config.description)
        self.ssh_host_edit.setText(config.ssh_host)
        self.ssh_port_spin.setValue(config.ssh_port)
        self.ssh_user_edit.setText(config.ssh_user)
        self.ssh_key_edit.setText(config.ssh_key_path or "")
        self.tunnel_type_combo.setCurrentText(config.tunnel_type)
        self.local_port_spin.setValue(config.local_port)
        # For a dynamic tunnel, remote_host/remote_port are legitimately unset
        # ("" / 0) - falling back to "localhost"/80 here would show a phantom value
        # that was never actually part of this tunnel's config.
        if config.tunnel_type != 'dynamic':
            self.remote_host_edit.setText(config.remote_host or "localhost")
            self.remote_port_spin.setValue(config.remote_port or 80)
        self.auto_start_check.setChecked(config.auto_start)
        self.verbosity_combo.setCurrentIndex(max(0, min(config.verbosity, 3)))
        self.extra_ssh_args_edit.setPlainText(config.extra_ssh_args or "")
        self.test_target_edit.setText(config.test_target or "")

        # Load RTSP URL
        if hasattr(config, 'rtsp_url') and config.rtsp_url:
            self.rtsp_url_edit.setText(config.rtsp_url)
        
        # Update field states
        self.on_tunnel_type_changed()
        self._update_command_preview()

    def get_config(self) -> TunnelConfig:
        """Get configuration from dialog fields."""
        return TunnelConfig(
            name=self.name_edit.text().strip(),
            description=self.description_edit.text().strip(),
            ssh_host=self.ssh_host_edit.text().strip(),
            ssh_port=self.ssh_port_spin.value(),
            ssh_user=self.ssh_user_edit.text().strip(),
            ssh_key_path=self.ssh_key_edit.text().strip() or "",
            tunnel_type=self.tunnel_type_combo.currentText(),
            local_port=self.local_port_spin.value(),
            remote_host=self.remote_host_edit.text().strip() if self.tunnel_type_combo.currentText() != 'dynamic' else "",
            remote_port=self.remote_port_spin.value() if self.tunnel_type_combo.currentText() != 'dynamic' else 0,
            auto_start=self.auto_start_check.isChecked(),
            rtsp_url=self.rtsp_url_edit.text().strip(),
            verbosity=self.verbosity_combo.currentIndex(),
            extra_ssh_args=self.extra_ssh_args_edit.toPlainText().strip(),
            test_target=self.test_target_edit.text().strip()
        )
