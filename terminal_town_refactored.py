import os
import sys
import time
import random
import logging
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.thread_manager import ThreadManager
from core.agent_manager import AgentManager
from core.error_handler import ErrorCategory, ErrorSeverity
from core.terminal_agent import TerminalAgent
from core.persistence_manager import PersistenceManager
from core.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, initialize_error_handler
from core.context_engine import AdvancedContextEngine
from core.smart_cleanup_manager import get_smart_cleanup_manager
from display.terminal_ui import TerminalUI
from display.status_display import StatusDisplay
from display.terminal_colors import TerminalColors
from chat.chat_handler import ChatHandler
from simulation.simulation_engine import SimulationEngine
from memory.memory_cleaner import get_memory_cleaner
from memory.vector_optimizer import get_vector_optimizer
from agents.behavior_manager import behavior_manager
from setup_logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

class TerminalTownRefactored:
   
    
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
        self.status_display = StatusDisplay()  # 添加状态显示器
        self.persistence_manager = PersistenceManager()
        self.error_handler = initialize_error_handler()  # 初始化错误处理系统
        self.memory_cleaner = get_memory_cleaner()  # 初始化内存清理器
        self.vector_optimizer = get_vector_optimizer()  # 初始化向量优化器
        self.context_engine = AdvancedContextEngine()  # 先进上下文引擎
        self.smart_cleanup_manager = get_smart_cleanup_manager(
            self.memory_cleaner, 
            self.vector_optimizer
        )  # 智能清理管理器
        
        self.agent_manager = AgentManager(self.thread_manager)
        self.chat_handler = ChatHandler(
            self.thread_manager, 
            self._clean_response, 
            self.context_engine  # 传递上下文引擎
        )
        self.simulation_engine = SimulationEngine(
            self.thread_manager, 
            self._clean_response, 
            behavior_manager,  # 传递行为管理器
            agents_ref=lambda: self.agents,  # 传递agents引用
            buildings_ref=lambda: self.buildings,  # 传递buildings引用
            agent_manager=self.agent_manager  # 传递agent_manager
        )
        
        # 移除对simulation_engine的动态方法注入，现在它内部已经有了这个方法
        
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
        
        # 启动智能清理管理器
        self.smart_cleanup_manager.start_monitoring()
        
        # 初始化Agent
        with self.error_handler.error_context(
            operation='initialize_agents',
            category=ErrorCategory.AGENT,
            severity=ErrorSeverity.HIGH
        ):
            self.agents = self.agent_manager.init_agents()
        
        # 加载持久化数据
        with self.error_handler.error_context(
            operation='load_persistent_data',
            category=ErrorCategory.PERSISTENCE,
            severity=ErrorSeverity.MEDIUM
        ):
            self.load_persistent_data()
        
        # 显示欢迎界面
        self.ui.clear_screen()
        self.ui.show_welcome()
        # 标记已显示
        self._welcome_shown = True
    
    def _clean_response(self, response: str) -> str:
        """清理AI回应中的多余内容 - 委托给context_engine"""
        return self.context_engine.clean_response(response)
    
    def show_map(self):
        """显示小镇地图"""
        self.ui.show_map(self.buildings, self.agents)
    
    def show_agents_status(self):
        """显示所有Agent状态"""
        self.ui.show_agents_status(self.agents)
    
    def show_social_network(self, mode: str = 'basic'):
        """统一显示社交网络状态
        
        Args:
            mode: 显示模式
                - 'basic': 基础关系矩阵
                - 'advanced': 高级状态和详细分析
        """
        try:
            if mode == 'advanced':
                return self._show_social_network_advanced()
            else:
                return self._show_social_network_basic()
                
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 显示社交网络失败: {e}{TerminalColors.END}")
            logger.error(f"显示社交网络失败: {e}")
    
    def _show_social_network_basic(self):
        """显示基础社交网络状态 - 委托给状态显示器"""
        self.status_display.show_social_network_basic(
            self.agents, 
            self.behavior_manager, 
            self._show_recent_interactions_delegate
        )
    
    def _show_recent_interactions_delegate(self):
        """显示最近交互的委托方法"""
        if hasattr(self, 'chat_history') and self.chat_history:
            # 过滤出Agent之间的交互（非用户聊天）
            agent_interactions = []
            for chat in self.chat_history[-20:]:  # 检查最近20条记录
                if 'interaction_type' in chat and chat.get('interaction_type') != 'user_chat':
                    agent_interactions.append(chat)
            
            if agent_interactions:
                recent_interactions = agent_interactions[-5:]  # 最近5次Agent交互
                print(f"\n{TerminalColors.CYAN}💬 最近交互记录:{TerminalColors.END}")
                
                for i, interaction in enumerate(recent_interactions, 1):
                    timestamp = interaction.get('timestamp', 'Unknown')[:19]
                    agent1 = interaction.get('agent1', interaction.get('agent_name', 'Unknown'))
                    agent2 = interaction.get('agent2', 'Unknown')
                    interaction_type = interaction.get('interaction_type', interaction.get('type', 'Unknown'))
                    location = interaction.get('location', 'Unknown')
                    
                    print(f"  {i}. [{timestamp}] {agent1} ↔ {agent2}")
                    print(f"     🎭 {interaction_type} @ 📍 {location}")
            else:
                print(f"\n💬 暂无Agent间交互记录")
                print(f"💡 提示: 使用 'auto' 命令来启动Agent自动交互")
        else:
            print(f"\n💬 暂无交互历史记录")
            print(f"💡 提示: 使用 'chat' 或 'auto' 命令来增加Agent互动")

    def _show_social_network_advanced(self):
        """显示高级社交网络状态和详细分析"""
        print(f"\n{TerminalColors.BOLD}━━━ 💫 高级社交网络分析 ━━━{TerminalColors.END}")
        
        agent_names = list(self.agents.keys())
        if not agent_names:
            print(f"❌ 暂无Agent")
            return
        
        # 基础统计信息
        print(f"🤝 社交网络统计:")
        total_relationships = 0
        if hasattr(self.behavior_manager, 'social_network'):
            for agent_relationships in self.behavior_manager.social_network.values():
                total_relationships += len(agent_relationships)
            total_relationships //= 2  # 避免重复计算
            print(f"  • 总关系数: {total_relationships}")
            
        # 显示最近交互统计
        if hasattr(self, 'chat_history'):
            agent_interactions = [chat for chat in self.chat_history if chat.get('interaction_type') != 'user_chat']
            print(f"  • 最近交互数: {len(agent_interactions)}")
        
        # 社交活跃度排行
        print(f"\n{TerminalColors.CYAN}🏆 社交活跃度排行:{TerminalColors.END}")
        social_scores = {}
        
        # 计算每个Agent的社交分数
        for agent_name in agent_names:
            score = 0
            interaction_count = 0
            
            # 统一从behavior_manager获取关系数据
            if hasattr(self.behavior_manager, 'social_network'):
                agent_relationships = self.behavior_manager.social_network.get(agent_name, {})
                for other_agent, strength in agent_relationships.items():
                    score += strength
                    interaction_count += 1
            
            # 从聊天历史统计用户交互
            user_chats = 0
            if hasattr(self, 'chat_history'):
                user_chats = len([chat for chat in self.chat_history if chat.get('agent_name') == agent_name])
                score += user_chats * 5  # 用户交互加分
            
            social_scores[agent_name] = {
                'total_score': score,
                'interaction_count': interaction_count,
                'user_chats': user_chats
            }
        
        # 排序并显示
        sorted_agents = sorted(social_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        for i, (agent_name, stats) in enumerate(sorted_agents, 1):
            agent = self.agents.get(agent_name)
            if agent:
                emoji = getattr(agent, 'emoji', '🤖')
                profession = getattr(agent, 'profession', '未知')
                location = getattr(agent, 'location', '未知')
                
                print(f"  {i:2d}. {emoji} {agent_name} ({profession})")
                print(f"      📍 {location} | 💯 {stats['total_score']:.1f} | 🤝 {stats['interaction_count']} | 💬 {stats['user_chats']}")
        
        # 关系强度分布
        print(f"\n{TerminalColors.CYAN}🕸️ 关系网络分析:{TerminalColors.END}")
        if hasattr(self.behavior_manager, 'social_network'):
            strength_distribution = {'敌对': 0, '冷淡': 0, '中性': 0, '友好': 0, '亲密': 0}
            total_rels = 0
            
            for agent_name, relationships in self.behavior_manager.social_network.items():
                for other_agent, strength in relationships.items():
                    total_rels += 1
                    if strength >= 80:
                        strength_distribution['亲密'] += 1
                    elif strength >= 60:
                        strength_distribution['友好'] += 1
                    elif strength >= 40:
                        strength_distribution['中性'] += 1
                    elif strength >= 20:
                        strength_distribution['冷淡'] += 1
                    else:
                        strength_distribution['敌对'] += 1
            
            print(f"  📊 关系分布 (总计 {total_rels//2} 对关系):")
            for level, count in strength_distribution.items():
                if count > 0:
                    percentage = (count / total_rels) * 100 if total_rels > 0 else 0
                    print(f"     {level}: {count//2} 对 ({percentage/2:.1f}%)")
        
        print(f"\n✌️  关系管理系统运行正常")
        print()
    



    def chat_with_agent(self, agent_name: str, message: str = None):
        """与Agent对话"""
        with self.error_handler.error_context(
            operation=f'chat_with_agent_{agent_name}',
            category=ErrorCategory.AGENT,
            severity=ErrorSeverity.LOW,
            agent_name=agent_name,
            message_length=len(message) if message else 0
        ):
            self.chat_handler.chat_with_agent(self.agents, agent_name, message)
    
    def move_agent(self, agent_name: str, location: str):
        """移动Agent"""
        with self.error_handler.error_context(
            operation=f'move_agent_{agent_name}_to_{location}',
            category=ErrorCategory.AGENT,
            severity=ErrorSeverity.MEDIUM,
            agent_name=agent_name,
            target_location=location
        ):
            # 获取当前位置
            current_location = None
            if agent_name in self.agents:
                current_location = getattr(self.agents[agent_name], 'location', '家')
            
            # 执行移动
            success = self.agent_manager.move_agent(
                self.agents, self.buildings, self.behavior_manager, agent_name, location
            )
            
            # 如果移动成功，保存移动事件
            if success and current_location and current_location != location:
                movement_task = {
                    'type': 'movement',
                    'agent_name': agent_name,
                    'old_location': current_location,
                    'new_location': location,
                    'reason': 'user_command',  # 用户手动移动
                    'timestamp': datetime.now().isoformat()
                }
            self.thread_manager.add_memory_task(movement_task)
        
        return success
    
    def toggle_auto_simulation(self):
        """切换自动模拟"""
        self.simulation_engine.toggle_auto_simulation()
    
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
            # 简化日志：只在调试模式下输出详细信息
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔄 开始异步处理交互: {interaction_data.get('agent1_name')} ↔ {interaction_data.get('agent2_name')}")
            
            # 更新社交网络
            relationship_info = self.thread_manager.safe_social_update(
                self.behavior_manager,
                interaction_data['agent1_name'],
                interaction_data['agent2_name'],
                interaction_data['interaction_type'],
                interaction_data.get('context', {})
            )
            
            # 只在有重要变化时输出日志
            if relationship_info and relationship_info.get('level_changed', False):
                logger.info(f"📊 关系等级变化: {interaction_data.get('agent1_name')} ↔ {interaction_data.get('agent2_name')} -> {relationship_info.get('new_level')}")
            
            # 定期保存社交网络数据
            if not hasattr(self, '_last_social_save_time'):
                self._last_social_save_time = time.time()
            
            # 每5分钟保存一次社交网络数据
            current_time = time.time()
            if current_time - self._last_social_save_time > 300:  # 5分钟 = 300秒
                self.behavior_manager.save_social_network_to_file()
                self._last_social_save_time = current_time
                logger.debug("🗄️ 定期保存社交网络数据完成")
            
            # 保存交互记录
            memory_task = {
                'type': 'interaction',
                'data': {
                    **interaction_data,
                    'relationship_info': relationship_info
                }
            }
            
            # 简化日志：只在调试模式下输出详细信息
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"💾 准备保存交互记录到向量数据库...")
            
            self.thread_manager.add_memory_task(memory_task)
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"✅ 交互记录任务已添加到内存队列")
                
        except Exception as e:
            logger.error(f"异步处理交互数据失败: {e}")
            import traceback
            traceback.print_exc()
    
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
        try:
            agent1_name = data.get('agent1_name')
            agent2_name = data.get('agent2_name')
            interaction_type = data.get('interaction_type', 'unknown')
            
            logger.info(f"🗄️ 开始保存交互到向量数据库: {agent1_name} ↔ {agent2_name} ({interaction_type})")
            
            # 简化日志：只在调试模式下输出详细信息
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🗄️ 保存交互: {agent1_name} ↔ {agent2_name} ({interaction_type})")
            
            context = data.get('context', {})
            relationship_info = data.get('relationship_info', {})
            
            if not agent1_name or not agent2_name:
                logger.warning("保存交互时缺少Agent名称信息")
                return
            
            # 构建交互内容描述
            interaction_content = f"{agent1_name}与{agent2_name}进行了{interaction_type}交互"
            
            # 添加上下文信息
            if context:
                location = context.get('location', '未知位置')
                interaction_content += f"，地点：{location}"
                
                if 'message' in context:
                    interaction_content += f"，内容：{context['message'][:50]}"
            
            # 添加关系变化信息
            if relationship_info:
                relationship_change = relationship_info.get('relationship_change', 0)
                if relationship_change != 0:
                    direction = "提升" if relationship_change > 0 else "下降"
                    interaction_content += f"，关系{direction}{abs(relationship_change):.2f}"
            
            # 计算交互重要性
            importance = 0.6  # 基础重要性
            if interaction_type in ['conflict', 'argument']:
                importance = 0.8  # 冲突类交互更重要
            elif interaction_type in ['deep_talk', 'emotional_support']:
                importance = 0.9  # 深度交流更重要
            elif interaction_type in ['greeting', 'casual_chat']:
                importance = 0.4  # 简单问候重要性较低
            
            # 保存到两个Agent的记忆中
            saved_count = 0
            for agent_name in [agent1_name, agent2_name]:
                # 确保使用正确的Agent名字查找
                if agent_name in self.agents and hasattr(self.agents[agent_name], 'real_agent'):
                    agent = self.agents[agent_name].real_agent
                    if hasattr(agent, 'memory_manager'):
                        # 简化日志：只在调试模式下输出详细信息
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"🗂️ 保存到{agent_name}记忆库: {agent.memory_manager.collection_name}")
                        
                        memory_id = agent.memory_manager.add_memory(
                            content=interaction_content,
                            memory_type='social_interaction',
                            base_importance=importance,
                            metadata={
                                'interaction_type': interaction_type,
                                'participants': [agent1_name, agent2_name],
                                'other_agent': agent2_name if agent_name == agent1_name else agent1_name,
                                'location': context.get('location', '未知'),
                                'relationship_change': relationship_info.get('relationship_change', 0),
                                'relationship_score': relationship_info.get('new_score', 0),
                                'timestamp': datetime.now().isoformat(),
                                'interaction_context': 'agent_to_agent'
                            }
                        )
                        
                        if memory_id:
                            if logger.isEnabledFor(logging.DEBUG):
                                logger.debug(f"✅ 成功保存到{agent_name}记忆库: {memory_id}")
                            saved_count += 1
                        else:
                            logger.error(f"❌ 保存到{agent_name}记忆库失败")
                    else:
                        logger.warning(f"⚠️ {agent_name}没有memory_manager")
                else:
                    logger.warning(f"⚠️ {agent_name}没有real_agent")
            
            # 只在保存成功时输出简要日志
            if saved_count > 0:
                logger.info(f"✅ 完成保存交互记录: {agent1_name} ↔ {agent2_name}")
            
        except Exception as e:
            logger.error(f"❌ 保存交互到向量数据库失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_movement_to_vector_db(self, **data):
        """保存移动事件到向量数据库"""
        try:
            agent_name = data.get('agent_name')
            old_location = data.get('old_location', '未知')
            new_location = data.get('new_location', '未知')
            timestamp = data.get('timestamp', datetime.now().isoformat())
            reason = data.get('reason', 'autonomous_movement')  # 移动原因
            
            if not agent_name:
                logger.warning("保存移动事件时缺少Agent名称")
                return
            
            # 构建移动事件描述
            movement_content = f"从{old_location}移动到{new_location}"
            
            # 添加移动原因
            reason_descriptions = {
                'user_command': '用户指令',
                'autonomous_movement': '自主移动',
                'social_interaction': '社交需求',
                'work_requirement': '工作需要',
                'random_exploration': '随机探索',
                'following_schedule': '按照日程'
            }
            
            if reason in reason_descriptions:
                movement_content += f"（{reason_descriptions[reason]}）"
            
            # 计算移动重要性（根据移动类型和位置）
            importance = 0.3  # 基础重要性
            
            # 特殊位置的移动更重要
            important_locations = ['医院', '办公室', '家']
            if new_location in important_locations or old_location in important_locations:
                importance = 0.5
            
            # 用户指令的移动重要性更高
            if reason == 'user_command':
                importance = 0.7
            
            # 保存到Agent的记忆中
            if agent_name in self.agents and hasattr(self.agents[agent_name], 'real_agent'):
                agent = self.agents[agent_name].real_agent
                if hasattr(agent, 'memory_manager'):
                    agent.memory_manager.add_memory(
                        content=movement_content,
                        memory_type='movement',
                        base_importance=importance,
                        metadata={
                            'movement_type': 'location_change',
                            'old_location': old_location,
                            'new_location': new_location,
                            'movement_reason': reason,
                            'timestamp': timestamp,
                            'movement_context': 'spatial_navigation'
                        }
                    )
            
            logger.debug(f"已保存{agent_name}的移动事件({old_location}→{new_location})到向量数据库")
            
        except Exception as e:
            logger.warning(f"保存移动事件到向量数据库失败: {e}")
    
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
            # 先保存社交网络
            social_saved = self.behavior_manager.save_social_network_to_file()
            
            # 再保存其他系统数据
            system_data = self.get_system_data_for_persistence()
            system_saved = self.persistence_manager.save_system_state(system_data)
            
            if social_saved and system_saved:
                print(f"{TerminalColors.GREEN}💾 系统状态保存成功！{TerminalColors.END}")
                logger.info("手动保存系统状态成功")
            else:
                print(f"{TerminalColors.RED}❌ 系统状态保存失败{TerminalColors.END}")
                logger.error("手动保存系统状态失败")
            
            return social_saved and system_saved
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 保存过程中发生异常: {e}{TerminalColors.END}")
            logger.error(f"手动保存系统状态异常: {e}")
    
    def show_persistence_status(self):
        """显示持久化状态 - 委托给状态显示器"""
        self.status_display.show_persistence_status(
            self.persistence_manager,
            self.vector_optimizer,
            self.memory_manager
        )

    def show_system_health(self):
        """显示系统健康状态 - 委托给状态显示器"""
        self.status_display.show_system_health(self.error_handler)
    
    def show_comprehensive_stats(self):
        """显示综合统计信息"""
        try:
            print(f"\n{TerminalColors.CYAN}📊 === 小镇综合统计信息 === {TerminalColors.END}")
            
            # Agent 统计
            print(f"\n{TerminalColors.YELLOW}👥 Agent 统计：{TerminalColors.END}")
            agent_count = len(self.agents)
            print(f"  • 总 Agent 数量: {agent_count}")
            
            # 按类型统计 Agents
            agent_types = {}
            for agent in self.agents.values():
                agent_type = getattr(agent, 'profession', '未知')  # 使用 profession 而不是 agent_type
                agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
            
            if agent_types:
                print(f"  • 按类型分布:")
                for agent_type, count in agent_types.items():
                    print(f"    - {agent_type}: {count}")
            
            # 位置统计
            locations = {}
            for agent in self.agents.values():
                location = getattr(agent, 'location', '未知')  # 使用 location 而不是 current_location
                locations[location] = locations.get(location, 0) + 1
            
            if locations:
                print(f"  • 位置分布:")
                for location, count in locations.items():
                    print(f"    - {location}: {count}")
            
            # 社交网络统计
            print(f"\n{TerminalColors.YELLOW}🤝 社交网络统计：{TerminalColors.END}")
            total_relationships = 0
            relationship_levels = {'敌对': 0, '冷淡': 0, '中性': 0, '友好': 0, '亲密': 0}
            
            for agent in self.agents.values():
                if hasattr(agent, 'relationships'):
                    for other_agent, level in agent.relationships.items():
                        if other_agent in self.agents:
                            total_relationships += 1
                            if level < 20:
                                relationship_levels['敌对'] += 1
                            elif level < 40:
                                relationship_levels['冷淡'] += 1
                            elif level < 60:
                                relationship_levels['中性'] += 1
                            elif level < 80:
                                relationship_levels['友好'] += 1
                            else:
                                relationship_levels['亲密'] += 1
            
            # 避免重复计算（A->B 和 B->A）
            total_relationships //= 2
            for key in relationship_levels:
                relationship_levels[key] //= 2
            
            print(f"  • 总关系数: {total_relationships}")
            print(f"  • 关系质量分布:")
            for level, count in relationship_levels.items():
                if count > 0:
                    print(f"    - {level}: {count}")
            
            # 系统性能统计
            print(f"\n{TerminalColors.YELLOW}⚡ 系统性能：{TerminalColors.END}")
            
            # 内存使用统计
            try:
                if hasattr(self, 'memory_manager'):
                    memory_stats = self.memory_manager.get_memory_statistics()
                    print(f"  • 记忆系统:")
                    print(f"    - 总记忆条目: {memory_stats.get('total_memories', 0)}")
                    print(f"    - 缓存命中率: {memory_stats.get('cache_hit_rate', 0):.1%}")
                    print(f"    - 内存使用: {memory_stats.get('memory_usage_mb', 0):.1f} MB")
                else:
                    print(f"  • 记忆系统: 未初始化")
            except Exception as e:
                print(f"    - 记忆统计获取失败: {e}")
            
            # 数据持久化统计
            try:
                persistence_stats = self.persistence_manager.get_system_statistics()
                print(f"  • 数据存储:")
                print(f"    - 缓存文件: {persistence_stats.get('cache_files', 0)} 个")
                print(f"    - 交互记录: {persistence_stats.get('interaction_files', 0)} 个")
                print(f"    - 数据大小: {persistence_stats.get('total_data_size_mb', 0)} MB")
            except Exception as e:
                print(f"    - 存储统计获取失败: {e}")
            
            # 错误统计简要版
            try:
                error_stats = self.error_handler.get_error_statistics()
                total_errors = error_stats.get('total_errors', 0)
                health = error_stats.get('system_health', 'unknown')
                health_color = TerminalColors.GREEN if health == 'healthy' else TerminalColors.YELLOW if health == 'warning' else TerminalColors.RED
                
                print(f"  • 系统健康: {health_color}{health}{TerminalColors.END}")
                print(f"  • 总错误数: {total_errors}")
            except Exception as e:
                print(f"  • 健康状态获取失败: {e}")
            
            # 系统运行时间和自动模式状态
            print(f"\n{TerminalColors.YELLOW}🏃 运行状态：{TerminalColors.END}")
            auto_sim_enabled = getattr(self.simulation_engine, 'auto_simulation', False) if hasattr(self, 'simulation_engine') else False
            print(f"  • 自动模拟: {'✅ 启用' if auto_sim_enabled else '❌ 禁用'}")
            print(f"  • 系统状态: {'🟢 运行中' if self.running else '🔴 已停止'}")
            
            print(f"\n{TerminalColors.CYAN}💡 提示: 使用 'stats <类型>' 查看详细统计 (system/errors/memory/agents/social){TerminalColors.END}")
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取综合统计失败: {e}{TerminalColors.END}")
            logger.error(f"显示综合统计失败: {e}")
    
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
    
    def show_system_history(self):
        """显示系统历史记录"""
        try:
            print(f"\n{TerminalColors.CYAN}📜 === 系统历史记录 === {TerminalColors.END}")
            
            # 显示最近的聊天记录
            if hasattr(self, 'chat_history') and self.chat_history:
                print(f"\n{TerminalColors.YELLOW}💬 最近聊天 (最多5条):{TerminalColors.END}")
                recent_chats = self.chat_history[-5:] if len(self.chat_history) > 5 else self.chat_history
                for i, chat in enumerate(recent_chats, 1):
                    agent_name = chat.get('agent_name', '未知')
                    user_msg = chat.get('user_message', '')[:30]
                    agent_msg = chat.get('agent_response', '')[:30]
                    timestamp = chat.get('timestamp', '')[:19]
                    print(f"  {i}. [{timestamp}] {agent_name}")
                    print(f"     用户: {user_msg}...")
                    print(f"     回应: {agent_msg}...")
            else:
                print(f"\n{TerminalColors.YELLOW}💬 聊天记录: 暂无{TerminalColors.END}")
            
            # 显示交互历史
            if hasattr(self.behavior_manager, 'interaction_history'):
                interactions = self.behavior_manager.interaction_history
                if interactions:
                    print(f"\n{TerminalColors.YELLOW}🤝 最近交互 (最多5条):{TerminalColors.END}")
                    recent_interactions = interactions[-5:] if len(interactions) > 5 else interactions
                    for i, interaction in enumerate(recent_interactions, 1):
                        agent1 = interaction.get('agent1', '未知')
                        agent2 = interaction.get('agent2', '未知')
                        action = interaction.get('interaction_type', '未知')
                        location = interaction.get('location', '未知')
                        print(f"  {i}. {agent1} ↔ {agent2}: {action} ({location})")
                else:
                    print(f"\n{TerminalColors.YELLOW}🤝 交互记录: 暂无{TerminalColors.END}")
            else:
                print(f"\n{TerminalColors.YELLOW}🤝 交互记录: 暂无{TerminalColors.END}")
            
            print(f"\n{TerminalColors.CYAN}💡 提示: 使用 'history <类型>' 查看详细历史 (chat/interactions/movements){TerminalColors.END}")
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取系统历史失败: {e}{TerminalColors.END}")
            logger.error(f"显示系统历史失败: {e}")
    
    def show_chat_history(self):
        """显示聊天历史"""
        try:
            print(f"\n{TerminalColors.CYAN}💬 === 聊天历史记录 === {TerminalColors.END}")
            
            if hasattr(self, 'chat_history') and self.chat_history:
                print(f"总聊天记录: {len(self.chat_history)} 条")
                
                # 显示最近10条记录
                recent_chats = self.chat_history[-10:] if len(self.chat_history) > 10 else self.chat_history
                
                for i, chat in enumerate(recent_chats, 1):
                    agent_name = chat.get('agent_name', '未知')
                    user_msg = chat.get('user_message', '')
                    agent_msg = chat.get('agent_response', '')
                    timestamp = chat.get('timestamp', '')[:19]
                    
                    print(f"\n--- 对话 #{len(self.chat_history)-len(recent_chats)+i} ---")
                    print(f"🕐 时间: {timestamp}")
                    print(f"👤 对象: {agent_name}")
                    print(f"💭 用户: {user_msg}")
                    print(f"🤖 回应: {agent_msg}")
                
                if len(self.chat_history) > 10:
                    print(f"\n{TerminalColors.YELLOW}... 还有 {len(self.chat_history)-10} 条更早的记录{TerminalColors.END}")
            else:
                print(f"暂无聊天记录")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取聊天历史失败: {e}{TerminalColors.END}")
            logger.error(f"显示聊天历史失败: {e}")
    
    def show_interaction_history(self):
        """显示交互历史"""
        try:
            print(f"\n{TerminalColors.CYAN}🤝 === 交互历史记录 === {TerminalColors.END}")
            
            if hasattr(self.behavior_manager, 'interaction_history'):
                interactions = self.behavior_manager.interaction_history
                if interactions:
                    print(f"总交互记录: {len(interactions)} 条")
                    
                    # 显示最近15条
                    recent_interactions = interactions[-15:] if len(interactions) > 15 else interactions
                    
                    for i, interaction in enumerate(recent_interactions, 1):
                        agent1 = interaction.get('agent1', '未知')
                        agent2 = interaction.get('agent2', '未知')
                        action = interaction.get('interaction_type', '未知')
                        location = interaction.get('location', '未知')
                        timestamp = interaction.get('timestamp', '')[:19]
                        outcome = interaction.get('outcome', '成功')
                        
                        print(f"{i:2d}. [{timestamp}] {agent1} ↔ {agent2}")
                        print(f"    📍 {location} | 🎭 {action} | 📊 {outcome}")
                    
                    if len(interactions) > 15:
                        print(f"\n{TerminalColors.YELLOW}... 还有 {len(interactions)-15} 条更早的记录{TerminalColors.END}")
                else:
                    print(f"暂无交互记录")
            else:
                print(f"交互历史系统未初始化")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取交互历史失败: {e}{TerminalColors.END}")
            logger.error(f"显示交互历史失败: {e}")
    
    def show_movement_history(self):
        """显示移动历史"""
        try:
            print(f"\n{TerminalColors.CYAN}🚶 === 移动历史记录 === {TerminalColors.END}")
            
            # 从持久化管理器获取移动记录
            try:
                movement_data = self.persistence_manager.load_component_data('movements')
                if movement_data and 'movements' in movement_data:
                    movements = movement_data['movements']
                    print(f"总移动记录: {len(movements)} 条")
                    
                    # 显示最近10条
                    recent_movements = movements[-10:] if len(movements) > 10 else movements
                    
                    for i, movement in enumerate(recent_movements, 1):
                        agent_name = movement.get('agent_name', '未知')
                        old_loc = movement.get('old_location', '未知')
                        new_loc = movement.get('new_location', '未知')
                        reason = movement.get('reason', '未知')
                        timestamp = movement.get('timestamp', '')[:19]
                        
                        print(f"{i:2d}. [{timestamp}] {agent_name}")
                        print(f"    🏃 {old_loc} → {new_loc} ({reason})")
                    
                    if len(movements) > 10:
                        print(f"\n{TerminalColors.YELLOW}... 还有 {len(movements)-10} 条更早的记录{TerminalColors.END}")
                else:
                    print(f"暂无移动记录")
            except Exception:
                print(f"暂无移动记录")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取移动历史失败: {e}{TerminalColors.END}")
            logger.error(f"显示移动历史失败: {e}")
    
    def show_recent_events(self):
        """显示最近事件"""
        try:
            print(f"\n{TerminalColors.CYAN}🎉 === 最近事件 === {TerminalColors.END}")
            
            # 收集各种事件
            events = []
            
            # 聊天事件
            if hasattr(self, 'chat_history') and self.chat_history:
                for chat in self.chat_history[-5:]:
                    events.append({
                        'type': '💬 聊天',
                        'description': f"用户与{chat.get('agent_name', '未知')}对话",
                        'timestamp': chat.get('timestamp', ''),
                        'priority': 2
                    })
            
            # 交互事件
            if hasattr(self.behavior_manager, 'interaction_history'):
                interactions = self.behavior_manager.interaction_history
                for interaction in interactions[-5:]:
                    events.append({
                        'type': '🤝 交互',
                        'description': f"{interaction.get('agent1', '未知')}与{interaction.get('agent2', '未知')}进行{interaction.get('interaction_type', '未知')}",
                        'timestamp': interaction.get('timestamp', ''),
                        'priority': 3
                    })
            
            # 系统事件（如果有错误记录）
            try:
                recent_errors = self.error_handler.get_recent_errors(3)
                for error in recent_errors:
                    events.append({
                        'type': '⚠️ 系统',
                        'description': f"{error.get('operation', '未知操作')}出现{error.get('severity', '未知')}错误",
                        'timestamp': error.get('timestamp', ''),
                        'priority': 1
                    })
            except Exception:
                pass
            
            if events:
                # 按时间排序
                events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                print(f"最近事件 (最多15条):")
                for i, event in enumerate(events[:15], 1):
                    timestamp = event.get('timestamp', '')[:19]
                    event_type = event.get('type', '未知')
                    description = event.get('description', '无描述')
                    
                    print(f"{i:2d}. [{timestamp}] {event_type}")
                    print(f"    {description}")
                
                if len(events) > 15:
                    print(f"\n{TerminalColors.YELLOW}... 还有 {len(events)-15} 个更早的事件{TerminalColors.END}")
            else:
                print(f"暂无最近事件")
            
            print(f"\n{TerminalColors.CYAN}💡 提示: 使用 'event create' 创建自定义事件{TerminalColors.END}")
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取最近事件失败: {e}{TerminalColors.END}")
            logger.error(f"显示最近事件失败: {e}")
    
    def create_event(self, event_type: str = 'custom'):
        """创建事件"""
        try:
            print(f"\n{TerminalColors.CYAN}🎉 创建事件{TerminalColors.END}")
            
            if event_type == 'meeting':
                # 创建聚会事件
                print(f"🎪 正在创建小镇聚会事件...")
                self._create_meeting_event()
            elif event_type == 'conflict':
                # 创建冲突事件
                print(f"⚔️ 正在创建冲突事件...")
                self._create_conflict_event()
            elif event_type == 'celebration':
                # 创建庆祝事件
                print(f"🎊 正在创建庆祝事件...")
                self._create_celebration_event()
            else:
                # 创建自定义事件
                print(f"✨ 正在创建自定义事件...")
                self._create_custom_event()
            
            print(f"{TerminalColors.GREEN}✅ 事件创建完成！{TerminalColors.END}")
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 创建事件失败: {e}{TerminalColors.END}")
            logger.error(f"创建事件失败: {e}")
    
    def _create_meeting_event(self):
        """创建聚会事件"""
        import random
        # 随机选择地点
        locations = ['咖啡厅', '公园', '图书馆']
        location = random.choice(locations)
        
        # 移动部分Agent到聚会地点
        available_agents = list(self.agents.keys())
        if len(available_agents) >= 2:
            selected_agents = random.sample(available_agents, min(3, len(available_agents)))
            for agent_name in selected_agents:
                self.move_agent(agent_name, location)
            
            print(f"📍 聚会地点: {location}")
            print(f"👥 参与者: {', '.join(selected_agents)}")
    
    def _create_conflict_event(self):
        """创建冲突事件"""
        import random
        
        agents = list(self.agents.keys())
        if len(agents) >= 2:
            # 随机选择两个Agent
            agent1, agent2 = random.sample(agents, 2)
            
            # 获取当前关系值
            current_relationship = self.behavior_manager.get_relationship_strength(agent1, agent2)
            
            # 简单的冲突逻辑
            conflict_topics = [
                '工作方式的分歧',
                '对小镇发展的不同看法',
                '生活理念的差异'
            ]
            topic = random.choice(conflict_topics)
            
            print(f"⚔️ 冲突事件发生!")
            print(f"👥 冲突双方: {agent1} vs {agent2}")
            print(f"🎭 冲突话题: {topic}")
            print(f"� 当前关系: {current_relationship}")
            
            # 降低关系强度
            self.behavior_manager.update_social_network(
                agent1, agent2, 'argument',
                {'location': 'artificial_conflict', 'topic': topic}
            )
            
            print(f"� 关系受到影响")
        else:
            print("⚠️ 需要至少2个Agent才能创建冲突")
        
        return None
    
    def _create_celebration_event(self):
        """创建庆祝事件"""
        import random
        # 创建积极的社区事件
        celebration_types = ['生日派对', '工作成功庆祝', '友谊纪念', '技能展示']
        celebration = random.choice(celebration_types)
        
        # 提升所有Agent的心情
        for agent in self.agents.values():
            if hasattr(agent, 'mood'):
                current_mood = getattr(agent, 'mood', 50)
                setattr(agent, 'mood', min(100, current_mood + 10))
        
        print(f"🎊 庆祝类型: {celebration}")
        print(f"😊 所有居民心情得到提升！")
    
    def _create_custom_event(self):
        """创建自定义事件"""
        import random
        events = [
            "小镇来了新居民",
            "天气特别好，大家都想出门",
            "图书馆举办读书分享会",
            "咖啡厅推出新口味咖啡",
            "公园里发现了有趣的东西"
        ]
        event = random.choice(events)
        print(f"✨ 事件: {event}")
    
    def clear_event_history(self):
        """清除事件历史"""
        try:
            # 清除聊天历史
            if hasattr(self, 'chat_history'):
                self.chat_history.clear()
            
            # 清除交互历史
            if hasattr(self.behavior_manager, 'interaction_history'):
                self.behavior_manager.interaction_history.clear()
            
            print(f"{TerminalColors.GREEN}✅ 事件历史已清除{TerminalColors.END}")
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 清除事件历史失败: {e}{TerminalColors.END}")
            logger.error(f"清除事件历史失败: {e}")

    def shutdown(self):
        """安全关闭系统"""
        try:
            logger.info("开始关闭系统...")
            self.running = False
            if hasattr(self, 'simulation_engine'):
                self.simulation_engine.auto_simulation = False
                self.simulation_engine.running = False
                logger.info("自动模拟已停止")
            print(f"{TerminalColors.YELLOW}💾 正在快速保存关键数据...{TerminalColors.END}")
            try:
                quick_data = {
                    'agents': {name: {'location': getattr(agent, 'location', '家')} for name, agent in self.agents.items()},
                    'social_network': getattr(self.behavior_manager, 'social_network', {}),
                    'config': {'auto_simulation': False, 'last_shutdown': datetime.now().isoformat()}
                }
                self.persistence_manager.save_system_state(quick_data, quick_mode=True)
            except Exception as e:
                logger.warning(f"快速保存失败: {e}")
            components_to_close = [
                ('smart_cleanup_manager', 2.0),
                ('memory_cleaner', 2.0),
                ('persistence_manager', 1.0),
                ('error_handler', 1.0),
                ('thread_manager', 3.0)
            ]
            for component_name, _ in components_to_close:
                if hasattr(self, component_name):
                    comp = getattr(self, component_name)
                    if hasattr(comp, 'shutdown'):
                        try:
                            comp.shutdown()
                        except Exception as e:
                            logger.warning(f"关闭组件 {component_name} 失败: {e}")
            print(f"{TerminalColors.GREEN}✅ 系统已安全关闭{TerminalColors.END}")
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 关闭系统时出错: {e}{TerminalColors.END}")
            logger.error(f"关闭系统失败: {e}")


def main():
    """命令行主入口"""
    town = TerminalTownRefactored()

    HELP_TEXT = f"""
{TerminalColors.CYAN}可用命令:{TerminalColors.END}
  help                      显示帮助
  map                       显示地图
  agents                    显示所有Agent状态
  social [basic|adv]        显示社交网络(默认basic, adv=高级)
  chat <Agent> <内容>       与Agent聊天
  move <Agent> <地点>       移动Agent到地点
  auto                      切换自动模拟开/关
  stats                     显示综合统计
  history [chat|inter|move] 查看历史 (默认概览)
  events                    查看最近事件
  event <type>              创建事件(meeting/conflict/celebration/custom)
  mem                       查看内存状态
  vec                       查看向量数据库状态
  optimize                  执行向量库优化
  cleanup [normal|vector|all|emergency] 内存清理
  save                      手动保存系统状态
  exit / quit               退出程序
"""
    print(HELP_TEXT)

    while town.running:
        try:
            cmd = input(f"{TerminalColors.YELLOW}🧭 指令>{TerminalColors.END} ").strip()
            if not cmd:
                continue
            if cmd in ("exit", "quit", "q"):
                town.shutdown()
                break
            if cmd == "help":
                print(HELP_TEXT)
                continue
            if cmd == "map":
                town.show_map(); continue
            if cmd == "agents":
                town.show_agents_status(); continue
            if cmd.startswith("social"):
                parts = cmd.split()
                mode = 'advanced' if len(parts) > 1 and parts[1] in ('adv','advanced') else 'basic'
                town.show_social_network('advanced' if mode=='advanced' else 'basic'); continue
            if cmd.startswith("chat "):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    print("格式: chat <Agent名字> <内容>"); continue
                agent, message = parts[1], parts[2]
                town.chat_with_agent(agent, message); continue
            if cmd.startswith("move "):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    print("格式: move <Agent名字> <地点>"); continue
                agent, loc = parts[1], parts[2]
                ok = town.move_agent(agent, loc)
                if ok:
                    print(f"✅ 已移动 {agent} 到 {loc}")
                else:
                    print(f"❌ 移动失败 (检查名字/地点)")
                continue
            if cmd == "auto":
                town.toggle_auto_simulation(); continue
            if cmd.startswith("stats"):
                town.show_comprehensive_stats(); continue
            if cmd.startswith("history"):
                parts = cmd.split()
                if len(parts)==1:
                    town.show_system_history()
                else:
                    t = parts[1]
                    if t.startswith('chat'): town.show_chat_history()
                    elif t.startswith('inter'): town.show_interaction_history()
                    elif t.startswith('move'): town.show_movement_history()
                    else: town.show_system_history()
                continue
            if cmd == "events":
                town.show_recent_events(); continue
            if cmd.startswith("event"):
                parts = cmd.split()
                etype = parts[1] if len(parts)>1 else 'custom'
                town.create_event(etype); continue
            if cmd == "mem":
                town.show_memory_status(); continue
            if cmd == "vec":
                town.show_vector_database_status(); continue
            if cmd == "optimize":
                town.optimize_vector_database(); continue
            if cmd.startswith("cleanup"):
                parts = cmd.split()
                ctype = parts[1] if len(parts)>1 else 'normal'
                town.cleanup_memory(ctype); continue
            if cmd == "save":
                town.save_system_state(); continue
            print("未知命令, 输入 help 查看可用命令")
        except KeyboardInterrupt:
            print("\n收到中断信号，正在关闭...")
            town.shutdown()
            break
        except EOFError:
            print("\nEOF，退出...")
            town.shutdown()
            break
        except Exception as e:
            print(f"{TerminalColors.RED}命令执行出错: {e}{TerminalColors.END}")
            logger.exception("命令执行出错")


if __name__ == "__main__":
    main()
