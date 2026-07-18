#!/usr/bin/env bash
# One-click build for macOS: creates DragonTop.app and DragonTop.dmg in dist/.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This script builds the macOS app and must be run on macOS." >&2
    exit 1
fi

PYTHON_BIN="${DRAGONTOP_PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.9-3.13 was not found. Install it from https://www.python.org/downloads/macos/" >&2
    echo "or with Homebrew: brew install python@3.12" >&2
    exit 1
fi

echo "Using $($PYTHON_BIN --version) at $(command -v "$PYTHON_BIN")"

VENV_DIR=".venv"
if [[ -d "$VENV_DIR" ]]; then
    echo "Removing the previous virtual environment..."
    rm -rf "$VENV_DIR"
fi

echo "Creating virtual environment..."
"$PYTHON_BIN" -m venv "$VENV_DIR"
VENV_PYTHON="$VENV_DIR/bin/python"

echo "Preparing pip..."
"$VENV_PYTHON" -m pip install --upgrade --quiet pip setuptools wheel

echo "Installing DragonTop build dependencies..."
"$VENV_PYTHON" -m pip install --quiet -r requirements.txt

echo "Verifying transparent animation assets..."
"$VENV_PYTHON" tools/verify_assets.py

echo "Generating the macOS application icon..."
"$VENV_PYTHON" -c "from PIL import Image; im = Image.open('assets/dragon_icon.png').convert('RGBA'); im.save('assets/dragon_icon.icns')"

rm -rf build dist

echo "Packaging DragonTop.app..."
"$VENV_PYTHON" -m PyInstaller --clean --noconfirm DragonTop.spec

APP_PATH="dist/DragonTop.app"
if [[ ! -d "$APP_PATH" ]]; then
    echo "The build finished without creating: $APP_PATH" >&2
    exit 1
fi

echo "Packaging DragonTop.dmg..."
DMG_STAGING="$(mktemp -d)"
trap 'rm -rf "$DMG_STAGING"' EXIT
cp -R "$APP_PATH" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"
rm -f dist/DragonTop.dmg
hdiutil create -volname DragonTop -srcfolder "$DMG_STAGING" -ov -format UDZO dist/DragonTop.dmg

echo
echo "App bundle created:"
echo "  $(pwd)/$APP_PATH"
echo "Disk image created:"
echo "  $(pwd)/dist/DragonTop.dmg"
echo
echo "To install: open dist/DragonTop.dmg and drag DragonTop into Applications."
echo
echo "Note: this build is unsigned and not notarized. Right-click (or Control-click)"
echo "DragonTop in Applications and choose Open the first time to bypass Gatekeeper,"
echo "since macOS will otherwise refuse to launch an unidentified developer's app."
