"""
Agent管理器模块
负责Agent的初始化、移动等管理功能
"""

import logging
from datetime import datetime
from display.terminal_colors import TerminalColors

logger = logging.getLogger(__name__)

class AgentManager:
    """Agent管理器"""
    
    def __init__(self, thread_manager):
        self.thread_manager = thread_manager
    
    def init_agents(self):
        """初始化AI Agent"""
        from agents.specific_agents import (
            AlexProgrammer, EmmaArtist, SarahTeacher, 
            DavidBusinessman, LisaStudent, MikeRetired,
            JohnDoctor, AnnaChef, TomMechanic
        )
        from .terminal_agent import TerminalAgent
        from display.terminal_colors import TerminalColors
        
        try:
            agents = {
                'Alex': TerminalAgent(AlexProgrammer(), TerminalColors.ALEX, '👨‍💻'),
                'Emma': TerminalAgent(EmmaArtist(), TerminalColors.EMMA, '👩‍🎨'),
                'Sarah': TerminalAgent(SarahTeacher(), TerminalColors.SARAH, '👩‍🏫'),
                'David': TerminalAgent(DavidBusinessman(), TerminalColors.CYAN, '👨‍💼'),
                'Lisa': TerminalAgent(LisaStudent(), TerminalColors.YELLOW, '👩‍🎓'),
                'Mike': TerminalAgent(MikeRetired(), TerminalColors.BLUE, '👴'),
                'John': TerminalAgent(JohnDoctor(), TerminalColors.GREEN, '👨‍⚕️'),
                'Anna': TerminalAgent(AnnaChef(), TerminalColors.RED, '👩‍🍳'),
                'Tom': TerminalAgent(TomMechanic(), TerminalColors.BOLD, '👨‍🔧')
            }
            print("🧠 真实AI Agent系统初始化完成 (9个Agent)")
            return agents
            
        except Exception as e:
            print(f"❌ AI初始化失败: {e}")
            logger.error(f"AI Agent初始化失败: {e}")
            return {}
    
    def move_agent(self, agents, buildings, behavior_manager, agent_name: str, location: str, show_output: bool = True):
        """移动Agent - 线程安全版本
        show_output: 是否在此函数内打印移动信息（模拟引擎会自行打印更完整的区块，因此可关闭）"""
        try:
            # 验证参数
            if location not in buildings:
                print(f"{TerminalColors.RED}❌ 找不到地点: {location}{TerminalColors.END}")
                print(f"可用地点: {', '.join(buildings.keys())}")
                return False
            
            # 线程安全地访问和修改Agent
            with self.thread_manager.safe_agent_access(agents, agent_name) as agent:
                old_location = agent.location
                
                # 原子性地更新位置
                with self.thread_manager.agents_lock:
                    agent.location = location
                    
                    # 更新真实Agent的位置
                    if hasattr(agent, 'real_agent'):
                        agent.real_agent.current_location = location
                
                # 更新建筑物状态
                self.thread_manager.safe_building_update(buildings, agent_name, old_location, location)
                
                # 异步更新地点热度
                self._async_update_location_popularity(behavior_manager, old_location, location)
                
                if show_output:
                    print(f"{TerminalColors.GREEN}🚶 {agent.emoji} {agent_name} 从 {old_location} 移动到 {location}{TerminalColors.END}")
                
                # 记录移动事件
                self._record_movement_event(agent_name, old_location, location)
                
                return True
                
        except ValueError as e:
            print(f"{TerminalColors.RED}❌ {e}{TerminalColors.END}")
            return False
        except Exception as e:
            logger.error(f"移动Agent异常: {e}")
            print(f"{TerminalColors.RED}❌ 移动操作失败{TerminalColors.END}")
            return False
    
    def _async_update_location_popularity(self, behavior_manager, old_location: str, new_location: str):
        """异步更新地点热度"""
        try:
            def update_popularity():
                with self.thread_manager.social_lock:
                    # 降低旧地点热度
                    if old_location in behavior_manager.location_popularity:
                        current = behavior_manager.location_popularity[old_location]
                        behavior_manager.location_popularity[old_location] = max(0, current - 2)
                    
                    # 提高新地点热度
                    if new_location not in behavior_manager.location_popularity:
                        behavior_manager.location_popularity[new_location] = 50
                    current = behavior_manager.location_popularity[new_location]
                    behavior_manager.location_popularity[new_location] = min(100, current + 3)
            
            # 在线程池中执行
            self.thread_manager.submit_task(update_popularity)
            
        except Exception as e:
            logger.error(f"异步更新地点热度失败: {e}")
    
    def _record_movement_event(self, agent_name: str, old_location: str, new_location: str):
        """记录移动事件到向量数据库"""
        try:
            movement_task = {
                'type': 'movement',
                'agent_name': agent_name,
                'old_location': old_location,
                'new_location': new_location,
                'timestamp': datetime.now().isoformat()
            }
            
            # 非阻塞添加到队列
            self.thread_manager.add_memory_task(movement_task)
                
        except Exception as e:
            logger.error(f"记录移动事件失败: {e}")
