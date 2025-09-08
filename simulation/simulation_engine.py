"""
模拟引擎模块
负责Agent的自动模拟逻辑
"""

import time
import random
import threading
import logging
import concurrent.futures
from datetime import datetime
from display.terminal_colors import TerminalColors

logger = logging.getLogger(__name__)

class SimulationEngine:
    """模拟引擎"""
    
    def __init__(self, thread_manager, response_cleaner_func, behavior_manager=None, agents_ref=None, buildings_ref=None, agent_manager=None):
        self.thread_manager = thread_manager
        self.clean_response = response_cleaner_func
        self.auto_simulation = False
        self.simulation_thread = None
        self.running = True
        self.behavior_manager = behavior_manager  # 保存behavior_manager为实例变量
        self.last_actions = {}  # 记录每个Agent的最近行动，避免重复
        self.active_interactions = set()  # 记录正在进行的交互，避免重复
        self.simulation_lock = threading.Lock()  # 模拟执行锁
        
        # 添加依赖引用
        self.agents_ref = agents_ref  # 对agents字典的引用
        self.buildings_ref = buildings_ref  # 对buildings字典的引用
        self.agent_manager = agent_manager  # agent_manager引用
        
        logger.info("🔄 模拟引擎已初始化")
    
    def toggle_auto_simulation(self):
        """简单切换自动模拟状态"""
        # 防止多线程重复启动
        if not self.auto_simulation:
            # 开启自动模拟
            self.auto_simulation = True
            print(f"{TerminalColors.GREEN}🤖 自动模拟已开启！Agent将开始自主行动{TerminalColors.END}")
            print(f"{TerminalColors.CYAN}💡 再次输入 'auto' 可以关闭自动模拟{TerminalColors.END}")
            
            # 如果没有运行的线程，启动一个新的
            if self.simulation_thread is None or not self.simulation_thread.is_alive():
                self.simulation_thread = threading.Thread(
                    target=self._simple_auto_loop, 
                    name="AutoSimulation",
                    daemon=True
                )
                self.simulation_thread.start()
                logger.info("新的自动模拟线程已启动")
            else:
                logger.info("模拟线程已在运行中")
        else:
            # 关闭自动模拟
            self.auto_simulation = False
            print(f"{TerminalColors.YELLOW}⏸️  自动模拟已关闭{TerminalColors.END}")
            logger.info("自动模拟已手动关闭")
    
    def _simple_auto_loop(self):
        """简单的自动模拟循环"""
        logger.info("自动模拟循环启动")
        
        while self.auto_simulation and self.running:
            try:
                # 执行一个模拟步骤
                if hasattr(self, '_execute_simulation_step_safe') and callable(self._execute_simulation_step_safe):
                    success = self._execute_simulation_step_safe()
                    if not success:
                        # 如果模拟步骤失败，短暂休眠后继续
                        time.sleep(3)
                else:
                    logger.warning("_execute_simulation_step_safe 方法未找到，跳过此轮模拟")
                    time.sleep(5)
                
                # 增加模拟步骤间隔，减少刷屏
                time.sleep(random.uniform(5, 10))  # 5-10秒随机间隔，比之前更长
                
            except Exception as e:
                logger.error(f"自动模拟循环错误: {e}")
                time.sleep(8)  # 错误后等待8秒
        
        logger.info("自动模拟循环结束")
    
    def choose_agent_action(self, agent, agent_name: str) -> str:
        """选择Agent行动类型"""
        # 智能行动选择权重
        action_weights = {
            'social': 35,
            'group_discussion': 20,
            'move': 20,
            'think': 10,
            'work': 10,
            'relax': 5
        }
        
        # 获取Agent最近的行动，避免重复
        if agent_name in self.last_actions:
            last_action = self.last_actions[agent_name]
            # 降低最近执行过的行动的权重
            if last_action in action_weights:
                action_weights[last_action] = max(1, action_weights[last_action] - 15)
        
        # 根据Agent状态调整权重
        energy = getattr(agent, 'energy', 80)
        if energy < 30:
            action_weights['relax'] += 20
            action_weights['work'] -= 5
        
        # 根据位置调整权重
        location = getattr(agent, 'location', '家')
        if location in ['办公室', '修理店']:
            action_weights['work'] += 15
        elif location in ['公园', '家']:
            action_weights['relax'] += 10
        elif location in ['咖啡厅', '图书馆']:
            action_weights['social'] += 10
        
        # 加权随机选择
        actions = []
        for action, weight in action_weights.items():
            actions.extend([action] * max(1, weight))
        
        chosen_action = random.choice(actions)
        
        # 记录Agent的最近行动
        self.last_actions[agent_name] = chosen_action
        
        return chosen_action
    
    def execute_solo_thinking(self, agent, agent_name: str, location: str) -> bool:
        """执行独自思考"""
        try:
            think_prompt = f"在{location}独自思考："
            
            # 异步获取思考内容
            def get_thought():
                if hasattr(agent, 'real_agent'):
                    return agent.real_agent.think_and_respond(think_prompt)
                return "在安静地思考..."
            
            future = self.thread_manager.submit_task(get_thought)
            try:
                thought = future.result(timeout=10.0)
                cleaned_thought = self.clean_response(thought)
            except concurrent.futures.TimeoutError:
                cleaned_thought = "在深度思考中..."
            
            print(f"\n{TerminalColors.BOLD}━━━ 💭 独自思考 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.YELLOW}{agent_name}{TerminalColors.END}: {cleaned_thought}")
            print()
            
            return True
            
        except Exception as e:
            logger.error(f"执行独自思考异常: {e}")
            return False
    
    def execute_think_action_safe(self, agent, agent_name: str) -> bool:
        """安全执行思考行动"""
        try:
            current_location = getattr(agent, 'location', '家')
            think_prompt = f"在{current_location}思考当前的情况："
            
            def get_thought():
                if hasattr(agent, 'real_agent'):
                    return agent.real_agent.think_and_respond(think_prompt)
                return "在思考人生..."
            
            future = self.thread_manager.submit_task(get_thought)
            try:
                thought = future.result(timeout=15.0)
                cleaned_thought = self.clean_response(thought)
            except concurrent.futures.TimeoutError:
                cleaned_thought = "陷入了深度思考..."
            
            print(f"\n{TerminalColors.BOLD}━━━ 💭 思考 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.YELLOW}{agent_name}{TerminalColors.END}: {cleaned_thought}")
            print()
            
            # 思考后可能更新Agent状态
            if hasattr(agent, 'update_status'):
                self.thread_manager.submit_task(agent.update_status)
            
            return True
            
        except Exception as e:
            logger.error(f"执行思考行动异常: {e}")
            return False
    
    def execute_work_action_safe(self, agent, agent_name: str) -> bool:
        """安全执行工作行动"""
        try:
            profession = getattr(agent, 'profession', '通用')
            
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
            
            works = profession_works.get(profession, ["专注工作"])
            work_activity = random.choice(works)
            
            print(f"\n{TerminalColors.BOLD}━━━ 💼 工作 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.BLUE}{agent_name}{TerminalColors.END}: {work_activity}")
            print()
            
            # 工作后恢复精力（线程安全）
            def update_energy():
                with self.thread_manager.agents_lock:
                    if hasattr(agent, 'energy_level'):
                        agent.energy_level = min(100, agent.energy_level + random.randint(5, 15))
                    elif hasattr(agent, 'energy'):
                        agent.energy = min(100, agent.energy + random.randint(5, 15))
            
            self.thread_manager.submit_task(update_energy)
            return True
            
        except Exception as e:
            logger.error(f"执行工作行动异常: {e}")
            return False
    
    def execute_relax_action_safe(self, agent, agent_name: str) -> bool:
        """安全执行放松行动"""
        try:
            relax_activities = [
                "散步放松", "听音乐休息", "喝茶思考", "看书充电",
                "晒太阳", "呼吸新鲜空气", "欣赏风景", "静坐冥想"
            ]
            relax_activity = random.choice(relax_activities)
            
            print(f"\n{TerminalColors.BOLD}━━━ 🌸 放松 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.GREEN}{agent_name}{TerminalColors.END}: {relax_activity}")
            print()
            
            # 放松后恢复精力和改善心情（线程安全）
            def update_wellness():
                with self.thread_manager.agents_lock:
                    if hasattr(agent, 'energy_level'):
                        agent.energy_level = min(100, agent.energy_level + random.randint(10, 20))
                        if hasattr(agent, 'current_mood') and agent.current_mood in ["疲惫", "焦虑", "紧张"]:
                            agent.current_mood = random.choice(["平静", "愉快", "舒适"])
                    elif hasattr(agent, 'energy'):
                        agent.energy = min(100, agent.energy + random.randint(10, 20))
            
            self.thread_manager.submit_task(update_wellness)
            return True
            
        except Exception as e:
            logger.error(f"执行放松行动异常: {e}")
            return False
    
    def execute_social_action_safe(self, agents, agent, agent_name: str) -> bool:
        """统一的社交行动执行入口"""
        try:
            return self._unified_social_execution(agents, agent, agent_name)
        except Exception as e:
            logger.error(f"执行社交行动异常: {e}")
            return self._fallback_solo_thinking(agent, agent_name)
    
    def _unified_social_execution(self, agents, agent, agent_name: str) -> bool:
        """统一的社交执行逻辑"""
        current_location = getattr(agent, 'location', '家')
        
        # 线程安全地找到同位置的其他Agent
        with self.thread_manager.agents_lock:
            other_agents = [
                name for name, other_agent in agents.items()
                if name != agent_name and getattr(other_agent, 'location', '家') == current_location
            ]
        
        if not other_agents:
            return self._fallback_solo_thinking(agent, agent_name)
        
        # 选择交互对象
        target_agent_name = random.choice(other_agents)
        target_agent = agents[target_agent_name]
        
        # 执行社交互动
        return self._execute_social_interaction(
            agent, agent_name, target_agent, target_agent_name, current_location
        )
    
    def _execute_social_interaction(self, agent1, agent1_name: str, agent2, agent2_name: str, location: str) -> bool:
        """执行社交互动的核心逻辑"""
        try:
            # 创建交互标识符，防止重复交互
            interaction_id = tuple(sorted([agent1_name, agent2_name]))
            
            # 检查是否已有活跃交互
            with self.simulation_lock:
                if interaction_id in self.active_interactions:
                    logger.info(f"跳过重复交互: {agent1_name} ↔ {agent2_name}")
                    return False
                self.active_interactions.add(interaction_id)
            
            try:
                # 确保两人在同一位置
                if getattr(agent1, 'location') != getattr(agent2, 'location'):
                    agent2.move_to(location)
                    if hasattr(agent2, 'real_agent'):
                        agent2.real_agent.current_location = location
                
                # 获取当前关系强度
                if self.behavior_manager:
                    current_relationship = self.behavior_manager.get_relationship_strength(agent1_name, agent2_name)
                else:
                    current_relationship = 50  # 默认中性关系
                
                # 显示对话标题
                print(f"\n{TerminalColors.BOLD}━━━ 💬 对话交流 ━━━{TerminalColors.END}")
                print(f"📍 地点: {location}")
                print(f"👥 参与者: {agent1_name} ↔ {agent2_name} (关系: {current_relationship})")
                
                # Agent1发起对话
                topic_prompt = f"在{location}遇到{agent2_name}，简短地打个招呼或说句话："
                topic = agent1.think_and_respond(topic_prompt)
                topic = self.clean_response(topic)
                
                print(f"  {agent1.emoji} {TerminalColors.CYAN}{agent1_name} → {agent2_name}{TerminalColors.END}: {topic}")
                
                # 根据关系决定互动类型
                interaction_type = self._choose_interaction_type(current_relationship)
                
                # Agent2回应
                response = self._generate_agent_response(agent2, agent2_name, agent1_name, topic, interaction_type)
                display_color = self._get_interaction_color(interaction_type)
                
                print(f"  {agent2.emoji} {display_color}{agent2_name} → {agent1_name}{TerminalColors.END}: {response}")
                
                # Agent1的反馈
                feedback = self._generate_feedback_response(agent1, agent1_name, agent2_name, response, interaction_type)
                feedback_color = self._get_interaction_color(interaction_type)
                
                print(f"  {agent1.emoji} {feedback_color}{agent1_name} → {agent2_name}{TerminalColors.END}: {feedback}")
                
                # 更新社交网络
                self._update_relationship(agent1_name, agent2_name, interaction_type, location)
                
                print()  # 空行分隔
                return True
                
            finally:
                # 清理活跃交互标识
                with self.simulation_lock:
                    self.active_interactions.discard(interaction_id)
            
        except Exception as e:
            logger.error(f"执行社交互动异常: {e}")
            # 确保清理
            with self.simulation_lock:
                interaction_id = tuple(sorted([agent1_name, agent2_name]))
                self.active_interactions.discard(interaction_id)
            return False
    
    def _fallback_solo_thinking(self, agent, agent_name: str) -> bool:
        """后备的独自思考行动"""
        try:
            current_location = getattr(agent, 'location', '家')
            think_prompt = f"在{current_location}独自思考："
            
            # 使用线程池获取思考内容
            future = self.thread_manager.submit_task(lambda: agent.think_and_respond(think_prompt))
            try:
                thought = future.result(timeout=8.0)
                cleaned_thought = self.clean_response(thought)
            except Exception:
                cleaned_thought = "在安静地思考..."
            
            print(f"\n{TerminalColors.BOLD}━━━ 💭 独自思考 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.YELLOW}{agent_name}{TerminalColors.END}: {cleaned_thought}")
            print()
            
            return True
            
        except Exception as e:
            logger.error(f"独自思考异常: {e}")
            return False

    def stop_simulation(self):
        """停止模拟"""
        self.running = False
        self.auto_simulation = False
        
        # 等待模拟线程结束
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=10.0)
    
    def _choose_interaction_type(self, relationship_strength: int) -> str:
        """根据关系强度选择互动类型 - 委托给工具类"""
        from .interaction_utils import InteractionUtils
        return InteractionUtils.choose_interaction_type(relationship_strength)
    
    def _generate_agent_response(self, agent, agent_name: str, other_name: str, topic: str, interaction_type: str) -> str:
        """生成Agent的回应"""
        try:
            # 根据互动类型生成不同的提示词
            if interaction_type == 'friendly_chat':
                prompt = f"{other_name}说：'{topic}'，友好积极地回应："
            elif interaction_type == 'casual_meeting':
                prompt = f"{other_name}说：'{topic}'，简短中性地回应："
            elif interaction_type == 'misunderstanding':
                prompt = f"{other_name}说：'{topic}'，表示困惑不解，不要赞同："
            elif interaction_type == 'argument':
                prompt = f"{other_name}说：'{topic}'，表示不同意和反对："
            else:
                prompt = f"{other_name}说：'{topic}'，简短回应："
            
            response = agent.think_and_respond(prompt)
            response = self.clean_response(response)
            
            # 验证负面互动的真实性
            if interaction_type in ['misunderstanding', 'argument']:
                response = self._ensure_negative_response(response, interaction_type, agent, prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"生成回应异常: {e}")
            return "..."
    
    def _generate_feedback_response(self, agent, agent_name: str, other_name: str, response: str, interaction_type: str) -> str:
        """生成反馈回应"""
        try:
            # 限制回应长度，确保简洁连贯
            max_length = 50  # 最大字符数限制
            
            if interaction_type == 'friendly_chat':
                prompt = f"{other_name}说：'{response}'，用1-2句话表示认同或进一步交流："
            elif interaction_type == 'casual_meeting':
                prompt = f"{other_name}说：'{response}'，用1句话简单回应或结束对话："
            elif interaction_type == 'misunderstanding':
                prompt = f"{other_name}说：'{response}'，用1句话尝试澄清或表示困惑："
            elif interaction_type == 'argument':
                prompt = f"{other_name}说：'{response}'，用1句话继续表达不同观点："
            else:
                prompt = f"{other_name}说：'{response}'，简短回应："
            
            feedback = agent.think_and_respond(prompt)
            feedback = self.clean_response(feedback)
            
            # 限制回应长度
            if len(feedback) > max_length:
                # 截取到最后一个完整的句子
                sentences = feedback.split('。')
                if len(sentences) > 1 and len(sentences[0]) <= max_length:
                    feedback = sentences[0] + '。'
                else:
                    feedback = feedback[:max_length] + '...'
            
            return feedback
            
        except Exception as e:
            logger.error(f"生成反馈异常: {e}")
            return "好的。"
    
    def _ensure_negative_response(self, response: str, interaction_type: str, agent, prompt: str) -> str:
        """确保负面互动的真实性"""
        # 检查回应是否真的是负面的
        positive_indicators = ['好', '棒', '对', '是', '赞同', '同意', '理解', '明白', '谢谢', '太好了']
        if any(indicator in response for indicator in positive_indicators):
            # 如果生成了正面回应，使用默认的负面回应
            if interaction_type == 'argument':
                default_responses = [
                    "我不这么认为。",
                    "这说不通。",
                    "我不同意你的观点。",
                    "这听起来不对。"
                ]
                response = random.choice(default_responses)
            elif interaction_type == 'misunderstanding':
                default_responses = [
                    "我有点困惑，不太明白。",
                    "这听起来很奇怪。",
                    "我不太理解你的意思。",
                    "这是什么意思？"
                ]
                response = random.choice(default_responses)
        
        return response
    
    def _get_interaction_color(self, interaction_type: str) -> str:
        """获取互动类型对应的显示颜色"""
        color_map = {
            'friendly_chat': TerminalColors.GREEN,
            'casual_meeting': TerminalColors.YELLOW,
            'misunderstanding': TerminalColors.RED,
            'argument': TerminalColors.RED,
            'deep_conversation': TerminalColors.CYAN,
            'collaboration': TerminalColors.BLUE
        }
        return color_map.get(interaction_type, TerminalColors.YELLOW)
    
    def _update_relationship(self, agent1_name: str, agent2_name: str, interaction_type: str, location: str):
        """更新社交关系"""
        try:
            if not self.behavior_manager:
                logger.warning("behavior_manager未初始化，跳过关系更新")
                return None
                
            # 立即更新关系
            relationship_info = self.behavior_manager.update_social_network(
                agent1_name, agent2_name, interaction_type, 
                {
                    'same_location': True,
                    'location': location,
                    'interaction_initiator': agent1_name,
                    'description': f"在{location}的{interaction_type}互动"
                }
            )
            
            # 显示关系变化
            if relationship_info and relationship_info.get('change', 0) != 0:
                change_color = TerminalColors.GREEN if relationship_info['change'] > 0 else TerminalColors.RED
                change_symbol = "+" if relationship_info['change'] > 0 else ""
                
                # 根据互动类型显示不同的图标
                icon_map = {
                    'friendly_chat': "💫",
                    'casual_meeting': "💭",
                    'misunderstanding': "❓",
                    'argument': "💥"
                }
                icon = icon_map.get(interaction_type, "🔄")
                
                print(f"  {icon} {relationship_info.get('relationship_emoji', '🤝')} "
                      f"{relationship_info.get('new_level', '普通')} "
                      f"({change_color}{change_symbol}{relationship_info['change']:.1f}{TerminalColors.END})")
                
                # 只在重大等级变化时显示详情
                if relationship_info.get('level_changed', False):
                    level_color = TerminalColors.GREEN if relationship_info['new_strength'] > relationship_info['old_strength'] else TerminalColors.YELLOW
                    print(f"    {level_color}🌟 {relationship_info.get('level_change_message', '关系等级发生变化')}{TerminalColors.END}")
            
            # 异步后台处理
            interaction_data = {
                'agent1_name': agent1_name,
                'agent2_name': agent2_name,
                'interaction_type': interaction_type,
                'location': location,
                'context': {
                    'same_location': True,
                    'location': location,
                    'interaction_initiator': agent1_name,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            self.thread_manager.add_interaction_task(interaction_data)
            # 简化日志：只在调试模式下输出详细信息
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"📤 交互任务已添加到队列: {agent1_name} ↔ {agent2_name}")
            
        except Exception as e:
            logger.error(f"更新社交关系失败: {e}")

    def execute_group_discussion_safe(self, agents, agent, agent_name: str) -> bool:
        """统一的群体讨论执行"""
        try:
            # 如果有社交处理器，委托给它处理
            if self.social_handler:
                return self.social_handler.execute_group_discussion_safe(agents, agent, agent_name)
            else:
                # 后备简单实现
                current_location = getattr(agent, 'location', '家')
                print(f"\n{TerminalColors.BOLD}━━━ 👥 群体讨论 ━━━{TerminalColors.END}")
                print(f"  {agent.emoji} {TerminalColors.BLUE}{agent_name}{TerminalColors.END} 在{current_location}参与群体讨论")
                print()
                return True
        except Exception as e:
            logger.error(f"群体讨论异常: {e}")
            return False
    
    def _execute_simulation_step_safe(self) -> bool:
        """执行一个安全的模拟步骤"""
        try:
            if not self.agents_ref or not self.agents_ref():
                logger.warning("没有可用的Agent进行模拟")
                return False
            
            agents = self.agents_ref()
            buildings = self.buildings_ref() if self.buildings_ref else {}
            
            # 获取所有Agent列表
            with self.thread_manager.agents_lock:
                available_agents = list(agents.items())
            
            if not available_agents:
                return False
            
            # 随机选择一个Agent
            agent_name, agent = random.choice(available_agents)
            
            # 检查Agent是否有效
            if not agent:
                logger.warning(f"Agent {agent_name} 无效")
                return False
            
            # 选择行动类型
            action = self.choose_agent_action(agent, agent_name)
            
            # 执行相应的行动
            success = False
            try:
                if action == 'social':
                    success = self.execute_social_action_safe(agents, agent, agent_name)
                elif action == 'group_discussion':
                    success = self.execute_group_discussion_safe(agents, agent, agent_name)
                elif action == 'move':
                    success = self._execute_move_action_safe(agent, agent_name, buildings)
                elif action == 'think':
                    success = self.execute_think_action_safe(agent, agent_name)
                elif action == 'work':
                    success = self.execute_work_action_safe(agent, agent_name)
                elif action == 'relax':
                    success = self.execute_relax_action_safe(agent, agent_name)
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
    
    def _execute_move_action_safe(self, agent, agent_name: str, buildings: dict) -> bool:
        """安全执行移动行动"""
        try:
            current_location = getattr(agent, 'location', '家')
            available_locations = [loc for loc in buildings.keys() if loc != current_location]
            
            if not available_locations:
                return False
            
            new_location = random.choice(available_locations)
            
            # 执行移动 - 使用agent_manager
            if self.agent_manager:
                agents = self.agents_ref() if self.agents_ref else {}
                success = self.agent_manager.move_agent(
                    agents, buildings, self.behavior_manager, agent_name, new_location
                )
                
                if success:
                    print(f"\n{TerminalColors.BOLD}━━━ 🚶 移动 ━━━{TerminalColors.END}")
                    print(f"  {agent.emoji} {TerminalColors.MAGENTA}{agent_name}{TerminalColors.END}: {current_location} → {new_location}")
                    print()
                    
                    # 保存移动事件到向量数据库
                    movement_task = {
                        'type': 'movement',
                        'agent_name': agent_name,
                        'old_location': current_location,
                        'new_location': new_location,
                        'reason': 'autonomous_movement',
                        'timestamp': datetime.now().isoformat()
                    }
                    self.thread_manager.add_memory_task(movement_task)
                
                return success
            else:
                logger.warning("没有可用的agent_manager")
                return False
                
        except Exception as e:
            logger.error(f"执行移动行动异常: {e}")
            return False
