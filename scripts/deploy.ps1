[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('staging','production')][string]$Environment,
  [Parameter(Mandatory)][string]$Image,
  [string]$ExpectedSha = '',
  [string]$ExpectedDigest = '',
  [string]$ExpectedRegistry = '',
  [string]$ExpectedRepository = '',
  [string]$VerifiedRollbackDigest = '',
  [string]$VerifiedRollbackCommit = '',
  [string]$VerifiedRollbackVerifiedAt = '',
  [string]$VerifiedRollbackSourceRelease = '',
  [string]$VerifiedRollbackEnvironment = 'production',
  [string]$FirstReleaseDecision = '',
  [string]$FirstReleaseDecidedBy = '',
  [string]$FirstReleaseDecidedAt = '',
  [string]$FirstReleaseRationale = '',
  [string]$FirstReleaseAcceptedRisk = ''
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

function Get-ImageIdentity {
  param([Parameter(Mandatory)][string]$ImageRef)
  $digest = ''
  $name = $ImageRef
  if ($ImageRef -match '^(?<name>.+)@(?<digest>sha256:[0-9a-f]{64})$') {
    $name = $Matches['name']
    $digest = $Matches['digest']
  } elseif ($ImageRef -match '^(?<name>.+):(?<tag>[^:/]+)$') {
    $name = $Matches['name']
  }
  $registry = ''
  $repository = $name
  if ($name.Contains('/')) {
    $parts = $name.Split('/', 2)
    $registry = $parts[0]
    $repository = $parts[1]
  }
  [pscustomobject]@{
    Registry = $registry
    Repository = $repository
    Digest = $digest
  }
}

$python = Resolve-Python
$identity = Get-ImageIdentity -ImageRef $Image
if (-not $ExpectedDigest) { $ExpectedDigest = $identity.Digest }
if (-not $ExpectedRegistry) { $ExpectedRegistry = $identity.Registry }
if (-not $ExpectedRepository) { $ExpectedRepository = $identity.Repository }

if ($Environment -eq 'production') {
  if (-not $ExpectedDigest) {
    throw 'production deploy requires an immutable ExpectedDigest (or Image pinned as registry/repo@sha256:...)'
  }
  $gateArgs = @(
    'scripts/verify_deployment.py', 'promotion-gate',
    '--candidate-digest', $ExpectedDigest,
    '--verified-rollback-digest', $VerifiedRollbackDigest,
    '--verified-rollback-commit', $VerifiedRollbackCommit,
    '--verified-rollback-verified-at', $VerifiedRollbackVerifiedAt,
    '--verified-rollback-source-release', $VerifiedRollbackSourceRelease,
    '--verified-rollback-environment', $VerifiedRollbackEnvironment,
    '--first-release-decision', $FirstReleaseDecision,
    '--first-release-decided-by', $FirstReleaseDecidedBy,
    '--first-release-decided-at', $FirstReleaseDecidedAt,
    '--first-release-rationale', $FirstReleaseRationale,
    '--first-release-accepted-risk', $FirstReleaseAcceptedRisk
  )
  & $python @gateArgs
  if ($LASTEXITCODE -ne 0) {
    throw 'production promotion blocked by rollback-target / first-release gate'
  }
}

$stateDir = Join-Path $root 'deploy/state'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$stateFile = Join-Path $stateDir "$Environment.env"
$previousFile = Join-Path $stateDir "$Environment.previous.env"
if (Test-Path -LiteralPath $stateFile) { Copy-Item -LiteralPath $stateFile -Destination $previousFile -Force }
$variable = if ($Environment -eq 'staging') { 'STAGING_IMAGE' } else { 'PRODUCTION_IMAGE' }
"$variable=$Image" | Set-Content -LiteralPath $stateFile
docker compose --profile deploy --env-file $stateFile up -d $Environment

$port = if ($Environment -eq 'staging') { 8081 } else { 8082 }
$verifyArgs = @(
  'scripts/verify_deployment.py', 'verify',
  '--base-url', "http://localhost:$port",
  '--compose-service', $Environment,
  '--mode', 'verify'
)
if ($ExpectedDigest -and $ExpectedRegistry -and $ExpectedRepository) {
  $verifyArgs += @(
    '--expected-digest', $ExpectedDigest,
    '--expected-registry', $ExpectedRegistry,
    '--expected-repository', $ExpectedRepository
  )
  if ($ExpectedSha) { $verifyArgs += @('--expected-sha', $ExpectedSha) }
  $verifyArgs += @('--expected-environment', $Environment)
  try { & $python @verifyArgs }
  catch {
    if (Test-Path -LiteralPath $previousFile) {
      Copy-Item -LiteralPath $previousFile -Destination $stateFile -Force
      docker compose --profile deploy --env-file $stateFile up -d $Environment
    }
    throw
  }
  if ($LASTEXITCODE -ne 0) {
    if (Test-Path -LiteralPath $previousFile) {
      Copy-Item -LiteralPath $previousFile -Destination $stateFile -Force
      docker compose --profile deploy --env-file $stateFile up -d $Environment
    }
    throw 'deployment verification failed'
  }
} else {
  # Staging may still use tag aliases locally, but digest-bound proof is preferred.
  $smokeArgs = @('scripts/smoke_test.py', '--base-url', "http://localhost:$port", '--expected-environment', $Environment)
  if ($ExpectedSha) { $smokeArgs += @('--expected-sha', $ExpectedSha) }
  try { & $python @smokeArgs }
  catch {
    if (Test-Path -LiteralPath $previousFile) {
      Copy-Item -LiteralPath $previousFile -Destination $stateFile -Force
      docker compose --profile deploy --env-file $stateFile up -d $Environment
    }
    throw
  }
  if ($LASTEXITCODE -ne 0) {
    if (Test-Path -LiteralPath $previousFile) {
      Copy-Item -LiteralPath $previousFile -Destination $stateFile -Force
      docker compose --profile deploy --env-file $stateFile up -d $Environment
    }
    throw 'smoke verification failed'
  }
}
