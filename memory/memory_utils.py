"""
内存管理工具模块
提供统一的内存操作，减少重复代码
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MemoryUtils:
    """统一的内存管理工具类"""
    
    @staticmethod
    def save_interaction_memory(agent, interaction_content: str, interaction_type: str, 
                              participants: list, other_agent: str, location: str, 
                              relationship_change: float = 0, relationship_score: float = 0) -> Optional[str]:
        """保存交互记忆到Agent的记忆库"""
        try:
            if not hasattr(agent, 'memory_manager'):
                logger.warning(f"Agent缺少memory_manager")
                return None
            
            # 计算重要性
            importance = MemoryUtils._calculate_interaction_importance(interaction_type, relationship_change)
            
            memory_id = agent.memory_manager.add_memory(
                content=interaction_content,
                memory_type='social_interaction',
                base_importance=importance,
                metadata={
                    'interaction_type': interaction_type,
                    'participants': participants,
                    'other_agent': other_agent,
                    'location': location,
                    'relationship_change': relationship_change,
                    'relationship_score': relationship_score,
                    'timestamp': datetime.now().isoformat(),
                    'interaction_context': 'agent_to_agent'
                }
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"保存交互记忆失败: {e}")
            return None
    
    @staticmethod
    def save_user_chat_memory(agent, agent_name: str, user_message: str, agent_response: str) -> Optional[str]:
        """保存用户对话记忆"""
        try:
            if not hasattr(agent, 'memory_manager'):
                logger.warning(f"Agent {agent_name} 缺少memory_manager")
                return None
            
            chat_content = f"用户与{agent_name}对话：用户说'{user_message}'，{agent_name}回答'{agent_response}'"
            
            memory_id = agent.memory_manager.add_memory(
                content=chat_content,
                memory_type='user_interaction',
                base_importance=0.8,  # 用户对话通常重要性较高
                metadata={
                    'interaction_type': 'user_chat',
                    'user_message': user_message[:100],
                    'agent_response': agent_response[:100],
                    'timestamp': datetime.now().isoformat(),
                    'response_time': datetime.now().timestamp(),
                    'interaction_context': 'terminal_chat'
                }
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"保存用户对话记忆失败: {e}")
            return None
    
    @staticmethod
    def save_movement_memory(agent, agent_name: str, old_location: str, new_location: str, 
                           reason: str = 'autonomous_movement') -> Optional[str]:
        """保存移动记忆"""
        try:
            if not hasattr(agent, 'memory_manager'):
                logger.warning(f"Agent {agent_name} 缺少memory_manager")
                return None
            
            movement_content = f"从{old_location}移动到{new_location}"
            
            # 添加移动原因描述
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
            
            # 计算移动重要性
            importance = MemoryUtils._calculate_movement_importance(old_location, new_location, reason)
            
            memory_id = agent.memory_manager.add_memory(
                content=movement_content,
                memory_type='movement',
                base_importance=importance,
                metadata={
                    'movement_type': 'location_change',
                    'old_location': old_location,
                    'new_location': new_location,
                    'movement_reason': reason,
                    'timestamp': datetime.now().isoformat(),
                    'movement_context': 'spatial_navigation'
                }
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"保存移动记忆失败: {e}")
            return None
    
    @staticmethod
    def _calculate_interaction_importance(interaction_type: str, relationship_change: float = 0) -> float:
        """计算交互重要性"""
        base_importance = 0.6
        
        # 根据交互类型调整重要性
        if interaction_type in ['conflict', 'argument']:
            base_importance = 0.8
        elif interaction_type in ['deep_talk', 'emotional_support']:
            base_importance = 0.9
        elif interaction_type in ['greeting', 'casual_chat']:
            base_importance = 0.4
        
        # 根据关系变化调整重要性
        if abs(relationship_change) > 10:
            base_importance += 0.1
        
        return min(1.0, base_importance)
    
    @staticmethod
    def _calculate_movement_importance(old_location: str, new_location: str, reason: str) -> float:
        """计算移动重要性"""
        base_importance = 0.3
        
        # 特殊位置的移动更重要
        important_locations = ['医院', '办公室', '家']
        if new_location in important_locations or old_location in important_locations:
            base_importance = 0.5
        
        # 用户指令的移动重要性更高
        if reason == 'user_command':
            base_importance = 0.7
        
        return base_importance
