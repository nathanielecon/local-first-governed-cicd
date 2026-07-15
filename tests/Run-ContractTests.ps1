[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'scripts/Harness.Common.psm1') -Force

function Assert-Throws {
    param([scriptblock]$Action, [string]$Message)
    try { & $Action } catch { return }
    throw $Message
}

Assert-Throws { Get-ChangedPaths -ExcludedPaths @('.harness/runtime/*') } 'Glob exclusion was accepted.'
Assert-Throws { Get-ChangedPaths -ExcludedPaths @('C:/temp/file') } 'Absolute exclusion was accepted.'
Assert-Throws { Get-ChangedPaths -ExcludedPaths @('.harness/../runtime/smoke.log') } 'Parent traversal exclusion was accepted.'
Assert-Throws { Get-ChangedPaths -ExcludedPaths @('.harness/runtime') } 'Runtime directory exclusion was accepted.'
Assert-Throws { Get-ChangedPaths -ExcludedPaths @('.harness/runtime/stop.flag') } 'stop.flag was hidden outside Resume preflight.'

$null = Get-ChangedPaths -ExcludedPaths @('.harness/runtime/smoke.log')
$null = Get-ChangedPaths -ExcludedPaths @('.harness/runtime/stop.flag') -ResumePreflight
$fingerprint = Get-DiffFingerprint
if ($fingerprint -notmatch '^[a-f0-9]{64}$') { throw 'Diff fingerprint is not a SHA-256 hex digest.' }
Write-Output 'Harness contract tests passed.'
