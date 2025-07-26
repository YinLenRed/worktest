@echo off
echo ========================================
echo    博客阅读量统计系统启动脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] 检查虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo 错误: 找不到虚拟环境，请确保 venv 目录存在
    pause
    exit /b 1
)

echo [2/5] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/5] 检查Redis连接...
python -c "import redis; r=redis.Redis(); r.ping(); print('Redis连接正常')" 2>nul
if errorlevel 1 (
    echo 警告: Redis连接失败，请确保Redis服务正在运行
    echo 你可以使用以下命令启动Redis:
    echo   redis-server
    echo 或使用Docker:
    echo   docker run -d -p 6379:6379 redis:latest
    echo.
    choice /c YN /m "是否继续启动项目"
    if errorlevel 2 exit /b 1
)

echo [4/5] 进入项目目录...
cd boketest

echo [5/5] 启动Django开发服务器...
echo.
echo ========================================
echo 服务器启动中...
echo 访问地址:
echo   主页: http://127.0.0.1:8000/
echo   管理后台: http://127.0.0.1:8000/admin/
echo   监控仪表板: http://127.0.0.1:8000/dashboard/
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python manage.py runserver

pause 