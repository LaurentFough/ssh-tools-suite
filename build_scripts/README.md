# Build Scripts for SSH Tools Suite

Standalone executables are built by [`.github/workflows/build-and-release.yml`](../.github/workflows/build-and-release.yml),
which runs on `windows-latest` whenever a GitHub Release is published (or via manual dispatch).
That workflow is the source of truth for build arguments — see it for the exact PyInstaller invocation.

## Building locally

To reproduce a build locally on Windows:

```bash
pip install -e .[dev]

pyinstaller --onedir --windowed --name="SSH-Tunnel-Manager" \
           --add-data="src/ssh_tunnel_manager/gui/assets;assets" \
           --clean ssh_tunnel_manager_app.py

pyinstaller --onedir --windowed --name="SSH-Tools-Installer" \
           --clean third_party_installer_app.py
```

## Output
- Executables are created in `dist/`
- Build files are in `build/`
