#!/usr/bin/env python3
"""
SSH Tunnel Manager - Connection Testing Utilities
"""

import socket
import urllib.request
import urllib.error
from typing import Optional

from ..core.models import TunnelConfig
from ..core.constants import HTTP_PORTS, HTTPS_PORTS, RTSP_PORTS


class ConnectionTester:
    """Utilities for testing tunnel connections."""
    
    @staticmethod
    def test_local_port(port: int, host: str = "localhost", timeout: int = 2) -> bool:
        """Test if a local port is accessible."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def test_tunnel_connection(config: TunnelConfig) -> tuple[bool, str]:
        """Test the actual tunnel connection."""
        try:
            if not ConnectionTester.test_local_port(config.local_port):
                return False, f"Local port {config.local_port} is not accessible"
            
            # Test based on service type
            if config.remote_port in RTSP_PORTS:
                success, message = ConnectionTester._test_rtsp_service(config.local_port)
            elif config.remote_port in HTTP_PORTS + HTTPS_PORTS:
                success, message = ConnectionTester._test_http_service(config.local_port)
            else:
                # Generic port test
                success = True
                message = f"Port {config.local_port} is accessible"
            
            return success, message
            
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    @staticmethod
    def _test_rtsp_service(local_port: int) -> tuple[bool, str]:
        """Test RTSP service connectivity."""
        try:
            # RTSP uses TCP initially
            if ConnectionTester.test_local_port(local_port, timeout=3):
                rtsp_url = f"rtsp://localhost:{local_port}/live/0"
                return True, f"RTSP service responding. Try: {rtsp_url}"
            return False, "RTSP service not responding"
            
        except Exception as e:
            return False, f"RTSP test failed: {str(e)}"
    
    @staticmethod
    def _test_http_service(local_port: int) -> tuple[bool, str]:
        """Test HTTP service connectivity."""
        try:
            # Try HTTP first, then HTTPS
            for protocol in ['http', 'https']:
                try:
                    url = f"{protocol}://localhost:{local_port}"
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'SSH-Tunnel-Tester/1.0')
                    
                    with urllib.request.urlopen(req, timeout=3) as response:
                        return True, f"{protocol.upper()} service responding: {url}"
                        
                except urllib.error.HTTPError as e:
                    # Even HTTP errors mean the service is responding
                    if e.code in [200, 301, 302, 401, 403, 404]:
                        return True, f"{protocol.upper()} service responding (HTTP {e.code}): {url}"
                except:
                    continue
                    
            return False, "HTTP/HTTPS service not responding"
            
        except Exception as e:
            return False, f"HTTP test failed: {str(e)}"
    
    @staticmethod
    def get_service_urls(config: TunnelConfig) -> list[str]:
        """Get potential service URLs for a tunnel."""
        if config.tunnel_type != 'local':
            return []
        
        urls = []
        port = config.local_port
        
        # RTSP URLs
        if config.remote_port in RTSP_PORTS:
            urls.extend([
                f"rtsp://localhost:{port}/live/0",
                f"rtsp://localhost:{port}/stream",
                f"rtsp://localhost:{port}/",
            ])
        
        # HTTP URLs
        if config.remote_port in HTTP_PORTS:
            urls.append(f"http://localhost:{port}")
        
        # HTTPS URLs
        if config.remote_port in HTTPS_PORTS:
            urls.append(f"https://localhost:{port}")
        
        # Generic URL for other services
        if not urls:
            if config.remote_port in [80, 8080, 3000, 5000, 8000, 9000]:
                urls.append(f"http://localhost:{port}")
            elif config.remote_port in [443, 8443]:
                urls.append(f"https://localhost:{port}")
        
        return urls
    
    @staticmethod
    def test_socks_proxy(local_port: int, target_host: str, target_port: int, timeout: float = 5) -> tuple[bool, str]:
        """Test a dynamic (SOCKS5) tunnel by connecting THROUGH it to target_host:target_port.

        A minimal no-auth SOCKS5 CONNECT handshake (RFC 1928, domain-name addressing so
        the proxy itself resolves the target - works for hostnames and IP literals
        alike). Proves the proxy actually relays a connection end-to-end, not just that
        the local port is listening (test_local_port() only confirms the latter).
        """
        try:
            target_bytes = target_host.encode('ascii')
        except UnicodeEncodeError:
            return False, f"Invalid test target host: {target_host!r}"

        if not target_bytes or len(target_bytes) > 255:
            return False, f"Invalid test target host: {target_host!r}"

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(('localhost', local_port))

            # Greeting: SOCKS version 5, 1 auth method offered, no-auth (0x00)
            sock.sendall(b'\x05\x01\x00')
            greeting_reply = sock.recv(2)
            if len(greeting_reply) != 2 or greeting_reply[0] != 0x05:
                return False, "SOCKS proxy did not respond with a valid SOCKS5 greeting"
            if greeting_reply[1] != 0x00:
                return False, "SOCKS proxy requires authentication this test doesn't support"

            # CONNECT request, ATYP=0x03 (domain name)
            request = (
                b'\x05\x01\x00\x03' + bytes([len(target_bytes)]) + target_bytes
                + target_port.to_bytes(2, 'big')
            )
            sock.sendall(request)
            reply = sock.recv(4)

            if len(reply) < 2 or reply[0] != 0x05:
                return False, "SOCKS proxy sent an invalid CONNECT reply"

            status = reply[1]
            if status == 0x00:
                return True, f"SOCKS proxy successfully connected to {target_host}:{target_port}"

            reasons = {
                0x01: "general SOCKS server failure",
                0x02: "connection not allowed by ruleset",
                0x03: "network unreachable",
                0x04: "host unreachable",
                0x05: "connection refused by target",
                0x06: "TTL expired",
                0x07: "command not supported",
                0x08: "address type not supported",
            }
            reason = reasons.get(status, f"error code {status}")
            return False, f"SOCKS CONNECT to {target_host}:{target_port} failed: {reason}"

        except socket.timeout:
            return False, "SOCKS proxy test timed out"
        except ConnectionRefusedError:
            return False, f"Could not connect to local SOCKS port {local_port} - is the tunnel running?"
        except Exception as e:
            return False, f"SOCKS proxy test failed: {e}"
        finally:
            if sock:
                sock.close()

    @staticmethod
    def test_ssh_connectivity(host: str, port: int = 22, timeout: int = 5) -> tuple[bool, str]:
        """Test basic SSH connectivity (port 22)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return True, f"SSH port {port} is accessible on {host}"
            else:
                return False, f"Cannot connect to SSH port {port} on {host}"
                
        except socket.gaierror:
            return False, f"Cannot resolve hostname: {host}"
        except Exception as e:
            return False, f"SSH connectivity test failed: {str(e)}"
