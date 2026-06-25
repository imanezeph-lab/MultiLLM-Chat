#!/bin/bash
# ===================================================
# Build MultiLLM-Chat for macOS
# ===================================================
# Produces a .dmg installer in the installer/ folder.
# Run on any Mac with Python 3.10+ installed.
#
# Usage:
#   chmod +x build_macos.sh
#   ./build_macos.sh
# ===================================================

set -e

echo "==> Installing dependencies..."
pip3 install -r requirements.txt

echo "==> Building .app with PyInstaller..."
rm -rf build dist

pyinstaller --windowed \
    --name "MultiLLM-Chat" \
    --icon assets/icon.png \
    --add-data "assets:assets" \
    --strip \
    --noconfirm \
    --clean \
    main.py

echo "==> Signing the .app (ad-hoc)..."
codesign --force --deep --sign - "dist/MultiLLM-Chat.app" 2>/dev/null || true

echo "==> Creating .dmg installer..."
mkdir -p installer

if ! command -v create-dmg &>/dev/null; then
    echo "Installing create-dmg..."
    brew install create-dmg
fi

rm -f "installer/MultiLLM-Chat.dmg"
create-dmg \
    --volname "MultiLLM Chat" \
    --icon-size 128 \
    --app-drop-link 380 220 \
    "installer/MultiLLM-Chat.dmg" \
    "dist/MultiLLM-Chat.app"

echo ""
echo "Done! macOS installer at: installer/MultiLLM-Chat.dmg"
echo "Share this .dmg with any Mac user — no source code exposed."
