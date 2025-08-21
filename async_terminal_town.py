"""
异步版AI小镇主程序 - 支持高并发和Redis缓存
"""
import asyncio
import logging
import signal
import sys
import time
from typing import Dict, List, Any
from datetime import datetime

from agents.async_specific_agents import create_async_agents, AsyncBaseAgent
from utils.async_task_manager import get_task_manager, TaskPriority
from utils.redis_manager import get_redis_manager
from setup_logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

class AsyncTerminalTown:
    """异步AI小镇"""
    
    def __init__(self):
        self.agents: Dict[str, AsyncBaseAgent] = {}
        self.locations = {
            '咖啡厅': {'x': 1, 'y': 3, 'emoji': '☕', 'occupants': []},
            '图书馆': {'x': 2, 'y': 1, 'emoji': '📚', 'occupants': []},
            '公园': {'x': 3, 'y': 2, 'emoji': '🌳', 'occupants': []},
            '市场': {'x': 0, 'y': 4, 'emoji': '🏪', 'occupants': []},
            '学校': {'x': 4, 'y': 0, 'emoji': '🏫', 'occupants': []},
            '医院': {'x': 1, 'y': 4, 'emoji': '🏥', 'occupants': []}
        }
        
        self.is_running = False
        self.simulation_tasks: List[asyncio.Task] = []
        
        # 统计信息
        self.stats = {
            "total_interactions": 0,
            "total_movements": 0,
            "simulation_cycles": 0,
            "start_time": None
        }
    
    async def initialize(self):
        """初始化异步小镇"""
        logger.info("🏘️ 初始化异步AI小镇...")
        
        # 初始化Redis和任务管理器
        redis_manager = await get_redis_manager()
        task_manager = await get_task_manager()
        
        # 创建异步Agent
        self.agents = await create_async_agents()
        
        # 设置初始位置
        locations = list(self.locations.keys())
        for i, agent in enumerate(self.agents.values()):
            initial_location = locations[i % len(locations)]
            await agent.move_to_async(initial_location, "初始化位置")
            self.locations[initial_location]['occupants'].append(agent.name)
        
        self.stats["start_time"] = time.time()
        
        logger.info(f"✅ 异步AI小镇初始化完成，共有 {len(self.agents)} 个Agent")
        
        # 打印系统状态
        await self._print_system_status()
    
    async def start_simulation(self, cycles: int = 50):
        """启动异步仿真"""
        if self.is_running:
            logger.warning("仿真已在运行中")
            return
        
        self.is_running = True
        logger.info(f"🚀 启动异步仿真，预计运行 {cycles} 个周期")
        
        try:
            # 创建仿真任务
            simulation_task = asyncio.create_task(
                self._simulation_loop(cycles)
            )
            
            # 创建状态监控任务
            monitor_task = asyncio.create_task(
                self._monitor_system()
            )
            
            # 创建数据持久化任务
            persistence_task = asyncio.create_task(
                self._periodic_save()
            )
            
            self.simulation_tasks = [simulation_task, monitor_task, persistence_task]
            
            # 等待仿真完成
            await simulation_task
            
        except KeyboardInterrupt:
            logger.info("接收到停止信号，正在关闭仿真...")
        finally:
            await self.stop_simulation()
    
    async def _simulation_loop(self, cycles: int):
        """仿真主循环"""
        for cycle in range(cycles):
            if not self.is_running:
                break
            
            logger.info(f"🔄 仿真周期 {cycle + 1}/{cycles}")
            
            # 并行执行Agent行为
            agent_tasks = []
            
            for agent in self.agents.values():
                # 随机决定Agent行为
                action = await self._decide_agent_action(agent)
                
                if action == "move":
                    task = self._schedule_movement(agent)
                elif action == "interact":
                    task = self._schedule_interaction(agent)
                elif action == "think":
                    task = self._schedule_thinking(agent)
                else:
                    continue
                
                agent_tasks.append(task)
            
            # 等待所有Agent完成当前周期的行为
            if agent_tasks:
                await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            self.stats["simulation_cycles"] += 1
            
            # 周期间隔
            await asyncio.sleep(2)
        
        logger.info("🏁 仿真循环完成")
    
    async def _decide_agent_action(self, agent: AsyncBaseAgent) -> str:
        """决定Agent的行为"""
        # 基于Agent特征和随机性决定行为
        import random
        
        actions = ["move", "interact", "think", "rest"]
        weights = [0.3, 0.4, 0.2, 0.1]
        
        # 根据精力调整权重
        if agent.energy_level < 30:
            weights = [0.1, 0.1, 0.1, 0.7]  # 低精力时主要休息
        elif agent.energy_level > 80:
            weights = [0.4, 0.5, 0.1, 0.0]  # 高精力时更活跃
        
        return random.choices(actions, weights=weights)[0]
    
    async def _schedule_movement(self, agent: AsyncBaseAgent):
        """安排Agent移动"""
        try:
            # 选择新位置
            current_location = agent.current_location
            available_locations = [loc for loc in self.locations.keys() 
                                 if loc != current_location]
            
            if available_locations:
                import random
                new_location = random.choice(available_locations)
                
                # 移除旧位置
                if current_location in self.locations:
                    if agent.name in self.locations[current_location]['occupants']:
                        self.locations[current_location]['occupants'].remove(agent.name)
                
                # 移动到新位置
                await agent.move_to_async(new_location, "随机探索")
                self.locations[new_location]['occupants'].append(agent.name)
                
                self.stats["total_movements"] += 1
                logger.debug(f"📍 {agent.name} 移动到 {new_location}")
        
        except Exception as e:
            logger.error(f"Agent {agent.name} 移动失败: {e}")
    
    async def _schedule_interaction(self, agent: AsyncBaseAgent):
        """安排Agent交互"""
        try:
            # 找到同位置的其他Agent
            current_location = agent.current_location
            occupants = self.locations[current_location]['occupants']
            
            other_agents = [name for name in occupants if name != agent.name]
            
            if other_agents:
                import random
                other_agent_name = random.choice(other_agents)
                other_agent = self.agents.get(other_agent_name)
                
                if other_agent:
                    # 进行异步交互
                    interaction_result = await agent.interact_async(
                        other_agent, 
                        f"在{current_location}偶然相遇"
                    )
                    
                    self.stats["total_interactions"] += 1
                    logger.debug(f"💬 {agent.name} 与 {other_agent.name} 在 {current_location} 交流")
        
        except Exception as e:
            logger.error(f"Agent {agent.name} 交互失败: {e}")
    
    async def _schedule_thinking(self, agent: AsyncBaseAgent):
        """安排Agent思考"""
        try:
            # 生成思考主题
            topics = [
                "今天的生活",
                f"在{agent.current_location}的感受", 
                "未来的计划",
                "最近的经历",
                f"作为{agent.profession}的想法"
            ]
            
            import random
            topic = random.choice(topics)
            
            # 异步思考
            thought = await agent.think_async(topic)
            logger.debug(f"💭 {agent.name} 思考: {thought[:50]}...")
        
        except Exception as e:
            logger.error(f"Agent {agent.name} 思考失败: {e}")
    
    async def _monitor_system(self):
        """监控系统状态"""
        while self.is_running:
            try:
                # 获取任务管理器状态
                task_manager = await get_task_manager()
                task_stats = task_manager.get_stats()
                
                # 获取Redis状态
                redis_manager = await get_redis_manager()
                redis_stats = await redis_manager.get_stats()
                
                # 每30秒打印一次状态
                if self.stats["simulation_cycles"] % 15 == 0:
                    logger.info(f"""
📊 系统状态 (第 {self.stats["simulation_cycles"]} 周期):
  🤖 任务队列: {sum(task_stats["queue_sizes"].values())} 待处理
  ⚡ 已完成任务: {task_stats["completed_tasks"]}
  🗄️ Redis连接: {"✅" if redis_stats["connected"] else "❌"}
  🔄 总交互数: {self.stats["total_interactions"]}
  📍 总移动数: {self.stats["total_movements"]}
""")
                
                await asyncio.sleep(4)
                
            except Exception as e:
                logger.error(f"系统监控失败: {e}")
                await asyncio.sleep(10)
    
    async def _periodic_save(self):
        """定期保存数据"""
        while self.is_running:
            try:
                # 每分钟保存一次Agent状态
                for agent in self.agents.values():
                    await agent._save_to_cache()
                
                # 保存仿真统计
                redis_manager = await get_redis_manager()
                if redis_manager.is_connected:
                    await redis_manager.set_cache(
                        "system", 
                        "simulation_stats", 
                        self.stats
                    )
                
                logger.debug("💾 数据保存完成")
                await asyncio.sleep(60)  # 1分钟保存一次
                
            except Exception as e:
                logger.error(f"数据保存失败: {e}")
                await asyncio.sleep(120)
    
    async def stop_simulation(self):
        """停止仿真"""
        logger.info("🛑 正在停止异步仿真...")
        
        self.is_running = False
        
        # 取消所有仿真任务
        for task in self.simulation_tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务完成
        if self.simulation_tasks:
            await asyncio.gather(*self.simulation_tasks, return_exceptions=True)
        
        # 清理Agent资源
        cleanup_tasks = [agent.cleanup() for agent in self.agents.values()]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # 停止任务管理器
        task_manager = await get_task_manager()
        await task_manager.stop()
        
        # 断开Redis连接
        redis_manager = await get_redis_manager()
        await redis_manager.disconnect()
        
        logger.info("✅ 异步仿真已停止")
    
    async def _print_system_status(self):
        """打印系统状态"""
        redis_manager = await get_redis_manager()
        task_manager = await get_task_manager()
        
        redis_stats = await redis_manager.get_stats()
        task_stats = task_manager.get_stats()
        
        print(f"""
🏘️ 异步AI小镇系统状态
════════════════════════════════════
🤖 Agent数量: {len(self.agents)}
📍 位置数量: {len(self.locations)}
⚡ 任务管理器: {task_stats["workers_count"]} 个工作线程
🗄️ Redis状态: {"连接正常" if redis_stats["connected"] else "连接失败"}
💾 缓存键数: {redis_stats.get("total_keys", 0)}
🔧 内存使用: {redis_stats.get("used_memory", "未知")}
════════════════════════════════════
""")

async def main():
    """主函数"""
    print("🚀 启动异步AI小镇...")
    
    # 创建异步小镇
    town = AsyncTerminalTown()
    
    # 设置信号处理
    def signal_handler():
        logger.info("接收到停止信号")
        asyncio.create_task(town.stop_simulation())
    
    # 注册信号处理器
    if sys.platform != "win32":
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, lambda s, f: signal_handler())
    
    try:
        # 初始化小镇
        await town.initialize()
        
        # 启动仿真
        await town.start_simulation(cycles=100)
        
    except KeyboardInterrupt:
        logger.info("用户中断仿真")
    except Exception as e:
        logger.error(f"仿真运行错误: {e}")
    finally:
        # 确保清理资源
        if town.is_running:
            await town.stop_simulation()

if __name__ == "__main__":
    # 运行异步主程序
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 感谢使用异步AI小镇！")
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        sys.exit(1)
