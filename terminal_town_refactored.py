"""
重构后的终端小镇主类
将原有的臃肿类拆分成多个专门的模块
"""

import os
import sys
import time
import random
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入重构后的模块
from core.thread_manager import ThreadManager
from core.agent_manager import AgentManager
from core.terminal_agent import TerminalAgent
from core.persistence_manager import PersistenceManager
from core.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, initialize_error_handler
from display.terminal_ui import TerminalUI
from display.terminal_colors import TerminalColors
from chat.chat_handler import ChatHandler
from simulation.simulation_engine import SimulationEngine
from memory.memory_cleaner import get_memory_cleaner
from memory.vector_optimizer import get_vector_optimizer

# 导入原有模块
from agents.behavior_manager import behavior_manager
from setup_logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

class TerminalTownRefactored:
    """重构后的终端版AI小镇"""
    
    def __init__(self):
        # 基础数据结构
        self.agents = {}
        self.buildings = {
            '咖啡厅': {'x': 1, 'y': 3, 'emoji': '☕', 'occupants': []},
            '图书馆': {'x': 4, 'y': 3, 'emoji': '📚', 'occupants': []},
            '公园': {'x': 2, 'y': 1, 'emoji': '🌳', 'occupants': []},
            '办公室': {'x': 5, 'y': 1, 'emoji': '💼', 'occupants': []},
            '家': {'x': 3, 'y': 5, 'emoji': '🏠', 'occupants': []},
            '医院': {'x': 0, 'y': 2, 'emoji': '🏥', 'occupants': []},
            '餐厅': {'x': 5, 'y': 4, 'emoji': '🍽️', 'occupants': []},
            '修理店': {'x': 1, 'y': 0, 'emoji': '🔧', 'occupants': []}
        }
        self.chat_history = []
        
        # 初始化各个模块
        self.thread_manager = ThreadManager()
        self.ui = TerminalUI()
        self.persistence_manager = PersistenceManager()
        self.error_handler = initialize_error_handler()  # 初始化错误处理系统
        self.memory_cleaner = get_memory_cleaner()  # 初始化内存清理器
        self.vector_optimizer = get_vector_optimizer()  # 初始化向量优化器
        self.agent_manager = AgentManager(self.thread_manager)
        self.chat_handler = ChatHandler(self.thread_manager, self._clean_response)
        self.simulation_engine = SimulationEngine(
            self.thread_manager, 
            self._clean_response, 
            behavior_manager  # 传递行为管理器
        )
        
        # 重写模拟引擎的执行方法以访问agents
        self.simulation_engine._execute_simulation_step_safe = self._execute_simulation_step_safe
        
        # 系统状态
        self.running = True
        self.behavior_manager = behavior_manager
        
        # 启动后台任务
        self.thread_manager.start_background_workers(
            self._process_memory_save_batch,
            self._process_interaction_async
        )
        
        # 启动自动保存
        self.persistence_manager.start_auto_save(self.get_system_data_for_persistence)
        
        # 启动内存清理
        self.memory_cleaner.start_background_cleanup()
        
        # 初始化Agent
        self.agents = self.agent_manager.init_agents()
        
        # 加载持久化数据
        self.load_persistent_data()
        
        # 显示欢迎界面
        self.ui.clear_screen()
        self.ui.show_welcome()
    
    def _clean_response(self, response: str) -> str:
        """清理AI回应中的多余内容"""
        if not response:
            return "..."
        
        # 移除可能的提示词残留和非对话内容
        patterns_to_remove = [
            r"简短地?回应：?",
            r"回应：?",
            r"回答：?", 
            r"说：?",
            r"思考：?",
            r".*?说：['\"](.*?)['\"].*",
            r".*?回应：['\"](.*?)['\"].*",
            # 移除英文提示词
            r"If you are .+?, how would you respond to this situation\?",
            r"As .+?, I'd .+",
            r"How would you respond\?",
            r"What would you say\?",
            r".*respond to this situation.*",
            r".*how would you.*",
            r".*As \w+, I.*would.*",
            # 移除多语言混合的部分
            r"[a-zA-Z]{30,}",  # 移除长串英文
            # 移除重复的名字和角色描述
            r".*我是\w+.*",
            r".*作为\w+.*",
            r".*我叫\w+.*",
            # 移除非对话内容
            r"你正在与.+?交谈。?",
            r".*正在与.*交谈.*",
            r"你是.+?，.*",
            r"在这种情况下.*",
            r"根据.*情况.*",
        ]
        
        cleaned = response.strip()
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, r"\1" if "(" in pattern else "", cleaned, flags=re.IGNORECASE)
        
        # 移除引号包围
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # 按句号分割，处理重复和长度问题
        sentences = re.split(r'[。！？\n]', cleaned)
        valid_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 移除包含大量英文的句子
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', sentence))
            english_chars = len(re.findall(r'[a-zA-Z]', sentence))
            total_chars = len(sentence)
            
            if total_chars > 0 and english_chars / total_chars > 0.7:
                continue
            
            # 移除明显的指令性开头和非对话内容
            if sentence.startswith(('请注意', '请记住', '如果', '当然可以', '好的我来', '我会帮助', '你正在', '根据')):
                continue
            
            # 移除包含特定非对话关键词的句子
            if any(keyword in sentence for keyword in ['交谈', '对话', '情况下', '根据']):
                continue
            
            # 移除代码相关内容
            if any(keyword in sentence for keyword in ['```', 'def ', 'import ', 'python', 'def(', 'pass']):
                continue
            
            # 避免重复句子，但保留技术内容
            if sentence not in valid_sentences and len(sentence) > 2:
                valid_sentences.append(sentence)
        
        # 保留前2句，确保对话内容简洁
        if valid_sentences:
            result_sentences = valid_sentences[:2]
            cleaned = '。'.join(result_sentences)
            if not cleaned.endswith(('。', '！', '？')):
                cleaned += '。'
        else:
            # 如果没有有效句子，尝试保留原始中文部分
            chinese_only = re.sub(r'[a-zA-Z]{20,}', '', response)
            # 移除非对话标识
            chinese_only = re.sub(r'你正在与.+?交谈。?', '', chinese_only)
            if len(chinese_only.strip()) > 8:
                cleaned = chinese_only.strip()[:80] + ('。' if not chinese_only.strip().endswith(('。', '！', '？')) else '')
            else:
                cleaned = "嗯，我明白了。"
        
        # 最终长度限制
        if len(cleaned) > 100:
            cleaned = cleaned[:97] + "..."
        
        return cleaned.strip()
    
    def show_map(self):
        """显示小镇地图"""
        self.ui.show_map(self.buildings, self.agents)
    
    def show_agents_status(self):
        """显示所有Agent状态"""
        self.ui.show_agents_status(self.agents)
    
    def show_social_network(self):
        """显示社交网络状态"""
        try:
            print(f"\n{TerminalColors.BOLD}━━━ 👥 社交网络状态 ━━━{TerminalColors.END}")
            
            # 显示Agent关系
            if hasattr(self.behavior_manager, 'relationships') and self.behavior_manager.relationships:
                print(f"🤝 Agent关系网络:")
                
                for agent_pair, relationship in self.behavior_manager.relationships.items():
                    agent1, agent2 = agent_pair.split('_', 1)
                    relationship_score = relationship.get('relationship_score', 0)
                    interaction_count = relationship.get('interaction_count', 0)
                    last_interaction = relationship.get('last_interaction_time', 'Unknown')
                    
                    # 根据关系分数显示不同颜色
                    if relationship_score > 0.7:
                        color = TerminalColors.GREEN
                        status = "亲密"
                    elif relationship_score > 0.3:
                        color = TerminalColors.CYAN
                        status = "友好"
                    elif relationship_score > -0.3:
                        color = TerminalColors.YELLOW
                        status = "中性"
                    else:
                        color = TerminalColors.RED
                        status = "冷淡"
                    
                    print(f"  • {agent1} ↔ {agent2}: {color}{status}({relationship_score:.2f}){TerminalColors.END}")
                    print(f"    交互次数: {interaction_count}, 最近交互: {last_interaction[:19] if isinstance(last_interaction, str) else 'N/A'}")
            else:
                print(f"📊 暂无Agent关系记录")
            
            # 显示交互历史统计
            if hasattr(self.behavior_manager, 'interaction_history') and self.behavior_manager.interaction_history:
                recent_interactions = self.behavior_manager.interaction_history[-10:]  # 最近10次
                print(f"\n💬 最近交互记录 (最多10条):")
                
                for interaction in recent_interactions:
                    timestamp = interaction.get('timestamp', 'Unknown')[:19]
                    agent1 = interaction.get('agent1', 'Unknown')
                    agent2 = interaction.get('agent2', 'Unknown')
                    interaction_type = interaction.get('type', 'Unknown')
                    location = interaction.get('location', 'Unknown')
                    
                    print(f"  • {timestamp} | {agent1} & {agent2} | {interaction_type} @ {location}")
            else:
                print(f"\n💬 暂无交互历史记录")
            
            # 显示活跃度统计
            print(f"\n📈 社交活跃度:")
            most_social_agents = {}
            
            for agent_name, agent in self.agents.items():
                interaction_count = getattr(agent, 'interaction_count', 0)
                most_social_agents[agent_name] = interaction_count
            
            # 按交互次数排序
            sorted_agents = sorted(most_social_agents.items(), key=lambda x: x[1], reverse=True)
            
            for i, (agent_name, count) in enumerate(sorted_agents[:5]):  # 显示前5名
                rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                agent_emoji = self.agents[agent_name].emoji if agent_name in self.agents else "👤"
                print(f"  {rank_emoji} {agent_emoji} {agent_name}: {count} 次交互")
            
            # 显示位置热度
            location_popularity = {}
            for agent_name, agent in self.agents.items():
                location = getattr(agent, 'location', '未知')
                location_popularity[location] = location_popularity.get(location, 0) + 1
            
            if location_popularity:
                print(f"\n🏠 位置热度:")
                sorted_locations = sorted(location_popularity.items(), key=lambda x: x[1], reverse=True)
                
                for location, count in sorted_locations:
                    building_emoji = self.buildings.get(location, {}).get('emoji', '🏢')
                    print(f"  • {building_emoji} {location}: {count} 人")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取社交网络状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示社交网络状态失败: {e}")
    
    def chat_with_agent(self, agent_name: str, message: str = None):
        """与Agent对话"""
        self.chat_handler.chat_with_agent(self.agents, agent_name, message)
    
    def move_agent(self, agent_name: str, location: str):
        """移动Agent"""
        return self.agent_manager.move_agent(
            self.agents, self.buildings, self.behavior_manager, agent_name, location
        )
    
    def toggle_auto_simulation(self):
        """切换自动模拟"""
        self.simulation_engine.toggle_auto_simulation()
    
    def _execute_simulation_step_safe(self) -> bool:
        """执行一个安全的模拟步骤"""
        try:
            if not self.agents:
                logger.warning("没有可用的Agent进行模拟")
                return False
            
            # 获取所有Agent列表
            with self.thread_manager.agents_lock:
                available_agents = list(self.agents.items())
            
            if not available_agents:
                return False
            
            # 随机选择一个Agent
            agent_name, agent = random.choice(available_agents)
            
            # 检查Agent是否有效
            if not agent:
                logger.warning(f"Agent {agent_name} 无效")
                return False
            
            # 选择行动类型
            action = self.simulation_engine.choose_agent_action(agent, agent_name)
            
            # 执行相应的行动
            success = False
            try:
                if action == 'social':
                    success = self.simulation_engine.execute_social_action_safe(self.agents, agent, agent_name)
                elif action == 'group_discussion':
                    success = self.simulation_engine.execute_group_discussion_safe(self.agents, agent, agent_name)
                elif action == 'move':
                    success = self._execute_move_action_safe(agent, agent_name)
                elif action == 'think':
                    success = self.simulation_engine.execute_think_action_safe(agent, agent_name)
                elif action == 'work':
                    success = self.simulation_engine.execute_work_action_safe(agent, agent_name)
                elif action == 'relax':
                    success = self.simulation_engine.execute_relax_action_safe(agent, agent_name)
                else:
                    logger.warning(f"未知行动类型: {action}")
                    success = False
                
                # 更新Agent的交互计数
                if success and hasattr(agent, 'interaction_count'):
                    with self.thread_manager.agents_lock:
                        agent.interaction_count += 1
                
                return success
                
            except Exception as e:
                logger.error(f"执行Agent行动失败: {e}")
                return False
                
        except Exception as e:
            logger.error(f"模拟步骤执行异常: {e}")
            return False
    
    def _execute_move_action_safe(self, agent, agent_name: str) -> bool:
        """安全执行移动行动"""
        try:
            current_location = getattr(agent, 'location', '家')
            available_locations = [loc for loc in self.buildings.keys() if loc != current_location]
            
            if not available_locations:
                return False
            
            new_location = random.choice(available_locations)
            
            # 执行移动
            success = self.move_agent(agent_name, new_location)
            
            if success:
                print(f"\n{TerminalColors.BOLD}━━━ 🚶 移动 ━━━{TerminalColors.END}")
                print(f"  {agent.emoji} {TerminalColors.MAGENTA}{agent_name}{TerminalColors.END}: {current_location} → {new_location}")
                print()
            
            return success
            
        except Exception as e:
            logger.error(f"执行移动行动异常: {e}")
            return False
    
    def _process_memory_save_batch(self, tasks: List[dict]):
        """批量处理内存保存任务"""
        try:
            with self.thread_manager.vector_db_lock:
                for task in tasks:
                    if task['type'] == 'user_chat':
                        self._save_user_chat_to_vector_db(
                            task['agent_name'],
                            task['user_message'], 
                            task['agent_response']
                        )
                    elif task['type'] == 'interaction':
                        self._save_interaction_to_vector_db(**task['data'])
                    elif task['type'] == 'movement':
                        self._save_movement_to_vector_db(**task)
                        
        except Exception as e:
            logger.error(f"批量保存内存任务失败: {e}")
    
    def _process_interaction_async(self, interaction_data: dict):
        """异步处理交互数据"""
        try:
            # 更新社交网络
            relationship_info = self.thread_manager.safe_social_update(
                self.behavior_manager,
                interaction_data['agent1_name'],
                interaction_data['agent2_name'],
                interaction_data['interaction_type'],
                interaction_data.get('context', {})
            )
            
            # 保存交互记录
            memory_task = {
                'type': 'interaction',
                'data': {
                    **interaction_data,
                    'relationship_info': relationship_info
                }
            }
            
            self.thread_manager.add_memory_task(memory_task)
                
        except Exception as e:
            logger.error(f"异步处理交互数据失败: {e}")
    
    def _save_user_chat_to_vector_db(self, agent_name, user_message, agent_response):
        """保存用户对话到向量数据库"""
        try:
            if agent_name in self.agents and hasattr(self.agents[agent_name], 'real_agent'):
                agent = self.agents[agent_name].real_agent
                if hasattr(agent, 'memory_manager'):
                    # 构建对话内容
                    chat_content = f"用户与{agent_name}对话：用户说'{user_message}'，{agent_name}回答'{agent_response}'"
                    
                    # 用户对话通常重要性较高
                    importance = 0.8
                    
                    agent.memory_manager.add_memory(
                        content=chat_content,
                        memory_type='user_interaction',
                        base_importance=importance,
                        metadata={
                            'interaction_type': 'user_chat',
                            'user_message': user_message[:100],
                            'agent_response': agent_response[:100],
                            'timestamp': datetime.now().isoformat(),
                            'response_time': time.time(),
                            'interaction_context': 'terminal_chat'
                        }
                    )
                    
                    logger.debug(f"已保存用户对话到{agent_name}的记忆中")
        except Exception as e:
            logger.warning(f"保存用户对话到向量数据库失败: {e}")
    
    def _save_interaction_to_vector_db(self, **data):
        """保存交互到向量数据库"""
        # TODO: 实现交互保存逻辑
        pass
    
    def _save_movement_to_vector_db(self, **data):
        """保存移动事件到向量数据库"""
        # TODO: 实现移动事件保存逻辑
        pass
    
    def get_system_data_for_persistence(self) -> Dict[str, Any]:
        """获取系统数据用于持久化"""
        try:
            return {
                'agents': self.agents,
                'buildings': self.buildings,
                'chat_history': self.chat_history,
                'social_network': self.behavior_manager,
                'config': {
                    'auto_simulation': getattr(self.simulation_engine, 'auto_simulation', False),
                    'system_version': '1.0',
                    'last_active': datetime.now().isoformat()
                },
                'memory_data': getattr(self, 'memory_manager', None)
            }
        except Exception as e:
            logger.error(f"获取持久化数据失败: {e}")
            return {}
    
    def load_persistent_data(self):
        """加载持久化数据"""
        try:
            logger.info("开始加载持久化数据...")
            
            # 加载系统状态
            loaded_data = self.persistence_manager.load_system_state()
            
            if not loaded_data:
                logger.info("没有找到持久化数据，使用默认配置")
                return
            
            # 恢复Agent状态
            if 'agents' in loaded_data and loaded_data['agents']:
                self._restore_agent_states(loaded_data['agents'])
            
            # 恢复建筑物状态
            if 'buildings' in loaded_data and loaded_data['buildings']:
                self._restore_buildings_state(loaded_data['buildings'])
            
            # 恢复聊天历史
            if 'chat_history' in loaded_data and loaded_data['chat_history']:
                self.chat_history = loaded_data['chat_history']
                logger.info(f"恢复了 {len(self.chat_history)} 条聊天记录")
            
            # 恢复社交网络
            if 'social_network' in loaded_data and loaded_data['social_network']:
                self._restore_social_network(loaded_data['social_network'])
            
            # 恢复系统配置
            if 'config' in loaded_data and loaded_data['config']:
                self._restore_system_config(loaded_data['config'])
            
            logger.info("持久化数据加载完成")
            
        except Exception as e:
            logger.error(f"加载持久化数据失败: {e}")
    
    def _restore_agent_states(self, agent_data: Dict):
        """恢复Agent状态"""
        try:
            restored_count = 0
            for name, data in agent_data.items():
                if name in self.agents:
                    agent = self.agents[name]
                    
                    # 恢复基本属性
                    if hasattr(agent, 'location'):
                        agent.location = data.get('location', '家')
                    if hasattr(agent, 'energy_level'):
                        agent.energy_level = data.get('energy_level', 80)
                    if hasattr(agent, 'current_mood'):
                        agent.current_mood = data.get('current_mood', '平静')
                    if hasattr(agent, 'interaction_count'):
                        agent.interaction_count = data.get('interaction_count', 0)
                    
                    # 恢复real_agent属性
                    if hasattr(agent, 'real_agent') and agent.real_agent:
                        agent.real_agent.current_location = data.get('location', '家')
                        if hasattr(agent.real_agent, 'profession'):
                            agent.real_agent.profession = data.get('profession', '通用')
                    
                    restored_count += 1
            
            logger.info(f"恢复了 {restored_count} 个Agent的状态")
            
        except Exception as e:
            logger.error(f"恢复Agent状态失败: {e}")
    
    def _restore_buildings_state(self, buildings_data: Dict):
        """恢复建筑物状态"""
        try:
            for name, data in buildings_data.items():
                if name in self.buildings:
                    self.buildings[name]['occupants'] = data.get('occupants', [])
            
            logger.info("建筑物状态恢复完成")
            
        except Exception as e:
            logger.error(f"恢复建筑物状态失败: {e}")
    
    def _restore_social_network(self, social_data: Dict):
        """恢复社交网络"""
        try:
            if 'relationships' in social_data:
                # 如果behavior_manager有恢复方法
                if hasattr(self.behavior_manager, 'restore_relationships'):
                    self.behavior_manager.restore_relationships(social_data['relationships'])
                
            logger.info("社交网络状态恢复完成")
            
        except Exception as e:
            logger.error(f"恢复社交网络失败: {e}")
    
    def _restore_system_config(self, config_data: Dict):
        """恢复系统配置"""
        try:
            # 恢复自动模拟状态
            if 'auto_simulation' in config_data:
                auto_sim = config_data['auto_simulation']
                if auto_sim and hasattr(self.simulation_engine, 'auto_simulation'):
                    self.simulation_engine.auto_simulation = False  # 先设为False，让用户手动开启
            
            logger.info("系统配置恢复完成")
            
        except Exception as e:
            logger.error(f"恢复系统配置失败: {e}")
    
    def save_system_state(self):
        """手动保存系统状态"""
        try:
            system_data = self.get_system_data_for_persistence()
            success = self.persistence_manager.save_system_state(system_data)
            
            if success:
                print(f"{TerminalColors.GREEN}💾 系统状态保存成功！{TerminalColors.END}")
                logger.info("手动保存系统状态成功")
            else:
                print(f"{TerminalColors.RED}❌ 系统状态保存失败{TerminalColors.END}")
                logger.error("手动保存系统状态失败")
            
            return success
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 保存过程中发生异常: {e}{TerminalColors.END}")
            logger.error(f"手动保存系统状态异常: {e}")
            return False
    
    def show_persistence_status(self):
        """显示持久化状态"""
        try:
            stats = self.persistence_manager.get_system_statistics()
            
            print(f"\n{TerminalColors.BOLD}━━━ 💾 持久化状态 ━━━{TerminalColors.END}")
            print(f"📁 数据目录: {stats.get('data_directory', 'Unknown')}")
            print(f"📄 缓存文件: {stats.get('cache_files', 0)} 个")
            print(f"💿 备份文件: {stats.get('backup_files', 0)} 个") 
            print(f"💬 交互记录: {stats.get('interaction_files', 0)} 个")
            print(f"👤 Agent档案: {stats.get('agent_profiles', 0)} 个")
            print(f"💽 数据总大小: {stats.get('total_data_size_mb', 0)} MB")
            print(f"🤖 自动保存: {'✅ 已启用' if stats.get('auto_save_enabled', False) else '❌ 未启用'}")
            
            if stats.get('last_save_times'):
                print(f"⏰ 最近保存时间:")
                for component, save_time in stats['last_save_times'].items():
                    print(f"   • {component}: {save_time}")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取持久化状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示持久化状态失败: {e}")

    def show_system_health(self):
        """显示系统健康状态"""
        try:
            stats = self.error_handler.get_error_statistics()
            recent_errors = self.error_handler.get_recent_errors(10)
            
            print(f"\n{TerminalColors.BOLD}━━━ 🏥 系统健康状态 ━━━{TerminalColors.END}")
            
            # 系统健康状态
            health = stats.get('system_health', 'unknown')
            health_colors = {
                'healthy': TerminalColors.GREEN,
                'warning': TerminalColors.YELLOW,
                'degraded': TerminalColors.RED,
                'critical': TerminalColors.RED,
                'recovering': TerminalColors.CYAN
            }
            health_color = health_colors.get(health, TerminalColors.WHITE)
            print(f"💊 系统状态: {health_color}{health.upper()}{TerminalColors.END}")
            
            # 错误统计
            print(f"📊 错误统计:")
            print(f"  • 总错误数: {stats.get('total_errors', 0)}")
            
            # 按类别统计
            category_stats = stats.get('errors_by_category', {})
            if category_stats:
                print(f"  • 按类别:")
                for category, count in category_stats.items():
                    print(f"    - {category}: {count}")
            
            # 按严重程度统计
            severity_stats = stats.get('errors_by_severity', {})
            if severity_stats:
                print(f"  • 按严重程度:")
                for severity, count in severity_stats.items():
                    color = TerminalColors.RED if severity == 'critical' else TerminalColors.YELLOW if severity == 'high' else TerminalColors.WHITE
                    print(f"    - {color}{severity}{TerminalColors.END}: {count}")
            
            # 熔断器状态
            circuit_breaker_status = stats.get('circuit_breaker_status', {})
            if circuit_breaker_status:
                print(f"🔥 熔断器状态:")
                for category, count in circuit_breaker_status.items():
                    if count > 0:
                        print(f"  • {category}: {TerminalColors.RED}激活 ({count}){TerminalColors.END}")
                    else:
                        print(f"  • {category}: {TerminalColors.GREEN}正常{TerminalColors.END}")
            
            # 最近错误
            if recent_errors:
                print(f"🚨 最近错误 (最多10条):")
                for error in recent_errors[-10:]:
                    timestamp = error.get('timestamp', '')[:19]  # 只显示到秒
                    severity = error.get('severity', 'unknown')
                    operation = error.get('operation', 'Unknown')
                    message = error.get('message', '')[:50]  # 限制消息长度
                    
                    severity_color = TerminalColors.RED if severity == 'critical' else TerminalColors.YELLOW if severity == 'high' else TerminalColors.WHITE
                    print(f"  • {timestamp} [{severity_color}{severity}{TerminalColors.END}] {operation}: {message}")
            
            print(f"⏰ 检查时间: {stats.get('health_check_time', 'Unknown')[:19]}")
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取系统健康状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示系统健康状态失败: {e}")
    
    def show_vector_database_status(self):
        """显示向量数据库状态"""
        try:
            from memory.vector_store import get_vector_store
            vector_store = get_vector_store()
            
            print(f"\n{TerminalColors.BOLD}━━━ 🗄️ 向量数据库状态 ━━━{TerminalColors.END}")
            
            # 连接状态
            connection_status = vector_store.get_connection_status()
            
            if connection_status.get('connected', False):
                print(f"🟢 连接状态: {TerminalColors.GREEN}已连接{TerminalColors.END}")
                print(f"🏠 服务器: {connection_status.get('host', 'Unknown')}:{connection_status.get('port', 'Unknown')}")
                print(f"📊 向量维度: {connection_status.get('embedding_dimension', 'Unknown')}")
                print(f"📁 集合数量: {connection_status.get('total_collections', 0)}")
                print(f"📄 记忆总数: {connection_status.get('total_points', 0)}")
                print(f"💿 客户端类型: {connection_status.get('client_type', 'Unknown')}")
                
                # 显示各集合详情
                if connection_status.get('total_collections', 0) > 0:
                    print(f"\n📋 集合详情:")
                    try:
                        collections = vector_store.client.get_collections()
                        for collection in collections.collections:
                            try:
                                stats = vector_store.get_collection_stats(collection.name)
                                agent_name = collection.name.replace('agent_', '').replace('_memories', '')
                                print(f"  • {agent_name}: {stats.get('total_points', 0)} 条记忆")
                                print(f"    - 平均重要性: {stats.get('average_importance', 0):.2f}")
                                print(f"    - 平均访问次数: {stats.get('average_access_count', 0):.1f}")
                                if stats.get('memory_types'):
                                    types_str = ', '.join([f"{k}({v})" for k, v in stats['memory_types'].items()])
                                    print(f"    - 记忆类型: {types_str}")
                            except Exception as e:
                                print(f"  • {collection.name}: 获取统计失败 ({e})")
                    except Exception as e:
                        print(f"  获取集合详情失败: {e}")
            else:
                print(f"🔴 连接状态: {TerminalColors.RED}未连接{TerminalColors.END}")
                error_msg = connection_status.get('error', '未知错误')
                print(f"❌ 错误信息: {error_msg}")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取向量数据库状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示向量数据库状态失败: {e}")
    
    def show_memory_status(self):
        """显示内存状态"""
        try:
            memory_status = self.memory_cleaner.get_memory_status()
            
            print(f"\n{TerminalColors.BOLD}━━━ 🧠 内存状态 ━━━{TerminalColors.END}")
            
            # 系统内存状态
            sys_mem = memory_status.get('system_memory', {})
            print(f"💾 系统内存:")
            print(f"  • 总容量: {sys_mem.get('total_gb', 0):.1f} GB")
            print(f"  • 已使用: {sys_mem.get('used_gb', 0):.1f} GB ({sys_mem.get('percent_used', 0):.1f}%)")
            print(f"  • 可用: {sys_mem.get('available_gb', 0):.1f} GB")
            
            # 内存使用警告
            memory_percent = sys_mem.get('percent_used', 0)
            if memory_percent > 80:
                print(f"  ⚠️  {TerminalColors.RED}内存使用率过高！{TerminalColors.END}")
            elif memory_percent > 60:
                print(f"  ⚠️  {TerminalColors.YELLOW}内存使用率较高{TerminalColors.END}")
            else:
                print(f"  ✅ {TerminalColors.GREEN}内存使用正常{TerminalColors.END}")
            
            # 进程内存
            proc_mem = memory_status.get('process_memory', {})
            print(f"🔬 进程内存:")
            print(f"  • RSS: {proc_mem.get('rss_mb', 0):.1f} MB")
            print(f"  • VMS: {proc_mem.get('vms_mb', 0):.1f} MB")
            
            # 向量数据库状态
            vector_db = memory_status.get('vector_database', {})
            if vector_db.get('connected', False):
                print(f"🗄️  向量数据库:")
                print(f"  • 集合数量: {vector_db.get('total_collections', 0)}")
                print(f"  • 记忆总数: {vector_db.get('total_memories', 0)}")
            else:
                print(f"🗄️  向量数据库: {TerminalColors.RED}未连接{TerminalColors.END}")
            
            # 清理统计
            cleanup_stats = memory_status.get('cleanup_stats', {})
            print(f"🧹 清理统计:")
            print(f"  • 总清理次数: {cleanup_stats.get('total_cleanups', 0)}")
            print(f"  • 清理记忆数: {cleanup_stats.get('memories_cleaned', 0)}")
            print(f"  • 释放空间: {cleanup_stats.get('space_freed_mb', 0):.1f} MB")
            
            last_cleanup = cleanup_stats.get('last_cleanup_time')
            if last_cleanup:
                print(f"  • 上次清理: {last_cleanup[:19]}")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取内存状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示内存状态失败: {e}")
    
    def cleanup_memory(self, cleanup_type: str = 'normal'):
        """执行内存清理"""
        try:
            print(f"{TerminalColors.YELLOW}🧹 开始内存清理...{TerminalColors.END}")
            
            if cleanup_type == 'emergency':
                results = self.memory_cleaner.emergency_cleanup()
                print(f"{TerminalColors.CYAN}⚡ 紧急清理完成{TerminalColors.END}")
            elif cleanup_type == 'vector':
                results = self.memory_cleaner.cleanup_vector_database()
                print(f"{TerminalColors.CYAN}🗄️ 向量数据库清理完成{TerminalColors.END}")
            elif cleanup_type == 'all':
                results = self.memory_cleaner.force_cleanup_all()
                print(f"{TerminalColors.CYAN}🔄 全面清理完成{TerminalColors.END}")
            else:
                results = self.memory_cleaner.cleanup_system_memory()
                print(f"{TerminalColors.CYAN}💾 系统内存清理完成{TerminalColors.END}")
            
            # 显示清理结果
            if isinstance(results, dict):
                if 'memory_freed_mb' in results:
                    freed_mb = results.get('memory_freed_mb', 0)
                    print(f"✅ 释放内存: {freed_mb:.2f} MB")
                
                if 'memories_deleted' in results:
                    deleted = results.get('memories_deleted', 0)
                    print(f"✅ 清理记忆: {deleted} 条")
                
                if 'gc_collected' in results:
                    collected = results.get('gc_collected', 0)
                    print(f"✅ 垃圾回收: {collected} 个对象")
                
                if 'errors' in results and results['errors']:
                    print(f"⚠️  警告: {len(results['errors'])} 个错误")
                    for error in results['errors']:
                        print(f"  • {error}")
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 内存清理失败: {e}{TerminalColors.END}")
            logger.error(f"内存清理失败: {e}")
    
    def optimize_vector_database(self):
        """优化向量数据库"""
        try:
            print(f"{TerminalColors.YELLOW}🚀 开始向量数据库优化...{TerminalColors.END}")
            print(f"{TerminalColors.CYAN}⏰ 这可能需要几分钟时间，请耐心等待...{TerminalColors.END}")
            
            # 执行完整优化
            result = self.vector_optimizer.run_full_optimization()
            
            if result.get('success', False):
                print(f"{TerminalColors.GREEN}✅ 向量数据库优化完成！{TerminalColors.END}")
                
                # 显示优化结果
                memories_before = result.get('total_memories_before', 0)
                memories_after = result.get('total_memories_after', 0)
                memories_cleaned = memories_before - memories_after
                
                print(f"📊 优化结果:")
                print(f"  • 优化前记忆数: {memories_before}")
                print(f"  • 优化后记忆数: {memories_after}")
                print(f"  • 清理记忆数: {TerminalColors.GREEN}{memories_cleaned}{TerminalColors.END}")
                
                # 显示完成的步骤
                steps = result.get('steps_completed', [])
                print(f"  • 完成步骤: {len(steps)}")
                for step in steps:
                    print(f"    ✓ {step}")
                
                # 显示性能改进
                improvements = result.get('performance_improvements', {})
                if improvements:
                    reduction_percent = improvements.get('memory_reduction_percent', 0)
                    speedup_percent = improvements.get('estimated_query_speedup_percent', 0)
                    
                    if reduction_percent > 0:
                        print(f"  • 数据减少: {reduction_percent:.1f}%")
                    if speedup_percent > 0:
                        print(f"  • 预计查询速度提升: {speedup_percent:.1f}%")
                
            else:
                print(f"{TerminalColors.RED}❌ 向量数据库优化失败{TerminalColors.END}")
                errors = result.get('errors', [])
                if errors:
                    print(f"错误信息:")
                    for error in errors:
                        print(f"  • {error}")
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 优化过程中发生异常: {e}{TerminalColors.END}")
            logger.error(f"向量数据库优化异常: {e}")
    
    def show_optimization_report(self):
        """显示优化报告"""
        try:
            print(f"\n{TerminalColors.BOLD}━━━ 📈 向量数据库优化报告 ━━━{TerminalColors.END}")
            
            report = self.vector_optimizer.get_optimization_report()
            
            if 'error' in report:
                print(f"{TerminalColors.RED}❌ 获取报告失败: {report['error']}{TerminalColors.END}")
                return
            
            # 数据库状态
            db_status = report.get('database_status', {})
            if db_status.get('connected', False):
                print(f"🗄️  数据库状态: {TerminalColors.GREEN}已连接{TerminalColors.END}")
                print(f"  • 服务器: {db_status.get('host', 'Unknown')}:{db_status.get('port', 'Unknown')}")
                print(f"  • 集合数量: {db_status.get('total_collections', 0)}")
                print(f"  • 记忆总数: {db_status.get('total_points', 0)}")
            else:
                print(f"🗄️  数据库状态: {TerminalColors.RED}未连接{TerminalColors.END}")
            
            # 当前统计
            current_stats = report.get('current_statistics', {})
            print(f"\n📊 当前统计:")
            print(f"  • 总集合数: {current_stats.get('total_collections', 0)}")
            print(f"  • 总记忆数: {current_stats.get('total_memories', 0)}")
            
            # 记忆类型分布
            memory_dist = current_stats.get('memory_distribution', {})
            if memory_dist:
                print(f"  • 记忆类型分布:")
                for mem_type, count in memory_dist.items():
                    print(f"    - {mem_type}: {count}")
            
            # 性能统计
            perf_stats = report.get('performance_statistics', {})
            print(f"\n⚡ 性能统计:")
            print(f"  • 总优化次数: {perf_stats.get('total_optimizations', 0)}")
            print(f"  • 总清理记忆数: {perf_stats.get('total_memories_cleaned', 0)}")
            print(f"  • 节省空间: {perf_stats.get('total_space_saved_mb', 0):.2f} MB")
            print(f"  • 平均查询时间: {perf_stats.get('average_query_time_ms', 0):.1f} ms")
            
            last_optimization = perf_stats.get('last_optimization')
            if last_optimization:
                print(f"  • 上次优化: {last_optimization[:19]}")
            
            # 优化建议
            recommendations = report.get('recommendations', [])
            if recommendations:
                print(f"\n💡 优化建议:")
                for i, recommendation in enumerate(recommendations, 1):
                    print(f"  {i}. {recommendation}")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 显示优化报告失败: {e}{TerminalColors.END}")
            logger.error(f"显示优化报告失败: {e}")
    
    def reset_error_statistics(self):
        """重置错误统计"""
        try:
            self.error_handler.reset_error_stats()
            print(f"{TerminalColors.GREEN}✅ 错误统计已重置{TerminalColors.END}")
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 重置错误统计失败: {e}{TerminalColors.END}")
            logger.error(f"重置错误统计失败: {e}")

    def shutdown(self):
        """安全关闭系统"""
        try:
            logger.info("开始关闭系统...")
            self.running = False
            
            # 保存最终状态
            print(f"{TerminalColors.YELLOW}💾 正在保存系统状态...{TerminalColors.END}")
            self.save_system_state()
            
            # 关闭各个组件
            if hasattr(self, 'memory_cleaner'):
                self.memory_cleaner.shutdown()
            
            if hasattr(self, 'persistence_manager'):
                self.persistence_manager.shutdown()
            
            if hasattr(self, 'error_handler'):
                self.error_handler.shutdown()
            
            if hasattr(self, 'thread_manager'):
                self.thread_manager.shutdown()
            
            print(f"{TerminalColors.GREEN}✅ 系统已安全关闭{TerminalColors.END}")
            logger.info("系统关闭完成")
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 关闭过程中发生异常: {e}{TerminalColors.END}")
            logger.error(f"系统关闭异常: {e}")
            
            # 使用错误处理系统记录关闭异常
            if hasattr(self, 'error_handler'):
                self.error_handler.handle_error({
                    'operation': 'system_shutdown',
                    'category': ErrorCategory.SYSTEM,
                    'severity': ErrorSeverity.HIGH,
                    'exception': e,
                    'context': {'phase': 'shutdown'}
                })

def main():
    """主函数"""
    try:
        town = TerminalTownRefactored()
        
        print(f"\n{TerminalColors.GREEN}🎮 系统就绪！输入命令开始体验{TerminalColors.END}")
        print(f"{TerminalColors.CYAN}💡 输入 'help' 查看所有可用命令{TerminalColors.END}\n")
        
        while town.running:
            try:
                user_input = input(f"{TerminalColors.BOLD}🏘️  小镇> {TerminalColors.END}").strip()
                
                if not user_input:
                    continue
                
                # 解析命令
                parts = user_input.split()
                command = parts[0].lower()
                
                if command in ['quit', 'exit', '退出']:
                    town.ui.show_info("正在关闭系统...")
                    break
                elif command == 'map':
                    town.show_map()
                elif command == 'agents':
                    town.show_agents_status()
                elif command == 'social':
                    town.show_social_network()
                elif command == 'chat':
                    if len(parts) > 1:
                        agent_name = parts[1]
                        message = ' '.join(parts[2:]) if len(parts) > 2 else None
                        town.chat_with_agent(agent_name, message)
                    else:
                        town.ui.show_error("请指定要对话的Agent名称")
                elif command == 'move':
                    if len(parts) >= 3:
                        agent_name = parts[1]
                        location = ' '.join(parts[2:])
                        town.move_agent(agent_name, location)
                    else:
                        town.ui.show_error("用法: move <agent_name> <location>")
                elif command == 'auto':
                    town.toggle_auto_simulation()
                elif command == 'save':
                    town.save_system_state()
                elif command == 'status':
                    town.show_persistence_status()
                elif command == 'health':
                    town.show_system_health()
                elif command == 'memory':
                    town.show_memory_status()
                elif command == 'vector':
                    town.show_vector_database_status()
                elif command == 'cleanup':
                    if len(parts) > 1:
                        cleanup_type = parts[1]
                        if cleanup_type in ['normal', 'emergency', 'vector', 'all']:
                            town.cleanup_memory(cleanup_type)
                        else:
                            town.ui.show_error("用法: cleanup [normal|emergency|vector|all]")
                    else:
                        town.cleanup_memory('normal')
                elif command == 'optimize':
                    if len(parts) > 1:
                        if parts[1] == 'vector':
                            town.optimize_vector_database()
                        elif parts[1] == 'report':
                            town.show_optimization_report()
                        else:
                            town.ui.show_error("用法: optimize [vector|report]")
                    else:
                        town.ui.show_error("用法: optimize [vector|report]")
                elif command == 'reset':
                    if len(parts) > 1 and parts[1] == 'errors':
                        town.reset_error_statistics()
                    else:
                        town.ui.show_error("用法: reset errors")
                elif command == 'help':
                    town.ui.show_welcome()
                else:
                    town.ui.show_error(f"未知命令: {command}")
                    
            except KeyboardInterrupt:
                town.ui.show_warning("\\n检测到中断信号，正在安全关闭...")
                break
            except EOFError:
                break
            except Exception as e:
                town.ui.show_error(f"命令执行失败: {e}")
                logger.error(f"命令执行异常: {e}")
        
    except Exception as e:
        print(f"{TerminalColors.RED}❌ 系统启动失败: {e}{TerminalColors.END}")
        logger.error(f"系统启动失败: {e}")
    finally:
        if 'town' in locals():
            town.shutdown()

if __name__ == "__main__":
    main()
