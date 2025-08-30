"""
🏘️ AI Agent虚拟小镇 - 主启动文件

运行方式：
python main.py - 启动Web界面
python main.py --termin🏘️ AI Agent虚拟小镇 - 帮助

📖 使用方法：
  python main.py              启动Web界面
  python main.py --help       显示此帮助
  python main.py --terminal   启动终端版本

🌐 Web界面功能：
• 3D地图可视化
• Agent智能交互
• 实时聊天对话（重构版）
python main.py --terminal-old - 启动终端界面（原版）
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import threading
import time
from pathlib import Path

def start_web_server():
    """启动本地Web服务器"""
    PORT = 8080
    
    # 切换到UI目录
    ui_dir = Path(__file__).parent / "ui"
    if ui_dir.exists():
        os.chdir(ui_dir)
    
    # 检查端口是否可用
    for port in range(8080, 8090):
        try:
            with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
                PORT = port
                break
        except OSError:
            continue
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            server_url = f"http://localhost:{PORT}/modern_web_ui.html"
            print(f"""
🏘️ AI Agent虚拟小镇已启动！

🌐 访问地址: {server_url}
🚀 服务端口: {PORT}
📁 文件目录: {ui_dir if ui_dir.exists() else Path.cwd()}

💡 提示：
- 浏览器将自动打开
- 按 Ctrl+C 停止服务器
- 支持多人同时访问

🎮 功能特性：
✨ 智能Agent交互系统
🗺️ 3D可视化地图
💬 实时对话功能
🤝 社交网络分析
📊 地点热度统计
🎪 群体活动组织

""")
            
            # 延迟打开浏览器
            def open_browser():
                time.sleep(1.5)
                webbrowser.open(server_url)
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            print("🖥️  服务器正在运行中...")
            print("� 在浏览器中体验AI虚拟小镇")
            print("=" * 50)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n� 感谢使用AI虚拟小镇！")
        print("🔗 项目地址: https://github.com/your-repo")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

def show_help():
    """显示帮助信息"""
    print("""
🏘️ AI Agent虚拟小镇 - 帮助

📖 使用方法：
  python main.py          启动Web界面
  python main.py --help   显示此帮助
  python terminal_town.py 启动终端版本

� Web界面功能：
• 3D地图可视化
• Agent智能交互
• 实时聊天对话
• 社交网络分析
• 地点热度统计
• 群体活动组织

🛠️ 技术特性：
• 现代化Web界面
• 响应式设计
• 实时动画效果
• 智能Agent行为模拟
• 社交关系网络
• 自动交互系统

🌐 浏览器支持：
• Chrome (推荐)
• Firefox
• Safari
• Edge

📞 如需帮助，请查看README.md
""")

def run_terminal_refactored():
    """运行终端界面"""
    try:
        from terminal_town_refactored import main as terminal_main
        terminal_main()
    except ImportError as e:
        print(f"❌ 无法导入终端模块: {e}")
        print("请确保所有模块都已正确安装")
    except Exception as e:
        print(f"❌ 终端启动失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            show_help()
        elif sys.argv[1] == '--terminal':
            print("🏘️ 启动终端界面...")
            run_terminal_refactored()
        else:
            print(f"❌ 未知参数: {sys.argv[1]}")
            print("使用 --help 查看帮助")
    else:
        start_web_server()
