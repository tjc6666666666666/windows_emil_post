@echo off
chcp 65001 >nul
echo ========================================
echo   Email Server Build Script (Windows)
echo ========================================

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv not installed, please run: pip install uv
    pause
    exit /b 1
)

echo [1/2] Syncing dependencies...
uv sync
if errorlevel 1 (
    echo [ERROR] Dependency sync failed
    pause
    exit /b 1
)

echo [2/2] Building executable...
.venv\Scripts\python.exe -m PyInstaller EmailServer.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Success!
echo   Output: dist\EmailServer.exe
echo ========================================
pause
