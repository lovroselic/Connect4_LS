# build_release.ps1
#
# Builds the final portable Windows release of Connect4_LS.
# Run while the Connect4_LS Conda environment is active.

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$SpecPath = Join-Path $ProjectRoot "Connect4_LS.spec"
$IconPath = Join-Path $ProjectRoot "C4.ico"
$VersionInfoPath = Join-Path $ProjectRoot "version_info.txt"

$BuildDirectory = Join-Path $ProjectRoot "build"
$DistributionDirectory = Join-Path $ProjectRoot "dist"
$ReleaseDirectory = Join-Path $DistributionDirectory "Connect4_LS"
$ExecutablePath = Join-Path $ReleaseDirectory "Connect4_LS.exe"

$ReleaseName = "Connect4_LS-v0.6.0-win64"
$ZipPath = Join-Path $DistributionDirectory ($ReleaseName + ".zip")
$LogPath = Join-Path $ProjectRoot "pyinstaller_build.log"

Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================"
Write-Host " Connect4_LS final portable release"
Write-Host "============================================"
Write-Host "Project: $ProjectRoot"
Write-Host ""

$RequiredFiles = @(
    (Join-Path $ProjectRoot "main.py"),
    $SpecPath,
    $IconPath,
    $VersionInfoPath,
    (Join-Path $ProjectRoot "models\PPO_2004.pt"),
    (Join-Path $ProjectRoot "assets\audio\button_click.mp3"),
    (Join-Path $ProjectRoot "assets\audio\disc_drop.mp3"),
    (Join-Path $ProjectRoot "assets\audio\win.mp3"),
    (Join-Path $ProjectRoot "assets\images\connect4_title.webp"),
    (Join-Path $ProjectRoot "config\lookahead.json"),
    (Join-Path $ProjectRoot "config\settings.json")
)

foreach ($RequiredFile in $RequiredFiles) {
    if (-not (Test-Path $RequiredFile -PathType Leaf)) {
        throw "Required release file is missing: $RequiredFile"
    }
}

Write-Host "Checking Python..."
& python --version

if ($LASTEXITCODE -ne 0) {
    throw "Python is not available in the active environment."
}

Write-Host "Checking PyInstaller..."
& python -m PyInstaller --version

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not available in the active environment."
}

Write-Host ""
Write-Host "Removing previous build output..."

if (Test-Path $BuildDirectory) {
    Remove-Item $BuildDirectory -Recurse -Force
}

if (Test-Path $DistributionDirectory) {
    Remove-Item $DistributionDirectory -Recurse -Force
}

if (Test-Path $LogPath) {
    Remove-Item $LogPath -Force
}

New-Item `
    -ItemType Directory `
    -Path $DistributionDirectory `
    -Force |
    Out-Null

Write-Host ""
Write-Host "Building windowed release..."
Write-Host "PyTorch makes this a substantial build. The discs deny responsibility."
Write-Host ""

$BuildCommand = (
    'python -m PyInstaller --noconfirm --clean "' +
    $SpecPath +
    '" 2>&1'
)

& cmd.exe /d /s /c $BuildCommand |
    Tee-Object -FilePath $LogPath

$BuildExitCode = $LASTEXITCODE

if ($BuildExitCode -ne 0) {
    throw (
        "PyInstaller failed with exit code $BuildExitCode. " +
        "See: $LogPath"
    )
}

if (-not (Test-Path $ExecutablePath -PathType Leaf)) {
    throw "Executable not found after build: $ExecutablePath"
}

Write-Host ""
Write-Host "Creating portable ZIP..."

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Compress-Archive `
    -Path $ReleaseDirectory `
    -DestinationPath $ZipPath `
    -CompressionLevel Optimal

if (-not (Test-Path $ZipPath -PathType Leaf)) {
    throw "ZIP archive was not created: $ZipPath"
}

$ExeSize = (
    Get-Item $ExecutablePath
).Length

$ZipSize = (
    Get-Item $ZipPath
).Length

$ExeSizeMB = [Math]::Round(
    $ExeSize / 1MB,
    2
)

$ZipSizeMB = [Math]::Round(
    $ZipSize / 1MB,
    2
)

Write-Host ""
Write-Host "============================================"
Write-Host " Final portable release completed"
Write-Host "============================================"
Write-Host ""
Write-Host "Executable:"
Write-Host "  $ExecutablePath"
Write-Host "  EXE size: $ExeSizeMB MB"
Write-Host ""
Write-Host "Distributable ZIP:"
Write-Host "  $ZipPath"
Write-Host "  ZIP size: $ZipSizeMB MB"
Write-Host ""
Write-Host "Build log:"
Write-Host "  $LogPath"
Write-Host ""
Write-Host "Distribute the ZIP, not the EXE by itself."
Write-Host ""
