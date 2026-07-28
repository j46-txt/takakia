Write-Host "=== Takakia CLI Installer for Windows ===" -ForegroundColor Cyan

# 1. Verify Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Error: Python execution binary could not be discovered in your PATH context."
    exit 1
}

$pyVersionString = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyVersionString -lt [version]"3.9") {
    Write-Error "❌ Error: Takakia requires Python 3.9 or higher. Found version $pyVersionString"
    exit 1
}

# 2. Configure target execution paths
$installDir = Join-Path $env:LOCALAPPDATA "takakia"
$binDir = Join-Path $installDir "bin"
$venvDir = Join-Path $installDir "venv"

Write-Host "Creating target execution directory at $installDir..." -ForegroundColor Yellow
if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Path $installDir | Out-Null }
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir | Out-Null }

# 3. Provision Virtual Environment
& python -m venv $venvDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to construct internal Python Virtual Environment."
    exit 1
}

# 4. Install Dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
$pipPath = Join-Path $venvDir "Scripts\pip.exe"
& $pipPath install --upgrade pip --quiet
& $pipPath install . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pip internal execution phase encountered a failure."
    exit 1
}

# 5. Create Batch & Cmd Wrapper Scripts
Write-Host "Generating execution script wrappers..." -ForegroundColor Yellow
$cmdContent = "@echo off`r`n`"$venvDir\Scripts\takakia.exe`" %*"
Set-Content -Path (Join-Path $binDir "takakia.cmd") -Value $cmdContent
Set-Content -Path (Join-Path $binDir "takakia.bat") -Value $cmdContent

# 6. Safely bind binary pathway to User PATH environment & broadcast changes
$cleanBinDir = $binDir.TrimEnd('\')
$currentUserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ([string]::IsNullOrEmpty($currentUserPath)) { $currentUserPath = "" }

$expandedUserPath = [System.Environment]::ExpandEnvironmentVariables($currentUserPath)
$pathElements = $currentUserPath -split ';' | Where-Object { $_.Trim() -ne "" }
$expandedElements = $expandedUserPath -split ';' | Where-Object { $_.Trim() -ne "" }

if ($expandedElements -notcontains $cleanBinDir) {
    Write-Host "Injecting local binary path to User PATH environment..." -ForegroundColor Yellow
    $newPathString = (($pathElements + $cleanBinDir) -join ';')
    [System.Environment]::SetEnvironmentVariable("Path", $newPathString, "User")
} else {
    # Force broadcast to fix stale environment states across Windows
    [System.Environment]::SetEnvironmentVariable("Path", $currentUserPath, "User")
}

# Sync active session PATH immediately
if (($env:Path -split ';') -notcontains $cleanBinDir) {
    $env:Path = "$env:Path;$cleanBinDir"
}

Write-Host "✅ Installation completed successfully! Run the application using: takakia" -ForegroundColor Green
