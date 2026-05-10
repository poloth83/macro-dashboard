@echo off
REM 회사 PC(Windows)에서 매일 06:30 KST에 작업 스케줄러로 실행
REM 1) blpapi로 데이터 fetch  2) HTML 빌드  3) 로그 기록

setlocal
chcp 65001 > nul
set ROOT=%~dp0..
cd /d "%ROOT%"

REM 가상환경 활성화 (없으면 system Python 사용)
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM 로그 디렉터리
if not exist logs mkdir logs
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set LOGDATE=%%I
set LOGFILE=logs\%LOGDATE%.log

echo === %date% %time% === >> "%LOGFILE%"

python fetch_bloomberg.py --mode production >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo FETCH FAILED >> "%LOGFILE%"
    exit /b 1
)

python build_dashboard.py >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo BUILD FAILED >> "%LOGFILE%"
    exit /b 1
)

echo OK >> "%LOGFILE%"
endlocal
