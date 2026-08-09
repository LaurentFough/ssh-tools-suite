#!/usr/bin/env python3
"""
SSH Tunnel Manager - Data Models
"""

import shlex
from dataclasses import dataclass, asdict
from typing import Optional

from .constants import TUNNEL_PROCESS_MARKER


@dataclass
class TunnelConfig:
    """Configuration for an SSH tunnel."""
    name: str
    ssh_host: str
    ssh_port: int
    ssh_user: str
    local_port: int
    remote_host: str
    remote_port: int
    tunnel_type: str  # 'local', 'remote', 'dynamic'
    description: str = ""
    auto_start: bool = False
    ssh_key_path: str = ""
    ssh_password: str = ""  # Runtime password (not saved to config)
    rtsp_url: str = ""  # Custom RTSP URL (single URL)
    verbosity: int = 0  # 0-3, maps to that many -v flags
    extra_ssh_args: str = ""  # Advanced: raw extra ssh flags/options, e.g. "-o ProxyJump=bastion"
    test_target: str = ""  # Optional "host:port" for Test Tunnel; see get_test_target()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization (excludes password)."""
        data = asdict(self)
        # Remove password from serialization for security
        data.pop('ssh_password', None)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TunnelConfig':
        """Create from dictionary."""
        # Make a copy to avoid modifying the original
        data = data.copy()
        
        # Ensure ssh_password is not loaded from saved config
        data.pop('ssh_password', None)
        
        # Remove any unknown fields that aren't part of the TunnelConfig dataclass
        # This handles backwards compatibility when fields are removed or renamed
        import inspect
        signature = inspect.signature(cls)
        valid_fields = set(signature.parameters.keys())
        
        # Filter out any fields not in the current TunnelConfig definition
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def copy(self) -> 'TunnelConfig':
        """Create a copy of this configuration."""
        return TunnelConfig(
            name=self.name,
            ssh_host=self.ssh_host,
            ssh_port=self.ssh_port,
            ssh_user=self.ssh_user,
            local_port=self.local_port,
            remote_host=self.remote_host,
            remote_port=self.remote_port,
            tunnel_type=self.tunnel_type,
            description=self.description,
            auto_start=self.auto_start,
            ssh_key_path=self.ssh_key_path,
            ssh_password=self.ssh_password,
            rtsp_url=self.rtsp_url,
            verbosity=self.verbosity,
            extra_ssh_args=self.extra_ssh_args,
            test_target=self.test_target
        )
    
    def validate(self) -> tuple[bool, str]:
        """Validate configuration."""
        if not self.name.strip():
            return False, "Tunnel name is required"
        
        if not self.ssh_host.strip():
            return False, "SSH host is required"
        
        if not self.ssh_user.strip():
            return False, "SSH user is required"
        
        if not 1 <= self.ssh_port <= 65535:
            return False, "SSH port must be between 1 and 65535"
        
        if not 1024 <= self.local_port <= 65535:
            return False, "Local port must be between 1024 and 65535"
        
        if self.tunnel_type not in ['local', 'remote', 'dynamic']:
            return False, "Invalid tunnel type"
        
        if self.tunnel_type != 'dynamic':
            if not self.remote_host.strip():
                return False, "Remote host is required for local/remote tunnels"

            if not 1 <= self.remote_port <= 65535:
                return False, "Remote port must be between 1 and 65535"

        if self.extra_ssh_args and self.extra_ssh_args.strip():
            is_valid, error_msg = self._validate_extra_ssh_args()
            if not is_valid:
                return False, error_msg

        return True, ""

    def _validate_extra_ssh_args(self) -> tuple[bool, str]:
        """Validate the Advanced 'extra SSH options' field by delegating to ssh itself.

        `ssh -G <options> <host>` prints the fully resolved configuration and exits
        without ever connecting (confirmed: ~4ms, no network I/O even against an
        unresolvable hostname), so it's a fast, accurate way to catch malformed/unknown
        options using ssh's own parser instead of a hand-rolled regex.
        """
        import subprocess

        try:
            tokens = shlex.split(self.extra_ssh_args.strip())
        except ValueError as e:
            return False, f"Extra SSH options: could not parse ({e})"

        if not tokens:
            return True, ""

        try:
            result = subprocess.run(
                ['ssh', '-G', *tokens, 'validation-placeholder-host'],
                capture_output=True, text=True, timeout=5
            )
        except FileNotFoundError:
            return False, "Extra SSH options: could not validate ('ssh' not found on PATH)"
        except subprocess.TimeoutExpired:
            return False, "Extra SSH options: validation timed out"

        if result.returncode != 0:
            detail = result.stderr.strip() or "ssh rejected these options"
            return False, f"Extra SSH options: {detail}"

        return True, ""
    
    def resolve_ssh_key_path(self) -> Optional[str]:
        """Resolve the SSH private key to use: explicit path first, then default locations."""
        import os
        from pathlib import Path

        if self.ssh_key_path and self.ssh_key_path.strip():
            # os.path.exists() never expands a literal "~" the way a shell or ssh itself
            # would, so a manually-typed "~/.ssh/id_..." path would otherwise always
            # silently fail to resolve even though the file genuinely exists.
            expanded = os.path.expanduser(self.ssh_key_path.strip())

            # A ".pub" file is a public key - never usable as an ssh -i identity file
            # for authentication - but it's an easy mistake to point at one (e.g. in a
            # file browser, sitting right next to the private key with the same base
            # name). Confirmed in practice: this silently "half-works" if an ssh-agent
            # happens to already have the matching key loaded (agent fallback masks
            # the broken -i path), but fails when launched headlessly without that
            # luck. Auto-correct to the private key counterpart rather than ever
            # resolving to a .pub path.
            if expanded.endswith('.pub'):
                expanded = expanded[:-4]

            if expanded and os.path.exists(expanded):
                return expanded

        home = Path.home()
        default_keys = [
            home / '.ssh' / 'id_ed25519',
            home / '.ssh' / 'id_ecdsa',
            home / '.ssh' / 'id_rsa',
            home / '.ssh' / 'id_dsa'
        ]

        for key_path in default_keys:
            if key_path.exists():
                return str(key_path)

        return None

    def get_ssh_command_args(self) -> list[str]:
        """Generate SSH command arguments for this tunnel.

        Requires a resolvable SSH key (see resolve_ssh_key_path()) since tunnels run
        headlessly with no TTY for interactive password entry.

        Deliberately never requests connection sharing (no ControlMaster/ControlPath):
        confirmed by direct reproduction that with `-o ControlMaster=auto` - even a
        brand-new master, with NO ControlPersist set anywhere (neither here nor in the
        user's own ssh config) - this ssh build (OpenSSH 10.4p1) silently forks the
        real connection into an orphaned background process and the originally
        launched process exits with status 0 almost immediately. That's fatal for this
        app's whole tracking model, which watches the launched `subprocess.Popen`
        handle directly (poll()/terminate()) rather than a control socket. Since this
        app only ever launches one ssh process per tunnel and tracks it directly,
        connection sharing was never actually needed - it existed only to support a
        clean `-O exit` shutdown, which a plain SIGTERM achieves just as well for a
        `-N` session.
        """
        # Build tunnel argument based on type
        if self.tunnel_type == 'local':
            tunnel_arg = f"-L {self.local_port}:{self.remote_host}:{self.remote_port}"
        elif self.tunnel_type == 'remote':
            # remote_host is the destination the remote server forwards back to, as
            # seen from this machine - almost always "localhost", but the field is
            # user-editable and saved, so it must actually be honored here rather
            # than silently ignored in favor of a hardcoded "localhost".
            forward_target = self.remote_host.strip() if self.remote_host and self.remote_host.strip() else "localhost"
            tunnel_arg = f"-R {self.remote_port}:{forward_target}:{self.local_port}"
        else:  # dynamic
            tunnel_arg = f"-D {self.local_port}"

        key_to_use = self.resolve_ssh_key_path()
        if not key_to_use:
            raise ValueError(
                f"No SSH key found for tunnel '{self.name}'. Generate or deploy one via "
                f"Tools -> SSH Keys, or set a key path in Edit -> SSH Key Path."
            )

        cmd = [
            'ssh',
            '-N',  # Don't execute remote command
            tunnel_arg,
            f"{self.ssh_user}@{self.ssh_host}",
            '-p', str(self.ssh_port),
            '-i', key_to_use,
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ServerAliveInterval=30',
            '-o', 'ServerAliveCountMax=3',
            '-o', 'TCPKeepAlive=yes',
            '-o', 'ExitOnForwardFailure=yes',
            '-o', 'ConnectTimeout=30',
            '-o', 'ControlMaster=no',
            '-o', 'ControlPath=none',
            # A harmless, inert marker (the remote side just ignores an unrecognized
            # SetEnv name) that lets process_utils.find_orphaned_tunnel_processes()
            # recognize this app's own tunnel processes by their command line, now that
            # ControlPath is no longer available to serve as that marker.
            '-o', f'SetEnv={TUNNEL_PROCESS_MARKER}=1',
        ]

        if self.verbosity > 0:
            cmd.extend(['-v'] * min(self.verbosity, 3))

        if self.extra_ssh_args and self.extra_ssh_args.strip():
            # Appended last, deliberately: ssh uses first-occurrence-wins for repeated
            # "-o Key=value" flags, so anything required above (BatchMode, ControlMaster,
            # etc.) always takes precedence over a conflicting user-supplied override here.
            cmd.extend(shlex.split(self.extra_ssh_args.strip()))

        return cmd

    def get_test_target(self) -> tuple[str, int]:
        """Resolve the (host, port) to test against for the Test Tunnel action.

        Uses the explicit test_target override ("host:port") if set and parseable;
        otherwise defaults to the tunnel's own SSH server. That default matters most
        for dynamic (SOCKS) tunnels, which have no destination of their own to test -
        the SSH server is always reachable through the proxy without requiring the
        user to configure anything just to run a basic test.
        """
        if self.test_target and self.test_target.strip():
            text = self.test_target.strip()
            if ':' in text:
                host, _, port_text = text.rpartition(':')
                if host and port_text.isdigit():
                    return host, int(port_text)

        return self.ssh_host, self.ssh_port

    def get_resolved_command_string(self) -> str:
        """Human-readable preview of the ssh command this tunnel would actually run.

        Never raises - shows a specific placeholder for each of the two ways this can
        fail (no key resolvable, or unparseable extra_ssh_args) instead of propagating.
        """
        if self.extra_ssh_args and self.extra_ssh_args.strip():
            try:
                shlex.split(self.extra_ssh_args.strip())
            except ValueError as e:
                return f"(extra SSH options: could not parse - {e})"

        try:
            args = self.get_ssh_command_args()
        except ValueError:
            return "(no SSH key configured - see Tools -> SSH Keys)"

        return shlex.join(args)

    def get_display_name(self) -> str:
        """Get a display-friendly name for the tunnel."""
        if self.description:
            return f"{self.name} - {self.description}"
        return self.name
    
    def get_connection_string(self) -> str:
        """Get connection string representation."""
        if self.tunnel_type == 'dynamic':
            return f"SOCKS Proxy on localhost:{self.local_port}"
        elif self.tunnel_type == 'local':
            return f"localhost:{self.local_port} → {self.remote_host}:{self.remote_port}"
        else:  # remote
            return f"{self.remote_host}:{self.remote_port} ← localhost:{self.local_port}"
    
    def get_rtsp_url(self) -> str:
        """Get the RTSP URL for this tunnel configuration."""
        if self.rtsp_url:
            return self.rtsp_url
        else:
            # Generate default RTSP URL using the local port
            return f"rtsp://localhost:{self.local_port}/live/0"
    
    def get_common_rtsp_urls(self) -> list[str]:
        """Get common RTSP URL patterns for this tunnel configuration."""
        base_url = f"rtsp://localhost:{self.local_port}"
        return [
            f"{base_url}/live/0",
            f"{base_url}/stream/0",
            f"{base_url}/cam/realmonitor?channel=1&subtype=0",
            f"{base_url}/av0_0",
            f"{base_url}/axis-media/media.amp",
            f"{base_url}/video.mjpg",
            f"{base_url}/live",
            f"{base_url}/stream",
            f"{base_url}/"
        ]
