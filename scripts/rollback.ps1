[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('staging','production')][string]$Environment)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$stateFile = Join-Path $root "deploy/state/$Environment.env"
$previousFile = Join-Path $root "deploy/state/$Environment.previous.env"
if (-not (Test-Path -LiteralPath $previousFile)) { throw "No rollback target recorded for $Environment" }
Copy-Item -LiteralPath $previousFile -Destination $stateFile -Force
docker compose --profile deploy --env-file $stateFile up -d $Environment
