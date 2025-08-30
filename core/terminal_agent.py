"""
TerminalAgent类 - 终端版Agent包装器
将AI Agent包装成适合终端交互的格式
"""

import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TerminalAgent:
    """终端版Agent包装器"""
    
    def __init__(self, real_agent, color: str, emoji: str):
        """
        初始化TerminalAgent
        
        Args:
            real_agent: 实际的AI Agent实例
            color: 终端显示颜色
            emoji: Agent的表情符号
        """
        self.real_agent = real_agent
        self.color = color
        self.emoji = emoji
        
        # 从real_agent获取基础信息
        self.location = getattr(real_agent, 'current_location', '家')
        self.profession = getattr(real_agent, 'profession', '通用')
        self.name = getattr(real_agent, 'name', 'Unknown')
        
        # 状态信息
        self._last_action = '闲逛'
        self._interaction_count = 0
        
        logger.debug(f"初始化TerminalAgent: {self.name} ({self.profession})")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取Agent状态
        
        Returns:
            包含位置、心情、能量等信息的字典
        """
        try:
            return {
                'location': self.location,
                'mood': getattr(self.real_agent, 'current_mood', '平静'),
                'energy': getattr(self.real_agent, 'energy_level', 80),
                'current_action': getattr(self.real_agent, 'current_action', self._last_action),
                'profession': self.profession,
                'name': self.name,
                'interaction_count': self._interaction_count
            }
        except Exception as e:
            logger.error(f"获取{self.name}状态失败: {e}")
            return {
                'location': self.location,
                'mood': '未知',
                'energy': 50,
                'current_action': '状态获取失败',
                'profession': self.profession,
                'name': self.name,
                'interaction_count': self._interaction_count
            }
    
    def respond(self, message: str) -> str:
        """
        响应用户消息
        
        Args:
            message: 用户输入的消息
            
        Returns:
            Agent的回应
        """
        try:
            self._interaction_count += 1
            self._last_action = '与用户对话'
            
            # 调用真实Agent的响应方法
            if hasattr(self.real_agent, 'think_and_respond'):
                response = self.real_agent.think_and_respond(message)
            elif hasattr(self.real_agent, 'respond'):
                response = self.real_agent.respond(message)
            else:
                response = self._generate_fallback_response(message)
            
            return response
            
        except Exception as e:
            logger.error(f"{self.name}响应消息失败: {e}")
            return f"*{self.name}遇到了一些技术问题，暂时无法很好地回应*"
    
    def think_and_respond(self, situation: str) -> str:
        """
        思考并回应特定情况
        
        Args:
            situation: 当前情况描述
            
        Returns:
            Agent的思考结果
        """
        try:
            self._last_action = '思考中'
            
            if hasattr(self.real_agent, 'think_and_respond'):
                return self.real_agent.think_and_respond(situation)
            else:
                return self._generate_thinking_response(situation)
                
        except Exception as e:
            logger.error(f"{self.name}思考失败: {e}")
            return self._generate_fallback_thinking()
    
    def interact_with(self, other_agent: 'TerminalAgent') -> str:
        """
        与其他Agent交互
        
        Args:
            other_agent: 另一个TerminalAgent实例
            
        Returns:
            交互时的话语
        """
        try:
            self._interaction_count += 1
            self._last_action = f'与{other_agent.name}交流'
            
            # 根据关系和情境生成交互内容
            return self._generate_interaction_response(other_agent)
            
        except Exception as e:
            logger.error(f"{self.name}与{other_agent.name}交互失败: {e}")
            return f"*{self.name}想要与{other_agent.name}交流，但似乎有些紧张*"
    
    def update_status(self):
        """更新状态信息"""
        try:
            if hasattr(self.real_agent, 'update_status'):
                self.real_agent.update_status()
            
            # 同步位置信息
            if hasattr(self.real_agent, 'current_location'):
                self.location = self.real_agent.current_location
                
        except Exception as e:
            logger.error(f"更新{self.name}状态失败: {e}")
    
    def move_to(self, new_location: str):
        """
        移动到新位置
        
        Args:
            new_location: 新的位置名称
        """
        try:
            old_location = self.location
            self.location = new_location
            
            # 更新真实Agent的位置
            if hasattr(self.real_agent, 'current_location'):
                self.real_agent.current_location = new_location
            
            self._last_action = f'从{old_location}移动到{new_location}'
            
            logger.debug(f"{self.name}从{old_location}移动到{new_location}")
            
        except Exception as e:
            logger.error(f"{self.name}移动失败: {e}")
    
    def _generate_fallback_response(self, message: str) -> str:
        """生成备用回应"""
        fallback_responses = [
            "这是一个很有趣的话题。",
            "我需要想想这个问题。",
            "你说得很有道理。",
            "这让我想到了一些事情。",
            "我觉得这个观点很值得讨论。"
        ]
        return random.choice(fallback_responses)
    
    def _generate_thinking_response(self, situation: str) -> str:
        """生成思考回应"""
        thinking_patterns = [
            f"在{self.location}，我觉得{situation}...",
            f"作为一个{self.profession}，我认为{situation}...",
            f"关于{situation}，我有一些想法...",
            f"在这种情况下，我觉得应该..."
        ]
        return random.choice(thinking_patterns)
    
    def _generate_fallback_thinking(self) -> str:
        """生成备用思考内容"""
        thoughts = [
            f"我在{self.location}安静地思考着生活...",
            f"作为{self.profession}，我在思考工作中的一些问题...",
            "我在思考最近发生的一些事情...",
            "这个地方让我感到很平静，适合思考..."
        ]
        return random.choice(thoughts)
    
    def _generate_interaction_response(self, other_agent: 'TerminalAgent') -> str:
        """生成与其他Agent的交互回应"""
        # 基础问候语
        basic_greetings = [
            f"嗨，{other_agent.name}！",
            f"在{self.location}遇到你真巧！",
            "你好！今天过得怎么样？",
            "有什么新鲜事吗？"
        ]
        
        # 职业相关的交流
        if self.profession == other_agent.profession:
            professional_greetings = [
                f"同行！我们都是{self.profession}呢。",
                f"作为{self.profession}，你最近工作怎么样？",
                f"遇到同行真开心！{self.profession}的工作确实有意思。"
            ]
            return random.choice(professional_greetings)
        
        # 地点相关的交流
        location_greetings = [
            f"在{self.location}遇到你真是太好了！",
            f"你也喜欢来{self.location}吗？",
            f"{self.location}真是个不错的地方。"
        ]
        
        # 随机选择一种类型的问候
        all_greetings = basic_greetings + location_greetings
        return random.choice(all_greetings)
    
    def get_mood_emoji(self) -> str:
        """根据心情获取表情符号"""
        mood = getattr(self.real_agent, 'current_mood', '平静')
        mood_emojis = {
            '开心': '😊',
            '高兴': '😄', 
            '平静': '😌',
            '思考': '🤔',
            '疲惫': '😴',
            '兴奋': '🤩',
            '焦虑': '😰',
            '满意': '😇',
            '好奇': '🧐'
        }
        return mood_emojis.get(mood, '😊')
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.emoji} {self.name} ({self.profession}) - {self.location}"
    
    def __repr__(self) -> str:
        """详细表示"""
        return f"TerminalAgent(name='{self.name}', profession='{self.profession}', location='{self.location}')"
