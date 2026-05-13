# Windows 작업 스케줄러에 macro-dashboard HTTP 서버를 onlogon 트리거 + pythonw.exe(콘솔 없음)로 등록
# 재등록 필요해지면 PowerShell에서: .\scripts\_register_server_task.ps1
# 작업 이름: MacroRatesDashboardServer

$pythonw  = "C:\Users\Hana_FI\claude code_ai\macro-dashboard\.venv\Scripts\pythonw.exe"
$workDir  = "C:\Users\Hana_FI\claude code_ai\macro-dashboard"
$argument = "-m http.server 8001 --directory output --bind 0.0.0.0"

$action   = New-ScheduledTaskAction -Execute $pythonw -Argument $argument -WorkingDirectory $workDir
$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName "MacroRatesDashboardServer" `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -Force | Out-Null

Write-Host "Registered: MacroRatesDashboardServer (onlogon, pythonw -m http.server 8001)"
