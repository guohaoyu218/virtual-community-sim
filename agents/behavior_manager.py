"""
AI Agent行为管理器
管理Agent的复杂行为逻辑、社交网络和群体动态
"""

import random
import time
import json
import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

# 添加配置路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.relationship_config import (
    RELATIONSHIP_LEVELS, INTERACTION_EFFECTS, RELATIONSHIP_DECAY,
    PERSONALITY_MODIFIERS, PROFESSION_COMPATIBILITY, LOCATION_EFFECTS,
    RELATIONSHIP_CHANGE_MESSAGES, get_relationship_level, 
    calculate_interaction_effect
)

logger = logging.getLogger(__name__)

class AgentBehaviorManager:
    """Agent行为管理器"""
    
    def __init__(self):
        self.social_network = {}  # 社交网络图
        self.group_activities = []  # 群体活动
        self.town_events = []  # 小镇事件
        self.agent_schedules = {}  # Agent日程安排
        self.location_popularity = {}  # 地点热度
        self.conversation_topics = self._init_conversation_topics()
        
    def _init_conversation_topics(self) -> Dict[str, List[str]]:
        """初始化对话话题"""
        return {
            'casual': [
                "今天天气不错啊", "最近过得怎么样", "这个地方真不错",
                "你最近在忙什么", "有什么新鲜事吗", "周末有什么计划"
            ],
            'professional': [
                "工作上最近有什么挑战", "你对这个领域的看法如何",
                "最近学到了什么新东西", "有什么好的工作建议吗"
            ],
            'personal': [
                "你的兴趣爱好是什么", "最近读了什么好书",
                "有什么让你开心的事", "你的梦想是什么"
            ],
            'community': [
                "小镇最近的变化真大", "我们应该组织一个活动",
                "这里的人都很友善", "你觉得这里还需要什么改进"
            ]
        }
    
    def update_social_network(self, agent1_name: str, agent2_name: str, 
                             interaction_type: str, context: dict = None) -> dict:
        """
        更新社交网络 - 详细版本
        返回详细的关系变化信息
        """
        # 确保两个Agent都在网络中
        if agent1_name not in self.social_network:
            self.social_network[agent1_name] = {}
        if agent2_name not in self.social_network:
            self.social_network[agent2_name] = {}
        
        # 获取当前关系强度
        old_strength = self.social_network[agent1_name].get(agent2_name, 50)
        old_level = get_relationship_level(old_strength)
        
        # 构建互动条件
        conditions = {}
        if context:
            # 检查各种条件
            if context.get('same_location'):
                conditions['同地点'] = True
            if context.get('same_profession'):
                conditions['相同职业'] = True
            if context.get('first_interaction'):
                conditions['首次交流'] = True
            if context.get('private_location'):
                conditions['私密场所'] = True
            if old_strength >= 60:
                conditions['高关系基础'] = True
        
        # 计算关系变化
        change, effect_details = calculate_interaction_effect(interaction_type, conditions)
        
        # 应用专业相性修正 - 负面互动限制修正幅度
        if context and 'agent1_profession' in context and 'agent2_profession' in context:
            prof1 = context['agent1_profession']
            prof2 = context['agent2_profession']
            if prof1 in PROFESSION_COMPATIBILITY and prof2 in PROFESSION_COMPATIBILITY[prof1]:
                compatibility = PROFESSION_COMPATIBILITY[prof1][prof2]
                if compatibility != 1.0:
                    # 负面互动限制修正幅度，避免过度抵消
                    if change < 0 and compatibility > 1.0:
                        # 负面互动时，好的职业相性最多减少10%的扣分
                        compatibility = max(0.9, compatibility)
                    change = int(change * compatibility)
                    effect_details += f" | 职业相性: ×{compatibility}"
        
        # 应用地点加成 - 负面互动限制修正幅度
        if context and 'location' in context:
            location = context['location']
            if location in LOCATION_EFFECTS:
                location_effect = LOCATION_EFFECTS[location]
                if interaction_type in location_effect:
                    modifier = location_effect[interaction_type]
                    # 负面互动时，地点加成最多减少20%的扣分
                    if change < 0 and modifier > 1.0:
                        modifier = max(0.8, modifier)
                    change = int(change * modifier)
                    effect_details += f" | 地点加成({location}): ×{modifier}"
        
        # 计算新的关系强度
        new_strength = max(0, min(100, old_strength + change))
        new_level = get_relationship_level(new_strength)
        
        # 更新关系
        self.social_network[agent1_name][agent2_name] = new_strength
        self.social_network[agent2_name][agent1_name] = new_strength
        
        # 准备返回信息
        result = {
            'old_strength': old_strength,
            'new_strength': new_strength,
            'change': change,
            'old_level': old_level,
            'new_level': new_level,
            'level_changed': old_level != new_level,
            'effect_details': effect_details,
            'relationship_emoji': RELATIONSHIP_LEVELS[new_level]['emoji'],
            'relationship_desc': RELATIONSHIP_LEVELS[new_level]['description']
        }
        
        # 添加等级变化消息
        if result['level_changed']:
            if new_strength > old_strength:
                change_key = f"{old_level}→{new_level}"
                if change_key in RELATIONSHIP_CHANGE_MESSAGES['升级']:
                    result['level_change_message'] = RELATIONSHIP_CHANGE_MESSAGES['升级'][change_key]
            else:
                change_key = f"{old_level}→{new_level}"
                if change_key in RELATIONSHIP_CHANGE_MESSAGES['降级']:
                    result['level_change_message'] = RELATIONSHIP_CHANGE_MESSAGES['降级'][change_key]
        
        logger.debug(f"关系更新: {agent1_name} ↔ {agent2_name}: {old_strength}→{new_strength} ({effect_details})")
        
        return result
    
    def get_relationship_strength(self, agent1_name: str, agent2_name: str) -> int:
        """获取两个Agent的关系强度"""
        return self.social_network.get(agent1_name, {}).get(agent2_name, 50)
    
    def apply_relationship_decay(self):
        """应用关系衰减 - 模拟时间流逝对关系的影响"""
        if not RELATIONSHIP_DECAY.get('enabled', True):
            return
        
        current_time = datetime.now()
        
        # 检查是否需要应用衰减（每10分钟一次，更频繁）
        if not hasattr(self, '_last_decay_time'):
            self._last_decay_time = current_time
            return
        
        time_diff = current_time - self._last_decay_time
        if time_diff.total_seconds() < 600:  # 10分钟 = 600秒
            return
        
        self._last_decay_time = current_time
        
        # 计算衰减间隔（模拟游戏时间流逝）
        decay_factor = time_diff.total_seconds() / 86400  # 转换为天数
        
        # 添加随机衰减事件，增加关系下降的可能性
        random_decay_chance = 0.3  # 30%概率触发额外衰减
        
        for agent1_name in self.social_network:
            for agent2_name in self.social_network[agent1_name]:
                if agent1_name >= agent2_name:  # 避免重复处理
                    continue
                
                current_strength = self.social_network[agent1_name][agent2_name]
                if current_strength <= RELATIONSHIP_DECAY['min_threshold']:
                    continue  # 已经是最低值，不再衰减
                
                # 根据关系等级确定衰减率
                current_level = get_relationship_level(current_strength)
                decay_rate = RELATIONSHIP_DECAY['decay_intervals'].get(current_level, 0.5)
                
                # 计算基础衰减量
                decay_amount = RELATIONSHIP_DECAY['daily_decay'] * decay_rate * decay_factor
                
                # 随机衰减事件
                if random.random() < random_decay_chance:
                    # 随机衰减1-3点
                    random_decay = random.randint(1, 3)
                    decay_amount += random_decay
                    
                    # 记录随机衰减
                    logger.debug(f"随机衰减: {agent1_name} ↔ {agent2_name}: +{random_decay}")
                
                # 应用衰减
                new_strength = max(RELATIONSHIP_DECAY['min_threshold'], 
                                 current_strength - decay_amount)
                
                if new_strength != current_strength:
                    # 更新关系强度
                    self.social_network[agent1_name][agent2_name] = int(new_strength)
                    self.social_network[agent2_name][agent1_name] = int(new_strength)
                    
                    # 记录衰减日志
                    if decay_amount > 0.1:  # 只记录明显的衰减
                        logger.debug(f"关系衰减: {agent1_name} ↔ {agent2_name}: "
                                   f"{current_strength:.1f} → {new_strength:.1f} "
                                   f"(衰减: {decay_amount:.2f})")
    
    def suggest_conversation_topic(self, agent1_name: str, agent2_name: str, 
                                 agent1_prof: str, agent2_prof: str) -> str:
        """建议对话话题"""
        relationship = self.get_relationship_strength(agent1_name, agent2_name)
        
        # 根据关系强度选择话题类型
        if relationship < 30:
            topic_type = 'casual'
        elif relationship < 70:
            if random.random() < 0.5:
                topic_type = 'professional'
            else:
                topic_type = 'casual'
        else:
            topic_type = random.choice(['personal', 'community', 'professional'])
        
        # 职业相关话题
        if agent1_prof == agent2_prof and random.random() < 0.3:
            topic_type = 'professional'
        
        return random.choice(self.conversation_topics[topic_type])
    
    def plan_group_activity(self, agents: List, activity_type: str = None) -> Optional[Dict]:
        """规划群体活动"""
        if len(agents) < 2:
            return None
        
        activities = [
            {
                'name': '小镇聚会',
                'location': '公园',
                'duration': 30,
                'description': '大家聚在一起聊天，分享最近的生活'
            },
            {
                'name': '读书会',
                'location': '图书馆', 
                'duration': 45,
                'description': '讨论最近读的书籍和学习心得'
            },
            {
                'name': '咖啡时光',
                'location': '咖啡厅',
                'duration': 20,
                'description': '在轻松的氛围中交流想法'
            },
            {
                'name': '技术交流',
                'location': '办公室',
                'duration': 35,
                'description': '分享工作经验和专业知识'
            }
        ]
        
        if activity_type:
            activity = next((a for a in activities if a['name'] == activity_type), None)
        else:
            activity = random.choice(activities)
        
        if activity:
            activity['participants'] = [agent.name for agent in agents]
            activity['start_time'] = datetime.now()
            self.group_activities.append(activity)
            
            logger.info(f"规划群体活动: {activity['name']} 在 {activity['location']}")
        
        return activity
    
    def generate_agent_schedule(self, agent, time_of_day: str) -> List[Dict]:
        """为Agent生成日程安排"""
        profession = agent.profession
        
        schedules = {
            '程序员': {
                'morning': [
                    {'time': '9:00', 'activity': '在咖啡厅喝咖啡思考', 'location': '咖啡厅'},
                    {'time': '9:30', 'activity': '开始编程工作', 'location': '办公室'}
                ],
                'afternoon': [
                    {'time': '14:00', 'activity': '代码审查和调试', 'location': '办公室'},
                    {'time': '16:00', 'activity': '在公园散步思考算法', 'location': '公园'}
                ],
                'evening': [
                    {'time': '18:00', 'activity': '回家休息', 'location': '家'},
                    {'time': '20:00', 'activity': '阅读技术文档', 'location': '图书馆'}
                ]
            },
            '艺术家': {
                'morning': [
                    {'time': '8:00', 'activity': '在公园寻找灵感', 'location': '公园'},
                    {'time': '10:00', 'activity': '在咖啡厅素描', 'location': '咖啡厅'}
                ],
                'afternoon': [
                    {'time': '14:00', 'activity': '回家创作', 'location': '家'},
                    {'time': '16:00', 'activity': '整理作品', 'location': '家'}
                ],
                'evening': [
                    {'time': '18:00', 'activity': '在咖啡厅展示作品', 'location': '咖啡厅'},
                    {'time': '20:00', 'activity': '参加艺术交流', 'location': '公园'}
                ]
            },
            '老师': {
                'morning': [
                    {'time': '8:00', 'activity': '在图书馆备课', 'location': '图书馆'},
                    {'time': '9:00', 'activity': '准备教学材料', 'location': '办公室'}
                ],
                'afternoon': [
                    {'time': '14:00', 'activity': '批改作业', 'location': '办公室'},
                    {'time': '16:00', 'activity': '与同事讨论', 'location': '咖啡厅'}
                ],
                'evening': [
                    {'time': '18:00', 'activity': '回家休息', 'location': '家'},
                    {'time': '19:00', 'activity': '阅读教育书籍', 'location': '图书馆'}
                ]
            }
        }
        
        # 为其他职业生成通用日程
        if profession not in schedules:
            schedules[profession] = {
                'morning': [
                    {'time': '9:00', 'activity': '开始工作', 'location': '办公室'},
                    {'time': '10:30', 'activity': '短暂休息', 'location': '咖啡厅'}
                ],
                'afternoon': [
                    {'time': '14:00', 'activity': '继续工作', 'location': '办公室'},
                    {'time': '16:00', 'activity': '户外活动', 'location': '公园'}
                ],
                'evening': [
                    {'time': '18:00', 'activity': '回家', 'location': '家'},
                    {'time': '20:00', 'activity': '个人时间', 'location': '家'}
                ]
            }
        
        return schedules[profession].get(time_of_day, [])
    
    def decide_agent_action(self, agent, other_agents: List, current_time: str) -> Dict:
        """为Agent决定下一步行动"""
        # 获取agent的属性，支持不同的agent类型
        if hasattr(agent, 'current_location'):
            current_location = agent.current_location
        elif hasattr(agent, 'location'):
            current_location = agent.location
        else:
            current_location = '家'
            
        if hasattr(agent, 'energy_level'):
            energy_level = agent.energy_level
        elif hasattr(agent, 'energy'):
            energy_level = agent.energy
        else:
            energy_level = 80
            
        if hasattr(agent, 'current_mood'):
            current_mood = agent.current_mood
        elif hasattr(agent, 'mood'):
            current_mood = agent.mood
        else:
            current_mood = '平静'
        
        action = {
            'type': 'idle',
            'description': '闲逛',
            'location': current_location,
            'priority': 1
        }
        
        # 检查是否有预定活动
        current_schedule = self.get_current_schedule_item(agent, current_time)
        if current_schedule:
            action.update({
                'type': 'scheduled',
                'description': current_schedule['activity'],
                'location': current_schedule['location'],
                'priority': 5
            })
            return action
        
        # 社交倾向
        nearby_agents = self.find_nearby_agents(agent, other_agents)
        if nearby_agents and random.random() < 0.3:  # 30%概率社交
            target_agent = self.choose_social_target(agent, nearby_agents)
            if target_agent:
                action.update({
                    'type': 'social',
                    'description': f'与{target_agent.name}交流',
                    'target': target_agent,
                    'priority': 4
                })
                return action
        
        # 基于心情和能量的行为
        if energy_level < 30:
            action.update({
                'type': 'rest',
                'description': '寻找地方休息',
                'location': '家',
                'priority': 6
            })
        elif current_mood in ['无聊', '沮丧']:
            action.update({
                'type': 'entertainment',
                'description': '寻找有趣的活动',
                'location': '公园',
                'priority': 3
            })
        elif current_mood in ['兴奋', '快乐']:
            action.update({
                'type': 'exploration',
                'description': '探索新地方',
                'location': random.choice(['咖啡厅', '图书馆', '公园']),
                'priority': 2
            })
        else:
            # 随机移动到推荐地点
            recommendations = self.get_location_recommendations(agent)
            if recommendations:
                action.update({
                    'type': 'move',
                    'description': '寻找合适的地方',
                    'location': random.choice(recommendations),
                    'priority': 2
                })
        
        return action
    
    def find_nearby_agents(self, agent, other_agents: List) -> List:
        """找到附近的Agent"""
        nearby = []
        
        # 获取当前agent的位置
        if hasattr(agent, 'current_location'):
            agent_location = agent.current_location
        elif hasattr(agent, 'location'):
            agent_location = agent.location
        else:
            agent_location = '家'
        
        # 获取agent的名字
        agent_name = getattr(agent, 'name', 'Unknown')
        
        for other_agent in other_agents:
            # 获取其他agent的位置和名字
            if hasattr(other_agent, 'current_location'):
                other_location = other_agent.current_location
            elif hasattr(other_agent, 'location'):
                other_location = other_agent.location
            else:
                other_location = '家'
                
            other_name = getattr(other_agent, 'name', 'Unknown')
            
            if (other_name != agent_name and other_location == agent_location):
                nearby.append(other_agent)
        return nearby
    
    def choose_social_target(self, agent, nearby_agents: List):
        """选择社交目标"""
        if not nearby_agents:
            return None
        
        # 根据关系强度加权选择
        weights = []
        for other_agent in nearby_agents:
            relationship = self.get_relationship_strength(agent.name, other_agent.name)
            # 关系越好，互动概率越高
            weight = relationship / 100.0 + 0.1  # 最小权重0.1
            weights.append(weight)
        
        # 加权随机选择
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(nearby_agents)
        
        rand_val = random.uniform(0, total_weight)
        current_weight = 0
        
        for i, weight in enumerate(weights):
            current_weight += weight
            if rand_val <= current_weight:
                return nearby_agents[i]
        
        return nearby_agents[-1]  # 备选
    
    def get_current_schedule_item(self, agent, current_time: str) -> Optional[Dict]:
        """获取当前时间的日程项"""
        # 简化实现，可以根据实际时间匹配
        if agent.name not in self.agent_schedules:
            return None
        
        schedule = self.agent_schedules[agent.name]
        # 这里可以实现更复杂的时间匹配逻辑
        return None
    
    def create_town_event(self, event_type: str = None) -> Dict:
        """创建小镇事件"""
        events = [
            {
                'name': '小镇集市',
                'description': '每周的集市开始了，大家都来买东西',
                'location': '公园',
                'duration': 60,
                'effect': '增加公园的人气'
            },
            {
                'name': '技术讲座',
                'description': '在图书馆举办的技术分享会',
                'location': '图书馆',
                'duration': 45,
                'effect': '程序员和学生更愿意参加'
            },
            {
                'name': '艺术展览',
                'description': '本地艺术家的作品展示',
                'location': '咖啡厅',
                'duration': 90,
                'effect': '艺术家们聚集交流'
            },
            {
                'name': '健康检查日',
                'description': '免费的健康检查活动',
                'location': '办公室',
                'duration': 120,
                'effect': '大家关注健康话题'
            }
        ]
        
        if event_type:
            event = next((e for e in events if e['name'] == event_type), None)
        else:
            event = random.choice(events)
        
        if event:
            event['start_time'] = datetime.now()
            event['active'] = True
            self.town_events.append(event)
            logger.info(f"小镇事件开始: {event['name']} 在 {event['location']}")
        
        return event
    
    def update_location_popularity(self, location: str, change: int):
        """更新地点热度"""
        current_pop = self.location_popularity.get(location, 50)
        new_pop = max(0, min(100, current_pop + change))
        self.location_popularity[location] = new_pop
        
    def get_location_recommendations(self, agent) -> List[str]:
        """为Agent推荐地点"""
        recommendations = []
        
        # 获取agent的职业
        if hasattr(agent, 'profession'):
            profession = agent.profession
        elif hasattr(agent, 'real_agent') and hasattr(agent.real_agent, 'profession'):
            profession = agent.real_agent.profession
        else:
            profession = '其他'
        
        # 基于职业的偏好
        profession_preferences = {
            '程序员': ['办公室', '咖啡厅', '图书馆'],
            '艺术家': ['公园', '咖啡厅', '家'],
            '老师': ['图书馆', '办公室', '咖啡厅'],
            '学生': ['图书馆', '咖啡厅', '公园'],
            '商人': ['办公室', '咖啡厅'],
            '退休人员': ['公园', '家', '咖啡厅'],
            '医生': ['医院', '办公室', '咖啡厅'],
            '厨师': ['餐厅', '咖啡厅', '家'],
            '机械师': ['修理店', '办公室', '家']
        }
        
        preferred = profession_preferences.get(profession, ['公园', '咖啡厅'])
        
        # 考虑地点热度
        for location in preferred:
            popularity = self.location_popularity.get(location, 50)
            if popularity > 60:  # 热门地点
                recommendations.append(location)
        
        # 如果没有热门地点，返回职业偏好
        if not recommendations:
            recommendations = preferred
        
        return recommendations
    
    def generate_interaction_context(self, agent1, agent2) -> str:
        """生成互动背景信息"""
        relationship = self.get_relationship_strength(agent1.name, agent2.name)
        location = agent1.current_location
        
        context_parts = []
        
        # 关系背景
        if relationship > 80:
            context_parts.append(f"{agent1.name}和{agent2.name}是很好的朋友")
        elif relationship > 60:
            context_parts.append(f"{agent1.name}和{agent2.name}比较熟悉")
        elif relationship < 30:
            context_parts.append(f"{agent1.name}和{agent2.name}还不太熟")
        else:
            context_parts.append(f"{agent1.name}和{agent2.name}是普通朋友")
        
        # 地点背景
        context_parts.append(f"他们在{location}相遇")
        
        # 时间背景
        current_time = datetime.now().strftime("%H:%M")
        context_parts.append(f"现在是{current_time}")
        
        # 活动背景
        active_events = [e for e in self.town_events if e.get('active', False)]
        if active_events:
            event = active_events[0]
            if event['location'] == location:
                context_parts.append(f"正值{event['name']}活动期间")
        
        return "，".join(context_parts)

# 全局行为管理器实例
behavior_manager = AgentBehaviorManager()
