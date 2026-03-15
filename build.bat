@echo off
chcp 65001 >nul
echo ========================================
echo   Email Server 构建脚本 (Windows)
echo ========================================

:: 检查 uv 是否安装
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] uv 未安装，请先安装: pip install uv
    pause
    exit /b 1
)

:: 同步依赖
echo [1/2] 同步依赖...
uv sync
if %errorlevel% neq 0 (
    echo [错误] 依赖同步失败
    pause
    exit /b 1
)

:: 构建 exe
echo [2/2] 构建可执行文件...
uv run pyinstaller EmailServer.spec --noconfirm
if %errorlevel% neq 0 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   构建成功！
echo   输出文件: dist\EmailServer.exe
echo ========================================
pause
