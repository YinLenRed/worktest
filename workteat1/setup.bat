@echo off
echo ========================================
echo    博客阅读量统计系统初始化脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [2/6] 激活虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo 错误: 找不到虚拟环境，请确保 venv 目录存在
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

echo [3/6] 安装依赖包...
cd boketest
pip install -r ..\requirements.txt
if errorlevel 1 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo [4/6] 创建数据库迁移...
python manage.py makemigrations
if errorlevel 1 (
    echo 错误: 创建迁移失败
    pause
    exit /b 1
)

echo [5/6] 执行数据库迁移...
python manage.py migrate
if errorlevel 1 (
    echo 错误: 数据库迁移失败
    pause
    exit /b 1
)

echo [6/6] 创建超级用户账户...
echo.
echo 请创建管理员账户:
python manage.py createsuperuser

echo.
echo ========================================
echo 初始化完成！
echo.
echo 接下来的步骤:
echo 1. 确保Redis服务正在运行
echo 2. 运行 start.bat 启动项目
echo 3. 访问 http://127.0.0.1:8000/admin/ 添加文章
echo 4. 访问 http://127.0.0.1:8000/ 查看系统
echo ========================================

pause 