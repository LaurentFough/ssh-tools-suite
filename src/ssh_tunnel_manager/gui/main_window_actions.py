#!/usr/bin/env python3
"""
SSH Tunnel Manager - Main Window Actions
Extension of the main window with tunnel management actions.
"""

import os
import sys
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import QMessageBox, QDialog, QFileDialog

from ..core.models import TunnelConfig
from ..core.tunnel_process import TunnelProcess
from ..utils.connection_tester import ConnectionTester
from .dialogs.tunnel_config import TunnelConfigDialog


class MainWindowActions:
    """Mixin class providing tunnel management actions for the main window."""
    
    def __init__(self):
        """Initialize action-specific attributes."""
        self.parent_widget = None
        self.config_manager = None
        self.log = None
        self.refresh_table = None
        self.active_tunnels = {}
        self.tunnel_table = None
    
    def _get_parent(self, parent=None):
        """Helper to get the parent widget."""
        return parent or self.parent_widget
    
    def add_tunnel(self, parent=None):
        """Add a new tunnel configuration."""
        parent_widget = self._get_parent(parent)
        dialog = TunnelConfigDialog(parent=parent_widget)
        if dialog.exec() == QDialog.Accepted:
            config = dialog.get_config()
            
            success, error_msg = self.config_manager.add_configuration(config)
            if success:
                self.refresh_table()
                self.log(f"Added tunnel configuration: {config.name}")
            else:
                parent_widget = self._get_parent(parent)
                QMessageBox.warning(parent_widget, "Error", error_msg)
    
    def edit_tunnel(self, parent=None):
        """Edit selected tunnel configuration."""
        row = self.tunnel_table.currentRow()
        if row < 0:
            return
        
        name = self.tunnel_table.item(row, 0).text()
        config = self.config_manager.get_configuration(name)
        if not config:
            return
        
        parent_widget = self._get_parent(parent)
        dialog = TunnelConfigDialog(config, parent=parent_widget)
        if dialog.exec() == QDialog.Accepted:
            new_config = dialog.get_config()
            
            success, error_msg = self.config_manager.update_configuration(name, new_config)
            if success:
                # If name changed and tunnel was running, update active tunnels
                if new_config.name != name and name in self.active_tunnels:
                    tunnel_process = self.active_tunnels.pop(name)
                    self.active_tunnels[new_config.name] = tunnel_process
                
                self.refresh_table()
                self.log(f"Updated tunnel configuration: {new_config.name}")
            else:
                parent_widget = self._get_parent(parent)
                QMessageBox.warning(parent_widget, "Error", error_msg)
    
    def delete_tunnel(self, parent=None):
        """Delete selected tunnel configuration."""
        row = self.tunnel_table.currentRow()
        if row < 0:
            return
        
        name = self.tunnel_table.item(row, 0).text()
        
        parent_widget = self._get_parent(parent)
        reply = QMessageBox.question(
            parent_widget, "Confirm Delete",
            f"Are you sure you want to delete tunnel '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop tunnel if running
            if name in self.active_tunnels:
                self.active_tunnels[name].stop()
                del self.active_tunnels[name]
            
            # Remove from configurations
            if self.config_manager.delete_configuration(name):
                self.refresh_table()
                self.log(f"Deleted tunnel configuration: {name}")
    
    def start_tunnel(self):
        """Start selected tunnel as a headless background process."""
        row = self.tunnel_table.currentRow()
        if row < 0:
            return

        name = self.tunnel_table.item(row, 0).text()
        config = self.config_manager.get_configuration(name)
        if not config:
            return

        try:
            self.log(f"🔑 Starting SSH tunnel: {name}")
            self.log(f"🔗 Connecting to: {config.ssh_user}@{config.ssh_host}:{config.ssh_port}")

            # Create or get tunnel process
            if name not in self.active_tunnels:
                self.active_tunnels[name] = TunnelProcess(config, self.log)
            else:
                self.active_tunnels[name].config = config
                self.active_tunnels[name].log_callback = self.log

            tunnel = self.active_tunnels[name]
            if tunnel.start():
                self.log(f"✅ SSH tunnel started in the background: {name}")
                self.refresh_table()
                self.on_selection_changed()
            else:
                self.log(f"❌ Failed to start tunnel: {name}")

        except Exception as e:
            self.log(f"❌ Error starting tunnel {name}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start tunnel: {str(e)}")

    def stop_tunnel(self):
        """Stop selected tunnel."""
        row = self.tunnel_table.currentRow()
        if row < 0:
            return
        
        name = self.tunnel_table.item(row, 0).text()
        
        if name in self.active_tunnels:
            try:
                self.active_tunnels[name].stop()
                self.log(f"🛑 Stopped tunnel: {name}")
                self.refresh_table()
                self.on_selection_changed()
            except Exception as e:
                self.log(f"❌ Error stopping tunnel {name}: {str(e)}")
    
    def test_tunnel(self):
        """Test selected tunnel connection."""
        row = self.tunnel_table.currentRow()
        if row < 0:
            return
        
        name = self.tunnel_table.item(row, 0).text()
        config = self.config_manager.get_configuration(name)
        if not config or name not in self.active_tunnels:
            return
        
        self.log(f"🧪 Testing tunnel: {name}")
        
        try:
            if config.tunnel_type == 'local':
                # Test local port connectivity
                if ConnectionTester.test_local_port(config.local_port):
                    self.log(f"✅ Local port {config.local_port} is accessible")
                    
                    # Test tunnel connection
                    success, message = ConnectionTester.test_tunnel_connection(config)
                    if success:
                        self.log(f"✅ {message}")
                        QMessageBox.information(self, "Test Result", 
                                              f"✅ Tunnel '{name}' is working correctly!\n\n{message}")
                    else:
                        self.log(f"⚠️ {message}")
                        QMessageBox.warning(self, "Test Result",
                                          f"⚠️ Tunnel '{name}' has issues:\n\n{message}")
                else:
                    self.log(f"❌ Local port {config.local_port} is not accessible")
                    QMessageBox.critical(self, "Test Result",
                                       f"❌ Tunnel '{name}' test failed!\n\n"
                                       f"Local port {config.local_port} is not accessible")
                    
            elif config.tunnel_type == 'dynamic':
                # Test SOCKS proxy
                if ConnectionTester.test_local_port(config.local_port):
                    self.log(f"✅ SOCKS proxy on port {config.local_port} is accessible")
                    QMessageBox.information(self, "Test Result",
                                          f"✅ SOCKS proxy '{name}' is working!\n\n"
                                          f"Proxy available on localhost:{config.local_port}")
                else:
                    self.log(f"❌ SOCKS proxy port {config.local_port} is not accessible")
                    QMessageBox.critical(self, "Test Result",
                                       f"❌ SOCKS proxy '{name}' test failed!\n\n"
                                       f"Port {config.local_port} is not accessible")
            else:
                # Remote tunnel
                self.log(f"ℹ️ Remote tunnel testing limited - check remote server")
                QMessageBox.information(self, "Test Result",
                                      f"ℹ️ Remote tunnel '{name}' appears to be running\n\n"
                                      f"For remote tunnels, test from the remote server side")
                
        except Exception as e:
            self.log(f"❌ Test error for {name}: {str(e)}")
            QMessageBox.critical(self, "Test Error", f"Test failed: {str(e)}")
    
    def stop_all_tunnels(self):
        """Stop all running tunnels."""
        for name, tunnel in list(self.active_tunnels.items()):
            try:
                tunnel.stop()
                self.log(f"🛑 Stopped tunnel: {name}")
            except Exception as e:
                self.log(f"❌ Error stopping tunnel {name}: {str(e)}")
        
        self.refresh_table()
        self.on_selection_changed()
    
    def auto_start_tunnels(self):
        """Start all tunnels marked for auto-start."""
        auto_start_configs = self.config_manager.get_auto_start_configurations()
        count = 0
        
        for name, config in auto_start_configs.items():
            try:
                # Only auto-start if not already running
                if name not in self.active_tunnels or not self.active_tunnels[name].is_running:
                    # Auto-start requires key-based auth (no TTY available for a password prompt)
                    if config.resolve_ssh_key_path():
                        if name not in self.active_tunnels:
                            self.active_tunnels[name] = TunnelProcess(config, self.log)

                        if self.active_tunnels[name].start():
                            self.log(f"🚀 Auto-started tunnel: {name}")
                            count += 1
                        else:
                            self.log(f"❌ Failed to auto-start tunnel: {name}")
                    else:
                        self.log(f"⚠️ Skipping auto-start for {name} - no SSH key found (Tools -> SSH Keys)")
            except Exception as e:
                self.log(f"❌ Error auto-starting tunnel {name}: {str(e)}")
        
        if count > 0:
            # self.refresh_table is a MainWindowActions-mixin attribute that's never bound
            # to anything real (it's left as None from __init__); the live main window's
            # actual refresh method is _refresh_ui, same as every other handler in this file.
            self._refresh_ui()

    def import_tunnels(self):
        """Import tunnel configurations from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Tunnel Configurations",
            str(Path.home()), "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                success, message = self.config_manager.import_configurations(Path(file_path))
                if success:
                    self.refresh_table()
                    self.log(f"Import successful: {message}")
                    QMessageBox.information(self, "Import Success", message)
                else:
                    self.log(f"Import failed: {message}")
                    QMessageBox.critical(self, "Import Failed", message)
            except Exception as e:
                error_msg = f"Import failed: {str(e)}"
                self.log(error_msg)
                QMessageBox.critical(self, "Import Error", error_msg)
    
    def export_tunnels(self):
        """Export tunnel configurations to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Tunnel Configurations",
            str(Path.home() / "ssh_tunnels.json"), "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                success, message = self.config_manager.export_configurations(Path(file_path))
                if success:
                    self.log(f"Export successful: {message}")
                    QMessageBox.information(self, "Export Success", message)
                else:
                    self.log(f"Export failed: {message}")
                    QMessageBox.critical(self, "Export Failed", message)
            except Exception as e:
                error_msg = f"Export failed: {str(e)}"
                self.log(error_msg)
                QMessageBox.critical(self, "Export Error", error_msg)
    
    def launch_rtsp_viewer(self):
        """Launch RTSP viewer for selected tunnel."""
        # Try to find and launch external RTSP viewer
        viewer_paths = [
            "support/opencv_rtsp_viewer_improved.py",
            "support/opencv_rtsp_viewer.py"
        ]
        
        for viewer_path in viewer_paths:
            if os.path.exists(viewer_path):
                try:
                    os.system(f"python {viewer_path}")
                    self.log("🎥 Launched RTSP viewer")
                    return
                except Exception as e:
                    self.log(f"❌ Error launching RTSP viewer: {str(e)}")
        
        # If no viewer found, show instructions
        QMessageBox.information(self, "RTSP Viewer", 
                              "External RTSP viewer not found.\n\n"
                              "You can use any RTSP client like:\n"
                              "• VLC Media Player\n"
                              "• OBS Studio\n"
                              "• FFmpeg\n\n"
                              "Connect to: rtsp://localhost:PORT/stream_path")
    
    def launch_web_browser(self):
        """Launch web browser for selected tunnel."""
        row = self.tunnel_table.currentRow()
        if row < 0:
            return
        
        name = self.tunnel_table.item(row, 0).text()
        config = self.config_manager.get_configuration(name)
        if not config or config.tunnel_type != 'local':
            return
        
        # Get potential URLs
        urls = ConnectionTester.get_service_urls(config)
        if urls:
            url = urls[0]  # Use first URL
            try:
                webbrowser.open(url)
                self.log(f"🌐 Opened {url} in browser")
            except Exception as e:
                self.log(f"❌ Error opening browser: {str(e)}")
                QMessageBox.critical(self, "Browser Error", f"Failed to open browser: {str(e)}")
        else:
            # Generic URL
            url = f"http://localhost:{config.local_port}"
            try:
                webbrowser.open(url)
                self.log(f"🌐 Opened {url} in browser")
            except Exception as e:
                self.log(f"❌ Error opening browser: {str(e)}")
    
    def show_rtsp_help(self):
        """Show RTSP streaming help."""
        help_text = """
RTSP Streaming with SSH Tunnels

This application helps you securely access RTSP streams through SSH tunnels.

Common RTSP Setup:
1. Create a Local Port Forwarding tunnel
2. Set Local Port to 8554 (or any available port)
3. Set Remote Host to the IP of your RTSP camera/server
4. Set Remote Port to 554 (standard RTSP port)
5. Configure SSH connection to your server

Usage:
• Start the tunnel
• Connect your RTSP client to: rtsp://localhost:8554/your_stream_path
• The traffic will be securely forwarded through SSH

Example Configurations:
• VLC Media Player: rtsp://localhost:8554/stream
• OBS Studio: rtsp://localhost:8554/live
• Custom applications: Use localhost:8554 as RTSP server

Troubleshooting:
• Ensure SSH server allows port forwarding
• Check that remote RTSP service is running
• Verify firewall settings on both ends
• Use 'Test Connection' to verify tunnel status
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("RTSP Streaming Guide")
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()
    
    def show_about(self):
        """Show about dialog."""
        about_text = f"""
SSH Tunnel Manager v1.0

A professional tool for managing SSH tunnels,
specifically designed for RTSP streaming and
secure service access.

Features:
• Local, Remote, and Dynamic port forwarding
• Integrated SSH terminal for password authentication
• Auto-start tunnels on application launch
• Real-time tunnel monitoring
• System tray integration
• Configuration import/export
• Connection testing utilities

Built with PySide6 (Qt6) for reliability and performance.
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About SSH Tunnel Manager")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()
    
    def _build_ssh_command_for_console(self, config):
        """Build SSH command for console execution."""
        cmd = ["ssh"]
        
        # SSH options for tunneling
        cmd.extend(["-N"])  # Don't execute remote command
        cmd.extend(["-o", "StrictHostKeyChecking=ask"])  # Ask for host key verification
        cmd.extend(["-o", "ServerAliveInterval=60"])  # Keep connection alive
        cmd.extend(["-o", "ServerAliveCountMax=3"])
        cmd.extend(["-o", "PasswordAuthentication=yes"])  # Enable password auth
        cmd.extend(["-o", "BatchMode=no"])  # Disable batch mode to allow interactive input
        
        # Port forwarding based on tunnel type
        if config.tunnel_type == 'local':
            cmd.extend(["-L", f"{config.local_port}:{config.remote_host}:{config.remote_port}"])
        elif config.tunnel_type == 'remote':
            cmd.extend(["-R", f"{config.local_port}:{config.remote_host}:{config.remote_port}"])
        elif config.tunnel_type == 'dynamic':
            cmd.extend(["-D", str(config.local_port)])
        
        # SSH connection
        cmd.extend(["-p", str(config.ssh_port)])
        
        # Use SSH key if available
        if config.ssh_key_path and os.path.exists(config.ssh_key_path):
            cmd.extend(["-i", config.ssh_key_path])
        
        # Add user and host
        cmd.append(f"{config.ssh_user}@{config.ssh_host}")
        
        return cmd
