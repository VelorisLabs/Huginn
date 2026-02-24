@echo off
title Paper Auto Summarize

:: Switch to script directory (supports double-click)
cd /d "%~dp0"

echo ========================================
echo   Paper Auto Summarize - Starting...
echo ========================================
echo.

:: Check project root
if not exist "run.py" (
    echo [ERROR] run.py not found. Please run from project root.
    pause
    exit /b 1
)

:: Check uv
where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv not found. Install: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

:: Check npm
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm not found. Install Node.js: https://nodejs.org/
    pause
    exit /b 1
)

:: Check .env
if not exist ".env" (
    echo [WARN] .env not found, creating from template...
    if exist "deploy\.env.example" (
        copy "deploy\.env.example" ".env" >nul
        echo   Created .env - please set DEEPSEEK_API_KEY
    )
)

:: Python dependencies
echo [1/5] Checking Python dependencies...
uv sync --quiet 2>nul
if errorlevel 1 (
    echo   uv sync failed, trying pip install...
    uv pip install -r requirements.txt --quiet
)

:: Frontend dependencies
if not exist "frontend\node_modules" (
    echo [2/5] Installing frontend dependencies...
    pushd frontend
    call npm install --silent
    popd
    echo   Frontend dependencies installed.
) else (
    echo [2/5] Frontend dependencies ready.
)

:: Init database on first run
if not exist "paper_analysis.db" (
    echo [3/5] First run - initializing database...
    uv run python scripts/init_default_themes.py 2>nul
    uv run python scripts/create_test_user.py 2>nul
    echo   Database initialized.
) else (
    echo [3/5] Database exists.
)

echo.
echo Starting services...
echo.

:: Start backend API in new window
echo [4/5] Starting backend API (port 8000)...
start "Paper-Backend" cmd /k "cd /d %~dp0 && uv run python run.py api"

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start frontend in new window
echo [5/5] Starting frontend (port 4321)...
start "Paper-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait for frontend
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   Startup complete!
echo ========================================
echo.
echo   Frontend : http://localhost:4321
echo   API Docs : http://localhost:8000/api/v1/docs
echo.
echo   Test account: test@huginn.com / test123
echo.

:: Open browser
start http://localhost:4321

echo Services running in background windows.
echo Close "Paper-Backend" and "Paper-Frontend" windows to stop.
echo.
pause
