Write-Host "=== Takakia CLI Installer for Windows ===" -ForegroundColor Cyan

# 1. Verify Python availability
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Error: Python execution binary could not be discovered in your PATH context."
    exit 1
}

$pyVersionString = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
[version]$pyVersion = $pyVersionString
if ($pyVersion -lt [version]"3.9") {
    Write-Error "❌ Error: Takakia requires Python 3.9 or higher. Found version $pyVersionString"
    exit 1
}

# 2. Configure target execution paths
$installDir = Join-Path $env:LOCALAPPDATA "takakia"
$binDir = Join-Path $installDir "bin"
$venvDir = Join-Path $installDir "venv"

Write-Host "Creating background isolated target at $installDir..." -ForegroundColor Yellow
if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Path $installDir | Out-Null }
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir | Out-Null }

# 3. Provision Virtual Environment
& python -m venv $venvDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to construct internal Python Virtual Environment."
    exit 1
}

# 4. Process safe setup installations
Write-Host "Installing dependencies and packages natively..." -ForegroundColor Yellow
$pipPath = Join-Path $venvDir "Scripts\pip.exe"
& $pipPath install --upgrade pip --quiet
& $pipPath install . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pip internal execution phase encountered a critical failure sequence."
    exit 1
}

# 5. Create Batch Proxy Wrapper
Write-Host "Generating seamless execution script wrapper..." -ForegroundColor Yellow
$batPath = Join-Path $binDir "takakia.bat"
$batContent = @"
@echo off
"$venvDir\Scripts\takakia.exe" %*
"@
Set-Content -Path $batPath -Value $batContent

# 6. Safely bind binary pathway to target registry environment variables
$userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($userPath -notlike "*$binDir*") {
    Write-Host "Injecting local binary routing node to User PATH environment..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", [EnvironmentVariableTarget]::User)
    $env:Path += ";$binDir"
    Write-Host "✅ Installation completed successfully! Please restart your terminal application window to initialize path sync." -ForegroundColor Green
} else {
    Write-Host "✅ Installation completed successfully! Run the application globally using: takakia" -ForegroundColor Green
}
