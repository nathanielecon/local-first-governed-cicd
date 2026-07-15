Set-StrictMode -Version Latest

$script:SmokeLifecyclePaths = @(
    '.harness/runtime/smoke.lock',
    '.harness/runtime/smoke.pid',
    '.harness/runtime/smoke.log',
    '.harness/runtime/smoke-result.json'
)
$script:ResumeStopFlagPath = '.harness/runtime/stop.flag'

function ConvertTo-HarnessRelativePath {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path) -or
        [System.IO.Path]::IsPathRooted($Path) -or
        $Path -match '^[A-Za-z]:' -or
        $Path -match '[*?\[\]]') {
        throw "ExcludedPaths entries must be exact repository-relative paths: '$Path'."
    }

    $normalized = $Path.Replace('\', '/')
    $segments = $normalized.Split('/')
    if (@($segments | Where-Object { $_ -eq '' -or $_ -eq '.' -or $_ -eq '..' }).Count -gt 0) {
        throw "ExcludedPaths entries must not contain empty, '.' or '..' path segments: '$Path'."
    }

    return $normalized
}

function Assert-ValidExcludedPaths {
    [CmdletBinding()]
    param(
        [string[]]$ExcludedPaths = @(),
        [switch]$ResumePreflight
    )

    $normalized = @($ExcludedPaths | ForEach-Object { ConvertTo-HarnessRelativePath -Path $_ } | Select-Object -Unique)
    foreach ($path in $normalized) {
        if ($path -eq $script:ResumeStopFlagPath) {
            if (-not $ResumePreflight) {
                throw "'$path' may only be excluded by the Resume preflight."
            }
            continue
        }
        if ($path -notin $script:SmokeLifecyclePaths) {
            throw "'$path' is not an approved smoke lifecycle exclusion."
        }
    }
    return $normalized
}

function Get-ChangedPaths {
    [CmdletBinding()]
    param(
        [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
        [string[]]$ExcludedPaths = @(),
        [switch]$ResumePreflight
    )

    $excluded = Assert-ValidExcludedPaths -ExcludedPaths $ExcludedPaths -ResumePreflight:$ResumePreflight
    $status = & git -C $RepositoryRoot status --porcelain=v1 --untracked-files=all
    if ($LASTEXITCODE -ne 0) { throw "Unable to read git status for '$RepositoryRoot'." }

    $paths = foreach ($line in $status) {
        if ($line.Length -lt 4) { continue }
        $path = $line.Substring(3)
        if ($path -match ' -> ') { $path = $path.Split(' -> ')[-1] }
        ConvertTo-HarnessRelativePath -Path $path
    }
    return @($paths | Where-Object { $_ -notin $excluded } | Sort-Object -Unique)
}

function Assert-OnlyAllowedChanges {
    [CmdletBinding()]
    param(
        [string[]]$AllowedPaths,
        [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
        [string[]]$ExcludedPaths = @(),
        [switch]$ResumePreflight
    )

    $allowed = @($AllowedPaths | ForEach-Object { ConvertTo-HarnessRelativePath -Path $_ } | Select-Object -Unique)
    $changed = Get-ChangedPaths -RepositoryRoot $RepositoryRoot -ExcludedPaths $ExcludedPaths -ResumePreflight:$ResumePreflight
    $unexpected = @($changed | Where-Object { $_ -notin $allowed })
    if ($unexpected.Count -gt 0) {
        throw "Unexpected changed paths: $($unexpected -join ', ')"
    }
    return $changed
}

function Get-DiffFingerprint {
    [CmdletBinding()]
    param(
        [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
        [string[]]$ExcludedPaths = @(),
        [switch]$ResumePreflight
    )

    $paths = Get-ChangedPaths -RepositoryRoot $RepositoryRoot -ExcludedPaths $ExcludedPaths -ResumePreflight:$ResumePreflight
    $entries = foreach ($path in $paths) {
        $fullPath = Join-Path $RepositoryRoot ($path.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
        $contentHash = if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
            (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
        } else {
            '<deleted>'
        }
        "$path`:$contentHash"
    }
    $payload = [Text.Encoding]::UTF8.GetBytes(($entries -join "`n"))
    return ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($payload))).ToLowerInvariant()
}

Export-ModuleMember -Function Get-ChangedPaths, Assert-OnlyAllowedChanges, Get-DiffFingerprint
