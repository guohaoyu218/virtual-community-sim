@echo off
echo.
echo 🏘️ AI Agent虚拟小镇 - 终端模式 v2.0
echo ==========================================
echo.
echo 🎯 功能特色:
echo   • 9个独特AI Agent角色
echo   • 智能社交网络系统  
echo   • 群体活动和小镇事件
echo   • 实时统计和热度分析
echo   • 高级自动模拟
echo.
echo 🎮 选择启动方式:
echo   [1] 直接开始互动
echo   [2] 先观看功能演示
echo   [3] 运行系统测试
echo.
set /p choice=请输入选择 (1-3): 

if "%choice%"=="1" goto start_main
if "%choice%"=="2" goto start_demo  
if "%choice%"=="3" goto start_test
goto start_main

:start_demo
echo.
echo 🎬 启动功能演示...
cd /d "%~dp0"
python demo_terminal.py
pause
goto end

:start_test
echo.
echo 🧪 运行系统测试...
cd /d "%~dp0"
python test_terminal.py
pause
goto end

:start_main
echo.
echo 🚀 启动终端交互模式...
echo.
cd /d "%~dp0"
python terminal_town.py

:end
echo.
echo 👋 感谢使用AI Agent虚拟小镇！
pause
