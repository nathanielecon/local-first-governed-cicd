[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('staging','production')][string]$Environment,
  [Parameter(Mandatory)][string]$Image,
  [string]$ExpectedSha = ''
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$stateDir = Join-Path $root 'deploy/state'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$stateFile = Join-Path $stateDir "$Environment.env"
$previousFile = Join-Path $stateDir "$Environment.previous.env"
if (Test-Path -LiteralPath $stateFile) { Copy-Item -LiteralPath $stateFile -Destination $previousFile -Force }
$variable = if ($Environment -eq 'staging') { 'STAGING_IMAGE' } else { 'PRODUCTION_IMAGE' }
"$variable=$Image" | Set-Content -LiteralPath $stateFile
docker compose --profile deploy --env-file $stateFile up -d $Environment
$port = if ($Environment -eq 'staging') { 8081 } else { 8082 }
$args = @('scripts/smoke_test.py', '--base-url', "http://localhost:$port")
if ($ExpectedSha) { $args += @('--expected-sha', $ExpectedSha) }
try { python @args }
catch {
  if (Test-Path -LiteralPath $previousFile) {
    Copy-Item -LiteralPath $previousFile -Destination $stateFile -Force
    docker compose --profile deploy --env-file $stateFile up -d $Environment
  }
  throw
}
