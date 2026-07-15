@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"
set "BUILD_EXIT=%ERRORLEVEL%"

if not "%BUILD_EXIT%"=="0" (
    echo.
    echo DragonTop build failed. Read the error above for the exact cause.
    pause
    exit /b %BUILD_EXIT%
)

echo.
echo Build completed successfully.
pause
endlocal
