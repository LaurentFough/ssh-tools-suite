# SSH Tunnel Manager - Release Notes

## Version 2.2.1

**Release Date:** 2026-08-09

### Fixed: dynamic (SOCKS) tunnels silently failing for some destinations, but not others

Reported as: `curl --socks5` through the tunnel worked for some sites (e.g. an IPv4-only host)
but failed with "Failed to receive SOCKS response, proxy closed connection" for others (e.g.
`google.ca`, `example.com`), while `curl --socks4` worked for everything.

Root cause: SOCKS4 can only ever carry an IPv4 address, so a SOCKS4 client is forced to resolve
locally and hand the proxy an IPv4 literal. A SOCKS5 client resolving locally (curl's default
`--socks5`, as opposed to `--socks5-hostname`) can hand the proxy an IPv6 literal instead, for
any destination that has an AAAA record — confirmed by checking DNS: `example.com`/`google.ca`
have both A and AAAA records (and failed), `ipinfo.io` is IPv4-only (and worked). If the SSH
server's network has an IPv6 address assigned but no working IPv6 route out (common on
VPS/cloud hosts), `ssh -D`'s SOCKS server just fails that connect attempt and closes the
session — no Happy-Eyeballs-style fallback to IPv4 — which looks host-specific but is really an
IPv6-vs-IPv4 issue.

**Fix:** tunnels now pass `-o AddressFamily=inet`, forcing IPv4 for every connection the ssh
process makes on the tunnel's behalf, including ones proxied through a dynamic (SOCKS) tunnel.
Trade-off: an IPv6-only destination can no longer be reached through the proxy (rare in
practice).

## Version 2.2.0

**Release Date:** 2026-08-09

### Major Changes

#### Fixed: tunnels silently detaching from the app (Stopped / no Active Tunnels)

Root-caused a bug where a tunnel would connect successfully but the app would report it as
"Stopped," and the dashboard would show no active tunnels, even with a live tunnel running.
Two separate causes were found and fixed:

- The `%C` token previously used in `ControlPath` is a deterministic hash of host+port+user,
  so a second `ssh` invocation for the same tunnel (a retry, an orphan, or a manual copy-pasted
  command) would attach to an existing master as a "mux client" and exit almost immediately,
  which the app misread as failure even though the original tunnel kept running untracked.
- More fundamentally: `-o ControlMaster=auto`, used for every tunnel to enable clean `ssh -O
  exit` shutdown, causes this era of OpenSSH to fork the real connection into an orphaned
  background process and exit the originally-launched process with status 0 — independent of
  `ControlPersist`. The app's process tracking (`subprocess.Popen.poll()`) saw that exit and
  treated a genuinely-working tunnel as a failure to start.

  **Fix:** tunnels no longer request SSH connection sharing at all (`-o ControlMaster=no -o
  ControlPath=none`, set explicitly so it can't be overridden by a `ControlMaster`/
  `ControlPersist` setting in the user's own `~/.ssh/config` either). The app only ever launches
  one `ssh` process per tunnel and tracks it directly, so multiplexing was never actually
  needed — a plain `SIGTERM` closes a `-N` session just as cleanly as `-O exit` did. Orphaned
  tunnel processes are now identified by an inert `-o SetEnv=SSH_TUNNEL_MANAGER=1` marker
  instead of the old `ControlPath`-based marker.

#### New: configurable "Test Tunnel" + per-tunnel log rotation

- The "Test" button on a running tunnel's card now runs a real, type-appropriate check instead
  of a generic placeholder message: a live SOCKS5 handshake through the proxy for dynamic
  tunnels, auto-detected (or overridden) service checks for local tunnels, and SSH reachability
  for remote tunnels.
- New optional "Test Target" field in the tunnel dialog's Advanced section to override what
  gets tested, with type-aware placeholder text explaining the default when left blank.
- Per-tunnel log files under `~/.ssh/.stm/logs/` now rotate at 2MB (3 backups kept) instead of
  growing forever, and every line is timestamped (`hh:mm:ss`, matching the in-app log widget)
  to make correlating file and UI logs during debugging easier.

#### Other fixes this release

- Advanced SSH options: a verbosity control (`-v`/`-vv`/`-vvv`), a free-form extra-options field
  validated via `ssh -G` on save, and a quick-reference help dialog, in the tunnel config
  dialog's new Advanced section.
- Added a copy button to the resolved SSH command preview.
- Fixed the tunnel-type dialog leaving stale remote-host/remote-port values visible (though
  disabled) when switching to a dynamic (SOCKS) tunnel, and a related bug where saved dynamic
  tunnels showed phantom "localhost"/"80" values on reopen.
- Fixed "remote" tunnels silently ignoring a custom `remote_host` and always forwarding to
  `localhost`.
- Fixed SSH key generation hanging on overwrite (`ssh-keygen`'s own confirmation prompt was
  reading from inherited stdin with no way to answer it from the GUI).
- Fixed generated SSH keys not getting the recommended permissions (600 private / 644 public)
  when the shell's umask was more restrictive.
- Fixed key deployment ("ssh-copy-id") unexpectedly forking to a real terminal for password
  entry instead of using the prepared GUI askpass helper.
- Fixed the "Test Connection" button in the SSH key deployment dialog being a complete no-op.
- Fixed the public-key format validator rejecting the app's own generated keys (a multi-word
  default comment broke a naive `.split()`).
- Fixed a `.pub` file being usable as an SSH identity path (silently "worked" only via
  ssh-agent fallback; fails outright in headless launches) — now auto-corrected to the private
  key counterpart, both when browsing for a key and when resolving a saved path.
- Fixed crashes (segfaults) when deleting a tunnel, starting a tunnel, or resizing a tunnel
  card — caused by eliding command text synchronously inside Qt's layout pass; now deferred via
  `QTimer.singleShot`.
- Added a cross-platform single-instance guard so the app can no longer be launched more than
  once at a time.

## Version 2.1.0

**Release Date:** 2026-08-09

### Major Changes

#### Headless tunnel launching (breaking change for password-auth tunnels)

Tunnels no longer spawn a visible terminal window that has to stay open. They now launch as
headless background processes, using `autossh` when available (falling back to plain `ssh`),
with SSH `ControlMaster`/`ControlPath` multiplexing for clean status checks and shutdown
(`ssh -O exit`) instead of raw process signals.

- **Breaking:** starting a tunnel now requires a resolvable SSH key (explicit key path or a
  default key in `~/.ssh/`). Password-only tunnels, which relied on typing a password into the
  spawned terminal, can no longer be started this way — use Tools → SSH Keys to generate and
  deploy a key first.
- "Auto-start on application launch" (previously a no-op checkbox) now actually works.
- New Tools → Clean Up Orphaned Tunnel Processes, backed by `psutil`, to find and terminate
  ssh/autossh tunnel processes left running from a previous session.
- Per-tunnel output is now captured into both the app's log widget and a log file under
  `~/.ssh/.stm/logs/`.

#### Other fixes this release

- Fixed a crash on every launch of the main tunnel-manager window (`self.log` was never bound
  to a real callable).
- Fixed broken/missing `ssh-tunnel-manager-gui` and `third-party-installer-gui` entry points.
- Fixed `--version`/`--help` on the `ssh-tunnel-manager`/`ssh-tools-installer` CLI commands
  (previously `--version` launched the GUI instead of printing a version).
- Fixed cramped/overlapping fields in the tunnel dialog, missing spin-box arrow glyphs, and a
  white-background rendering bug that made several labels invisible depending on the system's
  Qt palette.
- Removed the legacy, conflicting `setup.py` in favor of `pyproject.toml`; cleaned up stale
  `MANIFEST.in` rules from an old repo layout.
- Added a Linux AppImage build to CI alongside the existing Windows build.

## Version 2.0.0 - Professional Edition

**Release Date:** January 30, 2026

### Major Changes

#### Complete UI Redesign

The SSH Tunnel Manager has been completely redesigned with a modern, professional card-based interface that replaces the traditional table layout. The new design provides better visual hierarchy, improved usability, and context-aware controls.

**Card-Based Layout**
- Each tunnel is now displayed as an individual card with clear visual separation
- Cards show tunnel name, status badge, and all connection details at a glance
- Fixed card height (220px) ensures consistent layout and prevents text cutoff
- Optimized spacing between elements for improved readability

**Professional Dark Theme**
- Enterprise-grade dark color scheme inspired by Linear, VS Code, and Slack
- Primary background: #0d1117
- Accent colors: Success (#2ea44f), Info (#1f6feb), Danger (#f85149)
- Improved contrast and typography for better legibility

#### Context-Aware Action Buttons

Actions have been moved from the toolbar to individual tunnel cards, providing context-specific controls based on tunnel state and type.

**Active Tunnel Actions:**
- Stop button (red)
- Service-specific quick launch buttons:
  - Open Browser (web services on ports 80, 443, 8080, 8443, 8000, 3000, 5000, 9000)
  - Open RTSP Stream (RTSP services on ports 554, 8554)
  - Open RDP (Remote Desktop on port 3389)
- Browse Files (SFTP access)
- Test Connection

**Inactive Tunnel Actions:**
- Start button (green)
- Edit configuration
- Delete tunnel

#### Interface Improvements

**Window Management**
- Default window size: 1400x900 pixels
- Minimum size: 1200x700 pixels
- Window position: Centered on screen at startup

**Space Allocation**
- Card area: 80% of vertical space
- Log panel: 20% of vertical space
- Resizable splitter allows manual adjustment
- Dashboard hidden by default (can be toggled)

**Simplified Toolbar**
- New Tunnel (primary action)
- Network Scanner
- SSH Key Management
- Settings
- About

#### Functional Improvements

**State Management**
- Fixed tunnel state refresh after stopping
- Cards now correctly check running status, not just presence in active tunnels dictionary
- Immediate UI updates when tunnel state changes

**Text Layout**
- Word wrapping enabled for long values
- Minimum width constraints prevent text cutoff
- Increased spacing between detail columns
- Labels use system font (Segoe UI) with appropriate weights

### Technical Details

**Dependencies**
- PySide6 (Qt6) for GUI framework
- No changes to core SSH tunnel functionality
- Backward compatible with existing configuration files

**Build Information**
- Executable size: 95.65 MB
- Platform: Windows x64
- Python version: 3.13.3
- PyInstaller: 6.14.2

### Migration Notes

**Configuration Compatibility**
- All existing tunnel configurations are fully compatible
- No manual migration required
- Settings and saved tunnels will load automatically

**User Interface Changes**
- Tunnel selection no longer required for most actions
- Actions are performed directly from tunnel cards
- Toolbar contains only application-level commands

### Known Limitations

- Dashboard statistics hidden by default (toggle to view)
- Card layout requires more vertical space than table view
- Custom themes not yet supported (professional dark theme only)

### Bug Fixes

- Fixed tunnel stop button not resetting card state
- Corrected text cutoff in connection detail fields
- Resolved word wrapping issues for long hostnames
- Fixed button height inconsistencies

### Future Enhancements

Planned for future releases:
- Customizable card layouts
- Theme selection (light/dark/custom)
- Tunnel grouping and filtering
- Export/import functionality improvements
- Advanced monitoring dashboards

---

For support or bug reports, please visit: https://github.com/NicholasKozma/ssh_tools_suite
