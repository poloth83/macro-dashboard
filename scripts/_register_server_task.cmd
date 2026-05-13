@echo off
chcp 65001 > nul
schtasks /create /tn "MacroRatesDashboardServer" /tr "wscript.exe \"C:\Users\Hana_FI\claude code_ai\macro-dashboard\scripts\_start_server.vbs\"" /sc ONLOGON /f
exit /b %ERRORLEVEL%
