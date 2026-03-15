# wafw00f GUI (Windows + Linux)

Desktop GUI wrapper for [wafw00f](https://github.com/EnableSecurity/wafw00f), built in Python.

This app runs the original `wafw00f` scanner under the hood and displays results in a desktop interface.

## Maintainer

- GitHub maintainer: **Letmehackyou011**

## Original wafw00f developers

- Sandro Gauci
- Pinaki Mondal
- Upstream project: https://github.com/EnableSecurity/wafw00f

## Features

- Cross-platform GUI (Windows + Linux)
- Live scan output + scan history
- Common options (`-a`, `-v`, `-r`) and extra CLI args
- Export output to TXT and JSON
- First-launch Terms & Conditions + legal disclaimer acceptance

## Tool Information

- **Tool name:** wafw00f GUI
- **Type:** Desktop GUI wrapper for web application firewall fingerprinting
- **Core engine:** Official `wafw00f` scanner (upstream project)
- **Primary purpose:** Detect and fingerprint WAF technologies protecting a target website
- **Request model:** Uses HTTP/HTTPS request/response behavior through `wafw00f` logic
- **Supported OS:** Windows and Linux
- **Runtime:** Python 3.10+
- **Packaging:** PyInstaller standalone binaries (`.exe` on Windows, native binary on Linux)

### How it works (high level)

1. You provide a target URL.
2. The GUI launches `wafw00f` with selected options.
3. Scanner output is streamed live into the app.
4. Detection summary and request count are extracted and shown.
5. Results can be exported to TXT or JSON.

### Data and privacy behavior

- The app does not require user login or cloud account.
- Scan history is kept in local app memory for the current session.
- Exported files are saved only to paths you choose.
- Application logs are stored locally for troubleshooting.

### Current scope and limitations

- Detection capability depends on upstream `wafw00f` signatures and logic.
- This tool does not bypass WAFs; it fingerprints likely protection layers.
- Accuracy can vary based on target behavior, CDN layers, and blocking policies.
- Use only on systems you are authorized to test.

---

## Complete Installation Guide

### 1) Prerequisites

- Python **3.10+** installed
- `pip` available
- Internet access for target scanning
- Windows: PowerShell
- Linux: Bash + Tkinter support (usually included with system Python)

Check Python version:

```bash
python --version
```

or on Linux if needed:

```bash
python3 --version
```

### 2) Get the source code

```bash
git clone https://github.com/Letmehackyou011/wafw00f-GUI
cd wafw00f
```

If you already have the folder, just open terminal in the project root.

### 3) Install dependencies

#### Windows (PowerShell)

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

#### Linux (Bash)

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

### 4) Run the app from source

#### Windows (recommended script)

```powershell
.\scripts\run.ps1
```

#### Linux (recommended script)

```bash
chmod +x scripts/*.sh
./scripts/run.sh
```

#### Manual run

```bash
python -m wafw00f_gui.main
```

or:

```bash
wafw00f-gui
```

### 5) First launch behavior

- You must accept Terms & Conditions and the legal disclaimer before scanning.
- This acceptance is required to use the app.

---

## Build Standalone Executable

### Windows `.exe`

```powershell
.\scripts\build.ps1
```

Generated output:

- `dist/wafw00f-gui.exe`
- `dist/LICENSE.txt`
- `dist/CREDITS.md`
- `dist/README.md`
- `dist/SHA256SUMS.txt`

### Linux binary

```bash
./scripts/build.sh
```

Generated output:

- `dist/wafw00f-gui`
- `dist/LICENSE.txt`
- `dist/CREDITS.md`
- `dist/README.md`
- `dist/SHA256SUMS.txt`

### Download prebuilt binaries (recommended for end users)

End users do **not** need Python when using PyInstaller builds.

- Use GitHub Actions workflow: `.github/workflows/build-binaries.yml`
- Trigger via `workflow_dispatch` or create a version tag like `v1.0.0`
- Download artifacts from the workflow run:
	- `wafw00f-gui-Windows`
	- `wafw00f-gui-Linux`

Each artifact includes binary + `SHA256SUMS.txt` for integrity verification.

### Verify checksums

Windows:

```powershell
Get-FileHash -Algorithm SHA256 dist\wafw00f-gui.exe
```

Linux:

```bash
sha256sum -c dist/SHA256SUMS.txt
```

---

## How to use after install

1. Start the app.
2. Enter target URL (example: `https://example.org`).
3. Select optional flags (`-a`, `-v`, `-r`) if needed.
4. Click **Run Scan**.
5. Watch live output panel for results.

## Manual: All Args (Extra Args)

Use the **Extra args** input field to pass any wafw00f CLI options directly.

Supported flags:

- `-h`, `--help`: show help
- `-v`, `--verbose`: increase verbosity (can be repeated)
- `-a`, `--findall`: find all matching WAF signatures
- `-r`, `--noredirect`: do not follow redirects
- `-t <name>`, `--test=<name>`: test a specific WAF signature
- `-o <file>`, `--output=<file>`: write output to file
- `-f <fmt>`, `--format=<fmt>`: force output format (`csv`, `json`, `text`)
- `-i <file>`, `--input-file=<file>`: read targets from input file
- `-l`, `--list`: list supported WAF signatures
- `-p <proxy>`, `--proxy=<proxy>`: use HTTP/SOCKS proxy
- `-V`, `--version`: print wafw00f version
- `-H <file>`, `--headers=<file>`: custom headers file
- `-T <seconds>`, `--timeout=<seconds>`: request timeout
- `--no-colors`: disable ANSI colors in output

Examples for **Extra args**:

- `-v -v --no-colors`
- `-p http://127.0.0.1:8080 -T 20`
- `-t "Cloudflare (Cloudflare Inc.)" -v`
- `-o result.json -f json`
- `-i targets.txt -a`
- `-l`

---

## Download
<a href="https://sourceforge.net/projects/wafw00f-gui/files/latest/download"><img alt="Download wafw00f-GUI" src="https://a.fsdn.com/con/app/sf-download-button" width=276 height=48 srcset="https://a.fsdn.com/con/app/sf-download-button?button_size=2x 2x"></a>

## Troubleshooting

### `No module named wafw00f`

Run:

```bash
python -m pip install wafw00f
```

Then rerun the app.

### GUI opens but scan fails

- Verify target URL starts with `http://` or `https://`
- Check internet connectivity
- Check app logs (status bar shows log path)

### Linux Tkinter missing

Install Tk package for your distro, then retry.

### Running Linux build script from Windows path fails

If `bash ./scripts/build.sh` fails from a Windows drive path, use one of these:

- Build Linux binary on a real Linux machine (recommended)
- Use the included GitHub Actions workflow to build Linux artifact automatically

### PowerShell script blocked (Windows)

Run PowerShell as current user with a relaxed execution policy:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## Security and Legal

- This GUI does **not** reimplement wafw00f detection logic; it calls the official package.
- Use only on targets you are explicitly authorized to test.
- Misuse may be illegal in your jurisdiction.

---

## License

This project uses the same license as wafw00f: **BSD-3-Clause**.
