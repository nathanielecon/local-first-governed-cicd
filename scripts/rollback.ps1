[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('staging','production')][string]$Environment,
  [Parameter(Mandatory)][string]$VerifiedRollbackDigest,
  [Parameter(Mandatory)][string]$ExpectedRegistry,
  [Parameter(Mandatory)][string]$ExpectedRepository,
  [string]$ExpectedSha = '',
  [string]$ImageReference = ''
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Resolve-Python {
  if (Test-Path -LiteralPath (Join-Path $root '.venv\Scripts\python.exe')) {
    return (Join-Path $root '.venv\Scripts\python.exe')
  }
  return 'python'
}

if (-not $VerifiedRollbackDigest) {
  throw 'VerifiedRollbackDigest is required; deploy/state previous.env is not a verified rollback target'
}
if ($Environment -eq 'production' -and -not $VerifiedRollbackDigest) {
  throw 'production rollback requires an event-backed verified digest'
}

$python = Resolve-Python
$digest = $VerifiedRollbackDigest.Trim()
if ($digest -notmatch '^sha256:[0-9a-f]{64}$') {
  if ($digest -match '^[0-9a-f]{64}$') { $digest = "sha256:$digest" }
  else { throw "invalid VerifiedRollbackDigest: $VerifiedRollbackDigest" }
}

if (-not $ImageReference) {
  $ImageReference = "$ExpectedRegistry/$ExpectedRepository@$digest"
  if (-not $ExpectedRegistry) {
    $ImageReference = "$ExpectedRepository@$digest"
  }
}

$stateDir = Join-Path $root 'deploy/state'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$stateFile = Join-Path $stateDir "$Environment.env"
$previousFile = Join-Path $stateDir "$Environment.previous.env"
# previous.env remains a non-authoritative operational cache only.
if (Test-Path -LiteralPath $stateFile) {
  Copy-Item -LiteralPath $stateFile -Destination $previousFile -Force
}

$variable = if ($Environment -eq 'staging') { 'STAGING_IMAGE' } else { 'PRODUCTION_IMAGE' }
"$variable=$ImageReference" | Set-Content -LiteralPath $stateFile
docker compose --profile deploy --env-file $stateFile up -d $Environment

$port = if ($Environment -eq 'staging') { 8081 } else { 8082 }
$verifyArgs = @(
  'scripts/verify_deployment.py', 'verify',
  '--base-url', "http://localhost:$port",
  '--compose-service', $Environment,
  '--expected-digest', $digest,
  '--expected-registry', $ExpectedRegistry,
  '--expected-repository', $ExpectedRepository,
  '--expected-environment', $Environment,
  '--mode', 'recovery'
)
if ($ExpectedSha) { $verifyArgs += @('--expected-sha', $ExpectedSha) }
& $python @verifyArgs
if ($LASTEXITCODE -ne 0) {
  throw 'recovery verification failed: digest, health, version, or business behavior check did not pass'
}
