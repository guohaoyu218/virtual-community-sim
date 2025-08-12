#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏘️ AI Agent虚拟小镇 - 终端交互模式
快速、流畅的命令行界面体验
"""

import os
import sys
import time
import random
import threading
import re
import traceback
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.specific_agents import (AlexProgrammer, EmmaArtist, SarahTeacher, 
                                       DavidBusinessman, LisaStudent, MikeRetired,
                                       JohnDoctor, AnnaChef, TomMechanic)
    from agents.behavior_manager import behavior_manager
    from setup_logging import setup_logging
    import logging
    
    setup_logging()
    logger = logging.getLogger(__name__)
    REAL_AGENTS_AVAILABLE = True
    print("✅ 真实AI Agent系统已加载 (8个Agent)")
except ImportError as e:
    REAL_AGENTS_AVAILABLE = False
    print(f"⚠️  使用简化Agent系统: {e}")

class TerminalColors:
    """终端颜色定义"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    # Agent专用颜色
    ALEX = '\033[94m'    # 蓝色 - 程序员
    EMMA = '\033[95m'    # 紫色 - 艺术家  
    SARAH = '\033[92m'   # 绿色 - 老师

class TerminalTown:
    """终端版AI小镇"""
    
    def __init__(self):
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
        self.auto_simulation = False
        self.simulation_thread = None
        self.running = True
        self.behavior_manager = behavior_manager
        
        self.init_agents()
        
        # 加载持久化数据
        self.load_persistent_data()
        
        self.clear_screen()
        self.show_welcome()
    
    def init_agents(self):
        """初始化AI Agent"""
        if REAL_AGENTS_AVAILABLE:
            try:
                self.agents = {
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
            except Exception as e:
                print(f"❌ AI初始化失败，使用简化版本: {e}")
                self.init_simple_agents()
        else:
            self.init_simple_agents()
    
    def init_simple_agents(self):
        """初始化简化Agent"""
        self.agents = {
            'Alex': SimpleAgent('Alex', '程序员', TerminalColors.ALEX, '👨‍💻'),
            'Emma': SimpleAgent('Emma', '艺术家', TerminalColors.EMMA, '👩‍🎨'),
            'Sarah': SimpleAgent('Sarah', '老师', TerminalColors.SARAH, '👩‍🏫'),
            'David': SimpleAgent('David', '商人', TerminalColors.CYAN, '👨‍💼'),
            'Lisa': SimpleAgent('Lisa', '学生', TerminalColors.YELLOW, '👩‍🎓'),
            'Mike': SimpleAgent('Mike', '退休人员', TerminalColors.BLUE, '👴'),
            'John': SimpleAgent('John', '医生', TerminalColors.GREEN, '👨‍⚕️'),
            'Anna': SimpleAgent('Anna', '厨师', TerminalColors.RED, '👩‍🍳'),
            'Tom': SimpleAgent('Tom', '机械师', TerminalColors.BOLD, '👨‍🔧')
        }
        
        # 设置初始位置
        initial_locations = {
            'Alex': '办公室',
            'Emma': '公园',
            'Sarah': '图书馆',
            'David': '办公室',
            'Lisa': '图书馆',
            'Mike': '公园',
            'John': '医院',
            'Anna': '餐厅',
            'Tom': '修理店'
        }
        
        for name, location in initial_locations.items():
            if name in self.agents:
                self.agents[name].location = location
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_welcome(self):
        """显示欢迎界面"""
        print(f"""
{TerminalColors.BOLD}{TerminalColors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                    🏘️  AI Agent 虚拟小镇                     ║
║                      终端交互模式                             ║
║                                                              ║
║  快速 • 流畅 • 直观的命令行体验                              ║
╚══════════════════════════════════════════════════════════════╝
{TerminalColors.END}

{TerminalColors.GREEN}✨ 欢迎来到AI Agent虚拟小镇！{TerminalColors.END}

{TerminalColors.YELLOW}🎮 可用命令：{TerminalColors.END}
  📍 map          - 查看小镇地图
  👥 agents       - 查看所有Agent状态  
  💬 chat <name>  - 与Agent对话
  🚶 move <name> <place> - 移动Agent
  🤖 auto         - 开启/关闭自动模拟
  
  🧠 智能命令：
  👫 social       - 查看社交网络
  🎪 event        - 创建小镇事件
  🎯 group <location> - 组织群体活动
  📊 stats        - 详细统计信息
  🔥 popular      - 查看热门地点
  
  📊 status       - 查看系统状态
  📜 history      - 查看对话历史
  🆘 help         - 显示帮助
  🚪 quit         - 退出程序

{TerminalColors.CYAN}💡 快速开始：输入 'map' 查看小镇布局，或 'social' 查看Agent关系网络{TerminalColors.END}
""")
    
    def show_map(self):
        """显示小镇地图"""
        print(f"\n{TerminalColors.BOLD}🗺️  小镇地图{TerminalColors.END}")
        print("=" * 50)
        
        # 创建6x6网格
        grid = [['⬜' for _ in range(6)] for _ in range(6)]
        
        # 放置建筑
        for name, building in self.buildings.items():
            x, y = building['x'], building['y']
            grid[y][x] = building['emoji']
        
        # 放置Agent
        agent_positions = {}
        for name, agent in self.agents.items():
            location = agent.location
            if location in self.buildings:
                x, y = self.buildings[location]['x'], self.buildings[location]['y']
                if (x, y) not in agent_positions:
                    agent_positions[(x, y)] = []
                agent_positions[(x, y)].append(f"{agent.color}{agent.emoji}{TerminalColors.END}")
        
        # 显示地图
        for y in range(6):
            row = ""
            for x in range(6):
                if (x, y) in agent_positions:
                    # 显示Agent
                    agents_here = agent_positions[(x, y)]
                    row += agents_here[0] + " "  # 只显示第一个Agent
                else:
                    # 显示建筑或空地
                    row += grid[y][x] + " "
            print(f"  {row}")
        
        print("\n📍 建筑说明:")
        for name, building in self.buildings.items():
            occupants = [f"{self.agents[agent_name].emoji}{agent_name}" 
                        for agent_name in self.agents.keys() 
                        if self.agents[agent_name].location == name]
            occupant_count = len(occupants)
            count_display = f"[{occupant_count}人]" if occupant_count > 0 else "[空]"
            occupant_text = f" {count_display} ({', '.join(occupants)})" if occupants else f" {count_display}"
            print(f"  {building['emoji']} {name}{occupant_text}")
        print()
    
    def show_agents_status(self):
        """显示所有Agent状态"""
        print(f"\n{TerminalColors.BOLD}👥 Agent状态总览{TerminalColors.END}")
        print("=" * 60)
        
        for name, agent in self.agents.items():
            status = agent.get_status()
            print(f"{agent.color}{agent.emoji} {name}{TerminalColors.END}")
            print(f"  📍 位置: {status['location']}")
            print(f"  😊 心情: {status['mood']}")
            print(f"  ⚡ 能量: {status['energy']}%")
            print(f"  🎯 行为: {status['current_action']}")
            
            if hasattr(agent, 'real_agent'):
                print(f"  🧠 类型: 真实AI Agent")
            else:
                print(f"  🤖 类型: 简化Agent")
            print()
    
    def chat_with_agent(self, agent_name: str, message: str = None):
        """与Agent对话"""
        if agent_name not in self.agents:
            print(f"{TerminalColors.RED}❌ 找不到Agent: {agent_name}{TerminalColors.END}")
            print(f"可用的Agent: {', '.join(self.agents.keys())}")
            return
        
        agent = self.agents[agent_name]
        
        print(f"\n{TerminalColors.BOLD}💬 与 {agent.color}{agent.emoji} {agent_name}{TerminalColors.END}{TerminalColors.BOLD} 对话{TerminalColors.END}")
        print("=" * 40)
        print(f"{TerminalColors.CYAN}💡 输入 'exit' 结束对话{TerminalColors.END}\n")
        
        if message:
            # 直接处理传入的消息
            self._process_chat_message(agent, agent_name, message)
        else:
            # 进入对话循环
            while True:
                try:
                    user_input = input(f"{TerminalColors.YELLOW}🧑 你: {TerminalColors.END}").strip()
                    
                    if user_input.lower() in ['exit', 'quit', '退出']:
                        print(f"{TerminalColors.GREEN}👋 对话结束{TerminalColors.END}\n")
                        break
                    
                    if not user_input:
                        continue
                        
                    self._process_chat_message(agent, agent_name, user_input)
                    
                except KeyboardInterrupt:
                    print(f"\n{TerminalColors.GREEN}👋 对话结束{TerminalColors.END}\n")
                    break
                except EOFError:
                    break
    
    def _process_chat_message(self, agent, agent_name: str, message: str):
        """处理聊天消息"""
        start_time = time.time()
        try:
            response = agent.respond(message)
            # 清理用户对话响应
            response = self._clean_response(response)
            end_time = time.time()
            
            print(f"{agent.color}{agent.emoji} {agent_name}: {TerminalColors.END}{response}")
            print(f"{TerminalColors.CYAN}⚡ 响应时间: {end_time - start_time:.2f}秒{TerminalColors.END}\n")
            
            # 记录对话历史
            self.chat_history.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'user': message,
                'agent': agent_name,
                'response': response
            })
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 对话失败: {e}{TerminalColors.END}\n")
    
    def move_agent(self, agent_name: str, location: str):
        """移动Agent"""
        if agent_name not in self.agents:
            print(f"{TerminalColors.RED}❌ 找不到Agent: {agent_name}{TerminalColors.END}")
            return
        
        if location not in self.buildings:
            print(f"{TerminalColors.RED}❌ 找不到地点: {location}{TerminalColors.END}")
            print(f"可用地点: {', '.join(self.buildings.keys())}")
            return
        
        agent = self.agents[agent_name]
        old_location = agent.location
        agent.location = location
        
        # 更新真实Agent的位置
        if hasattr(agent, 'real_agent'):
            agent.real_agent.current_location = location
        
        print(f"{TerminalColors.GREEN}🚶 {agent.emoji} {agent_name} 从 {old_location} 移动到 {location}{TerminalColors.END}")
    
    def toggle_auto_simulation(self):
        """切换自动模拟"""
        self.auto_simulation = not self.auto_simulation
        
        if self.auto_simulation:
            print(f"{TerminalColors.GREEN}🤖 自动模拟已开启！Agent将开始自主行动{TerminalColors.END}")
            self.simulation_thread = threading.Thread(target=self._auto_simulation_loop, daemon=True)
            self.simulation_thread.start()
        else:
            print(f"{TerminalColors.YELLOW}⏸️  自动模拟已暂停{TerminalColors.END}")
    
    def _auto_simulation_loop(self):
        """自动模拟循环"""
        print(f"{TerminalColors.GREEN}🔄 自动模拟循环启动{TerminalColors.END}")
        
        while self.auto_simulation and self.running:
            try:
                # 应用关系衰减
                self.behavior_manager.apply_relationship_decay()
                
                # 显示关系衰减信息（从10分钟改为30分钟一次，与衰减频率保持一致）
                if not hasattr(self, '_last_decay_display') or \
                   (datetime.now() - getattr(self, '_last_decay_display', datetime.now())).total_seconds() > 1800:
                    self._last_decay_display = datetime.now()
                    decay_info = self._get_decay_summary()
                    if decay_info:
                        print(f"{TerminalColors.YELLOW}⏰ 关系衰减提醒: {decay_info}{TerminalColors.END}")
                
                # 随机选择一个Agent进行行动
                agent_names = list(self.agents.keys())
                if not agent_names:
                    print(f"{TerminalColors.RED}❌ 没有可用的Agent{TerminalColors.END}")
                    break
                
                agent_name = random.choice(agent_names)
                agent = self.agents[agent_name]
                
                # 简化的Agent选择显示
                # print(f"{TerminalColors.CYAN}🎯 选择Agent: {agent_name}{TerminalColors.END}")  # 注释掉，减少干扰
                
                # 智能行动选择 - 增加多人讨论，移除独立负面互动
                action_weights = {
                    'social': 40,        # 增加社交权重，让负面互动在社交中自然产生
                    'group_discussion': 20,  # 增加多人讨论
                    'move': 20,
                    'think': 10,
                    'work': 10
                }
                
                # 根据权重选择行动
                actions = []
                for action, weight in action_weights.items():
                    actions.extend([action] * weight)
                action_type = random.choice(actions)
                
                # 在进行社交活动前，确保Agent有合理的地点分布
                if action_type in ['social', 'group_discussion'] and random.random() < 0.3:
                    # 30%概率重新分布Agent位置，增加社交机会
                    self._redistribute_agents_randomly()
                
                if action_type == 'social':
                    # 确保只有同地点的Agent才能对话
                    current_loc = agent.location if hasattr(agent, 'location') else agent.current_location
                    
                    # 找到同地点的其他Agent
                    other_agent_names = [name for name in self.agents.keys() if name != agent_name]
                    agents_same_location = [name for name in other_agent_names 
                                          if self.agents[name].location == current_loc]
                    
                    if not agents_same_location:
                        # 如果当前地点没有其他人，跳过此次社交或让Agent移动
                        if random.random() < 0.5:
                            # 50%概率移动到有人的地点
                            populated_locations = {}
                            for loc_name in self.buildings.keys():
                                agents_in_loc = [name for name in other_agent_names 
                                               if self.agents[name].location == loc_name]
                                if agents_in_loc:
                                    populated_locations[loc_name] = agents_in_loc
                            
                            if populated_locations:
                                new_location = random.choice(list(populated_locations.keys()))
                                agent.location = new_location
                                print(f"\n{TerminalColors.BOLD}━━━ 🚶 寻找伙伴 ━━━{TerminalColors.END}")
                                print(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END}: {current_loc} → {new_location}")
                                print(f"  💭 想找人聊聊")
                                print()
                                current_loc = new_location
                                agents_same_location = populated_locations[new_location]
                            else:
                                continue  # 没有人在任何地方，跳过
                        else:
                            continue  # 跳过此次社交
                    
                    # 现在确保有同地点的对话伙伴
                    target_name = random.choice(agents_same_location)
                    target_agent = self.agents[target_name]
                    
                    # 双重验证：确保两人确实在同一地点
                    target_location = target_agent.location if hasattr(target_agent, 'location') else target_agent.current_location
                    if current_loc != target_location:
                        # 位置不匹配，同步位置
                        target_agent.location = current_loc
                        if hasattr(target_agent, 'real_agent'):
                            target_agent.real_agent.current_location = current_loc
                    
                    # 显示对话标题，明确显示对话双方和位置信息
                    print(f"\n{TerminalColors.BOLD}━━━ 💬 对话交流 ━━━{TerminalColors.END}")
                    print(f"📍 地点: {current_loc}")
                    print(f"👥 参与者: {agent_name} ({current_loc}) ↔ {target_name} ({target_location})")
                    if current_loc != target_location:
                        print(f"   📌 {target_name} 已移动至 {current_loc} 参与对话")
                    
                    # 让Agent自主决定话题 - 完全自然的对话方式
                    topic_prompt = f"在{current_loc}遇到{target_name}，简短地打个招呼或说句话："
                    topic = agent.think_and_respond(topic_prompt)
                    
                    # 清理可能的提示词残留
                    topic = self._clean_response(topic)
                    
                    # 显示A→B对话开始
                    print(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name} → {target_name}{TerminalColors.END}: {topic}")
                    
                    # 目标Agent的自然回应
                    response_prompt = f"{agent_name}说：'{topic}'，简短回应："
                    response = target_agent.think_and_respond(response_prompt)
                    
                    # 清理回应中的提示词残留
                    response = self._clean_response(response)
                    
                    # 根据当前关系和随机因素决定对话结果
                    current_relationship = self.behavior_manager.get_relationship_strength(agent_name, target_name)
                    
                    # 根据关系强度决定对话类型的概率 - 减少负面互动概率，降低关系下降频率
                    if current_relationship >= 70:
                        # 关系很好：80%友好，15%中性，5%负面（从10%降低到5%）
                        interaction_weights = [('friendly_chat', 80), ('casual_meeting', 15), ('misunderstanding', 4), ('argument', 1)]
                    elif current_relationship >= 50:
                        # 关系一般：60%友好，25%中性，15%负面（从20%降低到15%）
                        interaction_weights = [('friendly_chat', 60), ('casual_meeting', 25), ('misunderstanding', 12), ('argument', 3)]
                    elif current_relationship >= 30:
                        # 关系较差：40%友好，35%中性，25%负面（从40%降低到25%）
                        interaction_weights = [('friendly_chat', 40), ('casual_meeting', 35), ('misunderstanding', 20), ('argument', 5)]
                    else:
                        # 关系很差：25%友好，30%中性，45%负面（从65%降低到45%）
                        interaction_weights = [('friendly_chat', 25), ('casual_meeting', 30), ('misunderstanding', 30), ('argument', 15)]
                    
                    # 根据权重随机选择互动类型
                    interaction_types = []
                    for interaction_type, weight in interaction_weights:
                        interaction_types.extend([interaction_type] * weight)
                    chosen_interaction = random.choice(interaction_types)
                    
                    # 根据互动类型生成不同的提示词，确保内容和情感一致
                    if chosen_interaction == 'friendly_chat':
                        response_prompt = f"{agent_name}说：'{topic}'，友好积极地回应："
                        display_color = TerminalColors.GREEN
                    elif chosen_interaction == 'casual_meeting':
                        response_prompt = f"{agent_name}说：'{topic}'，简短中性地回应："
                        display_color = TerminalColors.YELLOW
                    elif chosen_interaction == 'misunderstanding':
                        response_prompt = f"{agent_name}说：'{topic}'，表示困惑不解，不要赞同或支持："
                        display_color = TerminalColors.RED
                    elif chosen_interaction == 'argument':
                        response_prompt = f"{agent_name}说：'{topic}'，表示不同意和反对，坚持自己的观点："
                        display_color = TerminalColors.RED
                    
                    # 让AI根据指定情感生成回应
                    response = target_agent.think_and_respond(response_prompt)
                    response = self._clean_response(response)
                    
                    # 验证负面互动的回复是否真的负面，如果不是则重新生成
                    if chosen_interaction in ['misunderstanding', 'argument']:
                        # 检查回复是否包含负面关键词
                        negative_keywords = ['不同意', '反对', '不对', '错', '不行', '失望', '糟糕', '问题', '麻烦', '困惑', '不理解', '质疑', '批评', '反驳', '我觉得不对', '我不这么认为', '这有问题', '这样不好', '不', '没', '别', '拒绝', '否认', '怀疑', '担心', '忧虑', '不满', '抱怨', '牢骚', '反感', '厌恶', '讨厌', '恨', '愤怒', '生气', '恼火', '烦躁', '焦虑', '紧张', '害怕', '恐惧', '担心', '忧虑', '悲观', '消极', '负面', '不好', '不行', '不对', '错误', '失败', '损失', '伤害', '痛苦', '困难', '麻烦', '复杂', '混乱', '无序', '不稳定', '不确定', '模糊', '不清楚', '不明白', '不理解', '不知道', '不确定', '怀疑', '质疑', '否定', '拒绝', '否认', '反对', '不同意', '不赞同', '不支持', '不喜欢', '不认同', '不欣赏', '不感动', '不启发', '无趣', '不精彩', '不优秀', '不好', '不行', '不对', '错误', '失败', '损失', '伤害', '痛苦', '困难', '麻烦', '复杂', '混乱', '无序', '不稳定', '不确定', '模糊', '不清楚', '不明白', '不理解', '不知道', '不确定', '怀疑', '质疑', '否定', '拒绝', '否认', '反对', '不同意', '不赞同', '不支持', '不喜欢', '不认同', '不欣赏', '不感动', '不启发', '无趣', '不精彩', '不优秀']
                        positive_keywords = ['同意', '赞同', '很好', '不错', '棒', '对', '是的', '有道理', '支持', '喜欢', '认同', '欣赏', '感动', '启发', '有趣', '精彩', '优秀', '太好了', '好', '棒', '美', '对', '是', '有道理', '支持', '喜欢', '认同', '欣赏', '感动', '启发', '有趣', '精彩', '优秀', '太好了', '好', '棒', '美', '对', '是', '有道理', '支持', '喜欢', '认同', '欣赏', '感动', '启发', '有趣', '精彩', '优秀', '太好了']
                        
                        has_negative = any(keyword in response for keyword in negative_keywords)
                        has_positive = any(keyword in response for keyword in positive_keywords)
                        
                        # 如果回复太积极或中性，重新生成更自然的负面回复
                        if has_positive or (not has_negative and not has_positive):
                            if chosen_interaction == 'argument':
                                retry_prompt = f"{agent_name}说：'{topic}'，你坚决不同意，用自然的语言表达反对："
                            elif chosen_interaction == 'misunderstanding':
                                retry_prompt = f"{agent_name}说：'{topic}'，你感到困惑不解，用自然的语言表达质疑："
                            
                            # 重新生成回复
                            response = target_agent.think_and_respond(retry_prompt)
                            response = self._clean_response(response)
                            
                            # 如果重新生成后仍然不够负面，添加自然的前缀
                            has_negative = any(keyword in response for keyword in negative_keywords)
                            if not has_negative:
                                if chosen_interaction == 'argument':
                                    response = f"我不同意，{response}"
                                elif chosen_interaction == 'misunderstanding':
                                    response = f"我不太理解，{response}"
                    
                    # 显示回应
                    print(f"  {target_agent.emoji} {display_color}{target_name} → {agent_name}{TerminalColors.END}: {response}")
                    
                    # 添加A的简短反馈回应，完成双向对话
                    # 负面互动时，所有回复都必须保持负面，不允许缓解气氛
                    if chosen_interaction == 'friendly_chat':
                        feedback_prompt = f"{target_name}回应：'{response}'，表示赞同："
                        feedback_color = TerminalColors.GREEN
                    elif chosen_interaction in ['misunderstanding', 'argument']:
                        # 负面互动时，强制保持负面，不允许缓解气氛
                        feedback_prompt = f"{target_name}回应：'{response}'，坚持负面立场，不要缓解气氛，继续表达不同意见："
                        feedback_color = TerminalColors.RED
                    else:
                        feedback_prompt = f"{target_name}回应：'{response}'，简短回应："
                        feedback_color = TerminalColors.YELLOW
                    
                    feedback = agent.think_and_respond(feedback_prompt)
                    feedback = self._clean_response(feedback)
                    
                    # 同样验证反馈回复的负面性
                    if chosen_interaction in ['misunderstanding', 'argument']:
                        has_negative = any(keyword in feedback for keyword in negative_keywords)
                        has_positive = any(keyword in feedback for keyword in positive_keywords)
                        
                        # 如果反馈太积极或中性，重新生成更自然的负面回复
                        if has_positive or (not has_negative and not has_positive):
                            if chosen_interaction == 'argument':
                                retry_prompt = f"{target_name}回应：'{response}'，你坚持反对立场，用自然的语言继续表达不同意见："
                            elif chosen_interaction == 'misunderstanding':
                                retry_prompt = f"{target_name}回应：'{response}'，你仍然感到困惑，用自然的语言继续表达质疑："
                            
                            # 重新生成反馈
                            feedback = agent.think_and_respond(retry_prompt)
                            feedback = self._clean_response(feedback)
                            
                            # 如果重新生成后仍然不够负面，添加自然的前缀
                            has_negative = any(keyword in feedback for keyword in negative_keywords)
                            if not has_negative:
                                if chosen_interaction == 'argument':
                                    feedback = f"我坚持反对，{feedback}"
                                elif chosen_interaction == 'misunderstanding':
                                    feedback = f"我仍然困惑，{feedback}"
                    
                    # 显示A→B的反馈，完成完整对话循环
                    print(f"  {agent.emoji} {feedback_color}{agent_name} → {target_name}{TerminalColors.END}: {feedback}")
                    
                    # 更新社交网络 - 使用详细的关系系统
                    try:
                        # 构建互动上下文
                        context = {
                            'same_location': True,  # 在同一地点
                            'same_profession': agent.profession == target_agent.profession,
                            'first_interaction': current_relationship <= 50,
                            'location': current_loc,
                            'agent1_profession': agent.profession,
                            'agent2_profession': target_agent.profession,
                            'private_location': current_loc in ['家'],
                        }
                        
                        # 强制确保负面互动类型确实会扣分
                        if chosen_interaction in ['argument', 'misunderstanding', 'disappointment']:
                            # 负面互动强制扣分，不允许被其他因素抵消
                            relationship_info = self.behavior_manager.update_social_network(
                                agent_name, target_name, chosen_interaction, context
                            )
                            # 如果关系变化是正数，强制改为负数，并且增加扣分幅度
                            if relationship_info['change'] > 0:
                                relationship_info['change'] = -abs(relationship_info['change'])
                            # 额外增加负面互动的扣分，确保伤害更深刻
                            if relationship_info['change'] > -5:  # 如果扣分不够多
                                relationship_info['change'] = max(-8, relationship_info['change'] - 3)  # 至少扣8分
                            
                            relationship_info['new_strength'] = max(0, relationship_info['old_strength'] + relationship_info['change'])
                            # 重新计算关系等级
                            import sys
                            import os
                            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                            from config.relationship_config import get_relationship_level
                            relationship_info['new_level'] = get_relationship_level(relationship_info['new_strength'])
                            relationship_info['level_changed'] = relationship_info['old_level'] != relationship_info['new_level']
                        else:
                            # 正常更新关系
                            relationship_info = self.behavior_manager.update_social_network(
                                agent_name, target_name, chosen_interaction, context
                            )
                        
                        # 简化显示关系变化
                        if relationship_info['change'] != 0:
                            change_color = TerminalColors.GREEN if relationship_info['change'] > 0 else TerminalColors.RED
                            change_symbol = "+" if relationship_info['change'] > 0 else ""
                            
                            # 根据互动类型显示不同的图标
                            if chosen_interaction == 'friendly_chat':
                                icon = "💫"
                            elif chosen_interaction == 'casual_meeting':
                                icon = "💭" 
                            elif chosen_interaction == 'misunderstanding':
                                icon = "❓"
                            elif chosen_interaction == 'argument':
                                icon = "💥"
                            else:
                                icon = "🔄"
                            
                            print(f"     {icon} {relationship_info['relationship_emoji']} {relationship_info['new_level']} ({change_color}{change_symbol}{relationship_info['change']}{TerminalColors.END})")
                            
                            # 只在重大等级变化时显示详情
                            if relationship_info.get('level_changed', False):
                                level_color = TerminalColors.GREEN if relationship_info['new_strength'] > relationship_info['old_strength'] else TerminalColors.YELLOW
                                print(f"     {level_color}�� {relationship_info.get('level_change_message', '关系等级发生变化')}{TerminalColors.END}")
                        
                        print()  # 空行分隔
                    except Exception as e:
                        logger.warning(f"更新关系失败: {e}")
                        pass  # 静默处理错误
                
                elif action_type == 'group_discussion':
                    # 多人讨论事件 - 确保有足够参与者
                    current_loc = agent.location if hasattr(agent, 'location') else agent.current_location
                    
                    # 寻找同位置的其他Agent
                    agents_same_location = [
                        (name, agent_obj) for name, agent_obj in self.agents.items() 
                        if name != agent_name and agent_obj.location == current_loc
                    ]
                    
                    # 如果当前位置人数不够，尝试召集更多Agent到此位置
                    if len(agents_same_location) < 2:
                        # 寻找其他位置的Agent，邀请他们过来
                        other_agents = [name for name in self.agents.keys() 
                                      if name != agent_name and self.agents[name].location != current_loc]
                        
                        if other_agents:
                            # 确保至少邀请2个Agent，总共至少3人参与讨论
                            invite_count = min(max(2, random.randint(2, 3)), len(other_agents))
                            invited_agents = random.sample(other_agents, invite_count)
                            
                            print(f"\n{TerminalColors.BOLD}━━━ 📢 召集讨论 ━━━{TerminalColors.END}")
                            print(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END}: 想在{current_loc}组织讨论，邀请大家过来")
                            
                            for invited_name in invited_agents:
                                invited_agent = self.agents[invited_name]
                                old_location = invited_agent.location
                                invited_agent.location = current_loc
                                
                                # 更新真实Agent位置
                                if hasattr(invited_agent, 'real_agent'):
                                    invited_agent.real_agent.current_location = current_loc
                                
                                print(f"  {invited_agent.emoji} {TerminalColors.YELLOW}{invited_name}{TerminalColors.END}: {old_location} → {current_loc}")
                                agents_same_location.append((invited_name, invited_agent))
                            print()
                    
                    # 确保至少有3人参与讨论（包括发起者）
                    if len(agents_same_location) >= 2:  # 至少需要2个其他参与者
                        # 选择2-3个参与者，确保总人数在3-4人
                        participants_count = min(random.randint(2, 3), len(agents_same_location))
                        participants = random.sample(agents_same_location, participants_count)
                        
                        # 讨论话题
                        topics = [
                            "最近的工作情况",
                            "这个地方的变化",
                            "最近的新闻",
                            "周末的计划",
                            "对某个问题的看法",
                            "共同的兴趣爱好",
                            "小镇的发展",
                            "天气变化"
                        ]
                        
                        topic = random.choice(topics)
                        
                        print(f"\n{TerminalColors.BOLD}━━━ 💬 多人讨论 ━━━{TerminalColors.END}")
                        print(f"📍 地点: {current_loc}")
                        print(f"🎯 话题: {topic}")
                        
                        # 显示所有参与者位置信息
                        all_participants = [(agent_name, agent)] + participants
                        participant_locations = []
                        for p_name, p_agent in all_participants:
                            p_location = p_agent.location if hasattr(p_agent, 'location') else p_agent.current_location
                            participant_locations.append(f"{p_name}({p_location})")
                        print(f"👥 参与者: {' + '.join(participant_locations)} ({len(all_participants)}人)")
                        
                        # 验证所有参与者位置一致性
                        for p_name, p_agent in participants:
                            p_location = p_agent.location if hasattr(p_agent, 'location') else p_agent.current_location
                            if p_location != current_loc:
                                print(f"   📌 {p_name} 从 {p_location} 移动至 {current_loc}")
                                p_agent.location = current_loc
                                if hasattr(p_agent, 'real_agent'):
                                    p_agent.real_agent.current_location = current_loc
                        
                        # 发起讨论
                        discussion_prompt = f"在{current_loc}关于{topic}，对大家说："
                        starter = agent.think_and_respond(discussion_prompt)
                        starter = self._clean_response(starter)
                        
                        print(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END}: {starter}")
                        
                        # 参与者回应 - 根据关系决定情感倾向，然后生成匹配内容
                        for participant_name, participant_agent in participants:
                            # 真正公平的情感分配机制
                            current_rel = self.behavior_manager.get_relationship_strength(agent_name, participant_name)
                            
                            # 完全公平的基础概率：每个人都有相同的机会
                            base_positive = 40   # 基础正面概率从35增加到40
                            base_neutral = 40    # 基础中性概率从35增加到40
                            base_negative = 20   # 基础负面概率从30降低到20
                            
                            # 关系只做微调，不改变基本公平性（总调整幅度不超过±10%）
                            if current_rel > 70:
                                # 好关系：微调+10%正面，-5%负面
                                response_type = random.choices(['positive', 'neutral', 'negative'], weights=[50, 40, 10])[0]
                            elif current_rel > 50:
                                # 一般关系：微调+5%正面，-5%负面
                                response_type = random.choices(['positive', 'neutral', 'negative'], weights=[45, 40, 15])[0]
                            elif current_rel > 30:
                                # 较差关系：微调-5%正面，+5%负面
                                response_type = random.choices(['positive', 'neutral', 'negative'], weights=[35, 40, 25])[0]
                            else:
                                # 很差关系：微调-10%正面，+10%负面
                                response_type = random.choices(['positive', 'neutral', 'negative'], weights=[30, 40, 30])[0]
                            
                            # 根据预设情感类型生成匹配的提示词和内容
                            if response_type == 'positive':
                                interaction_type = 'friendly_chat'
                                color = TerminalColors.GREEN
                                response_prompt = f"对于{agent_name}说的：'{starter}'，表示赞同和支持，积极回应："
                            elif response_type == 'negative':
                                # 随机选择负面类型
                                negative_types = ['argument', 'misunderstanding', 'disappointment']
                                interaction_type = random.choice(negative_types)
                                color = TerminalColors.RED
                                
                                if interaction_type == 'argument':
                                    response_prompt = f"对于{agent_name}说的：'{starter}'，表示不同意和反对，坚持自己的观点："
                                elif interaction_type == 'misunderstanding':
                                    response_prompt = f"对于{agent_name}说的：'{starter}'，表示困惑和质疑，不要赞同或支持："
                                else:  # disappointment
                                    response_prompt = f"对于{agent_name}说的：'{starter}'，表示失望，不要缓解气氛："
                            else:  # neutral
                                interaction_type = 'casual_meeting'
                                color = TerminalColors.YELLOW
                                response_prompt = f"对于{agent_name}说的：'{starter}'，中性简短回应："
                            
                            # 让Agent根据指定情感生成回应
                            ai_response = participant_agent.think_and_respond(response_prompt)
                            ai_response = self._clean_response(ai_response)
                            
                            # 定义关键词列表（在函数外部，供后续使用）
                            positive_keywords = ['赞同', '同意', '很好', '不错', '棒', '美', '对', '是的', '有道理', '支持', '喜欢', '认同', '欣赏', '感动', '启发', '有趣', '精彩', '优秀', '太好了']
                            negative_keywords = ['不同意', '反对', '不对', '错', '不行', '失望', '糟糕', '问题', '麻烦', '困惑', '不理解', '质疑', '批评', '反驳', '我觉得不对', '我不这么认为', '这有问题', '这样不好']
                            
                            # 验证生成内容是否与预设情感匹配，如不匹配则调整
                            def validate_sentiment_match(text, expected_type):
                                """验证生成内容是否与期望情感匹配"""
                                positive_score = sum(1 for word in positive_keywords if word in text)
                                negative_score = sum(1 for word in negative_keywords if word in text)
                                
                                if expected_type == 'positive' and positive_score > 0:
                                    return True
                                elif expected_type == 'negative' and negative_score > 0:  # 负面回复必须有负面关键词
                                    return True
                                elif expected_type == 'neutral':
                                    return True
                                return False
                            
                            # 如果内容与预设不匹配，重新生成更自然的内容
                            if not validate_sentiment_match(ai_response, response_type):
                                if response_type == 'positive':
                                    positive_modifiers = ["我觉得这很有道理。", "这个想法不错！", "我很赞同。"]
                                    ai_response = f"{ai_response} {random.choice(positive_modifiers)}"
                                elif response_type == 'negative':
                                    # 负面互动时，重新生成更自然的负面回复
                                    if interaction_type == 'argument':
                                        retry_prompt = f"对于{agent_name}说的：'{starter}'，你坚决不同意，用自然的语言表达反对："
                                    elif interaction_type == 'misunderstanding':
                                        retry_prompt = f"对于{agent_name}说的：'{starter}'，你感到困惑不解，用自然的语言表达质疑："
                                    elif interaction_type == 'disappointment':
                                        retry_prompt = f"对于{agent_name}说的：'{starter}'，你感到失望，用自然的语言表达不满："
                                    
                                    # 重新生成回复
                                    ai_response = participant_agent.think_and_respond(retry_prompt)
                                    ai_response = self._clean_response(ai_response)
                                    
                                    # 如果重新生成后仍然不够负面，添加自然的前缀
                                    has_negative = any(keyword in ai_response for keyword in negative_keywords)
                                    if not has_negative:
                                        if interaction_type == 'argument':
                                            ai_response = f"我不同意，{ai_response}"
                                        elif interaction_type == 'misunderstanding':
                                            ai_response = f"我不太理解，{ai_response}"
                                        elif interaction_type == 'disappointment':
                                            ai_response = f"我很失望，{ai_response}"
                            
                            # 显示回应，明确是对发起者的回应
                            print(f"  {participant_agent.emoji} {color}{participant_name} → {agent_name}{TerminalColors.END}: {ai_response}")
                            
                            # 更新关系
                            context = {
                                'group_discussion': True,
                                'same_location': True,
                                'topic_sensitive': topic in ["对某个问题的看法", "小镇的发展"],
                                'public_discussion': True,
                            }
                            
                            # 强制确保负面互动类型确实会扣分
                            if interaction_type in ['argument', 'misunderstanding', 'disappointment']:
                                # 负面互动强制扣分
                                relationship_info = self.behavior_manager.update_social_network(
                                    agent_name, participant_name, interaction_type, context
                                )
                                # 如果关系变化是正数，强制改为负数，并且增加扣分幅度
                                if relationship_info['change'] > 0:
                                    relationship_info['change'] = -abs(relationship_info['change'])
                                # 额外增加负面互动的扣分，确保伤害更深刻
                                if relationship_info['change'] > -5:  # 如果扣分不够多
                                    relationship_info['change'] = max(-8, relationship_info['change'] - 3)  # 至少扣8分
                                
                                relationship_info['new_strength'] = max(0, relationship_info['old_strength'] + relationship_info['change'])
                                # 重新计算关系等级
                                import sys
                                import os
                                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                                from config.relationship_config import get_relationship_level
                                relationship_info['new_level'] = get_relationship_level(relationship_info['new_strength'])
                                relationship_info['level_changed'] = relationship_info['old_level'] != relationship_info['new_level']
                            else:
                                # 正常更新关系
                                relationship_info = self.behavior_manager.update_social_network(
                                    agent_name, participant_name, interaction_type, context
                                )
                            
                            # 简化显示关系变化
                            if abs(relationship_info['change']) > 2:
                                change_symbol = "+" if relationship_info['change'] > 0 else ""
                                change_color = TerminalColors.GREEN if relationship_info['change'] > 0 else TerminalColors.RED
                                print(f"       {relationship_info['relationship_emoji']} ({change_color}{change_symbol}{relationship_info['change']}{TerminalColors.END})")
                        
                        # 可能的后续互动 - 参与者之间的对话
                        if len(participants) >= 2 and random.random() < 0.4:  # 40%概率有后续互动
                            # 随机选择两个参与者进行额外对话
                            speaker_name, speaker_agent = random.choice(participants)
                            remaining_participants = [p for p in participants if p[0] != speaker_name]
                            if remaining_participants:
                                listener_name, listener_agent = random.choice(remaining_participants)
                                
                                # 真正公平的后续对话情感分配
                                followup_rel = self.behavior_manager.get_relationship_strength(speaker_name, listener_name)
                                
                                # 完全公平的基础概率，关系只做微调
                                if followup_rel < 30:
                                    # 差关系：微调-5%正面，+5%负面
                                    followup_type = random.choices(['positive', 'neutral', 'negative'], weights=[30, 35, 35])[0]
                                elif followup_rel < 50:
                                    # 一般关系：完全平衡
                                    followup_type = random.choices(['positive', 'neutral', 'negative'], weights=[35, 35, 30])[0]
                                elif followup_rel < 70:
                                    # 较好关系：微调+5%正面，-5%负面
                                    followup_type = random.choices(['positive', 'neutral', 'negative'], weights=[40, 35, 25])[0]
                                else:
                                    # 好关系：微调+10%正面，-10%负面
                                    followup_type = random.choices(['positive', 'neutral', 'negative'], weights=[45, 35, 20])[0]
                                
                                # 根据情感类型生成对应的提示词
                                if followup_type == 'positive':
                                    followup_prompt = f"对{listener_name}友好地说："
                                    followup_color = TerminalColors.GREEN
                                    followup_interaction = 'friendly_chat'
                                elif followup_type == 'negative':
                                    negative_prompts = [
                                        f"对{listener_name}表示不满，不要赞同或支持：",
                                        f"对{listener_name}质疑，坚持自己的观点：", 
                                        f"对{listener_name}抱怨，不要缓解气氛："
                                    ]
                                    followup_prompt = random.choice(negative_prompts)
                                    followup_color = TerminalColors.RED
                                    followup_interaction = 'misunderstanding'
                                else:  # neutral
                                    followup_prompt = f"对{listener_name}说："
                                    followup_color = TerminalColors.YELLOW
                                    followup_interaction = 'casual_meeting'
                                
                                # 生成后续对话
                                followup_response = speaker_agent.think_and_respond(followup_prompt)
                                followup_response = self._clean_response(followup_response)
                                
                                # 确保负面内容真的是负面的
                                if followup_type == 'negative':
                                    # 检查是否已包含负面词汇
                                    negative_keywords = ['不', '反对', '质疑', '问题', '错', '不同意', '我觉得不对', '这有问题', '这样不好', '失望', '糟糕']
                                    has_negative = any(word in followup_response for word in negative_keywords)
                                    
                                    if not has_negative:
                                        # 根据互动类型添加相应的负面前缀
                                        if followup_interaction == 'misunderstanding':
                                            followup_response = f"我对这个说法感到困惑。{followup_response}"
                                        elif followup_interaction == 'argument':
                                            followup_response = f"我不同意这个观点。{followup_response}"
                                        else:
                                            followup_response = f"我质疑这个说法。{followup_response}"
                                
                                print(f"  {speaker_agent.emoji} {followup_color}{speaker_name} → {listener_name}{TerminalColors.END}: {followup_response}")
                                
                                # 更新后续对话的关系
                                # 强制确保负面互动类型确实会扣分
                                if followup_interaction in ['misunderstanding', 'argument']:
                                    # 负面互动强制扣分
                                    followup_info = self.behavior_manager.update_social_network(
                                        speaker_name, listener_name, followup_interaction, context
                                    )
                                    # 如果关系变化是正数，强制改为负数
                                    if followup_info['change'] > 0:
                                        followup_info['change'] = -abs(followup_info['change'])
                                        followup_info['new_strength'] = max(0, followup_info['old_strength'] + followup_info['change'])
                                        # 重新计算关系等级
                                        import sys
                                        import os
                                        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                                        from config.relationship_config import get_relationship_level
                                        followup_info['new_level'] = get_relationship_level(followup_info['new_strength'])
                                        followup_info['level_changed'] = followup_info['old_level'] != followup_info['new_level']
                                else:
                                    # 正常更新关系
                                    followup_info = self.behavior_manager.update_social_network(
                                        speaker_name, listener_name, followup_interaction, context
                                    )
                                
                                if abs(followup_info['change']) > 1:
                                    change_symbol = "+" if followup_info['change'] > 0 else ""
                                    change_color = TerminalColors.GREEN if followup_info['change'] > 0 else TerminalColors.RED
                                    print(f"       {followup_info['relationship_emoji']} ({change_color}{change_symbol}{followup_info['change']}{TerminalColors.END})")
                        
                        # 如果有争吵，调解成功率很低
                        negative_interactions = [interaction_type for participant_name, participant_agent in participants 
                                               for interaction_type in ['argument', 'misunderstanding'] 
                                               if interaction_type in ['argument', 'misunderstanding']]
                        
                        if negative_interactions and random.random() < 0.2:  # 20%概率有人调解
                            potential_mediators = [name for name, _ in participants]
                            if potential_mediators:
                                mediator_name = random.choice(potential_mediators)
                                mediator_agent = self.agents[mediator_name]
                                
                                # 调解的AI回应
                                mediation_prompt = f"缓解气氛，对大家说："
                                mediation_response = mediator_agent.think_and_respond(mediation_prompt)
                                mediation_response = self._clean_response(mediation_response)
                                
                                # 调解也不一定有效
                                if random.random() < 0.5:  # 50%概率调解成功
                                    print(f"  {mediator_agent.emoji} {TerminalColors.BLUE}{mediator_name} → 大家{TerminalColors.END}: {mediation_response}")
                                    print(f"       🕊️ 气氛有所缓解")
                                else:
                                    # 调解失败
                                    print(f"  {mediator_agent.emoji} {TerminalColors.YELLOW}{mediator_name} → 大家{TerminalColors.END}: {mediation_response}")
                                    print(f"       😤 调解效果不佳，气氛依然紧张")
                        
                        print()  # 空行分隔
                    else:
                        # 如果没有其他人，转为AI自主独白
                        solo_prompt = f"在{current_loc}自言自语："
                        solo_thought = agent.think_and_respond(solo_prompt)
                        solo_thought = self._clean_response(solo_thought)
                        
                        print(f"\n{TerminalColors.BOLD}━━━ 💭 独自思考 ━━━{TerminalColors.END}")
                        print(f"  {agent.emoji} {TerminalColors.YELLOW}{agent_name}{TerminalColors.END}: {solo_thought}")
                        print()  # 空行分隔
                
                elif action_type == 'move':
                    # 简化移动决策 - 直接使用预设，避免AI生成冗长文本
                    locations = list(self.buildings.keys())
                    current_loc = agent.location if hasattr(agent, 'location') else agent.current_location
                    available_locations = [loc for loc in locations if loc != current_loc]
                    
                    if available_locations:
                        chosen_location = random.choice(available_locations)
                        
                        # 简洁的移动理由
                        simple_reasons = [
                            f"去{chosen_location}",
                            f"想到{chosen_location}看看",
                            f"前往{chosen_location}",
                            f"散步到{chosen_location}",
                            f"想换个地方"
                        ]
                        reason = random.choice(simple_reasons)
                        
                        # 执行移动
                        old_location = current_loc
                        if hasattr(agent, 'location'):
                            agent.location = chosen_location
                        else:
                            agent.current_location = chosen_location
                        
                        print(f"\n{TerminalColors.BOLD}━━━ 🚶 移动 ━━━{TerminalColors.END}")
                        print(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END}: {old_location} → {chosen_location}")
                        print(f"  💭 {reason}")
                        print()  # 空行分隔
                        
                        # 更新地点热度
                        try:
                            self.behavior_manager.update_location_popularity(chosen_location, 2)
                            self.behavior_manager.update_location_popularity(old_location, -1)
                        except Exception as e:
                            pass
                
                elif action_type == 'think':
                    # AI自主思考模式
                    current_time = time.strftime("%H:%M")
                    current_loc = agent.location if hasattr(agent, 'location') else agent.current_location
                    
                    think_prompt = f"在{current_loc}思考："
                    thought = agent.think_and_respond(think_prompt)
                    
                    # 清理思考内容中的提示词
                    thought = self._clean_response(thought)
                    
                    print(f"\n{TerminalColors.BOLD}━━━ 💭 思考 ━━━{TerminalColors.END}")
                    print(f"  {agent.emoji} {TerminalColors.YELLOW}{agent_name}{TerminalColors.END}: {thought}")
                    print()  # 空行分隔
                    
                    # 更新Agent状态
                    if hasattr(agent, 'update_status'):
                        agent.update_status()
                
                elif action_type == 'work':
                    # 简化的工作行为 - 使用预设工作内容
                    profession_works = {
                        '程序员': ["编写代码", "测试程序", "修复bug", "优化性能"],
                        '艺术家': ["绘画创作", "设计作品", "调色练习", "构图研究"],
                        '老师': ["备课", "批改作业", "制作课件", "研究教法"],
                        '医生': ["查看病历", "诊断病情", "制定治疗方案", "学习医学资料"],
                        '学生': ["做作业", "复习笔记", "预习课程", "准备考试"],
                        '商人': ["分析报表", "联系客户", "制定计划", "市场调研"],
                        '厨师': ["准备食材", "烹饪美食", "试验新菜", "清理厨房"],
                        '机械师': ["检修设备", "更换零件", "调试机器", "保养工具"],
                        '退休人员': ["整理家务", "阅读书籍", "园艺活动", "锻炼身体"]
                    }
                    
                    works = profession_works.get(agent.profession, ["忙碌工作"])
                    work_activity = random.choice(works)
                    
                    print(f"\n{TerminalColors.BOLD}━━━ 💼 工作 ━━━{TerminalColors.END}")
                    print(f"  {agent.emoji} {TerminalColors.BLUE}{agent_name}{TerminalColors.END}: {work_activity}")
                    print()  # 空行分隔
                    
                    # 工作提升精力（专业满足感）
                    if hasattr(agent, 'energy_level'):
                        agent.energy_level = min(100, agent.energy_level + random.randint(5, 15))
                    elif hasattr(agent, 'energy'):
                        agent.energy = min(100, agent.energy + random.randint(5, 15))
                
                elif action_type == 'relax':
                    # 简化的放松行为 - 使用预设放松内容
                    relax_activities = [
                        "在散步放松", "听音乐休息", "喝茶思考", "看书充电",
                        "晒太阳", "呼吸新鲜空气", "欣赏风景", "静坐冥想"
                    ]
                    relax_activity = random.choice(relax_activities)
                    
                    print(f"\n{TerminalColors.BOLD}━━━ 🌸 放松 ━━━{TerminalColors.END}")
                    print(f"  {agent.emoji} {TerminalColors.GREEN}{agent_name}{TerminalColors.END}: {relax_activity}")
                    print()  # 空行分隔
                    
                    # 放松恢复精力和改善心情
                    if hasattr(agent, 'energy_level'):
                        agent.energy_level = min(100, agent.energy_level + random.randint(10, 20))
                        if hasattr(agent, 'current_mood') and agent.current_mood in ["疲惫", "焦虑", "紧张"]:
                            agent.current_mood = random.choice(["平静", "愉快", "放松"])
                    elif hasattr(agent, 'energy'):
                        agent.energy = min(100, agent.energy + random.randint(10, 20))
                        if hasattr(agent, 'mood') and agent.mood in ["疲惫", "焦虑", "紧张"]:
                            agent.mood = random.choice(["平静", "愉快", "放松"])
                
                # 随机创建小镇事件 - 增加频率
                if random.random() < 0.3:  # 30%概率
                    try:
                        self.create_town_event()
                    except Exception as e:
                        print(f"{TerminalColors.YELLOW}⚠️ 创建小镇事件失败: {e}{TerminalColors.END}")
                
                # 等待间隔 - 适中的间隔保持活跃度
                sleep_time = random.uniform(2, 5)  # 从4-8秒减少到2-5秒
                time.sleep(sleep_time)
                
            except Exception as e:
                if self.auto_simulation:
                    print(f"{TerminalColors.RED}❌ 自动模拟错误: {e}{TerminalColors.END}")
                    import traceback
                    traceback.print_exc()
                time.sleep(1)
        
        print(f"{TerminalColors.RED}🛑 自动模拟循环结束{TerminalColors.END}")
    
    def _clean_response(self, response: str) -> str:
        """彻底清理AI回应中的提示词残留 - 强化版"""
        # 预处理：移除明显的提示词段落
        response = response.strip()
        
        # 移除英文段落
        english_patterns = [
            r'"[^"]*[A-Za-z]{10,}[^"]*"',  # 引号内的长英文内容
            r'[A-Za-z\s]{15,}',  # 连续的英文单词（15个字符以上）
            r'Hi\s+\w+[^。！？]*',  # Hi开头的英文问候
            r'[A-Z][a-z]+\s+[A-Z][a-z]+[^。！？]*',  # 人名格式的英文
            r'\*[^*]*\*',  # 星号包围的内容（通常是动作描述）
        ]
        
        for pattern in english_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # 如果开头就是明显的指令，直接截断
        if re.match(r'^\d+\.\s*(字数|不少于|不超过|在.*?字|控制)', response):
            # 寻找第一个正常的句子
            sentences = re.split(r'[。！？]', response)
            for sentence in sentences:
                cleaned_sentence = re.sub(r'^\d+\.\s*.*?(字数|不少于|不超过|控制).*?', '', sentence).strip()
                if len(cleaned_sentence) > 5 and not any(word in cleaned_sentence for word in ['字数', '句数', '要求', '控制']):
                    response = cleaned_sentence + '。'
                    break
            else:
                return "嗯。"
        
        # 分割成句子处理
        sentences = re.split(r'([。！？])', response)
        clean_sentences = []
        
        for i in range(0, len(sentences)-1, 2):  # 处理句子和标点对
            sentence = sentences[i].strip()
            punct = sentences[i+1] if i+1 < len(sentences) else '。'
            
            # 跳过包含指令词汇、英文或思考类语言的句子
            skip_indicators = [
                '字数', '句数', '不少于', '不超过', '控制在', '要求', '请', '务必', 
                '总长度', '在.*?字以内', '字以内', '在.*?内', '范围内',
                '图片', '照片', '图像', '画面', '视频', '音频', '文件',  # 多媒体相关
                '链接', '网址', 'http', 'https', 'www',  # 网络相关
                '点击', '下载', '上传', '保存',  # 操作相关
                '系统', '程序', '软件', '应用',  # 技术相关限制词
                'Hi ', 'Hello', 'As a', 'Let\'s', 'Did you know',  # 英文开头
                '我来想想', '让我思考', '我需要思考', '正在思考', '思考中',  # 思考类语言
                '我会这样', '我应该', '我可以', '我建议', '我认为可以',  # 模型逻辑语言
                '根据', '基于', '从.*角度', '考虑到', '综合来看',  # 分析性语言
                '首先', '其次', '然后', '最后', '总的来说',  # 结构化语言
                '这样的回应', '既表达了我', '也提供了', '同时也传递了',  # 解释性语言
                '我注意到', '我注意到你', '我注意到你今天',  # 观察性语言
                '这样的回应既表达了我对', '也提供了后续沟通的机会',  # 分析性回应
                '既表达了我对Alex态度的', '也提供了后续沟通的机会',  # 具体分析
                '同时也传递了健康生活的正面信息',  # 信息传递描述
            ]
            
            # 检查是否包含大量英文
            english_ratio = len(re.findall(r'[A-Za-z]', sentence)) / (len(sentence) + 1)
            if english_ratio > 0.3 or any(indicator in sentence for indicator in skip_indicators):
                continue
                
            # 移除句子开头的数字标记
            sentence = re.sub(r'^\d+\.\s*', '', sentence)
            
            if len(sentence) > 3:  # 保留有意义的句子
                clean_sentences.append(sentence + punct)
        
        if not clean_sentences:
            return "嗯。"
        
        # 重新组合，但限制长度
        result = ''.join(clean_sentences[:2])  # 最多保留2句话
        
        # 最终清理
        unwanted_patterns = [
            r'字数.*?',
            r'不少于.*?',
            r'不超过.*?',
            r'控制在.*?',
            r'总长度.*?',
            r'在\d+字.*?',
            r'\d+字以内.*?',
            r'在\d+至\d+.*?',  # 新增：在90至120个字符之间
            r'\d+个字符.*?',   # 新增：个字符限制
            r'[Hh]i\s+\w+.*?',  # 新增：Hi开头的英文
            r'"[^"]*[A-Za-z]{10,}[^"]*"',  # 新增：引号内长英文
            r'我来想想.*?',  # 思考类语言
            r'让我思考.*?',
            r'我需要思考.*?',
            r'正在思考.*?',
            r'思考中.*?',
            r'我会这样.*?',  # 模型逻辑语言
            r'我应该.*?',
            r'我可以.*?',
            r'我建议.*?',
            r'我认为可以.*?',
            r'根据.*?',  # 分析性语言开头
            r'基于.*?',
            r'从.*?角度.*?',
            r'考虑到.*?',
            r'综合来看.*?',
            r'这样的回应.*?',  # 解释性语言
            r'既表达了我.*?',
            r'也提供了.*?',
            r'同时也传递了.*?',
            r'我注意到.*?',
            r'我注意到你.*?',
            r'我注意到你今天.*?',
        ]
        
        for pattern in unwanted_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        # 特殊处理：移除类似 "在90至120个字符之间" 的指令
        result = re.sub(r'".*?在\d+.*?字符.*?"', '', result)
        result = re.sub(r'".*?Hi.*?[A-Za-z].*?"', '', result)  # 移除引号内英文问候
        
        # 移除多余空格和标点
        result = re.sub(r'\s+', ' ', result).strip()
        result = re.sub(r'^[。！？，、]+', '', result)  # 移除开头的标点
        
        # 如果太长，截断到合理长度
        if len(result) > 100:
            # 找到第一个句号截断
            first_period = result.find('。')
            if first_period > 10:
                result = result[:first_period + 1]
            else:
                result = result[:50] + '。'
        
        return result if result else "嗯。"
    
    def load_persistent_data(self):
        """加载持久化数据"""
        try:
            # 加载社交网络数据
            social_data_file = os.path.join("data", "cache", "social_network.json")
            if os.path.exists(social_data_file):
                with open(social_data_file, 'r', encoding='utf-8') as f:
                    social_data = json.load(f)
                    self.behavior_manager.social_network = social_data
                    print(f"📊 已加载社交网络数据：{len(social_data)} 个关系网络")
            
            # 加载Agent记忆摘要
            memories_file = os.path.join("data", "cache", "agent_memories.json")
            if os.path.exists(memories_file):
                with open(memories_file, 'r', encoding='utf-8') as f:
                    memories_data = json.load(f)
                    for agent_name, agent in self.agents.items():
                        if agent_name in memories_data and hasattr(agent, 'real_agent'):
                            # 恢复重要记忆
                            agent_memories = memories_data[agent_name]
                            print(f"🧠 {agent_name} 恢复了 {len(agent_memories)} 条重要记忆")
            
            # 加载地点热度数据
            location_data_file = os.path.join("data", "cache", "location_popularity.json")
            if os.path.exists(location_data_file):
                with open(location_data_file, 'r', encoding='utf-8') as f:
                    location_data = json.load(f)
                    self.behavior_manager.location_popularity = location_data
                    print(f"🏢 已加载地点热度数据：{len(location_data)} 个地点")
            
            print(f"{TerminalColors.GREEN}✅ 数据持久化加载完成{TerminalColors.END}")
            
        except Exception as e:
            print(f"{TerminalColors.YELLOW}⚠️ 加载持久化数据失败，使用默认设置: {e}{TerminalColors.END}")
    
    def _redistribute_agents_randomly(self):
        """随机重新分布Agent到各个地点，增加社交机会"""
        try:
            locations = list(self.buildings.keys())
            agent_names = list(self.agents.keys())
            
            # 确保每个地点至少有一些Agent，但不要太平均
            min_per_location = max(1, len(agent_names) // (len(locations) + 2))
            
            # 打乱Agent列表
            random.shuffle(agent_names)
            
            # 分配Agent到地点
            location_index = 0
            agents_assigned = 0
            
            for agent_name in agent_names:
                agent = self.agents[agent_name]
                
                # 70%概率随机分配，30%概率集中分配（增加社交）
                if random.random() < 0.7:
                    new_location = random.choice(locations)
                else:
                    # 选择已有Agent较多的地点
                    location_populations = {}
                    for loc in locations:
                        location_populations[loc] = sum(1 for a in self.agents.values() if a.location == loc)
                    
                    # 选择人口第二多的地点（避免过度集中）
                    sorted_locations = sorted(location_populations.items(), key=lambda x: x[1], reverse=True)
                    if len(sorted_locations) > 1:
                        new_location = sorted_locations[1][0]
                    else:
                        new_location = random.choice(locations)
                
                # 只有位置真的改变时才移动
                if agent.location != new_location:
                    agent.location = new_location
                    
                    # 更新真实Agent位置
                    if hasattr(agent, 'real_agent'):
                        agent.real_agent.current_location = new_location
                
                agents_assigned += 1
                location_index = (location_index + 1) % len(locations)
            
        except Exception as e:
            logger.warning(f"重新分布Agent失败: {e}")
    
    def save_persistent_data(self):
        """保存持久化数据"""
        try:
            # 确保cache目录存在
            cache_dir = os.path.join("data", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # 保存社交网络数据
            social_data_file = os.path.join(cache_dir, "social_network.json")
            with open(social_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.behavior_manager.social_network, f, ensure_ascii=False, indent=2)
            
            # 保存Agent重要记忆摘要
            memories_data = {}
            for agent_name, agent in self.agents.items():
                if hasattr(agent, 'real_agent') and hasattr(agent.real_agent, 'memory_manager'):
                    try:
                        # 获取最重要的几条记忆
                        important_memories = agent.real_agent.memory_manager.get_recent_memories(limit=10)
                        memories_data[agent_name] = important_memories
                    except:
                        pass
            
            memories_file = os.path.join(cache_dir, "agent_memories.json")
            with open(memories_file, 'w', encoding='utf-8') as f:
                json.dump(memories_data, f, ensure_ascii=False, indent=2)
            
            # 保存地点热度数据
            location_data_file = os.path.join(cache_dir, "location_popularity.json")
            with open(location_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.behavior_manager.location_popularity, f, ensure_ascii=False, indent=2)
            
            print(f"{TerminalColors.GREEN}💾 数据已保存到本地缓存{TerminalColors.END}")
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 保存数据失败: {e}{TerminalColors.END}")
    
    def create_town_event(self):
        """创建小镇随机事件"""
        try:
            events = [
                "🌤️ 天气变化：今天是个好天气！",
                "📢 公告：图书馆新书到货",
                "🎵 街头艺人在广场演奏",
                "🌸 公园里的花开了",
                "🚛 商店进了新货"
            ]
            event = random.choice(events)
            print(f"{TerminalColors.GREEN}{event}{TerminalColors.END}")
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 创建小镇事件错误: {e}{TerminalColors.END}")
    
    def organize_group_activity(self, location):
        """组织群体活动"""
        try:
            activities = [
                f"在{location}举办读书会",
                f"在{location}组织音乐聚会",
                f"在{location}开展讨论活动",
                f"在{location}进行社交聚餐"
            ]
            activity = random.choice(activities)
            print(f"{TerminalColors.BLUE}🎪 群体活动：{activity}{TerminalColors.END}")
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 组织群体活动错误: {e}{TerminalColors.END}")
    
    def show_status(self):
        """显示系统状态"""
        print(f"\n{TerminalColors.BOLD}📊 系统状态{TerminalColors.END}")
        print("=" * 40)
        
        # AI系统状态
        if REAL_AGENTS_AVAILABLE:
            print(f"{TerminalColors.GREEN}🧠 AI系统: 真实Agent系统已启用{TerminalColors.END}")
            print(f"   ✅ 本地Qwen模型: 可用")
            try:
                sample_agent = list(self.agents.values())[0]
                if hasattr(sample_agent, 'real_agent') and hasattr(sample_agent.real_agent, 'deepseek_api'):
                    if sample_agent.real_agent.deepseek_api.is_available():
                        print(f"   ✅ DeepSeek API: 已连接")
                    else:
                        print(f"   ❌ DeepSeek API: 未配置")
            except Exception as e:
                logger.warning(f"检查API状态失败: {e}")
                print(f"   ⚠️  API状态: 未知")
        else:
            print(f"{TerminalColors.YELLOW}🤖 AI系统: 简化Agent系统{TerminalColors.END}")
        
        # Agent状态
        total_agents = len(self.agents)
        active_agents = sum(1 for agent in self.agents.values() if agent.get_status()['energy'] > 50)
        print(f"👥 Agent总数: {total_agents}")
        print(f"🔋 活跃Agent: {active_agents}")
        
        # 对话统计
        print(f"💬 对话记录: {len(self.chat_history)} 条")
        print(f"📊 社交网络: {len(self.behavior_manager.social_network)} 个Agent")
        print(f"🎯 群体活动: {len(self.behavior_manager.group_activities)} 个")
        print(f"🏘️ 小镇事件: {len(self.behavior_manager.town_events)} 个")
    
    def show_history(self):
        """显示对话历史"""
        print(f"\n{TerminalColors.BOLD}📜 对话历史{TerminalColors.END}")
        print("=" * 50)
        
        if not self.chat_history:
            print(f"{TerminalColors.YELLOW}暂无对话记录{TerminalColors.END}\n")
            return
        
        # 显示最近10条记录
        recent_chats = self.chat_history[-10:]
        for chat in recent_chats:
            agent = self.agents[chat['agent']]
            print(f"{TerminalColors.CYAN}[{chat['time']}]{TerminalColors.END}")
            print(f"  🧑 你: {chat['user']}")
            print(f"  {agent.color}{agent.emoji} {chat['agent']}: {TerminalColors.END}{chat['response']}")
            print()
    
    def show_help(self):
        """显示帮助信息"""
        print(f"\n{TerminalColors.BOLD}🆘 命令帮助{TerminalColors.END}")
        print("=" * 60)
        
        commands = [
            ("🗺️  基础命令", ""),
            ("map", "查看小镇地图和Agent位置"),
            ("agents", "查看所有Agent的详细状态"),
            ("chat <name>", "与指定Agent开始对话 (例: chat Alex)"),
            ("move <name> <place>", "移动Agent到指定地点 (例: move Emma 咖啡厅)"),
            ("auto", "开启或关闭Agent自动模拟"),
            ("", ""),
            ("🧠 智能功能", ""),
            ("social", "查看Agent之间的社交网络关系"),
            ("event [type]", "创建小镇事件 (例: event 技术讲座)"),
            ("group [location]", "在指定地点组织群体活动"),
            ("stats", "查看详细的统计信息和分析"),
            ("popular", "查看当前最热门的地点"),
            ("", ""),
            ("📊 系统命令", ""),
            ("status", "查看系统运行状态"),
            ("history", "查看最近的对话历史"),
            ("help", "显示此帮助信息"),
            ("clear", "清屏"),
            ("quit", "退出程序")
        ]
        
        for cmd, desc in commands:
            if not desc:  # 分类标题
                if cmd:
                    print(f"\n{TerminalColors.BOLD}{cmd}{TerminalColors.END}")
            else:
                print(f"  {TerminalColors.CYAN}{cmd:<20}{TerminalColors.END} - {desc}")
        
        print(f"\n{TerminalColors.YELLOW}💡 小贴士:{TerminalColors.END}")
        print("  • 可以随时按 Ctrl+C 中断当前操作")
        print("  • 在对话模式中输入 'exit' 退出对话")
        print("  • 命令不区分大小写")
        print("  • 使用 'social' 查看Agent关系，'auto' 开启智能模拟")
        print()
    
    def show_social_network(self):
        """显示社交网络"""
        print(f"\n{TerminalColors.BOLD}👫 社交网络分析{TerminalColors.END}")
        print("=" * 50)
        
        network = self.behavior_manager.social_network
        if not network:
            print(f"{TerminalColors.YELLOW}还没有建立社交关系，让Agent们多互动一下吧！{TerminalColors.END}\n")
            return
        
        # 导入关系配置
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config.relationship_config import RELATIONSHIP_LEVELS, get_relationship_level
        
        # 显示关系矩阵
        agent_names = list(self.agents.keys())
        
        print(f"{TerminalColors.CYAN}关系等级矩阵:{TerminalColors.END}")
        print(f"{'':>8}", end="")
        for name in agent_names:  # 显示所有agent
            print(f"{name:>8}", end="")
        print()
        
        for name1 in agent_names:
            agent1 = self.agents[name1]
            print(f"{agent1.color}{name1:>8}{TerminalColors.END}", end="")
            for name2 in agent_names:
                if name1 == name2:
                    print(f"{'--':>8}", end="")
                else:
                    strength = self.behavior_manager.get_relationship_strength(name1, name2)
                    level = get_relationship_level(strength)
                    emoji = RELATIONSHIP_LEVELS[level]['emoji']
                    
                    if strength > 70:
                        color = TerminalColors.GREEN
                    elif strength > 50:
                        color = TerminalColors.YELLOW
                    else:
                        color = TerminalColors.RED
                    print(f"{color}{emoji}{strength:>6}{TerminalColors.END}", end="")
            print()
        
        # 显示最强关系
        print(f"\n{TerminalColors.GREEN}💖 友谊排行榜:{TerminalColors.END}")
        strongest_pairs = []
        for name1 in network:
            for name2, strength in network[name1].items():
                if name1 < name2:  # 避免重复
                    level = get_relationship_level(strength)
                    emoji = RELATIONSHIP_LEVELS[level]['emoji']
                    strongest_pairs.append((name1, name2, strength, level, emoji))
        
        strongest_pairs.sort(key=lambda x: x[2], reverse=True)
        for i, (name1, name2, strength, level, emoji) in enumerate(strongest_pairs[:8], 1):  # 显示前8对
            agent1 = self.agents[name1]
            agent2 = self.agents[name2]
            
            # 根据关系等级设置颜色
            if strength >= 80:
                color = TerminalColors.GREEN
            elif strength >= 60:
                color = TerminalColors.CYAN
            elif strength >= 40:
                color = TerminalColors.YELLOW
            else:
                color = TerminalColors.RED
            
            print(f"  {i}. {agent1.emoji} {name1} ↔ {agent2.emoji} {name2}: "
                  f"{color}{emoji} {level} ({strength}){TerminalColors.END}")
        
        # 显示关系等级统计
        print(f"\n{TerminalColors.CYAN}📊 关系分布统计:{TerminalColors.END}")
        level_count = {}
        total_relationships = 0
        
        for name1 in network:
            for name2, strength in network[name1].items():
                if name1 < name2:  # 避免重复计算
                    level = get_relationship_level(strength)
                    level_count[level] = level_count.get(level, 0) + 1
                    total_relationships += 1
        
        for level, config in RELATIONSHIP_LEVELS.items():
            count = level_count.get(level, 0)
            percentage = (count / total_relationships * 100) if total_relationships > 0 else 0
            print(f"  {config['emoji']} {level}: {count} 对 ({percentage:.1f}%)")
        
        print(f"\n{TerminalColors.CYAN}💡 关系系统说明:{TerminalColors.END}")
        print("  • 每次友好对话: +3分 (同地点+1, 同职业+1, 首次交流+2)")
        print("  • 深度交流: +5分 (高关系基础+2, 私密场所+1)")
        print("  • 合作共事: +6分 (成功合作+3, 相同专业+2)")
        print("  • 关系会根据职业相性和地点环境调整")
        print()
    
    def create_town_event(self, event_type: str = None):
        """创建小镇事件"""
        event = self.behavior_manager.create_town_event(event_type)
        if event:
            print(f"\n{TerminalColors.BOLD}🎪 小镇事件开始！{TerminalColors.END}")
            print("=" * 40)
            print(f"📅 事件: {TerminalColors.CYAN}{event['name']}{TerminalColors.END}")
            print(f"📍 地点: {event['location']}")
            print(f"📝 描述: {event['description']}")
            print(f"⏱️  持续时间: {event['duration']}分钟")
            print(f"✨ 效果: {event['effect']}")
            
            # 通知相关Agent
            relevant_agents = []
            for name, agent in self.agents.items():
                if (agent.location == event['location'] or 
                    event['location'] in self.behavior_manager.get_location_recommendations(agent)):
                    relevant_agents.append(name)
            
            if relevant_agents:
                print(f"\n{TerminalColors.YELLOW}📢 可能感兴趣的Agent:{TerminalColors.END}")
                for name in relevant_agents:
                    agent = self.agents[name]
                    print(f"  {agent.emoji} {name}")
            print()
    
    def organize_group_activity(self, location: str = None):
        """组织群体活动"""
        if location and location not in self.buildings:
            print(f"{TerminalColors.RED}❌ 找不到地点: {location}{TerminalColors.END}")
            return
        
        # 找到在指定位置或愿意参加的Agent
        participants = []
        if location:
            # 在指定位置的Agent
            for name, agent in self.agents.items():
                if agent.location == location:
                    participants.append(agent.real_agent if hasattr(agent, 'real_agent') else agent)
        else:
            # 随机选择一些Agent
            selected_agents = random.sample(list(self.agents.values()), min(4, len(self.agents)))
            participants = [agent.real_agent if hasattr(agent, 'real_agent') else agent 
                          for agent in selected_agents]
        
        if len(participants) < 2:
            print(f"{TerminalColors.YELLOW}⚠️  需要至少2个Agent才能组织群体活动{TerminalColors.END}")
            return
        
        activity = self.behavior_manager.plan_group_activity(participants)
        if activity:
            print(f"\n{TerminalColors.BOLD}🎯 群体活动开始！{TerminalColors.END}")
            print("=" * 40)
            print(f"🎪 活动: {TerminalColors.CYAN}{activity['name']}{TerminalColors.END}")
            print(f"📍 地点: {activity['location']}")
            print(f"📝 描述: {activity['description']}")
            print(f"⏱️  持续时间: {activity['duration']}分钟")
            
            print(f"\n{TerminalColors.GREEN}👥 参与者:{TerminalColors.END}")
            for participant_name in activity['participants']:
                if participant_name in self.agents:
                    agent = self.agents[participant_name]
                    print(f"  {agent.emoji} {participant_name}")
            
            # 移动参与者到活动地点
            for participant_name in activity['participants']:
                if participant_name in self.agents:
                    self.agents[participant_name].location = activity['location']
            
            print(f"\n{TerminalColors.CYAN}✨ 所有参与者已移动到{activity['location']}{TerminalColors.END}")
            print()
    
    def show_detailed_stats(self):
        """显示详细统计"""
        print(f"\n{TerminalColors.BOLD}📊 详细统计分析{TerminalColors.END}")
        print("=" * 60)
        
        # Agent统计
        print(f"{TerminalColors.CYAN}👥 Agent统计:{TerminalColors.END}")
        total_agents = len(self.agents)
        active_agents = sum(1 for agent in self.agents.values() 
                          if agent.get_status()['energy'] > 50)
        avg_energy = sum(agent.get_status()['energy'] for agent in self.agents.values()) / total_agents
        
        print(f"  总数量: {total_agents}")
        print(f"  活跃Agent: {active_agents}")
        print(f"  平均能量: {avg_energy:.1f}%")
        
        # 位置分布
        print(f"\n{TerminalColors.CYAN}📍 位置分布:{TerminalColors.END}")
        location_count = {}
        for agent in self.agents.values():
            loc = agent.location
            location_count[loc] = location_count.get(loc, 0) + 1
        
        for location, count in sorted(location_count.items(), key=lambda x: x[1], reverse=True):
            building_emoji = self.buildings.get(location, {}).get('emoji', '📍')
            print(f"  {building_emoji} {location}: {count} 人")
        
        # 职业分布
        print(f"\n{TerminalColors.CYAN}💼 职业分布:{TerminalColors.END}")
        profession_count = {}
        for agent in self.agents.values():
            if hasattr(agent, 'real_agent'):
                prof = agent.real_agent.profession
            else:
                prof = agent.profession
            profession_count[prof] = profession_count.get(prof, 0) + 1
        
        for profession, count in sorted(profession_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  {profession}: {count} 人")
        
        # 对话统计
        print(f"\n{TerminalColors.CYAN}💬 交互统计:{TerminalColors.END}")
        print(f"  对话记录: {len(self.chat_history)} 条")
        
        # 社交网络统计
        network = self.behavior_manager.social_network
        total_relationships = sum(len(relations) for relations in network.values()) // 2
        print(f"  建立关系: {total_relationships} 对")
        
        # 活动统计
        events = len(self.behavior_manager.town_events)
        activities = len(self.behavior_manager.group_activities)
        print(f"  小镇事件: {events} 个")
        print(f"  群体活动: {activities} 个")
        
        print()
    
    def show_popular_locations(self):
        """显示热门地点"""
        print(f"\n{TerminalColors.BOLD}🔥 热门地点排行{TerminalColors.END}")
        print("=" * 40)
        
        # 计算当前人气
        current_popularity = {}
        for location in self.buildings:
            agent_count = sum(1 for agent in self.agents.values() 
                            if agent.location == location)
            base_popularity = self.behavior_manager.location_popularity.get(location, 50)
            current_popularity[location] = base_popularity + agent_count * 10
        
        # 排序显示
        sorted_locations = sorted(current_popularity.items(), 
                                key=lambda x: x[1], reverse=True)
        
        for i, (location, popularity) in enumerate(sorted_locations, 1):
            building = self.buildings[location]
            agent_count = sum(1 for agent in self.agents.values() 
                            if agent.location == location)
            
            # 热度颜色
            if popularity > 80:
                color = TerminalColors.RED
            elif popularity > 60:
                color = TerminalColors.YELLOW
            else:
                color = TerminalColors.CYAN
            
            print(f"  {i}. {building['emoji']} {color}{location}{TerminalColors.END}")
            print(f"     热度: {popularity}% | 当前人数: {agent_count}")
            
            # 显示在此地点的Agent
            agents_here = [f"{agent.emoji}{name}" 
                          for name, agent in self.agents.items() 
                          if agent.location == location]
            if agents_here:
                print(f"     👥 {', '.join(agents_here)}")
            print()
        
        print(f"{TerminalColors.CYAN}💡 热度 = 基础人气 + 当前人数×10{TerminalColors.END}\n")
    
    def run(self):
        """运行主循环"""
        while self.running:
            try:
                # 显示提示符
                prompt = f"{TerminalColors.BOLD}🏘️ > {TerminalColors.END}"
                command = input(prompt).strip().lower()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0]
                
                if cmd in ['quit', 'exit', '退出']:
                    print(f"{TerminalColors.CYAN}💾 正在保存数据...{TerminalColors.END}")
                    self.save_persistent_data()
                    print(f"{TerminalColors.GREEN}👋 再见！感谢使用AI Agent虚拟小镇{TerminalColors.END}")
                    self.running = False
                    self.auto_simulation = False
                    break
                
                elif cmd == 'map':
                    self.show_map()
                
                elif cmd == 'agents':
                    self.show_agents_status()
                
                elif cmd == 'chat':
                    if len(parts) >= 2:
                        agent_name = parts[1].capitalize()
                        message = ' '.join(parts[2:]) if len(parts) > 2 else None
                        self.chat_with_agent(agent_name, message)
                    else:
                        print(f"{TerminalColors.RED}❌ 请指定Agent名称: chat <name>{TerminalColors.END}")
                
                elif cmd == 'move':
                    if len(parts) >= 3:
                        agent_name = parts[1].capitalize()
                        location = ' '.join(parts[2:])
                        self.move_agent(agent_name, location)
                    else:
                        print(f"{TerminalColors.RED}❌ 请指定Agent和地点: move <name> <place>{TerminalColors.END}")
                
                elif cmd == 'auto':
                    self.toggle_auto_simulation()
                
                elif cmd == 'status':
                    self.show_status()
                
                elif cmd == 'history':
                    self.show_history()
                
                elif cmd == 'help':
                    self.show_help()
                
                elif cmd == 'clear':
                    self.clear_screen()
                    self.show_welcome()
                
                elif cmd == 'social':
                    self.show_social_network()
                
                elif cmd == 'event':
                    if len(parts) >= 2:
                        event_type = ' '.join(parts[1:])
                        self.create_town_event(event_type)
                    else:
                        self.create_town_event()
                
                elif cmd == 'group':
                    if len(parts) >= 2:
                        location = ' '.join(parts[1:])
                        self.organize_group_activity(location)
                    else:
                        self.organize_group_activity()
                
                elif cmd == 'stats':
                    self.show_detailed_stats()
                
                elif cmd == 'popular':
                    self.show_popular_locations()
                
                else:
                    print(f"{TerminalColors.RED}❌ 未知命令: {command}{TerminalColors.END}")
                    print(f"{TerminalColors.CYAN}💡 输入 'help' 查看可用命令{TerminalColors.END}")
            
            except KeyboardInterrupt:
                print(f"\n{TerminalColors.YELLOW}⚠️  使用 'quit' 命令退出程序{TerminalColors.END}")
            except EOFError:
                print(f"\n{TerminalColors.GREEN}👋 再见！{TerminalColors.END}")
                break
            except Exception as e:
                print(f"{TerminalColors.RED}❌ 发生错误: {e}{TerminalColors.END}")
    
    def _get_decay_summary(self):
        """获取关系衰减摘要信息"""
        try:
            # 检查是否有关系强度下降的情况
            decay_count = 0
            total_relationships = 0
            
            for agent1_name in self.behavior_manager.social_network:
                for agent2_name in self.behavior_manager.social_network[agent1_name]:
                    if agent1_name >= agent2_name:
                        continue
                    
                    total_relationships += 1
                    current_strength = self.behavior_manager.social_network[agent1_name][agent2_name]
                    
                    # 如果关系强度低于50，可能受到衰减影响
                    if current_strength < 50:
                        decay_count += 1
            
            if decay_count > 0:
                decay_percentage = (decay_count / total_relationships) * 100
                return f"发现 {decay_count}/{total_relationships} 对关系强度较低 ({decay_percentage:.1f}%)"
            
            return None
        except Exception as e:
            logger.debug(f"获取衰减摘要失败: {e}")
            return None

class TerminalAgent:
    """终端版Agent包装器"""
    
    def __init__(self, real_agent, color: str, emoji: str):
        self.real_agent = real_agent
        self.color = color
        self.emoji = emoji
        self.location = real_agent.current_location
        # 添加profession属性
        self.profession = real_agent.profession
        self.name = real_agent.name
    
    def get_status(self):
        """获取状态"""
        return {
            'location': self.location,
            'mood': self.real_agent.current_mood,
            'energy': self.real_agent.energy_level,
            'current_action': getattr(self.real_agent, 'current_action', '闲逛')
        }
    
    def respond(self, message: str) -> str:
        """响应消息"""
        return self.real_agent.think_and_respond(message)
    
    def think_and_respond(self, situation: str) -> str:
        """思考并回应"""
        return self.real_agent.think_and_respond(situation)
    
    def update_status(self):
        """更新状态"""
        if hasattr(self.real_agent, 'update_status'):
            self.real_agent.update_status()
        # 同步位置
        self.location = self.real_agent.current_location
    
    def think(self) -> str:
        """思考"""
        thoughts = [
            f"我在{self.location}思考着...",
            "最近的工作让我学到了很多",
            "这个地方很适合思考",
            "我想起了一些往事"
        ]
        return random.choice(thoughts)
    
    def interact_with(self, other_agent) -> str:
        """与其他Agent交互"""
        greetings = [
            f"嗨，{other_agent.name}！",
            f"在{self.location}遇到你真巧！",
            "今天过得怎么样？",
            "有什么新鲜事吗？"
        ]
        return random.choice(greetings)

class SimpleAgent:
    """简化版Agent"""
    
    def __init__(self, name: str, profession: str, color: str, emoji: str):
        self.name = name
        self.profession = profession
        self.color = color
        self.emoji = emoji
        self.location = '家'
        self.mood = '平静'
        self.energy = 80
        self.current_action = '闲逛'
    
    def get_status(self):
        """获取状态"""
        return {
            'location': self.location,
            'mood': self.mood,
            'energy': self.energy,
            'current_action': self.current_action
        }
    
    def respond(self, message: str) -> str:
        """简化响应"""
        responses = {
            'Alex': [
                "作为程序员，我觉得这个问题很有趣。",
                "让我从技术角度思考一下...",
                "这让我想到了一个算法问题。",
                "编程世界里总有解决方案。",
                "代码的美在于逻辑的清晰。"
            ],
            'Emma': [
                "这激发了我的创作灵感！",
                "从艺术的角度来看，很有意思。",
                "我想用画笔记录下这个想法。",
                "美好的事物总是让人感动。",
                "艺术来源于生活的每一个细节。"
            ],
            'Sarah': [
                "这是一个很好的学习机会！",
                "让我来解释一下这个概念...",
                "分享知识是一件快乐的事。",
                "每个问题都有它的教育价值。",
                "我们一起来探讨这个话题吧。"
            ],
            'David': [
                "从商业角度看，这很有潜力。",
                "我们可以考虑这样的投资机会。",
                "效率和成果是关键指标。",
                "让我们谈谈如何实现盈利。",
                "成功的秘诀在于抓住机遇。"
            ],
            'Lisa': [
                "哇，这太有趣了！我想了解更多。",
                "作为学生，我总是充满好奇心。",
                "这个话题我们课堂上讨论过。",
                "学习新东西总是让我兴奋。",
                "我要把这个记在我的笔记里。"
            ],
            'Mike': [
                "这让我想起了年轻时的经历。",
                "根据我的人生经验...",
                "年轻人，这个问题很有深度。",
                "时间会告诉我们答案。",
                "智慧来源于生活的积累。"
            ],
            'John': [
                "从健康的角度来说...",
                "我建议要注意身体状况。",
                "预防总是比治疗更重要。",
                "健康是最大的财富。",
                "让我们关注一下安全问题。"
            ],
            'Anna': [
                "这就像烹饪一样，需要合适的配料。",
                "让我用美食来比喻一下...",
                "温暖的食物能治愈心灵。",
                "每个人都有自己的口味偏好。",
                "料理的艺术在于用心调配。"
            ],
            'Tom': [
                "这个问题很实际，需要动手解决。",
                "机械的原理其实很简单。",
                "修理东西就是要找到问题根源。",
                "实用性是最重要的考虑因素。",
                "工具合适，事半功倍。"
            ]
        }
        
        agent_responses = responses.get(self.name, ["我理解你的意思。", "这很有趣！"])
        return random.choice(agent_responses)
    
    def think_and_respond(self, situation: str) -> str:
        """思考并回应 - 简化版本"""
        # 简化Agent的智能回应
        contextual_responses = {
            'Alex': {
                '工作': "我正在优化一个算法，代码效率提升了30%。",
                '聊天': "从技术角度来说，这个问题有多种解决方案。",
                '放松': "我在调试代码的间隙，思考一下架构设计。",
                '移动': "我想去办公室，那里有更好的开发环境。",
                '默认': "作为程序员，我习惯用逻辑思维分析问题。"
            },
            'Emma': {
                '工作': "我正在创作一幅描绘城市黄昏的画作。",
                '聊天': "艺术就是要表达内心最真实的感受。",
                '放松': "我在公园里寻找创作灵感，自然的色彩很美。",
                '移动': "我想去艺术馆，那里的作品总能启发我。",
                '默认': "生活中的每个细节都可能成为艺术的素材。"
            },
            'Sarah': {
                '工作': "我在准备明天的课程，希望让学生们更好理解这个概念。",
                '聊天': "教育的本质是点亮学生心中的求知欲。",
                '放松': "阅读是我最好的放松方式，知识让人充实。",
                '移动': "图书馆是我的第二个家，安静的环境适合思考。",
                '默认': "分享知识是一件非常有意义的事情。"
            }
        }
        
        # 简单的上下文检测
        context = '默认'
        if any(word in situation for word in ['工作', '职业', '专业']):
            context = '工作'
        elif any(word in situation for word in ['聊天', '说话', '交流']):
            context = '聊天'
        elif any(word in situation for word in ['放松', '休息', '思考']):
            context = '放松'
        elif any(word in situation for word in ['去', '移动', '地方']):
            context = '移动'
        
        agent_contexts = contextual_responses.get(self.name, {})
        if context in agent_contexts:
            return agent_contexts[context]
        else:
            return agent_contexts.get('默认', self.respond(situation))
    
    def update_status(self):
        """更新状态"""
        # 简化的状态更新
        moods = ['平静', '愉快', '思考', '专注', '放松']
        if random.random() < 0.3:
            self.mood = random.choice(moods)
        
        self.energy = max(10, self.energy - random.randint(1, 3))
        if self.energy < 30:
            self.mood = '疲惫'
    
    def think(self) -> str:
        """思考"""
        thoughts = {
            'Alex': ["代码还可以优化...", "新技术值得学习", "这个Bug需要仔细调试", "算法效率还能提升"],
            'Emma': ["这个颜色很有趣", "想要创作新作品", "自然的光影变化很美", "艺术灵感来了"],
            'Sarah': ["学生们今天表现不错", "需要准备明天的课程", "教育方法可以改进", "知识传播很重要"],
            'David': ["市场机会不错", "投资回报率如何", "商业模式需要优化", "竞争对手在做什么"],
            'Lisa': ["这门课程很有意思", "考试要好好准备", "实习机会要把握", "未来规划很重要"],
            'Mike': ["年轻人真有活力", "时代变化真快", "经验值得分享", "健康最重要"],
            'John': ["病人的康复很重要", "医疗技术在进步", "预防胜过治疗", "同理心很关键"],
            'Anna': ["新食谱值得尝试", "食材的搭配很重要", "客人的笑容最珍贵", "烹饪是种艺术"],
            'Tom': ["这个机器需要保养", "工具要保持锋利", "安全操作最重要", "经验比理论重要"]
        }
        
        agent_thoughts = thoughts.get(self.name, ["我在思考..."])
        return random.choice(agent_thoughts)
    
    def interact_with(self, other_agent) -> str:
        """与其他Agent交互"""
        return f"嗨，{other_agent.name}！很高兴见到你。"

def main():
    """主函数"""
    try:
        town = TerminalTown()
        town.run()
    except Exception as e:
        print(f"{TerminalColors.RED}❌ 程序启动失败: {e}{TerminalColors.END}")

if __name__ == "__main__":
    main()
