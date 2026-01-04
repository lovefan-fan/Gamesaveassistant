@echo off
chcp 65001 >nul
echo ========================================
echo 游戏存档助手 - 同步服务器
echo ========================================
echo.

cd /d "%~dp0"

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 检查Flask依赖...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [提示] 未安装Flask，正在安装...
    pip install flask
)

echo.
echo 启动服务器...
echo 访问地址: http://127.0.0.1:5000
echo 管理密码: admin123
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python server.py

pause
