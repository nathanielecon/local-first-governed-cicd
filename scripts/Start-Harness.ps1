[CmdletBinding()]
param(
    [ValidateSet('Smoke', 'Resume')][string]$Mode = 'Smoke',
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'Harness.Common.psm1') -Force

$lifecycleExclusions = @(
    '.harness/runtime/smoke.lock',
    '.harness/runtime/smoke.pid',
    '.harness/runtime/smoke.log',
    '.harness/runtime/smoke-result.json'
)
if ($Mode -eq 'Resume') {
    # The stop signal is only ignored while checking whether a smoke run may resume.
    $null = Get-ChangedPaths -RepositoryRoot $RepositoryRoot -ExcludedPaths @('.harness/runtime/stop.flag') -ResumePreflight
}

$changed = Assert-OnlyAllowedChanges -RepositoryRoot $RepositoryRoot -AllowedPaths $lifecycleExclusions -ExcludedPaths $lifecycleExclusions
[pscustomobject]@{ Mode = $Mode; DiffFingerprint = Get-DiffFingerprint -RepositoryRoot $RepositoryRoot -ExcludedPaths $lifecycleExclusions; ChangedPaths = $changed } | ConvertTo-Json -Compress
