# DragonTop for Windows — HQ Transparent Edition

DragonTop is a minimal always-on-top animated desktop dragon for Windows 10 and Windows 11.

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
- Runs in the Windows system tray without a normal taskbar window
- Optional start-at-sign-in setting
- Single-instance protection
- Installable Windows Setup package using Inno Setup

## One-click build

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

## Build the installer

Install Inno Setup 6, then double-click:

```text
build_installer.bat
```

The installer will be created at:

```text
installer-output\DragonTop-Setup.exe
```

## Usage

- Move the pointer over the dragon to play the hover and fire animation.
- Click the visible dragon pixels to play the click animation and open the action menu.
- Drag the dragon to reposition it.
- Right-click the system-tray icon for Settings, Show Dragon or Quit.
- DragonTop continues running until you select Quit DragonTop or end it through Task Manager.

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

The ready-to-package transparent frames are in `assets`. The Windows build verifies their dimensions, RGBA mode and transparent corners before creating the executable.

## Distribution note

The generated executable and installer are unsigned. Windows SmartScreen may warn users until the application is signed with a trusted Windows code-signing certificate.
