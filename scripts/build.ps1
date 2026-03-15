$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install .

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

python -m PyInstaller @pyiArgs

Copy-Item -Path LICENSE -Destination dist\LICENSE.txt -Force
Copy-Item -Path CREDITS.md -Destination dist\CREDITS.md -Force
Copy-Item -Path README.md -Destination dist\README.md -Force

Get-FileHash -Algorithm SHA256 dist\wafw00f-gui.exe, dist\LICENSE.txt, dist\CREDITS.md, dist\README.md |
	ForEach-Object { "{0}  {1}" -f $_.Hash, [System.IO.Path]::GetFileName($_.Path) } |
	Set-Content -Path dist\SHA256SUMS.txt -Encoding utf8

Write-Host "Build complete. Binary is in dist/wafw00f-gui.exe"
