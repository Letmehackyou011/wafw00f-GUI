#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install .

pyinstaller --noconfirm --onefile --windowed --name wafw00f-gui src/wafw00f_gui/main.py

cp LICENSE dist/LICENSE.txt
cp CREDITS.md dist/CREDITS.md
cp README.md dist/README.md

echo "Build complete. Binary is in dist/wafw00f-gui"
