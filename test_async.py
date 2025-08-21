"""
测试异步系统启动
"""
import asyncio
import sys
import os

async def test_imports():
    """测试导入"""
    try:
        print("🔍 测试导入模块...")
        
        # 测试Redis管理器
        from utils.simple_redis_manager import get_redis_manager
        redis_manager = await get_redis_manager()
        print(f"✅ Redis管理器: {redis_manager.is_connected}")
        
        # 测试任务管理器
        from utils.async_task_manager import get_task_manager
        task_manager = await get_task_manager()
        print(f"✅ 任务管理器: {task_manager.is_running}")
        
        # 测试简单缓存
        await redis_manager.set_cache("test", "hello", "world")
        result = await redis_manager.get_cache("test", "hello", "default")
        print(f"✅ 缓存测试: {result}")
        
        # 关闭
        await task_manager.stop()
        await redis_manager.disconnect()
        
        print("🎉 所有模块测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🧪 开始测试异步系统...")
    
    success = await test_imports()
    
    if success:
        print("\n✅ 系统测试成功！现在可以启动完整的异步仿真了。")
        print("运行: python async_terminal_town_simple.py")
    else:
        print("\n❌ 系统测试失败，请检查依赖和配置。")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
