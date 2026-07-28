Write-Host "=== Uninstalling Takakia CLI ===" -ForegroundColor Yellow

$installDir = Join-Path $env:LOCALAPPDATA "takakia"
$binDir = Join-Path $installDir "bin"
$configDir = Join-Path $env:APPDATA "takakia"

# 1. Clean up User PATH Environment Variable via .NET API
$currentUserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

if (-not [string]::IsNullOrEmpty($currentUserPath)) {
    $cleanBinDir = $binDir.TrimEnd('\')
    $pathElements = $currentUserPath -split ';' | Where-Object { 
        $_.Trim() -ne "" -and $_.TrimEnd('\') -ne $cleanBinDir -and $_.TrimEnd('\') -ne "$cleanBinDir\"
    }
    $newPathString = ($pathElements -join ';')
    
    [System.Environment]::SetEnvironmentVariable("Path", $newPathString, "User")
    Write-Host "✓ Removed Takakia from User PATH environment variable." -ForegroundColor Green
}

# 2. Delete installation directory (venv + wrappers)
if (Test-Path $installDir) {
    Remove-Item -Path $installDir -Recurse -Force
    Write-Host "✓ Removed installation directory at $installDir" -ForegroundColor Green
}

# 3. Optional cleanup of user configs/keys
if (Test-Path $configDir) {
    $response = Read-Host "Do you also want to delete configuration files and saved profiles ($configDir)? [y/N]"
    if ($response -match "^[Yy]$") {
        Remove-Item -Path $configDir -Recurse -Force
        Write-Host "✓ Removed user configuration directory." -ForegroundColor Green
    } else {
        Write-Host "i Preserved configuration files at $configDir" -ForegroundColor Yellow
    }
}

Write-Host "✅ Takakia has been successfully uninstalled." -ForegroundColor Green
