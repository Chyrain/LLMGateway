@echo off
chcp 65001 >nul
REM =============================================
REM 灵模网关 - Claude Code Windows 适配脚本
REM =============================================

echo ============================================
echo    灵模网关 - Claude Code 适配脚本
echo ============================================
echo.

REM 检查是否安装了Claude Code
where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Claude Code，请先安装
    echo 下载地址: https://claude.com/downloads
    pause
    exit /b 1
)

REM 获取网关配置
set /p GATEWAY_URL="请输入灵模网关地址 (默认: http://localhost:8080): "
if "%GATEWAY_URL%"=="" set GATEWAY_URL=http://localhost:8080

set /p GATEWAY_KEY="请输入灵模网关API Key (默认: gateway_123456): "
if "%GATEWAY_KEY%"=="" set GATEWAY_KEY=gateway_123456

echo.
echo [信息] 正在配置环境变量...

REM 设置环境变量（当前终端有效）
set ANTHROPIC_API_KEY=%GATEWAY_KEY%
set ANTHROPIC_API_BASE=%GATEWAY_URL%/v1

echo [成功] 环境变量已设置
echo.

REM 检查用户shell类型
set /p PERMANENT="是否设置为永久环境变量? (y/n): "

if /i "%PERMANENT%"=="y" (
    echo [信息] 正在设置永久环境变量...
    
    REM 获取当前用户名
    for /f "tokens=*" %%u in ('whoami') do set USERNAME=%%u
    
    REM 设置用户级环境变量
    setx ANTHROPIC_API_KEY "%GATEWAY_KEY%" >nul 2>&1
    setx ANTHROPIC_API_BASE "%GATEWAY_URL%/v1" >nul 2>&1
    
    echo [成功] 永久环境变量已设置
    echo [提示] 请关闭当前终端，重新打开后使用Claude Code
)

echo.
echo ============================================
echo    配置完成！
echo ============================================
echo.
echo 使用方法:
echo   1. 当前终端有效: 直接运行 claude
echo   2. 新终端有效: 重启终端后运行 claude
echo.
echo 网关地址: %GATEWAY_URL%/v1
echo API Key: %GATEWAY_KEY%
echo.

pause
