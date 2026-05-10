# 회사 Windows PC의 Claude Code 전역 지침 파일을 설치하는 스크립트
param(
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$source = Join-Path $repoRoot "agent-config\CLAUDE.md"
$targetDir = Join-Path $env:USERPROFILE ".claude"
$target = Join-Path $targetDir "CLAUDE.md"

if (!(Test-Path $source)) {
    throw "Source CLAUDE.md not found: $source"
}

if (!(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir | Out-Null
}

if ((Test-Path $target) -and !$NoBackup) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backup = Join-Path $targetDir "CLAUDE.md.backup-$timestamp"
    Copy-Item -Path $target -Destination $backup -Force
    Write-Host "Backup created: $backup"
}

Copy-Item -Path $source -Destination $target -Force
Write-Host "Installed: $target"
