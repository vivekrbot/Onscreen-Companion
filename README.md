# DragonTop — HQ Transparent Edition

DragonTop is a minimal always-on-top animated desktop dragon for Windows 10, Windows 11 and macOS.

## What changed in version 1.2

- Added a native macOS build: `DragonTop.app`, distributed as a drag-to-install `DragonTop.dmg`
- "Open application" actions now use macOS's `open` command so they work for both `.app` bundles and files
- "Start DragonTop when I sign in" now works on macOS via a per-user LaunchAgent, in addition to the existing Windows Run-key support
- The system-tray icon now uses the portable PNG icon on every platform instead of a Windows-only `.ico`
- Windows and macOS binaries are now built and published together by CI for every tagged release

## What changed in version 1.1

- Rebuilt all 17 animation frames from the latest cleaned sprite sheet
- True transparent RGBA PNG cutouts with no white background
- Removed labels, divider lines, duplicated flame fragments and gray sheet shadows
- Preserved the red, orange and yellow fire sequence
- Native 360 × 240 lossless PNG canvases
- No fractional runtime image scaling by default, keeping pixel edges crisp
- Visible-pixel window mask so transparent canvas areas do not behave like a large invisible button
- Existing installations automatically migrate to the new native-resolution asset settings

## Features

- Idle, hover, fire-breathing and click animation states
- Drag the dragon anywhere on the screen
- Click the dragon to open a configurable action panel
- Supports application, URL, command, Settings and Quit actions
- Runs in the Windows system tray, or the macOS menu bar, without a normal taskbar/Dock window
- Optional start-at-sign-in setting (Windows Run key or macOS LaunchAgent)
- Single-instance protection
- Installable Windows Setup package using Inno Setup, and a drag-to-install macOS disk image

## Download

Prebuilt binaries for both platforms are attached to each [GitHub release](../../releases):

- **Windows**: `DragonTop.exe` — portable, no installation required
- **macOS**: `DragonTop.dmg` — open it and drag DragonTop into Applications

## One-click build (Windows)

Extract the entire ZIP first. Do not run scripts from inside the ZIP preview.

Double-click:

```text
build_windows.bat
```

When a compatible Python installation is missing, the script uses Windows Package Manager (`winget`) to install 64-bit Python 3.12 for the current user. It then creates `.venv`, installs dependencies, verifies every transparent frame and packages the application.

The portable application will be created at:

```text
dist\DragonTop.exe
```

Project paths containing spaces, such as `D:\Local Setup\...`, are supported.

## Build the Windows installer

Install Inno Setup 6, then double-click:

```text
build_installer.bat
```

The installer will be created at:

```text
installer-output\DragonTop-Setup.exe
```

## One-click build (macOS)

Requires Python 3.9-3.13 (install with `brew install python@3.12` if needed). From Terminal, in the project folder:

```bash
./build_macos.sh
```

This creates `.venv`, installs dependencies, verifies every transparent frame and packages the application at:

```text
dist/DragonTop.app
dist/DragonTop.dmg
```

The build is unsigned and not notarized, so the first launch requires right-click (Control-click) → Open on `DragonTop.app` to bypass Gatekeeper.

## Continuous release builds

`.github/workflows/release.yml` builds `DragonTop.exe` and `DragonTop.dmg` on every pushed `vX.Y.Z` tag and uploads both to the matching GitHub release automatically. It can also be run manually (`workflow_dispatch`) against an existing release tag.

## Usage

- Move the pointer over the dragon to play the hover and fire animation.
- Click the visible dragon pixels to play the click animation and open the action menu.
- Drag the dragon to reposition it.
- Right-click the tray icon (Windows) or menu-bar icon (macOS) for Settings, Show Dragon or Quit.
- DragonTop continues running until you select Quit DragonTop, end it through Task Manager (Windows) or Activity Monitor (macOS).

## Troubleshooting Python

Run this in PowerShell when automatic setup is unavailable:

```powershell
winget install --id Python.Python.3.12 --exact --source winget --scope user --architecture x64 --accept-source-agreements --accept-package-agreements
```

Then run `build_windows.bat` again.

For a custom Python path:

```powershell
$env:DRAGONTOP_PYTHON = 'C:\full\path\to\python.exe'
.\build_windows.ps1
```

## Source assets

The cleaned source sheet is included at:

```text
source\dragon_sprite_sheet_hq.png
```

The ready-to-package transparent frames are in `assets`. Both build scripts verify their dimensions, RGBA mode and transparent corners before creating the executable.

## Distribution note

All generated binaries are unsigned. Windows SmartScreen may warn users until the application is signed with a trusted Windows code-signing certificate, and macOS Gatekeeper will block the first launch until the app is notarized or the user explicitly chooses Open.
