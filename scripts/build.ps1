$ErrorActionPreference = "Stop"

function Invoke-NativeChecked {
	param(
		[Parameter(Mandatory = $true)]
		[string]$Command,
		[Parameter(Mandatory = $false)]
		[string]$Step = "Command"
	)

	Invoke-Expression $Command
	if ($LASTEXITCODE -ne 0) {
		throw "$Step failed with exit code $LASTEXITCODE"
	}
}

function Test-FileLocked {
	param(
		[Parameter(Mandatory = $true)]
		[string]$Path
	)

	if (-not (Test-Path $Path)) {
		return $false
	}

	try {
		$stream = [System.IO.File]::Open($Path, 'Open', 'ReadWrite', 'None')
		$stream.Close()
		return $false
	} catch {
		return $true
	}
}

Invoke-NativeChecked -Command "python -m pip install --upgrade pip" -Step "Upgrade pip"
Invoke-NativeChecked -Command "python -m pip install -r requirements.txt" -Step "Install requirements"
Invoke-NativeChecked -Command "python -m pip install ." -Step "Install project"

$pyiArgs = @(
	"--noconfirm",
	"--onefile",
	"--windowed",
	"--name", "wafw00f-gui",
	"src/wafw00f_gui/main.py"
)

if (Test-Path "assets/Wafw00w-GUI.png") {
	$pyiArgs = @("--add-data", "assets/Wafw00w-GUI.png;assets") + $pyiArgs
} elseif (Test-Path "assets/logo.png") {
	$pyiArgs = @("--add-data", "assets/logo.png;assets") + $pyiArgs
}

if (Test-Path "assets/logo.ico") {
	$pyiArgs = @("--icon", "assets/logo.ico") + $pyiArgs
}

$targetExe = "dist\wafw00f-gui.exe"
if (Test-FileLocked -Path $targetExe) {
	throw "Cannot build because '$targetExe' is locked. Close wafw00f-gui.exe (and any Explorer preview) and try again."
}

python -m PyInstaller @pyiArgs
if ($LASTEXITCODE -ne 0) {
	throw "PyInstaller build failed with exit code $LASTEXITCODE"
}

Copy-Item -Path LICENSE -Destination dist\LICENSE.txt -Force
Copy-Item -Path CREDITS.md -Destination dist\CREDITS.md -Force
Copy-Item -Path README.md -Destination dist\README.md -Force

Get-FileHash -Algorithm SHA256 dist\wafw00f-gui.exe, dist\LICENSE.txt, dist\CREDITS.md, dist\README.md |
	ForEach-Object { "{0}  {1}" -f $_.Hash, [System.IO.Path]::GetFileName($_.Path) } |
	Set-Content -Path dist\SHA256SUMS.txt -Encoding utf8

Write-Host "Build complete. Binary is in dist/wafw00f-gui.exe"
