"""
简化版异步AI小镇主程序 - 避免aioredis依赖问题
"""
import asyncio
import logging
import signal
import sys
import time
from typing import Dict, List, Any
from datetime import datetime

# 使用简化的Redis管理器
from utils.simple_redis_manager import get_redis_manager
from utils.async_task_manager import get_task_manager, TaskPriority
from setup_logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

class SimpleAsyncAgent:
    """简化的异步Agent"""
    
    def __init__(self, name: str, profession: str, personality: str):
        self.name = name
        self.profession = profession
        self.personality = personality
        self.current_location = "家"
        self.current_mood = "平静"
        self.energy_level = 80
        self.relationships = {}
        
        logger.info(f"简化Agent {self.name} ({self.profession}) 创建成功")
    
    async def think_async(self, topic: str) -> str:
        """异步思考"""
        # 简单的思考逻辑
        thoughts = [
            f"作为{self.profession}，我觉得{topic}很有趣",
            f"关于{topic}，我想起了我的经历",
            f"从{self.personality}的角度看，{topic}让我思考很多",
            f"在{self.current_location}思考{topic}，感觉很好"
        ]
        
        import random
        thought = random.choice(thoughts)
        
        # 缓存思考结果
        redis_manager = await get_redis_manager()
        await redis_manager.set_cache("agent_thoughts", f"{self.name}_{int(time.time())}", {
            "agent": self.name,
            "topic": topic,
            "thought": thought,
            "timestamp": time.time()
        })
        
        return thought
    
    async def move_to_async(self, location: str, reason: str = ""):
        """异步移动"""
        old_location = self.current_location
        self.current_location = location
        
        # 缓存状态
        redis_manager = await get_redis_manager()
        await redis_manager.cache_agent_status(self.name, {
            "location": location,
            "mood": self.current_mood,
            "energy": self.energy_level,
            "last_move": time.time()
        })
        
        logger.debug(f"{self.name} 从 {old_location} 移动到 {location}: {reason}")
    
    async def interact_async(self, other_agent: 'SimpleAsyncAgent', context: str) -> Dict[str, Any]:
        """异步交互"""
        interaction = {
            "participants": [self.name, other_agent.name],
            "context": context,
            "timestamp": time.time(),
            "location": self.current_location,
            "result": f"{self.name}和{other_agent.name}进行了友好的交流"
        }
        
        # 缓存交互
        redis_manager = await get_redis_manager()
        await redis_manager.set_cache("interactions", f"{self.name}_{other_agent.name}_{int(time.time())}", interaction)
        
        return interaction

class SimpleAsyncTown:
    """简化的异步AI小镇"""
    
    def __init__(self):
        self.agents: Dict[str, SimpleAsyncAgent] = {}
        self.locations = {
            '咖啡厅': {'emoji': '☕', 'occupants': []},
            '图书馆': {'emoji': '📚', 'occupants': []},
            '公园': {'emoji': '🌳', 'occupants': []},
            '市场': {'emoji': '🏪', 'occupants': []},
            '学校': {'emoji': '🏫', 'occupants': []},
        }
        
        self.is_running = False
        self.stats = {
            "interactions": 0,
            "movements": 0,
            "thoughts": 0,
            "cycles": 0
        }
    
    async def initialize(self):
        """初始化小镇"""
        logger.info("🏘️ 初始化简化异步AI小镇...")
        
        # 创建简化的Agent
        self.agents = {
            "Alex": SimpleAsyncAgent("Alex", "程序员", "内向、逻辑性强"),
            "Emma": SimpleAsyncAgent("Emma", "艺术家", "富有创造力、情感丰富"),
            "Sarah": SimpleAsyncAgent("Sarah", "教师", "耐心、负责、善于引导")
        }
        
        # 初始化位置
        locations = list(self.locations.keys())
        for i, agent in enumerate(self.agents.values()):
            location = locations[i % len(locations)]
            await agent.move_to_async(location, "初始化")
            self.locations[location]['occupants'].append(agent.name)
        
        logger.info(f"✅ 简化小镇初始化完成，{len(self.agents)}个Agent")
        await self._print_status()
    
    async def start_simulation(self, cycles: int = 20):
        """启动仿真"""
        self.is_running = True
        logger.info(f"🚀 启动仿真，运行 {cycles} 个周期")
        
        try:
            for cycle in range(cycles):
                if not self.is_running:
                    break
                
                logger.info(f"🔄 周期 {cycle + 1}/{cycles}")
                
                # 并行执行Agent行为
                tasks = []
                for agent in self.agents.values():
                    # 随机选择行为
                    import random
                    action = random.choice(["move", "think", "interact"])
                    
                    if action == "move":
                        tasks.append(self._agent_move(agent))
                    elif action == "think":
                        tasks.append(self._agent_think(agent))
                    elif action == "interact":
                        tasks.append(self._agent_interact(agent))
                
                # 等待所有任务完成
                await asyncio.gather(*tasks, return_exceptions=True)
                
                self.stats["cycles"] += 1
                
                # 每5个周期打印状态
                if cycle % 5 == 0:
                    await self._print_status()
                
                # 短暂等待
                await asyncio.sleep(1)
            
            logger.info("🏁 仿真完成")
            
        except KeyboardInterrupt:
            logger.info("用户中断仿真")
        finally:
            await self.stop()
    
    async def _agent_move(self, agent: SimpleAsyncAgent):
        """Agent移动"""
        try:
            # 移除当前位置
            for location in self.locations.values():
                if agent.name in location['occupants']:
                    location['occupants'].remove(agent.name)
            
            # 选择新位置
            import random
            new_location = random.choice(list(self.locations.keys()))
            
            await agent.move_to_async(new_location, "随机探索")
            self.locations[new_location]['occupants'].append(agent.name)
            self.stats["movements"] += 1
            
        except Exception as e:
            logger.error(f"Agent移动失败: {e}")
    
    async def _agent_think(self, agent: SimpleAsyncAgent):
        """Agent思考"""
        try:
            topics = ["工作", "生活", "梦想", "朋友", "未来"]
            import random
            topic = random.choice(topics)
            
            await agent.think_async(topic)
            self.stats["thoughts"] += 1
            
        except Exception as e:
            logger.error(f"Agent思考失败: {e}")
    
    async def _agent_interact(self, agent: SimpleAsyncAgent):
        """Agent交互"""
        try:
            # 找到同位置的其他Agent
            current_location = agent.current_location
            occupants = self.locations[current_location]['occupants']
            others = [name for name in occupants if name != agent.name]
            
            if others:
                import random
                other_name = random.choice(others)
                other_agent = self.agents[other_name]
                
                await agent.interact_async(other_agent, f"在{current_location}相遇")
                self.stats["interactions"] += 1
            
        except Exception as e:
            logger.error(f"Agent交互失败: {e}")
    
    async def _print_status(self):
        """打印状态"""
        redis_manager = await get_redis_manager()
        redis_stats = await redis_manager.get_stats()
        
        print(f"""
📊 小镇状态:
  🤖 Agent数量: {len(self.agents)}
  🔄 交互次数: {self.stats["interactions"]}
  📍 移动次数: {self.stats["movements"]}
  💭 思考次数: {self.stats["thoughts"]}
  🗄️ 缓存后端: {redis_stats.get("backend", "未知")}
  💾 缓存条目: {redis_stats.get("total_keys", 0)}
""")
        
        # 显示位置分布
        for location, info in self.locations.items():
            occupants = ", ".join(info['occupants']) if info['occupants'] else "无人"
            print(f"  {info['emoji']} {location}: {occupants}")
    
    async def stop(self):
        """停止仿真"""
        logger.info("🛑 停止仿真...")
        self.is_running = False
        
        # 关闭服务
        task_manager = await get_task_manager()
        await task_manager.stop()
        
        redis_manager = await get_redis_manager()
        await redis_manager.disconnect()
        
        logger.info("✅ 仿真已停止")

async def main():
    """主函数"""
    print("🚀 启动简化异步AI小镇...")
    
    town = SimpleAsyncTown()
    
    try:
        await town.initialize()
        await town.start_simulation(cycles=30)
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if town.is_running:
            await town.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 感谢使用简化异步AI小镇！")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
