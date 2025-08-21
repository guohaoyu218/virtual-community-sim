"""
启动异步AI小镇的便捷脚本
"""
import asyncio
import sys
import os

def main():
    print("🚀 启动异步AI小镇...")
    print("📋 可用选项:")
    print("  1. 简化异步仿真 (推荐，无依赖问题)")
    print("  2. 完整异步仿真 (需要Redis)")
    print("  3. 传统同步模式")
    print("  4. Web界面模式")
    print("  5. 测试异步系统")
    print("  6. 退出")
    
    while True:
        choice = input("\n请选择运行模式 (1-6): ").strip()
        
        if choice == "1":
            print("🔄 启动简化异步仿真...")
            try:
                from async_terminal_town_simple import main as simple_async_main
                asyncio.run(simple_async_main())
            except Exception as e:
                print(f"❌ 简化异步仿真失败: {e}")
            break
            
        elif choice == "2":
            print("🔄 启动完整异步仿真...")
            try:
                from async_terminal_town import main as async_main
                asyncio.run(async_main())
            except ImportError as e:
                print(f"❌ 完整异步模块导入失败: {e}")
                print("建议使用选项1的简化版本")
            except Exception as e:
                print(f"❌ 完整异步仿真失败: {e}")
            break
            
        elif choice == "3":
            print("🔄 启动传统同步模式...")
            try:
                from terminal_town import main as sync_main
                sync_main()
            except Exception as e:
                print(f"❌ 同步仿真启动失败: {e}")
            break
            
        elif choice == "4":
            print("🌐 启动Web界面模式...")
            try:
                from main import start_web_server
                start_web_server()
            except Exception as e:
                print(f"❌ Web界面启动失败: {e}")
            break
            
        elif choice == "5":
            print("🧪 测试异步系统...")
            try:
                from test_async import main as test_main
                asyncio.run(test_main())
            except Exception as e:
                print(f"❌ 测试失败: {e}")
            break
            
        elif choice == "6":
            print("👋 再见！")
            sys.exit(0)
            
        else:
            print("❌ 无效选择，请输入1-6")

if __name__ == "__main__":
    main()
