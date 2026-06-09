@echo off
title AWIP Launcher
pushd %~dp0

echo ===================================================
echo   Starting AWIP AI Data Science Workspace...
echo ===================================================

echo.
echo [1/2] Starting FastAPI Backend on Port 8000...
start "AWIP Backend" cmd /k "cd /d %~dp0backend && uv pip install -r requirements.txt && uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo [2/2] Waiting for backend to be ready...
set /a attempts=0
:wait_backend
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel%==0 goto backend_ready
set /a attempts+=1
if %attempts% lss 15 goto wait_backend
echo.
echo WARNING: Backend did not respond after 30 seconds.
echo Check the "AWIP Backend" terminal window for errors.
goto start_frontend

:backend_ready
echo Backend is ready.

:start_frontend
echo Starting Next.js Frontend on Port 3000...
start "AWIP Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===================================================
echo   AWIP is launching!
echo   Open: http://localhost:3000
echo   (Keep the AWIP Backend and AWIP Frontend windows open)
echo ===================================================
timeout /t 4
start http://localhost:3000
popd
