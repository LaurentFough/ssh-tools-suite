# SSH Tunnel Manager - Release Notes

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
