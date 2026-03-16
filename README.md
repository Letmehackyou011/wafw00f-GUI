# Wafw00f GUI

A cross-platform desktop GUI for `wafw00f`, built to make WAF fingerprinting easier, faster, and more operationally friendly on Windows and Linux.

This project wraps the official `wafw00f` engine with a visual interface for running scans, tuning options, reviewing output, exporting artifacts, and checking updates.

![Wafw00f GUI Main Screen](docs/screenshots/app-main.png)

## Why This Project

`wafw00f` is excellent for command-line workflows, but many users prefer a desktop experience for repeated testing and reporting.

Wafw00f GUI helps by providing:

- Faster onboarding for users who are not terminal-first
- Real-time output with less context switching
- Easy access to common options and manual flags
- Export-ready output for documentation and sharing

## Core Features

- Live scan execution powered by upstream `wafw00f`
- Real-time output panel
- Scan history viewer
- Built-in controls for common flags (`-a`, `-v`, `-r`)
- Manual args support through **Extra args**
- In-app args manual dialog
- Proxy (`-p`) and request-timeout (`-T`) controls
- Export to TXT and JSON
- GUI + wafw00f update checking
- Terms & legal acceptance flow
- PyInstaller packaging for Python-less end users

## Project Ownership And Credits

### GUI Developer

- `Letmehackyou011`
- GitHub: https://github.com/Letmehackyou011

### Upstream wafw00f Maintainers

- Sandro Gauci
- Pinaki Mondal
- Upstream project: https://github.com/EnableSecurity/wafw00f

## Screenshots

Store images in `docs/screenshots/` and reference them in this section.

Current screenshot:

- Main screen: `docs/screenshots/app-main.png`

Example pattern:

```markdown
### Scan Running
![Scan Running](docs/screenshots/scan-running.png)

### Terms Dialog
![Terms Dialog](docs/screenshots/terms-dialog.png)
```

## Architecture Summary

1. User configures target + options in GUI.
2. GUI constructs `ScanConfig`.
3. Runner starts `wafw00f` subprocess.
4. Output streams to UI in real time.
5. Result summary is parsed and shown in history.
6. User can export output artifacts.

## Installation

### Requirements

- Python `>=3.10`
- `pip`
- Internet access for scanning and update checks

### Clone Repository

```bash
git clone https://github.com/Letmehackyou011/wafw00f-GUI
cd wafw00f
```

### Install Dependencies (Windows)

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Install Dependencies (Linux)

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

## Run The Application

### Windows

```powershell
.\scripts\run.ps1
```

### Linux

```bash
chmod +x scripts/*.sh
./scripts/run.sh
```

### Direct Run

```bash
python -m wafw00f_gui.main
```

## Build Standalone Binary (PyInstaller)

### Windows

```powershell
.\scripts\build.ps1
```

### Linux

```bash
./scripts/build.sh
```

Build output in `dist/`:

- `wafw00f-gui.exe` (Windows) or `wafw00f-gui` (Linux)
- `LICENSE.txt`
- `CREDITS.md`
- `README.md`
- `SHA256SUMS.txt`

## Use Without Python (End Users)

End users can run prebuilt binaries directly and do not need Python installed.

Recommended release process:

1. Build using scripts above
2. Publish `dist/` artifacts
3. Publish checksums from `dist/SHA256SUMS.txt`

## In-App Usage Flow

1. Enter target URL (example: `https://example.org`)
2. Select options (`-a`, `-v`, `-r`) as needed
3. Configure `Proxy (-p)` and `Req timeout (-T)` if needed
4. Add advanced flags in **Extra args**
5. Click **Run Scan**
6. Review output and export results

## Full Args Manual (Extra Args)

Supported wafw00f flags:

- `-h`, `--help`
- `-v`, `--verbose`
- `-a`, `--findall`
- `-r`, `--noredirect`
- `-t <name>`, `--test=<name>`
- `-o <file>`, `--output=<file>`
- `-f <format>`, `--format=<format>` where format is `csv`, `json`, or `text`
- `-i <file>`, `--input-file=<file>`
- `-l`, `--list`
- `-p <proxy>`, `--proxy=<proxy>`
- `-V`, `--version`
- `-H <file>`, `--headers=<file>`
- `-T <seconds>`, `--timeout=<seconds>`
- `--no-colors`

Examples:

```text
-v -v --no-colors
-p http://127.0.0.1:8080 -T 30
-t "Cloudflare (Cloudflare Inc.)"
-o result.json -f json
-i targets.txt -a
-l
```

## Troubleshooting

### Target Timeout / Max Retries Exceeded

- Increase request timeout (`-T`)
- Verify DNS/network path
- Use a proxy if required

### `No module named wafw00f`

```bash
python -m pip install wafw00f
```

### Build Fails With `PermissionError: Access is denied` On `dist/wafw00f-gui.exe`

- Close running `wafw00f-gui.exe`
- Close any Explorer preview lock on `dist/`
- Re-run `scripts/build.ps1`

### Linux Build Fails From Windows Path

- Build on native Linux, or
- Use CI workflow for Linux artifact builds

## Update Check Behavior

- GUI checks:
  - Latest GUI version/tag from repository
  - Latest `wafw00f` version from PyPI
- Internet connectivity is required
- If release/tag is unavailable, GUI reports this gracefully

## Security And Legal Notice

- Use only on systems you own or are authorized to assess
- Unauthorized scanning may violate law and policy
- Results are heuristic and should be manually validated
- Software is provided as-is under BSD-3-Clause

## License

- GUI project: BSD-3-Clause
- Aligned with upstream wafw00f licensing
- See `LICENSE` for complete text

## Roadmap

- More advanced flag controls in dedicated UI panes
- Saved scan profiles
- CI release bundles for both platforms
- Enhanced structured security reporting
