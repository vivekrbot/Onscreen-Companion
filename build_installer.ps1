$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$outputExe = Join-Path $PSScriptRoot "dist\DragonTop.exe"
if (-not (Test-Path -LiteralPath $outputExe -PathType Leaf)) {
    Write-Host "DragonTop.exe was not found. Building it first..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "build_windows.ps1")
    if (-not (Test-Path -LiteralPath $outputExe -PathType Leaf)) {
        throw "The application build did not produce: $outputExe"
    }
}

$compilerCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
) | Where-Object { $_ }

$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $compiler) {
    throw "Inno Setup 6 was not found. Install it, then run build_installer.bat again."
}

& $compiler (Join-Path $PSScriptRoot "installer\DragonTop.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed to create the installer."
}

$installer = Join-Path $PSScriptRoot "installer-output\DragonTop-Setup.exe"
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "The installer compiler completed without creating: $installer"
}

Write-Host "Installer created successfully:" -ForegroundColor Green
Write-Host "  $installer"
