@echo off
chcp 65001 >nul
echo ========================================
echo 安装服务器依赖
echo ========================================
echo.

cd /d "%~dp0"

echo 检查Python...
python --version

echo.
echo 安装Flask...
pip install -r requirements.txt

echo.
echo 安装完成！
echo 可以运行 启动服务器.bat 来启动服务器
echo.
pause
