$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$log = Join-Path $PSScriptRoot "install-wsl-elevated.log"

Start-Transcript -LiteralPath $log -Append
try {
    Write-Host "=== $(Get-Date -Format o) Elevated WSL repair start ==="
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    & "C:\Windows\System32\wsl.exe" --install
    Write-Host "=== $(Get-Date -Format o) Elevated WSL repair end ==="
}
finally {
    Stop-Transcript
}
