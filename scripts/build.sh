#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install .

PYI_ARGS=(
	--noconfirm
	--onefile
	--windowed
	--name wafw00f-gui
	src/wafw00f_gui/main.py
)

if [ -f "assets/logo.png" ]; then
	PYI_ARGS=(--add-data assets/logo.png:assets "${PYI_ARGS[@]}")
fi

if [ -f "assets/logo.ico" ]; then
	PYI_ARGS=(--icon assets/logo.ico "${PYI_ARGS[@]}")
fi

pyinstaller "${PYI_ARGS[@]}"

cp LICENSE dist/LICENSE.txt
cp CREDITS.md dist/CREDITS.md
cp README.md dist/README.md

echo "Build complete. Binary is in dist/wafw00f-gui"
