[CmdletBinding()]
param(
    [ValidateSet('Smoke', 'Resume')][string]$Mode = 'Smoke',
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Start-Harness.ps1') -Mode $Mode -RepositoryRoot $RepositoryRoot
exit $LASTEXITCODE
