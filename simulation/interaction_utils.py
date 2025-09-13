"""
社交交互工具模块
提供统一的交互逻辑，避免代码重复
"""

import random
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class InteractionUtils:
    """统一的交互工具类"""
    
    @staticmethod
    def choose_interaction_type(relationship_strength: int) -> str:
        """根据关系强度选择互动类型"""
        if relationship_strength >= 70:
            # 关系很好：65%友好，20%中性，15%负面
            weights = [('friendly_chat', 65), ('casual_meeting', 20), ('misunderstanding', 12), ('argument', 3)]
        elif relationship_strength >= 50:
            # 关系一般：50%友好，25%中性，25%负面
            weights = [('friendly_chat', 50), ('casual_meeting', 25), ('misunderstanding', 18), ('argument', 7)]
        elif relationship_strength >= 30:
            # 关系较差：30%友好，30%中性，40%负面
            weights = [('friendly_chat', 30), ('casual_meeting', 30), ('misunderstanding', 25), ('argument', 15)]
        else:
            # 关系很差：40%友好，25%中性，35%负面
            weights = [('friendly_chat', 40), ('casual_meeting', 25), ('misunderstanding', 15), ('argument', 20)]

        # 根据权重随机选择 - 支持两种算法
        total_weight = sum(weight for _, weight in weights)
        random_num = random.randint(1, total_weight)
        
        cumulative_weight = 0
        for interaction_type, weight in weights:
            cumulative_weight += weight
            if random_num <= cumulative_weight:
                return interaction_type
        
        return 'casual_meeting'  # 默认返回
    
    @staticmethod
    def generate_interaction_prompt(agent_name: str, other_name: str, topic: str, interaction_type: str) -> str:
        """生成交互提示词"""
        if interaction_type == 'friendly_chat':
            return f"{other_name}说：'{topic}'，友好积极地回应："
        elif interaction_type == 'casual_meeting':
            return f"{other_name}说：'{topic}'，简短中性地回应："
        elif interaction_type == 'misunderstanding':
            return f"{other_name}说：'{topic}'，表示困惑不解，不要赞同："
        elif interaction_type == 'argument':
            return f"{other_name}说：'{topic}'，表示不同意和反对："
        else:
            return f"{other_name}说：'{topic}'，简短回应："
    
    @staticmethod
    def get_interaction_color(interaction_type: str) -> str:
        """获取交互类型对应的颜色"""
        from display.terminal_colors import TerminalColors
        
        color_map = {
            'friendly_chat': TerminalColors.GREEN,
            'casual_meeting': TerminalColors.CYAN,
            'misunderstanding': TerminalColors.YELLOW,
            'argument': TerminalColors.RED,
            'deep_conversation': TerminalColors.BLUE,
            'collaboration': TerminalColors.MAGENTA
        }
        return color_map.get(interaction_type, TerminalColors.WHITE)
    
    @staticmethod
    def get_interaction_icon(interaction_type: str) -> str:
        """获取交互类型对应的图标"""
        icon_map = {
            'friendly_chat': "💫",
            'casual_meeting': "💭",
            'misunderstanding': "❓",
            'argument': "💥",
            'deep_conversation': "🧠",
            'collaboration': "🤝"
        }
        return icon_map.get(interaction_type, "🔄")
