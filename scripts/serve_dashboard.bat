@echo off
REM macro-rates dashboard 정적 HTML을 8001 포트로 사내망에 서빙하는 launcher.
REM macro_trade_ai 프로젝트의 serve_reports(8000)와 포트 분리.
REM
REM 사용:
REM   - PC 부팅 후 한 번 더블클릭하면 백그라운드에서 운영. 콘솔 창 유지 시 Ctrl+C로 종료.
REM   - URL: http://<사내 IP>:8001/  (예: http://10.155.41.52:8001/)
REM   - history: http://<사내 IP>:8001/history/
REM
REM 주의:
REM   - 같은 포트로 이미 떠 있으면 두 번째 실행은 즉시 실패함. 그땐 기존 콘솔만 유지.
REM   - run_daily.bat은 fetch+build만 수행하므로 서버 운영과는 무관. output/ 폴더가 갱신되면 자동 반영.

setlocal
chcp 65001 > nul
cd /d "%~dp0.."

echo [serve_dashboard.bat] cwd = %CD%
echo [serve_dashboard.bat] 8001 서빙 시작. Ctrl+C로 종료.
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m http.server 8001 --directory output --bind 0.0.0.0
) else (
    python -m http.server 8001 --directory output --bind 0.0.0.0
)
set RC=%ERRORLEVEL%

echo [serve_dashboard.bat] exit code = %RC%

if "%~1"=="" pause
endlocal
exit /b %RC%
