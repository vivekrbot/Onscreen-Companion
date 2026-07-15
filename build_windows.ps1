param(
    [switch]$SkipAutoInstallPython
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Building DragonTop for Windows..." -ForegroundColor Green
Write-Host "Project folder: $PSScriptRoot"

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$PrefixArguments = @(),
        [Parameter(Mandatory = $true)][string]$Label
    )

    try {
        $probe = & $Command @PrefixArguments -c "import sys, struct; print(sys.executable + '|' + str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '|' + str(struct.calcsize('P') * 8))" 2>$null
        $exitCode = $LASTEXITCODE

        if ($exitCode -ne 0 -or -not $probe) {
            return $null
        }

        $probeLine = @($probe)[-1].ToString().Trim()
        $parts = $probeLine.Split('|')
        if ($parts.Count -ne 3) {
            return $null
        }

        $exe = $parts[0].Trim()
        $version = $parts[1].Trim()
        $bits = [int]$parts[2].Trim()
        $versionParts = $version.Split('.')
        $major = [int]$versionParts[0]
        $minor = [int]$versionParts[1]

        if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
            return $null
        }

        if ($major -ne 3 -or $minor -lt 9 -or $minor -gt 13 -or $bits -ne 64) {
            Write-Host "Skipping $Label ($version, $bits-bit). DragonTop needs 64-bit Python 3.9-3.13." -ForegroundColor Yellow
            return $null
        }

        return [PSCustomObject]@{
            Executable = $exe
            Version = $version
            Bits = $bits
            Label = $Label
        }
    }
    catch {
        return $null
    }
}

function Find-CompatiblePython {
    # Advanced/manual override for custom Python installations.
    if ($env:DRAGONTOP_PYTHON -and (Test-Path -LiteralPath $env:DRAGONTOP_PYTHON -PathType Leaf)) {
        $result = Test-PythonCandidate -Command $env:DRAGONTOP_PYTHON -Label "DRAGONTOP_PYTHON"
        if ($result) { return $result }
    }

    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($requestedVersion in @("-3.12", "-3.11", "-3.13", "-3.10", "-3.9", "-3")) {
            $result = Test-PythonCandidate -Command $launcher.Source -PrefixArguments @($requestedVersion) -Label "py $requestedVersion"
            if ($result) { return $result }
        }
    }

    foreach ($commandName in @("python.exe", "python3.exe", "python", "python3")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($command) {
            $result = Test-PythonCandidate -Command $command.Source -Label $commandName
            if ($result) { return $result }
        }
    }

    # Detect normal python.org and WinGet per-user installations even when PATH
    # was not refreshed in the current terminal session.
    $pythonPatterns = @()
    if ($env:LOCALAPPDATA) {
        $pythonPatterns += (Join-Path $env:LOCALAPPDATA "Programs\Python\Python*\python.exe")
        $pythonPatterns += (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python*.exe")
    }
    if ($env:ProgramFiles) {
        $pythonPatterns += (Join-Path $env:ProgramFiles "Python*\python.exe")
    }
    if (${env:ProgramFiles(x86)}) {
        $pythonPatterns += (Join-Path ${env:ProgramFiles(x86)} "Python*\python.exe")
    }

    $foundExecutables = @()
    foreach ($pattern in $pythonPatterns) {
        $foundExecutables += Get-ChildItem -Path $pattern -File -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName
    }

    foreach ($exe in ($foundExecutables | Sort-Object -Unique -Descending)) {
        $result = Test-PythonCandidate -Command $exe -Label $exe
        if ($result) { return $result }
    }

    return $null
}

$pythonInfo = Find-CompatiblePython

if (-not $pythonInfo -and -not $SkipAutoInstallPython) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host ""
        Write-Host "A compatible Python installation was not found." -ForegroundColor Yellow
        Write-Host "Installing 64-bit Python 3.12 for the current user through WinGet..." -ForegroundColor Cyan
        Write-Host "Windows may display an installer or permission prompt."

        & $winget.Source install `
            --id Python.Python.3.12 `
            --exact `
            --source winget `
            --scope user `
            --architecture x64 `
            --silent `
            --accept-source-agreements `
            --accept-package-agreements

        $wingetExitCode = $LASTEXITCODE
        if ($wingetExitCode -ne 0) {
            Write-Host "WinGet returned exit code $wingetExitCode. Rechecking in case Python is already installed..." -ForegroundColor Yellow
        }

        Start-Sleep -Seconds 2
        $pythonInfo = Find-CompatiblePython
    }
    else {
        Write-Host "WinGet is not available, so Python cannot be installed automatically." -ForegroundColor Yellow
    }
}

if (-not $pythonInfo) {
    throw @"
A compatible 64-bit Python installation is still unavailable.

Fastest manual fix:
  1. Open PowerShell.
  2. Run:
       winget install --id Python.Python.3.12 --exact --source winget --scope user --architecture x64 --accept-source-agreements --accept-package-agreements
  3. Run build_windows.bat again.

If winget is unavailable, install 64-bit Python 3.12 from python.org and enable:
  - Add python.exe to PATH
  - pip
  - venv

For a custom Python path, set it before building:
  `$env:DRAGONTOP_PYTHON = 'C:\full\path\to\python.exe'
"@
}

$pythonExe = $pythonInfo.Executable
Write-Host "Using Python $($pythonInfo.Version) (64-bit): $pythonExe" -ForegroundColor Cyan

$venvDir = Join-Path $PSScriptRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (Test-Path -LiteralPath $venvDir) {
    Write-Host "Removing the previous virtual environment..."
    Remove-Item -LiteralPath $venvDir -Recurse -Force
}

Write-Host "Creating virtual environment..."
& $pythonExe -m venv $venvDir
$venvExitCode = $LASTEXITCODE
if ($venvExitCode -ne 0 -or -not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw @"
Python could not create the virtual environment (exit code $venvExitCode).
Expected file was not created:
  $venvPython

Repair or reinstall 64-bit Python and ensure the optional pip and venv components are installed.
"@
}

# PySide6 includes Jinja template files that are intentionally not valid
# standalone Python. Disabling bytecode compilation prevents pip from trying
# to compile those template files during installation.
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"

Write-Host "Preparing pip..."
& $venvPython -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) {
    throw "Failed to prepare pip in the virtual environment."
}

& $venvPython -m pip install --upgrade --no-compile pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    throw "Failed to update pip, setuptools, or wheel."
}

Write-Host "Installing DragonTop build dependencies..."
& $venvPython -m pip install --no-compile -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed. Review the pip error printed above."
}

Write-Host "Verifying native-resolution transparent animation assets..."
& $venvPython (Join-Path $PSScriptRoot "tools\verify_assets.py")
if ($LASTEXITCODE -ne 0) {
    throw "Transparent animation asset verification failed."
}

Write-Host "Generating the Windows application icon..."
& $venvPython -c "from PIL import Image; im=Image.open(r'assets/dragon_icon.png').convert('RGBA'); im.save(r'assets/dragon_icon.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if ($LASTEXITCODE -ne 0) {
    throw "Could not generate assets\dragon_icon.ico."
}

foreach ($folder in @("build", "dist")) {
    $folderPath = Join-Path $PSScriptRoot $folder
    if (Test-Path -LiteralPath $folderPath) {
        Remove-Item -LiteralPath $folderPath -Recurse -Force
    }
}

Write-Host "Packaging DragonTop.exe..."
& $venvPython -m PyInstaller --clean --noconfirm (Join-Path $PSScriptRoot "DragonTop.spec")
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed to create DragonTop.exe."
}

$outputExe = Join-Path $PSScriptRoot "dist\DragonTop.exe"
if (-not (Test-Path -LiteralPath $outputExe -PathType Leaf)) {
    throw "The build finished without creating the expected file: $outputExe"
}

Write-Host ""
Write-Host "Portable application created successfully:" -ForegroundColor Green
Write-Host "  $outputExe"
Write-Host ""
Write-Host "To create the installer, install Inno Setup 6 and run build_installer.bat."
