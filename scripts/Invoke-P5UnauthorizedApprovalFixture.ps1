Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EvidenceDir = Join-Path $RepoRoot "evidence\phase-5"
$PipelineFile = Join-Path $RepoRoot "infra\jenkins\test-fixtures\p5-t04-unauthorized-approval.groovy"
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$HarnessScript = Join-Path $RepoRoot "scripts\p5_t04_unauthorized_fixture.py"

$env:COMPOSE_PROJECT_NAME = "project-c-p5-t04"
$env:JENKINS_LOCAL_ADMIN_ID = "local-admin"
$env:JENKINS_LOCAL_ADMIN_PASSWORD = "placeholder-admin-password"
$env:JENKINS_LOCAL_APPROVER_ID = "local-approver"
$env:JENKINS_LOCAL_APPROVER_PASSWORD = "placeholder-approver-password"
$env:JENKINS_LOCAL_VIEWER_ID = "local-viewer"
$env:JENKINS_LOCAL_VIEWER_PASSWORD = "placeholder-viewer-password"

$AttemptId = [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$EvidencePrefix = "p5-t04-$AttemptId"
$composeDownBeforeEvidence = Join-Path $EvidenceDir "$EvidencePrefix-compose-down-before.txt"
$composeBuildEvidence = Join-Path $EvidenceDir "$EvidencePrefix-compose-build.txt"
$composeUpEvidence = Join-Path $EvidenceDir "$EvidencePrefix-compose-up.txt"
$runtimeIdentityEvidence = Join-Path $EvidenceDir "$EvidencePrefix-runtime-identity.txt"
$composeLogsEvidence = Join-Path $EvidenceDir "$EvidencePrefix-compose-logs.txt"
$composeDownAfterEvidence = Join-Path $EvidenceDir "$EvidencePrefix-compose-down-after.txt"
$manifestEvidence = Join-Path $EvidenceDir "$EvidencePrefix-manifest.txt"
$proofEvidence = Join-Path $EvidenceDir "$EvidencePrefix-unauthorized-proof.txt"

New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null

function New-EvidenceSection {
    param(
        [Parameter(Mandatory)]
        [string]$Title,
        [AllowEmptyCollection()]
        [object[]]$Lines
    )

    $section = @("=== $Title ===")
    $renderedLines = @($Lines | ForEach-Object { "$_" })
    if ($renderedLines.Count -gt 0) {
        $section += $renderedLines
    } else {
        $section += "<no output>"
    }

    $section += ""
    return $section
}

function Write-EvidenceFile {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [object[]]$Lines
    )

    [System.IO.File]::WriteAllLines($Path, [string[]]@($Lines | ForEach-Object { "$_" }))
}

function Get-JenkinsContainerId {
    $containerOutput = & docker compose ps -a -q jenkins 2>&1
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    $containerId = @($containerOutput | ForEach-Object { "$_" } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
    if ($containerId.Count -eq 0) {
        return $null
    }

    return $containerId[0].Trim()
}

function Get-ContainerPathContent {
    param(
        [Parameter(Mandatory)]
        [string]$ContainerId,
        [Parameter(Mandatory)]
        [string]$ContainerPath
    )

    $tempDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("p5-t04-" + [Guid]::NewGuid().ToString("N"))
    $tempPath = Join-Path $tempDirectory "captured.txt"
    New-Item -ItemType Directory -Path $tempDirectory -Force | Out-Null

    try {
        $copySource = "{0}:{1}" -f $ContainerId, $ContainerPath
        $output = & docker cp $copySource $tempPath *>&1
        if ($LASTEXITCODE -ne 0) {
            return @($output | ForEach-Object { "$_" })
        }

        if (-not (Test-Path -LiteralPath $tempPath)) {
            return @("<copied file missing>")
        }

        return [System.IO.File]::ReadAllLines($tempPath)
    }
    finally {
        Remove-Item -LiteralPath $tempDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Get-WorkspacePathContent {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return @("<missing>")
    }

    return [System.IO.File]::ReadAllLines($Path)
}

function Get-ContentSha256 {
    param([AllowEmptyCollection()][string[]]$Lines)

    $normalized = [string]::Join("`n", @($Lines | ForEach-Object { "$_" }))
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($normalized)
    $hashBytes = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return [System.Convert]::ToHexString($hashBytes).ToLowerInvariant()
}

function Write-CommandEvidence {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Title,
        [AllowEmptyCollection()][object[]]$Lines
    )

    $evidenceLines = @(
        "attempt_id=$AttemptId"
        "evidence_prefix=$EvidencePrefix"
        "captured_at=$([DateTimeOffset]::UtcNow.ToString('o'))"
        "compose_project_name=$env:COMPOSE_PROJECT_NAME"
        ""
    )
    $evidenceLines += New-EvidenceSection -Title $Title -Lines $Lines
    Write-EvidenceFile -Path $Path -Lines $evidenceLines
}

function Write-ManifestEvidence {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$FixtureStatus,
        [string]$FailureMessage = ""
    )

    $lines = @(
        "attempt_id=$AttemptId"
        "evidence_prefix=$EvidencePrefix"
        "compose_project_name=$env:COMPOSE_PROJECT_NAME"
        "fixture_status=$FixtureStatus"
        "failure_message=$FailureMessage"
        "compose_down_before=$([System.IO.Path]::GetFileName($composeDownBeforeEvidence))"
        "compose_build=$([System.IO.Path]::GetFileName($composeBuildEvidence))"
        "compose_up=$([System.IO.Path]::GetFileName($composeUpEvidence))"
        "runtime_identity=$([System.IO.Path]::GetFileName($runtimeIdentityEvidence))"
        "unauthorized_proof=$([System.IO.Path]::GetFileName($proofEvidence))"
        "compose_logs=$([System.IO.Path]::GetFileName($composeLogsEvidence))"
        "compose_down_after=$([System.IO.Path]::GetFileName($composeDownAfterEvidence))"
    )

    Write-EvidenceFile -Path $Path -Lines $lines
}

function Write-RuntimeIdentityEvidence {
    param([Parameter(Mandatory)][string]$Path)

    $containerId = Get-JenkinsContainerId
    $workspaceCascPath = Join-Path $RepoRoot "infra\jenkins\casc.yaml"
    $workspaceCasc = Get-WorkspacePathContent -Path $workspaceCascPath
    $lines = @(
        "attempt_id=$AttemptId"
        "evidence_prefix=$EvidencePrefix"
        "captured_at=$([DateTimeOffset]::UtcNow.ToString('o'))"
        "compose_project_name=$env:COMPOSE_PROJECT_NAME"
        ""
    )

    $lines += New-EvidenceSection -Title "docker compose ps -a jenkins" -Lines (& docker compose ps -a jenkins *>&1)
    $lines += New-EvidenceSection -Title "docker compose images jenkins" -Lines (& docker compose images jenkins *>&1)
    $lines += New-EvidenceSection -Title "jenkins container id" -Lines @($(if ($containerId) { $containerId } else { "<container unavailable>" }))
    $lines += New-EvidenceSection -Title "workspace infra/jenkins/casc.yaml" -Lines $workspaceCasc
    $lines += New-EvidenceSection -Title "workspace infra/jenkins/casc.yaml sha256" -Lines @(Get-ContentSha256 -Lines $workspaceCasc)

    if ($containerId) {
        $refCasc = Get-ContainerPathContent -ContainerId $containerId -ContainerPath "/usr/share/jenkins/ref/casc.yaml"
        $homeCasc = Get-ContainerPathContent -ContainerId $containerId -ContainerPath "/var/jenkins_home/casc.yaml"
        $lines += New-EvidenceSection -Title "jenkins image reference" -Lines (& docker inspect --format '{{.Config.Image}}' $containerId *>&1)
        $lines += New-EvidenceSection -Title "jenkins image id" -Lines (& docker inspect --format '{{.Image}}' $containerId *>&1)
        $lines += New-EvidenceSection -Title "/usr/share/jenkins/ref/casc.yaml" -Lines $refCasc
        $lines += New-EvidenceSection -Title "/usr/share/jenkins/ref/casc.yaml sha256" -Lines @(Get-ContentSha256 -Lines $refCasc)
        $lines += New-EvidenceSection -Title "/var/jenkins_home/casc.yaml" -Lines $homeCasc
        $lines += New-EvidenceSection -Title "/var/jenkins_home/casc.yaml sha256" -Lines @(Get-ContentSha256 -Lines $homeCasc)
    } else {
        $lines += New-EvidenceSection -Title "jenkins image reference" -Lines @("<container unavailable>")
        $lines += New-EvidenceSection -Title "jenkins image id" -Lines @("<container unavailable>")
        $lines += New-EvidenceSection -Title "/usr/share/jenkins/ref/casc.yaml" -Lines @("<container unavailable>")
        $lines += New-EvidenceSection -Title "/usr/share/jenkins/ref/casc.yaml sha256" -Lines @("<container unavailable>")
        $lines += New-EvidenceSection -Title "/var/jenkins_home/casc.yaml" -Lines @("<container unavailable>")
        $lines += New-EvidenceSection -Title "/var/jenkins_home/casc.yaml sha256" -Lines @("<container unavailable>")
    }

    Write-EvidenceFile -Path $Path -Lines $lines
}

$fixtureStatus = "failed"
$failureMessage = ""

try {
    Write-CommandEvidence -Path $composeDownBeforeEvidence -Title "docker compose down --volumes --remove-orphans" -Lines (& docker compose down --volumes --remove-orphans *>&1)
    Write-CommandEvidence -Path $composeBuildEvidence -Title "docker compose build --pull --no-cache jenkins" -Lines (& docker compose build --pull --no-cache jenkins *>&1)
    Write-CommandEvidence -Path $composeUpEvidence -Title "docker compose up -d --force-recreate jenkins" -Lines (& docker compose up -d --force-recreate jenkins *>&1)
    Write-RuntimeIdentityEvidence -Path $runtimeIdentityEvidence

    & $PythonExe $HarnessScript `
        --pipeline-file $PipelineFile `
        --evidence-dir $EvidenceDir `
        --evidence-prefix $EvidencePrefix `
        --admin-user $env:JENKINS_LOCAL_ADMIN_ID `
        --admin-password $env:JENKINS_LOCAL_ADMIN_PASSWORD `
        --allowed-approver-id $env:JENKINS_LOCAL_APPROVER_ID `
        --viewer-user $env:JENKINS_LOCAL_VIEWER_ID `
        --viewer-password $env:JENKINS_LOCAL_VIEWER_PASSWORD

    if ($LASTEXITCODE -ne 0) {
        throw "P5-T04 fixture runner exited with code $LASTEXITCODE."
    }

    $fixtureStatus = "passed"
}
catch {
    $failureMessage = "$_"
    throw
}
finally {
    Write-CommandEvidence -Path $composeLogsEvidence -Title "docker compose logs --tail 200 jenkins" -Lines (& docker compose logs --tail 200 jenkins *>&1)
    Write-CommandEvidence -Path $composeDownAfterEvidence -Title "docker compose down --volumes --remove-orphans" -Lines (& docker compose down --volumes --remove-orphans *>&1)
    Write-ManifestEvidence -Path $manifestEvidence -FixtureStatus $fixtureStatus -FailureMessage $failureMessage
}
