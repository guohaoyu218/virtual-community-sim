"""
高级关系动态管理器
=================

解决社交关系只升不降的问题，增加真实的冲突和负面互动
"""

import random
import time
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConflictScenario:
    """冲突场景"""
    topic: str
    intensity: str  # 'mild', 'moderate', 'strong'
    duration: int   # 持续轮数
    participants: List[str]
    trigger: str
    resolution_chance: float

class AdvancedRelationshipManager:
    """高级关系动态管理器"""
    
    def __init__(self):
        self.active_conflicts = {}  # agent对 -> ConflictScenario
        self.relationship_tensions = {}  # agent对 -> tension_level
        self.last_interaction_times = {}  # agent对 -> timestamp
        self.conflict_probability = 0.15  # 基础冲突概率
        
        # 初始化冲突模板
        self.conflict_templates = self._init_conflict_templates()
        
    def _init_conflict_templates(self) -> List[Dict]:
        """初始化冲突模板"""
        return [
            {
                'topic': '工作方式的分歧',
                'triggers': [
                    'Alex倾向于直接高效解决问题',
                    'Sarah强调需要耐心教导过程',
                    'Anna认为要考虑情感因素'
                ],
                'intensity_factors': {
                    'mild': {'duration': 2, 'relationship_impact': -5},
                    'moderate': {'duration': 4, 'relationship_impact': -15},
                    'strong': {'duration': 6, 'relationship_impact': -25}
                }
            },
            {
                'topic': '小镇发展方向的争论',
                'triggers': [
                    '是否应该引入更多科技元素',
                    '传统文化保护vs现代化发展',
                    '社区活动的组织方式'
                ],
                'intensity_factors': {
                    'mild': {'duration': 3, 'relationship_impact': -8},
                    'moderate': {'duration': 5, 'relationship_impact': -18},
                    'strong': {'duration': 7, 'relationship_impact': -30}
                }
            },
            {
                'topic': '生活理念的差异',
                'triggers': [
                    '对效率vs享受生活的不同看法',
                    '个人时间vs社交时间的分配',
                    '风险承担vs稳健保守的态度'
                ],
                'intensity_factors': {
                    'mild': {'duration': 2, 'relationship_impact': -6},
                    'moderate': {'duration': 4, 'relationship_impact': -16},
                    'strong': {'duration': 5, 'relationship_impact': -28}
                }
            },
            {
                'topic': '资源分配的不同意见',
                'triggers': [
                    '小镇预算的使用优先级',
                    '公共设施的改进方案',
                    '个人时间和精力的投入'
                ],
                'intensity_factors': {
                    'mild': {'duration': 3, 'relationship_impact': -7},
                    'moderate': {'duration': 5, 'relationship_impact': -17},
                    'strong': {'duration': 6, 'relationship_impact': -27}
                }
            }
        ]
    
    def should_trigger_conflict(self, agent1_name: str, agent2_name: str, 
                               current_relationship: int, interaction_count: int) -> bool:
        """判断是否应该触发冲突"""
        # 基础冲突概率
        base_probability = self.conflict_probability
        
        # 调整因素
        factors = {
            'high_relationship': current_relationship > 70,    # 关系太好容易产生冲突
            'moderate_relationship': 40 < current_relationship < 70,  # 中等关系有分歧
            'frequent_interaction': interaction_count > 5,     # 互动频繁容易摩擦
            'existing_tension': self._get_tension_level(agent1_name, agent2_name) > 0.3,
            'time_factor': self._should_create_drama(),        # 时间因素
        }
        
        # 计算实际概率
        if factors['high_relationship']:
            base_probability *= 1.8  # 关系好的容易产生失望
        elif factors['moderate_relationship']:
            base_probability *= 1.3
        
        if factors['frequent_interaction']:
            base_probability *= 1.5
            
        if factors['existing_tension']:
            base_probability *= 2.0
            
        if factors['time_factor']:
            base_probability *= 1.4
        
        # 限制最大概率
        final_probability = min(base_probability, 0.35)
        
        trigger_conflict = random.random() < final_probability
        
        if trigger_conflict:
            logger.info(f"触发冲突: {agent1_name} vs {agent2_name} (概率: {final_probability:.2f})")
        
        return trigger_conflict
    
    def create_conflict(self, agent1_name: str, agent2_name: str, 
                       current_relationship: int) -> ConflictScenario:
        """创建冲突场景"""
        # 选择冲突模板
        template = random.choice(self.conflict_templates)
        
        # 确定冲突强度
        if current_relationship > 70:
            # 关系好的产生强烈失望
            intensity = random.choices(
                ['mild', 'moderate', 'strong'],
                weights=[0.3, 0.5, 0.2]
            )[0]
        elif current_relationship > 40:
            intensity = random.choices(
                ['mild', 'moderate', 'strong'],
                weights=[0.5, 0.4, 0.1]
            )[0]
        else:
            # 关系一般的多是小冲突
            intensity = random.choices(
                ['mild', 'moderate'],
                weights=[0.7, 0.3]
            )[0]
        
        # 创建冲突场景
        scenario = ConflictScenario(
            topic=template['topic'],
            intensity=intensity,
            duration=template['intensity_factors'][intensity]['duration'],
            participants=[agent1_name, agent2_name],
            trigger=random.choice(template['triggers']),
            resolution_chance=self._calculate_resolution_chance(current_relationship, intensity)
        )
        
        # 记录活跃冲突
        pair_key = tuple(sorted([agent1_name, agent2_name]))
        self.active_conflicts[pair_key] = scenario
        
        # 增加关系紧张度
        self._increase_tension(agent1_name, agent2_name, intensity)
        
        logger.info(f"创建冲突: {agent1_name} vs {agent2_name} - {scenario.topic} ({intensity})")
        
        return scenario
    
    def _calculate_resolution_chance(self, relationship: int, intensity: str) -> float:
        """计算冲突解决概率"""
        base_chance = {
            'mild': 0.8,
            'moderate': 0.6,
            'strong': 0.4
        }[intensity]
        
        # 关系越好越容易和解
        relationship_factor = relationship / 100.0
        
        return min(base_chance + relationship_factor * 0.3, 0.95)
    
    def generate_conflict_response(self, agent_name: str, other_agent: str, 
                                 scenario: ConflictScenario, is_initiator: bool) -> str:
        """生成冲突响应"""
        response_templates = {
            'mild': {
                'initiator': [
                    f"我觉得在{scenario.topic}这个问题上，{scenario.trigger}，你怎么看？",
                    f"关于{scenario.topic}，我有些不同的想法。",
                    f"我不太同意这种做法，{scenario.trigger}。"
                ],
                'responder': [
                    "我理解你的观点，但我觉得还有其他角度需要考虑。",
                    "嗯，我可能有些不同的看法。",
                    "这确实是个值得讨论的问题。"
                ]
            },
            'moderate': {
                'initiator': [
                    f"我必须说，在{scenario.topic}上我们的想法差别很大。",
                    f"对不起，但我不能认同这种观点，{scenario.trigger}。",
                    f"我觉得{scenario.topic}的处理方式有问题。"
                ],
                'responder': [
                    "我不同意你的说法，这样做有它的道理。",
                    "我觉得你可能没有考虑到全部情况。", 
                    "我们确实在这个问题上有分歧。"
                ]
            },
            'strong': {
                'initiator': [
                    f"我真的很失望，{scenario.topic}这么重要的事情你却{scenario.trigger}。",
                    f"我完全不能理解你在{scenario.topic}上的做法。",
                    f"关于{scenario.topic}，我必须坚持我的立场。"
                ],
                'responder': [
                    "我很抱歉让你失望，但我有我的理由。",
                    "我觉得你的反应有些过度了。",
                    "我坚持认为我的做法是对的。"
                ]
            }
        }
        
        role = 'initiator' if is_initiator else 'responder'
        templates = response_templates[scenario.intensity][role]
        
        return random.choice(templates)
    
    def update_conflict_progress(self, agent1_name: str, agent2_name: str) -> Optional[Dict]:
        """更新冲突进展"""
        pair_key = tuple(sorted([agent1_name, agent2_name]))
        
        if pair_key not in self.active_conflicts:
            return None
        
        scenario = self.active_conflicts[pair_key]
        scenario.duration -= 1
        
        result = {
            'scenario': scenario,
            'resolved': False,
            'relationship_change': 0
        }
        
        # 检查是否解决
        if scenario.duration <= 0 or random.random() < scenario.resolution_chance:
            # 冲突解决
            result['resolved'] = True
            
            # 计算关系影响
            if random.random() < 0.7:  # 70%概率和解
                result['relationship_change'] = random.randint(3, 8)  # 和解后关系改善
                result['resolution_type'] = 'reconciliation'
            else:  # 30%概率关系受损
                impact = self.conflict_templates[0]['intensity_factors'][scenario.intensity]['relationship_impact']
                result['relationship_change'] = impact // 2  # 减半的负面影响
                result['resolution_type'] = 'damage'
            
            # 移除活跃冲突
            del self.active_conflicts[pair_key]
            
            # 降低紧张度
            self._decrease_tension(agent1_name, agent2_name)
            
            logger.info(f"冲突解决: {agent1_name} vs {agent2_name} - {result['resolution_type']}")
        
        return result
    
    def _get_tension_level(self, agent1_name: str, agent2_name: str) -> float:
        """获取关系紧张度"""
        pair_key = tuple(sorted([agent1_name, agent2_name]))
        return self.relationship_tensions.get(pair_key, 0.0)
    
    def _increase_tension(self, agent1_name: str, agent2_name: str, intensity: str):
        """增加关系紧张度"""
        pair_key = tuple(sorted([agent1_name, agent2_name]))
        
        tension_increase = {
            'mild': 0.2,
            'moderate': 0.4,
            'strong': 0.6
        }[intensity]
        
        current_tension = self.relationship_tensions.get(pair_key, 0.0)
        self.relationship_tensions[pair_key] = min(current_tension + tension_increase, 1.0)
    
    def _decrease_tension(self, agent1_name: str, agent2_name: str):
        """降低关系紧张度"""
        pair_key = tuple(sorted([agent1_name, agent2_name]))
        
        if pair_key in self.relationship_tensions:
            self.relationship_tensions[pair_key] = max(
                self.relationship_tensions[pair_key] - 0.3, 0.0
            )
    
    def _should_create_drama(self) -> bool:
        """时间因素：是否应该制造戏剧性"""
        # 每10分钟增加一次戏剧性的可能性
        current_time = time.time()
        
        # 简单的时间周期检查
        cycle_time = 600  # 10分钟
        in_drama_window = (current_time % cycle_time) < 60  # 每10分钟的前1分钟
        
        return in_drama_window and random.random() < 0.3
    
    def has_active_conflict(self, agent1_name: str, agent2_name: str) -> bool:
        """检查是否有活跃冲突"""
        pair_key = tuple(sorted([agent1_name, agent2_name]))
        return pair_key in self.active_conflicts
    
    def get_conflict_context(self, agent1_name: str, agent2_name: str) -> Optional[str]:
        """获取冲突上下文"""
        pair_key = tuple(sorted([agent1_name, agent2_name]))
        
        if pair_key not in self.active_conflicts:
            return None
        
        scenario = self.active_conflicts[pair_key]
        return f"当前正在就'{scenario.topic}'发生{scenario.intensity}级分歧，原因是{scenario.trigger}"
    
    def apply_natural_decay(self, relationships: Dict) -> Dict[str, int]:
        """应用自然的关系衰减"""
        changes = {}
        current_time = time.time()
        
        for pair_key, last_time in list(self.last_interaction_times.items()):
            if current_time - last_time > 3600:  # 1小时没有互动
                agent1, agent2 = pair_key
                
                # 轻微衰减
                if agent1 in relationships and agent2 in relationships[agent1]:
                    old_value = relationships[agent1][agent2]
                    decay = random.randint(1, 3)
                    new_value = max(old_value - decay, 0)
                    
                    relationships[agent1][agent2] = new_value
                    relationships[agent2][agent1] = new_value
                    
                    changes[f"{agent1}-{agent2}"] = -decay
                    
                    # 更新时间
                    self.last_interaction_times[pair_key] = current_time
        
        return changes

# 全局关系管理器实例
relationship_manager = AdvancedRelationshipManager()
