@echo off
REM Hermes Gateway + Watchdog — 一键启动脚本
REM 用法: 双击此文件或命令行运行 start-services.bat

echo ============================================
echo   Hermes Agent — 启动所有服务
echo ============================================

cd /d G:\hermes-agent

echo [1/2] 清理旧锁...
if exist "%USERPROFILE%\.hermes\gateway.lock" del /f "%USERPROFILE%\.hermes\gateway.lock"

echo [2/2] 启动网关...
start "Hermes-Gateway" cmd /c "python -m gateway.run 2>&1"

echo [3/3] 等待网关就绪...
timeout /t 10 /nobreak >nul

echo [4/4] 启动健康检查守护...
start "Hermes-Watchdog" cmd /c "python ci\health-watchdog.py 2>&1"

echo.
echo ============================================
echo   网关: Hermes-Gateway 窗口
echo   监控: Hermes-Watchdog 窗口
echo   关闭任一窗口即停止对应服务
echo ============================================
echo.
pause
