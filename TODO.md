# TODO

Tracked feature work and technical debt for `ssh_tunnel_manager`, compiled from planning
sessions and code audits. Not a changelog — see `RELEASE_NOTES.md` for what's already shipped.

## Features

- [ ] **macOS `.dmg` build.** CI (`.github/workflows/build-and-release.yml`) currently builds a
  Windows zip and a Linux AppImage; the README still lists macOS as "coming soon." Needs a
  `macos-latest` job — PyInstaller `--onedir` + `hdiutil` (or `create-dmg`) for the `.dmg`
  packaging step, following the same pattern as the Linux AppImage job.

## Bugs / stubs

- [ ] **`SFTPFileBrowser.upload_folder()` is a no-op.**
  (`src/ssh_tunnel_manager/gui/dialogs/sftp_browser.py`, button "📂 Select Folder to Upload".)
  Currently just shows "Folder upload is not yet implemented. Please select individual files for
  now." Reachable today via any active tunnel's card → Files → Select Folder to Upload. Needs a
  real recursive upload (walk the local folder, mirror the structure via SFTP `mkdir`/`put`),
  ideally with a progress dialog since folders can be large — the `QThread` + signal pattern in
  `SSHKeyDeployWorker` (`gui/components/ssh_key_deployment.py`) is a reusable template.

## Technical debt / cleanup

- [ ] **Dead toolbar wiring.** `ProfessionalToolbar` (`gui/components/professional_toolbar.py`)
  only creates 3 real buttons now (New Tunnel, Network Scanner, SSH Keys) — per-tunnel actions
  moved to the cards — but still *declares* 11 more signals, and
  `main_window.py._setup_connections()` still wires all of them to handlers. Nothing emits those
  signals today, so none of it is reachable, but it's misleading dead code that would misbehave
  if anyone ever reconnected it:
  - `main_window.py` `_edit_tunnel`/`_delete_tunnel`/`_start_tunnel`/`_stop_tunnel`/
    `_test_tunnel`/`_browse_files`/`_open_web_browser` (~lines 384-495) are all placeholder
    stubs (`QMessageBox.information(..., "Please click X button on a tunnel card")`).
  - `RTSPHandler.launch_rtsp()`/`_show_rtsp_menu()` (`gui/components/rtsp_handler.py`) and
    `RDPHandler.launch_rdp()` (`gui/components/rdp_handler.py`) reference
    `self.parent.table_widget`/`self.parent.toolbar_manager`, which don't exist on the live
    `main_window.py` (it has `self.tunnel_cards`/`self.toolbar`) — would raise `AttributeError`
    if ever actually invoked. The `*_by_name` variants the cards actually use
    (`launch_rtsp_by_name`, `launch_rdp_by_name`) are correct and don't have this bug.
  - `MainWindowActions.edit_tunnel`/`delete_tunnel`/`start_tunnel`/`stop_tunnel`/`test_tunnel`
    (`gui/main_window_actions.py`, the non-underscore-prefixed versions) reference
    `self.tunnel_table.currentRow()`, and `self.tunnel_table` is permanently `None` in the live
    card-based UI — same crash risk, also unreachable.
  - Recommended direction: either delete the 11 unused signals and their dead handlers, or
    actually wire real toolbar buttons for them. Either way, resolve the half-wired state.

- [ ] **Delete unused legacy main-window variants.** `gui/main_window_backup.py`,
  `main_window_modern.py`, `main_window_professional.py`, `main_window_legacy.py` are confirmed
  unimported anywhere in the repo (verified via grep). Only `main_window.py` +
  `main_window_actions.py` are live.

- [ ] **Remove dead `_build_ssh_command_for_console`.**
  (`gui/main_window_actions.py:420`.) A second, unused SSH-command builder that duplicates
  `TunnelConfig.get_ssh_command_args()` — not called from anywhere.

## Platform coverage

- [ ] **Cross-platform verification.** Everything in the v2.1.0/v2.2.0 headless-tunnel-launch
  rewrite (the `autossh` detection/fallback, the `SSH_ASKPASS_REQUIRE=force` deploy-key fix,
  orphan-process detection via `psutil`) was developed and tested on Linux only this round.
  Needs real verification on Windows and macOS — particularly whether `autossh` is realistically
  available there at all (it's not part of a default Windows install). Note: as of v2.2.0,
  tunnels no longer use SSH `ControlMaster`/`ControlPath` at all (see `RELEASE_NOTES.md`), so
  the previous concern about Win32-OpenSSH's `ControlPath`/socket-path-length support no longer
  applies.

## Known limitations (deliberate, not bugs — revisit only if requested)

- Tunnels require a resolvable SSH key to start; password-only tunnels can no longer be started
  from the app (this was a deliberate trade-off for headless launching — see `RELEASE_NOTES.md`
  v2.1.0). An `SSH_ASKPASS`-based path to restore password-auth tunnel support was considered and
  explicitly not chosen, to keep the initial headless-launch change scoped. Worth reconsidering
  only if there's real demand for it.
