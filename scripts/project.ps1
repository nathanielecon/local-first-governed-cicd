[CmdletBinding(PositionalBinding=$false)]
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$python = if (Test-Path -LiteralPath '.venv/Scripts/python.exe') { './.venv/Scripts/python.exe' } else { 'python' }
& $python scripts/project_cli.py @Arguments
exit $LASTEXITCODE
