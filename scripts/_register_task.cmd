@echo off
schtasks /create /tn "MacroRatesDashboard" /tr "\"C:\Users\Hana_FI\claude code_ai\macro-dashboard\scripts\run_daily.bat\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 06:40 /f
exit /b %ERRORLEVEL%
