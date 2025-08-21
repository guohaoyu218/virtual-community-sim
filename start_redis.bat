@echo off
echo 🗄️ Redis 安装和启动脚本

REM 检查Redis是否已安装
redis-server --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Redis已安装
    goto :start_redis
)

echo ❌ Redis未安装
echo 📥 正在下载Redis for Windows...

REM 创建Redis目录
if not exist "redis" mkdir redis
cd redis

REM 下载Redis (Windows版本)
echo 请从 https://github.com/microsoftarchive/redis/releases 下载Redis
echo 或者使用 WSL/Docker 运行Redis
echo.
echo 快速启动Redis的几种方式:
echo 1. Docker: docker run -d -p 6379:6379 redis:latest
echo 2. WSL: sudo apt install redis-server ^&^& redis-server
echo 3. 手动下载Windows版本到redis文件夹
echo.
pause
goto :end

:start_redis
echo 🚀 启动Redis服务器...
redis-server --port 6379 --save 60 1

:end
pause
