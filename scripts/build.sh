#!/usr/bin/env bash
set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
	PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
	PYTHON_CMD="python"
else
	echo "Python is required but was not found." >&2
	exit 1
fi

"$PYTHON_CMD" -m pip install --upgrade pip
"$PYTHON_CMD" -m pip install -r requirements.txt
"$PYTHON_CMD" -m pip install .

PYI_ARGS=(
	--noconfirm
	--onefile
	--windowed
	--name wafw00f-gui
	src/wafw00f_gui/main.py
)

if [ -f "assets/Wafw00w-GUI.png" ]; then
	PYI_ARGS=(--add-data assets/Wafw00w-GUI.png:assets "${PYI_ARGS[@]}")
elif [ -f "assets/logo.png" ]; then
	PYI_ARGS=(--add-data assets/logo.png:assets "${PYI_ARGS[@]}")
fi

if [ -f "assets/logo.ico" ]; then
	PYI_ARGS=(--icon assets/logo.ico "${PYI_ARGS[@]}")
fi

"$PYTHON_CMD" -m PyInstaller "${PYI_ARGS[@]}"

cp LICENSE dist/LICENSE.txt
cp CREDITS.md dist/CREDITS.md
cp README.md dist/README.md

if command -v sha256sum >/dev/null 2>&1; then
	( cd dist && sha256sum wafw00f-gui LICENSE.txt CREDITS.md README.md > SHA256SUMS.txt )
elif command -v shasum >/dev/null 2>&1; then
	( cd dist && shasum -a 256 wafw00f-gui LICENSE.txt CREDITS.md README.md > SHA256SUMS.txt )
fi

echo "Build complete. Binary is in dist/wafw00f-gui"
