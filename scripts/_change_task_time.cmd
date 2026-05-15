@echo off
chcp 65001 > nul
schtasks /change /tn "MacroRatesDashboard" /st 08:10
exit /b %ERRORLEVEL%
