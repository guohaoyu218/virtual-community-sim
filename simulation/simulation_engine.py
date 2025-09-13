"""
模拟引擎模块
负责Agent的自动模拟逻辑
"""

import time
import random
import threading
import logging
import concurrent.futures
import re
# === 预编译正则 (高频清理/检测) ===
PAT_CN_BRACKETS = re.compile(r'（[^）]*）')
PAT_EN_BRACKETS = re.compile(r'\([^)]*\)')
PAT_NAME_PREFIX = re.compile(r'^(?:[\w\u4e00-\u9fff]{1,12}[：:,-，]\s*)')
PAT_NUM_SENT = re.compile(r'^["“‘\'\s]*\d+句话[^：:]{0,50}[：:]')
PAT_STYLE_PREFIX = re.compile(r'^["“‘\'\s]*(?:请|用)?[^：:]{0,25}?(?:体现|展现|语气|风格|方式|能力|格式|自信|情绪)[^：:]{0,25}[：:]')
PAT_MISC_PREFIX = re.compile(r'^["“‘\'\s]*(?:两句话|一句话|给出|输出|描述|总结|分析)[^：:]{0,20}[：:]')
PAT_BLACKLIST = re.compile(r'(请用中文|不要英文|只需一句|仅一句|内心独白|系统提示|分析如下|格式为|按照要求|根据要求|不要复述|不要解释|描述一下|给出答案|请回答)')
PAT_SENT_SPLIT_KEEP = re.compile(r'([。！？!?])')
PAT_REMOVE_EN = re.compile(r'[A-Za-z]+')
PAT_RENAME_PREFIX2 = re.compile(r'^(?:[\w\u4e00-\u9fff]{1,12}[：:,-，]\s*)')
PAT_RESTYLE2 = re.compile(r'^(?:请|用|再|继续|需要)?[^，。!?！？]{0,12}(?:语气|风格|方式)[：:，]')
PAT_MULTI_SPACE = re.compile(r'\s+')
PAT_MULTI_COMMA = re.compile(r'[，,]{2,}')
PAT_MULTI_END = re.compile(r'[。!！?？]{2,}')
PAT_QUOTES = re.compile(r'["“”‘’]+')
PAT_DUP_WORD = re.compile(r'(\b\S{1,6}\b)(\s+\1){1,3}')
PAT_ENGLISH_DETECT = re.compile(r'[a-zA-Z]{2,}')
from datetime import datetime
from display.terminal_colors import TerminalColors
from collections import deque

logger = logging.getLogger(__name__)

class SimulationEngine:
    """模拟引擎"""
    
    def __init__(self, thread_manager, response_cleaner_func, behavior_manager=None, agents_ref=None, buildings_ref=None, agent_manager=None, social_handler=None):
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
        self.social_handler = social_handler  # 可选的社交处理器，用于群体讨论委托

        # recent_actions 用于追踪最近的行动类型，防止讨论占比过高
        self.recent_actions = deque(maxlen=200)
        # 新增：防重复输出控制
        self._auto_hint_shown = False
        self._toggle_lock = threading.Lock()
        # 新增：打印锁，减少多线程输出穿插
        self.print_lock = threading.Lock()
        # 新增：防止重复启动的标志
        self._starting_simulation = False
        # A: 对话缓冲（pair -> deque[(speaker, text, ts)])
        self._pair_convo_buffers = {}
        # === ALL 策略配置 ===
        self.cfg = {
            'feedback_probability': 0.1,          # 维持低反馈触发率，如需彻底关闭设为0.0
            'feedback_async_timeout': 2.5,
            'pair_throttle_seconds': 8,
            'max_generate_retries': 1,
            'loop_sleep_success': (0.6, 1.2),
            'loop_sleep_fail': (0.25, 0.5),
            'enrich_min_core': 6,
            'enrich_enabled': False,              # 已关闭补充
        }
        logger.setLevel(logging.WARNING)  # 降低日志级别
        logger.info("🔄 模拟引擎已初始化 (ALL策略)")
    
    # === A: 一对一对话上下文辅助方法（补充缺失） ===
    def _get_pair_key(self, a: str, b: str):
        try:
            return tuple(sorted([a, b]))
        except Exception:
            return (a, b)

    def _append_pair_message(self, a: str, b: str, speaker: str, text: str):
        try:
            if not text:
                return
            from collections import deque as _dq
            key = self._get_pair_key(a, b)
            buf = self._pair_convo_buffers.get(key)
            if buf is None:
                buf = _dq(maxlen=10)
                self._pair_convo_buffers[key] = buf
            buf.append((speaker, text, time.time()))
        except Exception:
            pass

    def _get_recent_pair_context(self, a: str, b: str, max_messages: int = 2, max_age: int = 300) -> str:
        # 限制 pair 上下文为最近 2 条
        try:
            key = self._get_pair_key(a, b)
            buf = self._pair_convo_buffers.get(key)
            if not buf:
                return ""
            now = time.time()
            recent = [(spk, txt) for spk, txt, ts in list(buf)[-max_messages:] if now - ts <= max_age]
            if not recent:
                return ""
            return "\n".join(f"{spk}:{txt}" for spk, txt in recent)
        except Exception:
            return ""
    # === 结束 ===

    def _sanitize_dialog_reply(self, text: str, length_range=(12, 30), max_len: int = 90, allow_short: bool = False) -> str:
        """多句柔性清理 (1v1 对话专用 - 加强版)
        新增: allow_short=True 时放宽最小长度限制, 不再直接丢弃短回复; 清理前导反引号/逗号等孤立符号。
        """
        try:
            if not text:
                return ""
            filler_set = {"我还想再观察下", "细节还得再看看", "你觉得呢", "可以再说说看"}
            s = self.clean_response(text) if callable(getattr(self, 'clean_response', None)) else text
            s = s.replace('\n', ' ').strip().strip('"“”\'')
            s = PAT_CN_BRACKETS.sub('', s)
            s = PAT_EN_BRACKETS.sub('', s)
            for _ in range(3):
                s = PAT_NAME_PREFIX.sub('', s).strip()
            for _ in range(2):
                s_new = PAT_NUM_SENT.sub('', s)
                s_new = PAT_STYLE_PREFIX.sub('', s_new)
                s_new = PAT_MISC_PREFIX.sub('', s_new)
                if s_new == s:
                    break
                s = s_new.strip()
            raw_parts = PAT_SENT_SPLIT_KEEP.split(s)
            sentences, buf = [], ''
            for seg in raw_parts:
                if not seg:
                    continue
                if PAT_SENT_SPLIT_KEEP.fullmatch(seg):
                    buf += seg
                    if buf.strip():
                        sentences.append(buf.strip())
                    buf = ''
                else:
                    buf += seg
            if buf.strip():
                sentences.append(buf.strip())
            if not sentences:
                sentences = [s]
            cleaned = []
            for sent in sentences:
                sent = PAT_BLACKLIST.sub('', sent)
                sent = sent.strip('：:;；,，。.!?！？ ')
                if sent:
                    cleaned.append(sent)
            sentences = cleaned or sentences
            min_len, soft_max = length_range if length_range else (12, 30)
            result = sentences[0] if sentences else ''
            core_before = PAT_MULTI_SPACE.sub('', re.sub(r'[。！？，,.!？\s]', '', result))
            if len(core_before) < max(6, min_len - 4) and len(sentences) > 1:
                addon = sentences[1]
                addon_core = re.sub(r'[。！？，,.!？\s]', '', addon)
                if addon_core and addon_core != core_before:
                    joiner = '，' if not result.endswith(('，','。','!','！','?','？')) else ''
                    result = result.rstrip('。!?！？') + joiner + addon.strip('。!?！？')
            if len(re.sub(r'[。！？，,.!？\s]', '', result)) < min_len and len(sentences) > 2:
                third = sentences[2]
                if third:
                    joiner = '，' if not result.endswith(('，','。','!','！','?','？')) else ''
                    result += joiner + third.strip('。!?！？')[:12]
            if re.search(r'[\u4e00-\u9fff]', result):
                result = PAT_REMOVE_EN.sub('', result)
            for _ in range(2):
                r2 = PAT_RENAME_PREFIX2.sub('', result).strip()
                r2 = PAT_RESTYLE2.sub('', r2)
                if r2 == result:
                    break
                result = r2
            result = PAT_MULTI_SPACE.sub(' ', result)
            result = PAT_MULTI_COMMA.sub('，', result)
            result = PAT_MULTI_END.sub('。', result)
            result = PAT_QUOTES.sub('', result)
            result = PAT_DUP_WORD.sub(r'\1', result)
            # 去掉前导孤立符号/反引号
            result = re.sub(r'^[`´\'"，,。.!?！？:：;；\s]+', '', result)
            if len(result) > soft_max:
                cut_pos = None
                for m in re.finditer(r'[，,；;。.!?！？]', result):
                    if m.start() <= soft_max:
                        cut_pos = m.end()
                    else:
                        break
                if cut_pos and cut_pos >= int(min_len * 0.6):
                    result = result[:cut_pos].rstrip()
                else:
                    result = result[:soft_max].rstrip('，,；;。.!?！？ ') + '…'
            if len(result) > max_len:
                result = result[:max_len].rstrip('，,；;。.!?！？ ') + '…'
            core_len = len(re.sub(r'[。！？，,.!？\s]', '', result))
            if allow_short:
                # 允许短：只要≥3个核心字就保留
                if core_len < 3:
                    return ""
            else:
                if (result in filler_set and core_len < 6) or re.search(r'句话.*(体现|风格|语气|能力)', result):
                    return ""
                if core_len < max(4, min_len - 6):
                    return ""
            result = PAT_MULTI_COMMA.sub('，', result)
            result = PAT_MULTI_END.sub('。', result)
            if result and not result.endswith(('。','!','！','?','？','…')):
                result += '。'
            return result
        except Exception:
            return (text or '')[:max_len]

    def toggle_auto_simulation(self):
        """切换自动模拟状态，防止重复启动多个线程"""
        with self._toggle_lock:
            # 如果已经在启动过程中，避免重复执行
            if self._starting_simulation:
                with self.print_lock:
                    print(f"{TerminalColors.YELLOW}⏳ 自动模拟正在启动，请稍候...{TerminalColors.END}")
                return
            # 如果当前是开启状态 -> 关闭
            if self.auto_simulation:
                self.auto_simulation = False
                with self.print_lock:
                    print(f"{TerminalColors.YELLOW}⏸️  自动模拟已关闭{TerminalColors.END}")
                logger.info("自动模拟已手动关闭")
                return
            # 需要开启：若线程已存在且存活，则只提示已开启（不再再创建新线程）
            if self.simulation_thread and self.simulation_thread.is_alive():
                self.auto_simulation = True  # 确保标志同步
                with self.print_lock:
                    if not self._auto_hint_shown:
                        print(f"{TerminalColors.GREEN}🤖 自动模拟已开启！Agent将开始自主行动{TerminalColors.END}")
                        print(f"{TerminalColors.CYAN}💡 再次输入 'auto' 可以关闭自动模拟{TerminalColors.END}")
                        self._auto_hint_shown = True
                    else:
                        print(f"{TerminalColors.GREEN}🤖 自动模拟已在运行{TerminalColors.END}")
                logger.info("检测到已有模拟线程，忽略重复开启请求")
                return
            # 创建新线程
            self.auto_simulation = True
            if not self._auto_hint_shown:
                with self.print_lock:
                    print(f"{TerminalColors.GREEN}🤖 自动模拟已开启！Agent将开始自主行动{TerminalColors.END}")
                    print(f"{TerminalColors.CYAN}💡 再次输入 'auto' 可以关闭自动模拟{TerminalColors.END}")
                self._auto_hint_shown = True
            else:
                with self.print_lock:
                    print(f"{TerminalColors.GREEN}🤖 自动模拟已开启{TerminalColors.END}")
            # 标记启动中，防止极短时间内多次触发
            self._starting_simulation = True
            def _thread_entry():
                try:
                    self._starting_simulation = False
                    self._simple_auto_loop()
                finally:
                    # 线程结束时如果标志仍为 True 说明是外部关闭导致结束
                    pass
            self.simulation_thread = threading.Thread(
                target=_thread_entry,
                name="AutoSimulation",
                daemon=True
            )
            self.simulation_thread.start()
            logger.info("新的自动模拟线程已启动")
    
    def _simple_auto_loop(self):
        """简单的自动模拟循环 (加入自适应节奏)"""
        logger.info("自动模拟循环启动")
        base_min, base_max = self.cfg['loop_sleep_success']
        fail_min, fail_max = self.cfg['loop_sleep_fail']
        while self.auto_simulation and self.running:
            try:
                success = False
                if hasattr(self, '_execute_simulation_step_safe') and callable(self._execute_simulation_step_safe):
                    success = self._execute_simulation_step_safe()
                if success:
                    sleep_t = random.uniform(base_min, base_max)
                else:
                    sleep_t = random.uniform(fail_min, fail_max)
                time.sleep(sleep_t)
            except Exception as e:
                logger.error(f"自动模拟循环错误: {e}")
                time.sleep(2)
        logger.info("自动模拟循环结束")
    
    def choose_agent_action(self, agent, agent_name: str) -> str:
        """选择Agent行动类型
        - 基于历史 recent_actions 动态调整社交相关权重，防止讨论占比过高
        - 确保当位置没有其他人时不会选择社交/群体讨论
        """
        # 智能行动选择基础权重
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

        # 降低社交类行为的概率，如果最近历史中社交占比过高
        try:
            recent_len = len(self.recent_actions)
            if recent_len > 0:
                social_count = sum(1 for a in self.recent_actions if a in ('social', 'group_discussion'))
                social_ratio = social_count / recent_len
                # 若最近社交占比超过阈值，则线性衰减社交权重（阈值可调整）
                threshold = 0.35
                if social_ratio > threshold:
                    decay = min(0.9, (social_ratio - threshold) / (1 - threshold))  # 0..0.9
                    action_weights['social'] = max(1, int(action_weights['social'] * (1 - decay)))
                    action_weights['group_discussion'] = max(0, int(action_weights['group_discussion'] * (1 - decay)))
        except Exception:
            pass

        # 检查当前地点是否有其他可交互Agent；若没有则避免选择社交/群体讨论
        try:
            agents = self.agents_ref() if self.agents_ref else {}
            same_location_others = 0
            with self.thread_manager.agents_lock:
                for name, other in agents.items():
                    if name != agent_name and getattr(other, 'location', '家') == location:
                        same_location_others += 1
            if same_location_others == 0:
                # 没有人在同一位置，关闭社交选项
                action_weights['social'] = 0
                action_weights['group_discussion'] = 0
                # 增加移动和放松/思考机会
                action_weights['move'] += 20
                action_weights['think'] += 5
        except Exception:
            pass

        # 将原先构造扩展列表的 O(n) * weight 方式改为累积权重随机
        total_weight = 0
        filtered = {}
        for k,v in action_weights.items():
            if v > 0:
                filtered[k] = v
                total_weight += v
        if total_weight <= 0:
            chosen_action = 'think'
        else:
            r = random.uniform(0, total_weight)
            upto = 0
            chosen_action = 'think'
            for action, w in filtered.items():
                if upto + w >= r:
                    chosen_action = action
                    break
                upto += w

        # 记录Agent的最近行动
        self.last_actions[agent_name] = chosen_action
        # 记录到全局 recent_actions，用于全局频率控制
        try:
            self.recent_actions.append(chosen_action)
        except Exception:
            pass

        return chosen_action
    
    def execute_solo_thinking(self, agent, agent_name: str, location: str) -> bool:
        """执行独自思考"""
        try:
            think_prompt = f"在{location}独自思考："
            
            # 异步获取思考内容
            def get_thought():
                if hasattr(agent, 'real_agent'):
                    return agent.real_agent.think_and_respond(think_prompt + "（请用中文回答，不要使用英文）")
                return "在安静地思考..."
            
            future = self.thread_manager.submit_task(get_thought)
            try:
                thought = future.result(timeout=10.0)
                cleaned_thought = self.clean_response(thought)
            except concurrent.futures.TimeoutError:
                cleaned_thought = "在深度思考中..."
            
            with self.print_lock:
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
                    return agent.real_agent.think_and_respond(think_prompt + "（请用中文回答，不要使用英文）")
                return "在思考人生..."
            
            future = self.thread_manager.submit_task(get_thought)
            try:
                thought = future.result(timeout=15.0)
                cleaned_thought = self.clean_response(thought)
            except concurrent.futures.TimeoutError:
                cleaned_thought = "陷入了深度思考..."
            
            with self.print_lock:
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
            
            with self.print_lock:
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
            
            with self.print_lock:
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
        """执行社交互动的核心逻辑 (精简指令/批量打印/上下文裁剪=2)"""
        try:
            if not hasattr(self, '_recent_interaction_lru'):
                self._recent_interaction_lru = {}
            now_ts = time.time()
            key = tuple(sorted([agent1_name, agent2_name]))
            last_ts = self._recent_interaction_lru.get(key, 0)
            # 节流 使用配置
            if now_ts - last_ts < self.cfg['pair_throttle_seconds']:
                return False
            interaction_id = key
            with self.simulation_lock:
                if interaction_id in self.active_interactions:
                    return False
                self.active_interactions.add(interaction_id)
            try:
                if getattr(agent1, 'location') != getattr(agent2, 'location'):
                    agent2.move_to(location)
                    if hasattr(agent2, 'real_agent'):
                        agent2.real_agent.current_location = location
                if self.behavior_manager:
                    current_relationship = self.behavior_manager.get_relationship_strength(agent1_name, agent2_name)
                else:
                    current_relationship = 50
                if current_relationship < 40:
                    len_range = (12, 26)
                elif current_relationship <= 70:
                    len_range = (16, 34)
                else:
                    len_range = (20, 42)
                lines = []
                lines.append(f"\n{TerminalColors.BOLD}━━━ 💬 对话交流 ━━━{TerminalColors.END}")
                lines.append(f"📍 地点: {location}")
                lines.append(f"👥 参与者: {agent1_name} ↔ {agent2_name} (关系: {current_relationship})")
                pair_context = self._get_recent_pair_context(agent1_name, agent2_name)  # 已裁剪为2
                if pair_context:
                    topic_prompt_base = (
                        f"继续与{agent2_name}的对话。最近交流:\n{pair_context}\n"
                        f"在{location}自然续接一句({len_range[0]}~{len_range[1]}字,中文,具体,不复述):"
                    )
                else:
                    topic_prompt_base = (
                        f"在{location}遇到{agent2_name}，自然开启或延续一句 ({len_range[0]}~{len_range[1]}字,中文,具体):"
                    )
                raw_topic = agent1.think_and_respond(topic_prompt_base)
                topic = self._sanitize_dialog_reply(raw_topic, length_range=len_range, max_len=80)
                def _too_short(t: str) -> bool:
                    core = re.sub(r'[。！？，,.!？\s]','', t)
                    return len(core) < 3 or core in (agent1_name, agent2_name)
                if _too_short(topic):
                    raw_topic_2 = agent1.think_and_respond(topic_prompt_base + " 更具体,带细节或情绪线索。")
                    topic_retry = self._sanitize_dialog_reply(raw_topic_2, length_range=len_range, max_len=80)
                    if not _too_short(topic_retry):
                        topic = topic_retry
                if _too_short(topic):
                    fallbacks_low = ["最近状态怎样，休息得还行吗？","这边有点安静，你觉得呢？","感觉你今天情绪有点不一样。"]
                    fallbacks_mid = ["最近有没有让你分心的事情？","这段时间节奏挺奇怪的，你适应吗？","我在想之前我们提到的那个想法。"]
                    fallbacks_high = ["想起我们之前计划的那件事，不知道你还想继续吗？","感觉你现在心情比前几天稳定些了？","我还在想上次你提到的那个细节。"]
                    if current_relationship < 40:
                        topic = random.choice(fallbacks_low)
                    elif current_relationship <= 70:
                        topic = random.choice(fallbacks_mid)
                    else:
                        topic = random.choice(fallbacks_high)
                if not topic:
                    topic = "你好。"
                lines.append(f"  {agent1.emoji} {TerminalColors.CYAN}{agent1_name} → {agent2_name}{TerminalColors.END}: {topic}")
                self._append_pair_message(agent1_name, agent2_name, agent1_name, topic)
                interaction_type = self._choose_interaction_type(current_relationship)
                response = self._generate_agent_response(agent2, agent2_name, agent1_name, topic, interaction_type, pair_context=pair_context, length_range=len_range)
                response = self._sanitize_dialog_reply(response, length_range=len_range, max_len=85)
                if self.cfg['enrich_enabled'] and len(re.sub(r'[。！？，,.!？\s]','', response)) < max(self.cfg['enrich_min_core'], len_range[0]-5):
                    enrich_prompt = f"针对'{topic}' 输出更具体自然回应 (可补短分句,{len_range[0]}~{len_range[1]}字):"
                    try:
                        rich = agent2.think_and_respond(enrich_prompt)
                        rich_clean = self._sanitize_dialog_reply(rich, length_range=len_range, max_len=85)
                        if len(re.sub(r'[。！？，,.!？\s]','', rich_clean)) >= len_range[0]-4:
                            response = rich_clean
                    except Exception:
                        pass
                display_color = self._get_interaction_color(interaction_type)
                lines.append(f"  {agent2.emoji} {display_color}{agent2_name} → {agent1_name}{TerminalColors.END}: {response}")
                self._append_pair_message(agent1_name, agent2_name, agent2_name, response)
                use_model_feedback = random.random() < self.cfg['feedback_probability']
                feedback = None
                if use_model_feedback:
                    fb_len_range = (max(8, len_range[0]-2), len_range[1]-3)
                    def _gen_fb():
                        fb_prompt = (
                            f"上下文:\n{(pair_context[:160]+'...') if pair_context else topic}\n"
                            f"{agent2_name} 刚才说了: '{response}'\n"
                            f"作为{agent1_name} 给一个自然反馈({fb_len_range[0]}~{fb_len_range[1]}字,中文,不复述):"
                        )
                        try:
                            raw_fb = agent1.think_and_respond(fb_prompt)
                        except Exception:
                            return ""
                        return self._sanitize_dialog_reply(raw_fb, length_range=fb_len_range, max_len=80)
                    future = self.thread_manager.submit_task(_gen_fb)
                    try:
                        fb_clean = future.result(timeout=self.cfg['feedback_async_timeout'])
                        if len(re.sub(r'[。！？，,.!？\s]','', fb_clean)) >= 6:
                            feedback = fb_clean
                    except Exception:
                        feedback = None
                if not feedback:
                    feedback = self._choose_feedback_template(current_relationship)
                lines.append(f"  {agent1.emoji} {display_color}{agent1_name} → {agent2_name}{TerminalColors.END}: {feedback}")
                self._append_pair_message(agent1_name, agent2_name, agent1_name, feedback)
                bias = 0
                positive_kw = ('好','不错','赞','喜欢','同意','支持','开心','高兴','有意思')
                negative_kw = ('不','没','怪','困惑','不同意','否','糟','烦')
                text_mix = topic + response + feedback
                pos_count = sum(text_mix.count(k) for k in positive_kw)
                neg_count = sum(text_mix.count(k) for k in negative_kw)
                if pos_count > neg_count and pos_count >= 1:
                    bias = min(2, pos_count - neg_count)
                elif neg_count > pos_count and neg_count >= 1:
                    bias = -min(2, neg_count - pos_count)
                prev_strength = current_relationship
                self._update_relationship(agent1_name, agent2_name, interaction_type, location)
                if self.behavior_manager:
                    new_strength = self.behavior_manager.get_relationship_strength(agent1_name, agent2_name)
                    if bias != 0 and hasattr(self.behavior_manager, 'social_network'):
                        ns = max(0, min(100, new_strength + bias))
                        self.behavior_manager.social_network[agent1_name][agent2_name] = ns
                        self.behavior_manager.social_network[agent2_name][agent1_name] = ns
                        delta = ns - prev_strength
                        if delta != 0:
                            lines.append(f"  🔗 关系调整: {agent1_name} ↔ {agent2_name} {prev_strength} → {ns} (偏置 {bias:+d})")
                self._recent_interaction_lru[key] = now_ts
                if len(self._recent_interaction_lru) > 300 and random.random() < 0.15:
                    to_del = [k for k,v in self._recent_interaction_lru.items() if now_ts - v > 240]
                    for k in to_del:
                        self._recent_interaction_lru.pop(k, None)
                with self.print_lock:
                    print('\n'.join(lines) + '\n')
                return True
            finally:
                with self.simulation_lock:
                    self.active_interactions.discard(interaction_id)
        except Exception as e:
            logger.error(f"执行社交互动异常: {e}")
            with self.simulation_lock:
                self.active_interactions.discard(tuple(sorted([agent1_name, agent2_name])))
            return False
    
    def _fallback_solo_thinking(self, agent, agent_name: str) -> bool:
        """后备的独自思考行动"""
        try:
            current_location = getattr(agent, 'location', '家')
            think_prompt = f"在{current_location}独自思考："
            
            # 使用线程池获取思考内容
            future = self.thread_manager.submit_task(lambda: agent.think_and_respond(think_prompt + "（请用中文回答，不要使用英文）"))
            try:
                thought = future.result(timeout=8.0)
                cleaned_thought = self.clean_response(thought)
            except Exception:
                cleaned_thought = "在安静地思考..."
            
            with self.print_lock:
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
    
    def _generate_agent_response(self, agent, agent_name: str, other_name: str, topic: str, interaction_type: str, pair_context: str = None, length_range=None) -> str:
        # 精简提示，去冗余“请/不要”多组合
        try:
            from .interaction_utils import InteractionUtils
            base_prompt = InteractionUtils.generate_interaction_prompt(agent_name, other_name, topic, interaction_type)
            ctx_part = f"最近对话:\n{pair_context}\n" if pair_context else ""
            if length_range:
                lr_prompt = f"{length_range[0]}~{length_range[1]}字"
            else:
                lr_prompt = "尽量简洁"
            prompt = f"{ctx_part}{base_prompt}\n基于上面内容，自然中文 1 句回应 ({lr_prompt})，避免英文和复述。"
            max_retries = self.cfg.get('max_generate_retries', 1)
            response = ""
            for attempt in range(max_retries + 1):
                try:
                    raw = agent.think_and_respond(prompt)
                except Exception:
                    raw = ""
                response = self.clean_response(raw) if raw is not None else ""
                if self._contains_english(response):
                    if attempt < max_retries:
                        prompt += " 仅中文。"
                        continue
                cmp_resp = re.sub(r"[\s。！？!?,，；;\\.]+", "", (response or "")).strip()
                cmp_topic = re.sub(r"[\s。！？!?,，；;\\.]+", "", (topic or "")).strip()
                if not response:
                    if attempt < max_retries:
                        prompt += " 不要留空。"
                        continue
                    else:
                        response = "我在听，继续。"
                        break
                if cmp_resp and (cmp_resp == cmp_topic or cmp_topic in cmp_resp or cmp_resp in cmp_topic):
                    if attempt < max_retries:
                        prompt += " 不要复述，换个角度。"
                        continue
                    else:
                        response = random.choice(["我理解你的意思。","这点值得再想想。","可以具体一点吗？","听起来有点道理。"])
                        break
                break
            # 验证负面互动的真实性
            if interaction_type in ['misunderstanding', 'argument']:
                response = self._ensure_negative_response(response, interaction_type, agent, prompt)
            response = self._sanitize_reply(response, max_len=60)
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
            # 强制性：只输出一句话，不要分析或解释，强制中文
            prompt = prompt + " （请用中文回复，只用一句话回应，不要解释或分析，不要包含思考过程，不要使用英文）"
            
            feedback = agent.think_and_respond(prompt)
            feedback = self.clean_response(feedback)
            # 新增：统一高级清理
            feedback = self._sanitize_reply(feedback, max_len=55)
            
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

    def _clean_and_truncate(self, text: str, max_len: int = 120) -> str:
        """清理并截断文本，返回第一句的简短版本。"""
        try:
            if not text:
                return ""
            # 使用已有清理器
            cleaned = self.clean_response(text)
            # 合并行并去除多余引号
            cleaned = cleaned.replace('\n', ' ').strip().strip('"“”')
            # 按句子分割，优先中文标点
            parts = re.split(r'[。！？!?,，；;\\.]+\s*', cleaned)
            first = parts[0].strip() if parts and parts[0] else cleaned
            if len(first) > max_len:
                first = first[:max_len].rstrip() + '...'
            return first
        except Exception:
            return (text or '')[:max_len]

    def _sanitize_reply(self, text: str, max_len: int = 60) -> str:
        try:
            if not text:
                return ""
            s = self.clean_response(text) if callable(self.clean_response) else text
            s = s.strip().replace('\n', ' ').strip('"“”\'')
            s = PAT_CN_BRACKETS.sub('', s)
            s = PAT_EN_BRACKETS.sub('', s)
            for _ in range(3):
                prev = s
                s = PAT_NAME_PREFIX.sub('', s).strip()
                s = PAT_NUM_SENT.sub('', s)
                s = PAT_STYLE_PREFIX.sub('', s)
                s = PAT_MISC_PREFIX.sub('', s)
                if s == prev:
                    break
            parts = [seg.strip() for seg in re.split(r'[。!?！？]', s) if seg.strip()]
            if not parts:
                return s[:max_len]
            core = parts[0]
            if len(core) < 12 and len(parts) > 1 and len(parts[1]) < 10:
                core += parts[1]
            if re.search(r'[\u4e00-\u9fff]', core):
                core = PAT_REMOVE_EN.sub('', core)
            core = PAT_DUP_WORD.sub(r'\1', core)
            core = PAT_MULTI_SPACE.sub(' ', core).strip()
            core = PAT_MULTI_COMMA.sub('，', core)
            core = PAT_MULTI_END.sub('。', core)
            if len(core) > max_len:
                core = core[:max_len].rstrip('，,。.!?！？;； ') + '…'
            if not re.search(r'[。.!?！？]$', core) and len(core) < max_len:
                core += '。'
            return core
        except Exception:
            return (text or '')[:max_len]
    
    def _contains_english(self, text: str) -> bool:
        if not text:
            return False
        return bool(PAT_ENGLISH_DETECT.search(text))

    def execute_group_discussion_safe(self, agents, agent, agent_name: str) -> bool:
        # 精简提示 (去多余“不要英文/分析”) 保持功能
        try:
            if self.social_handler:
                return self.social_handler.execute_group_discussion_safe(agents, agent, agent_name)
            current_location = getattr(agent, 'location', '家')
            with self.thread_manager.agents_lock:
                other_agents = [(name, other_agent) for name, other_agent in agents.items() if name != agent_name and getattr(other_agent, 'location', '家') == current_location]
            if not other_agents:
                return self._fallback_solo_thinking(agent, agent_name)
            max_group = 4
            selected_count = min(len(other_agents), max_group - 1)
            selected = random.sample(other_agents, selected_count) if selected_count > 0 else []
            participants = [(agent_name, agent)] + selected
            participant_names = [name for name, _ in participants]
            output_lines = []
            output_lines.append(f"{TerminalColors.BOLD}━━━ 👥 群体讨论 ━━━{TerminalColors.END}")
            output_lines.append(f"📍 地点: {current_location}")
            output_lines.append(f"👥 参与者: {', '.join(participant_names)}")
            convo = []
            others_list = ', '.join([n for n in participant_names if n != agent_name])
            topic_prompt = f"在{current_location}与{others_list}开始讨论，提出具体话题或感受(1句,12~25字,中文):"
            try:
                raw_topic = agent.think_and_respond(topic_prompt)
            except Exception:
                raw_topic = "今天天气有点影响心情。"
            topic = self._sanitize_reply(self.clean_response(raw_topic), max_len=60)
            core_topic = re.sub(r'[。！？，,.!\s]','', topic)
            if len(core_topic) < 4:
                try:
                    raw_topic2 = agent.think_and_respond(topic_prompt + " 更具体一点,含细节。")
                    topic2 = self._sanitize_reply(self.clean_response(raw_topic2), max_len=60)
                    if len(re.sub(r'[。！？，,.!\s]','', topic2)) >= 4:
                        topic = topic2
                except Exception:
                    pass
            output_lines.append(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END} 发起: {topic}")
            convo.append((agent_name, topic))
            pending_rel_updates = []
            def gen_context_window():
                window = convo[-3:]
                return '\n'.join([f"{spk}:{txt}" for spk, txt in window])
            def generate_group_reply(pagent, pname):
                base_prompt = f"讨论主题: {topic}\n最近发言:\n{gen_context_window()}\n你是{pname}，自然中文续接1句具体/带情绪回应(10~28字):"
                try:
                    raw = pagent.think_and_respond(base_prompt)
                except Exception:
                    raw = "我也在想这个。"
                cleaned = self._sanitize_reply(self.clean_response(raw), max_len=70)
                core = re.sub(r'[。！？，,.!\s]','', cleaned)
                if len(core) < 6:
                    try:
                        raw2 = pagent.think_and_respond(base_prompt + " 更具体一点。")
                        cleaned2 = self._sanitize_reply(self.clean_response(raw2), max_len=70)
                        if len(re.sub(r'[。！？，,.!\s]','', cleaned2)) >= 6:
                            return cleaned2
                    except Exception:
                        pass
                return cleaned
            # 轮询其余参与者
            for pname, pagent in participants[1:]:
                response = generate_group_reply(pagent, pname)
                output_lines.append(f"  {pagent.emoji} {TerminalColors.GREEN}{pname}{TerminalColors.END}: {response}")
                convo.append((pname, response))
                # 发起者反馈
                fb_prompt = (
                    f"主题: {topic}\n对方最新发言:{pname}:{response}\n"
                    f"作为{agent_name}给一个自然反馈(1句,8~22字,表达态度,不复述):"
                )
                try:
                    raw_fb = agent.think_and_respond(fb_prompt)
                    feedback = self._sanitize_reply(self.clean_response(raw_fb), max_len=60)
                except Exception:
                    feedback = "听起来可以。"
                fb_core = re.sub(r'[。！？，,.!？\s]','', feedback)
                if len(fb_core) < 4:
                    try:
                        raw_fb2 = agent.think_and_respond(fb_prompt + " 更具体些。")
                        feedback2 = self._sanitize_reply(self.clean_response(raw_fb2), max_len=60)
                        if len(re.sub(r'[。！？，,.!？\s]','', feedback2)) >= 4:
                            feedback = feedback2
                    except Exception:
                        pass
                output_lines.append(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END}: {feedback}")
                convo.append((agent_name, feedback))
                pending_rel_updates.append((agent_name, pname))
            print('\n' + '\n'.join(output_lines) + '\n')
            for a1, a2 in pending_rel_updates:
                try:
                    self._update_relationship(a1, a2, 'group_discussion', current_location)
                except Exception:
                    pass
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
        # 增加移动事件采样（短时间重复移动不入库）
        try:
            if not hasattr(self, '_recent_move_ts'):
                self._recent_move_ts = {}
            current_location = getattr(agent, 'location', '家')
            available_locations = [loc for loc in buildings.keys() if loc != current_location]
            if not available_locations:
                return False
            new_location = random.choice(available_locations)
            if self.agent_manager:
                agents = self.agents_ref() if self.agents_ref else {}
                success = self.agent_manager.move_agent(
                    agents, buildings, self.behavior_manager, agent_name, new_location, show_output=False
                )
                if success:
                    with self.print_lock:
                        print(f"\n{TerminalColors.BOLD}━━━ 🚶 移动 ━━━{TerminalColors.END}")
                        print(f"  {agent.emoji} {TerminalColors.MAGENTA}{agent_name}{TerminalColors.END}: {current_location} → {new_location}\n")
                    last_move = self._recent_move_ts.get(agent_name, 0)
                    now_ts = time.time()
                    # 只有超过 20 秒或位置真正变化才写入
                    if now_ts - last_move > 20 and new_location != current_location:
                        movement_task = {
                            'type': 'movement',
                            'agent_name': agent_name,
                            'old_location': current_location,
                            'new_location': new_location,
                            'reason': 'autonomous_movement',
                            'timestamp': datetime.now().isoformat()
                        }
                        self.thread_manager.add_memory_task(movement_task)
                        self._recent_move_ts[agent_name] = now_ts
                return success
            else:
                logger.warning("没有可用的agent_manager")
                return False
        except Exception as e:
            logger.error(f"执行移动行动异常: {e}")
            return False
    
    def _get_interaction_color(self, interaction_type: str) -> str:
        """获取互动类型对应的显示颜色 - 委托给工具类"""
        try:
            from .interaction_utils import InteractionUtils
            return InteractionUtils.get_interaction_color(interaction_type)
        except Exception:
            # 如果工具不可用，返回默认终端颜色
            return TerminalColors.END
    
    def _update_relationship(self, agent1_name: str, agent2_name: str, interaction_type: str, location: str):
        """更新关系并异步保存 - 委托给behavior_manager"""
        try:
            if not self.behavior_manager:
                logger.warning("behavior_manager不可用，跳过关系更新")
                return
            
            # 创建交互数据并提交给异步处理
            interaction_data = {
                'agent1_name': agent1_name,
                'agent2_name': agent2_name,
                'interaction_type': interaction_type,
                'context': {
                    'location': location,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # 使用线程管理器的安全社交更新
            if hasattr(self.thread_manager, 'safe_social_update'):
                self.thread_manager.safe_social_update(
                    self.behavior_manager,
                    agent1_name,
                    agent2_name,
                    interaction_type,
                    interaction_data['context']
                )
            
            # 保存交互记录到向量数据库
            memory_task = {
                'type': 'interaction',
                'data': interaction_data
            }
            if hasattr(self.thread_manager, 'add_memory_task'):
                self.thread_manager.add_memory_task(memory_task)
        except Exception as e:
            logger.error(f"更新关系失败: {e}")
            # 不抛出异常，避免中断模拟流程

    def _choose_feedback_template(self, rel: int) -> str:
        """根据关系强度选取反馈模板 (缺失补全)"""
        templates = [
            "嗯，我在听。",
            "明白你的意思。",
            "可以，再说详细一点。",
            "这点挺有意思。",
            "我理解你的感受。"
        ]
        if rel > 70:
            templates.extend(["确实，有道理。","我基本同意。","你的观察挺细的。"])
        if rel < 40:
            templates.extend(["我还在了解你的想法。","不太熟，但我在听。"])
        return random.choice(templates)
