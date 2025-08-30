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
from simulation.social_interaction import SocialInteractionHandler

logger = logging.getLogger(__name__)

class SimulationEngine:
    """模拟引擎"""
    
    def __init__(self, thread_manager, response_cleaner_func, behavior_manager=None):
        self.thread_manager = thread_manager
        self.clean_response = response_cleaner_func
        self.auto_simulation = False
        self.simulation_thread = None
        self.running = True
        
        # 初始化社交交互处理器
        if behavior_manager:
            self.social_handler = SocialInteractionHandler(
                thread_manager, behavior_manager, response_cleaner_func
            )
        else:
            self.social_handler = None
    
    def toggle_auto_simulation(self):
        """切换自动模拟 - 线程安全版本"""
        with self.thread_manager.get_simulation_condition():
            self.auto_simulation = not self.auto_simulation
            
            if self.auto_simulation:
                print(f"{TerminalColors.GREEN}🤖 自动模拟已开启！Agent将开始自主行动{TerminalColors.END}")
                if self.simulation_thread is None or not self.simulation_thread.is_alive():
                    self.simulation_thread = threading.Thread(
                        target=self._auto_simulation_loop_safe, 
                        name="AutoSimulation",
                        daemon=True
                    )
                    self.simulation_thread.start()
                self.thread_manager.get_simulation_condition().notify_all()
            else:
                print(f"{TerminalColors.YELLOW}⏸️  自动模拟已暂停{TerminalColors.END}")
                self.thread_manager.get_simulation_condition().notify_all()
    
    def _auto_simulation_loop_safe(self):
        """线程安全的自动模拟循环"""
        logger.info("自动模拟循环启动（线程安全版本）")
        retry_count = 0
        max_retries = 3
        
        while self.running and not self.thread_manager.is_shutdown():
            try:
                with self.thread_manager.get_simulation_condition():
                    # 等待自动模拟开启
                    while not self.auto_simulation and not self.thread_manager.is_shutdown():
                        self.thread_manager.get_simulation_condition().wait()
                    
                    if self.thread_manager.is_shutdown():
                        break
                
                # 执行一轮模拟
                success = self._execute_simulation_step_safe()
                
                if success:
                    retry_count = 0  # 重置重试计数
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error("模拟步骤连续失败，暂停自动模拟")
                        with self.thread_manager.get_simulation_condition():
                            self.auto_simulation = False
                        break
                
                # 动态调整休眠时间
                sleep_time = random.uniform(2, 5) if success else min(10, 2 ** retry_count)
                time.sleep(sleep_time)
                
            except Exception as e:
                retry_count += 1
                logger.error(f"自动模拟循环异常 (重试 {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    logger.critical("自动模拟多次失败，停止模拟")
                    with self.thread_manager.get_simulation_condition():
                        self.auto_simulation = False
                    break
                    
                time.sleep(min(30, 5 * retry_count))  # 指数退避
        
        logger.info("自动模拟循环结束")
    
    def _execute_simulation_step_safe(self) -> bool:
        """执行一个安全的模拟步骤"""
        # 注意：这个方法在模拟引擎中，但需要访问主类的agents
        # 我们需要通过回调或者其他方式来访问agents
        logger.warning("_execute_simulation_step_safe 需要在主类中重写以访问agents")
        return False
    
    def choose_agent_action(self, agent, agent_name: str) -> str:
        """选择Agent行动类型 - 改进版本，确保行为多样性"""
        # 基础行动权重 - 平衡各种行为
        action_weights = {
            'social': 25,           # 社交对话
            'group_discussion': 15, # 群体讨论  
            'move': 25,            # 移动
            'think': 15,           # 思考
            'work': 15,            # 工作
            'relax': 5             # 放松
        }
        
        # 根据Agent状态调整权重
        energy = getattr(agent, 'energy', 80)
        if energy < 30:
            # 低能量时更倾向于放松和思考
            action_weights['relax'] += 25
            action_weights['think'] += 10
            action_weights['social'] -= 10
            action_weights['work'] -= 15
        elif energy > 70:
            # 高能量时更倾向于社交和工作
            action_weights['social'] += 10
            action_weights['work'] += 10
            action_weights['move'] += 5
        
        # 根据位置调整权重
        location = getattr(agent, 'location', '家')
        if location in ['办公室', '修理店']:
            action_weights['work'] += 20
            action_weights['social'] += 5  # 工作场所也可能有社交
            action_weights['move'] -= 10
        elif location in ['公园', '家']:
            action_weights['relax'] += 15
            action_weights['think'] += 10
            action_weights['move'] -= 5
        elif location in ['咖啡厅', '图书馆']:
            action_weights['social'] += 15
            action_weights['group_discussion'] += 10
            action_weights['think'] += 5
        elif location in ['餐厅']:
            action_weights['social'] += 20
            action_weights['group_discussion'] += 15
        
        # 根据时间和交互历史调整
        interaction_count = getattr(agent, 'interaction_count', 0)
        
        # 如果最近社交较少，增加社交权重
        if interaction_count < 3:
            action_weights['social'] += 15
            action_weights['group_discussion'] += 10
        
        # 如果很久没移动，增加移动权重
        if not hasattr(agent, '_last_move_time') or True:  # 简化处理
            action_weights['move'] += 10
        
        # 职业相关的行为偏好
        profession = getattr(agent.real_agent, 'profession', '通用') if hasattr(agent, 'real_agent') else '通用'
        if profession in ['程序员', '医生', '老师']:
            action_weights['work'] += 10
            action_weights['think'] += 5
        elif profession in ['艺术家', '学生']:
            action_weights['think'] += 10
            action_weights['relax'] += 5
        elif profession in ['商人', '厨师']:
            action_weights['social'] += 10
            action_weights['work'] += 5
        elif profession == '退休人员':
            action_weights['relax'] += 15
            action_weights['social'] += 10
            action_weights['work'] -= 10
        
        # 确保所有权重为正数
        for action in action_weights:
            action_weights[action] = max(1, action_weights[action])
        
        # 创建加权列表
        actions = []
        for action, weight in action_weights.items():
            actions.extend([action] * weight)
        
        selected_action = random.choice(actions)
        
        # 记录选择的行动类型（用于调试）
        logger.debug(f"{agent_name} 选择行动: {selected_action} (权重: {action_weights})")
        
        return selected_action
    
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
        """安全执行社交行动 - 改进版本"""
        if self.social_handler:
            return self.social_handler.execute_social_action_safe(agents, agent, agent_name)
        else:
            # 回退到基本版本
            return self._basic_social_action(agents, agent, agent_name)
    
    def execute_group_discussion_safe(self, agents, agent, agent_name: str) -> bool:
        """安全执行群体讨论"""
        if self.social_handler:
            return self.social_handler.execute_group_discussion_safe(agents, agent, agent_name)
        else:
            # 回退到基本版本
            return self._basic_group_discussion(agents, agent, agent_name)
    
    def _basic_social_action(self, agents, agent, agent_name: str) -> bool:
        """基本社交行动（后备方案）"""
        try:
            current_location = getattr(agent, 'location', '家')
            print(f"\n{TerminalColors.BOLD}━━━ 💬 社交互动 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END} 在{current_location}进行社交活动")
            print()
            return True
        except Exception as e:
            logger.error(f"基本社交行动异常: {e}")
            return False
    
    def _basic_group_discussion(self, agents, agent, agent_name: str) -> bool:
        """基本群体讨论（后备方案）"""
        try:
            current_location = getattr(agent, 'location', '家')
            print(f"\n{TerminalColors.BOLD}━━━ 👥 群体讨论 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.BLUE}{agent_name}{TerminalColors.END} 在{current_location}参与群体讨论")
            print()
            return True
        except Exception as e:
            logger.error(f"基本群体讨论异常: {e}")
            return False

    def stop_simulation(self):
        """停止模拟"""
        self.running = False
        self.auto_simulation = False
        
        # 等待模拟线程结束
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=10.0)
