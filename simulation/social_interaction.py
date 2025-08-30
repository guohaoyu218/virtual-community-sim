"""
社交交互模块
处理Agent之间的社交互动逻辑
"""

import random
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from display.terminal_colors import TerminalColors

logger = logging.getLogger(__name__)

class SocialInteractionHandler:
    """社交交互处理器"""
    
    def __init__(self, thread_manager, behavior_manager, response_cleaner_func):
        self.thread_manager = thread_manager
        self.behavior_manager = behavior_manager
        self.clean_response = response_cleaner_func
        
        # 负面关键词用于验证互动真实性
        self.negative_keywords = [
            '不同意', '反对', '不对', '错', '不行', '失望', '糟糕', '问题', '麻烦', 
            '困惑', '不理解', '质疑', '批评', '反驳', '不满', '抱怨', '反感', 
            '厌恶', '讨厌', '愤怒', '生气', '恼火', '烦躁', '焦虑', '紧张'
        ]
        
        self.positive_keywords = [
            '同意', '赞同', '很好', '不错', '棒', '对', '是的', '有道理', 
            '支持', '喜欢', '认同', '欣赏', '感动', '启发', '有趣', '精彩', '优秀'
        ]
    
    def execute_social_action_safe(self, agents, agent, agent_name: str) -> bool:
        """安全执行社交行动"""
        try:
            current_location = getattr(agent, 'location', '家')
            
            # 线程安全地找到同位置的其他Agent
            with self.thread_manager.agents_lock:
                other_agents = [
                    name for name, other_agent in agents.items()
                    if name != agent_name and getattr(other_agent, 'location', '家') == current_location
                ]
            
            if not other_agents:
                # 没有其他Agent，执行独自思考
                return self._execute_solo_thinking(agent, agent_name, current_location)
            
            # 选择交互对象
            target_agent_name = random.choice(other_agents)
            target_agent = agents[target_agent_name]
            
            # 执行双向对话
            return self._execute_agent_conversation(
                agent, agent_name, target_agent, target_agent_name, current_location
            )
            
        except Exception as e:
            logger.error(f"执行社交行动异常: {e}")
            return False
    
    def _execute_agent_conversation(self, agent1, agent1_name: str, agent2, agent2_name: str, location: str) -> bool:
        """执行Agent之间的对话"""
        try:
            # 确保两人在同一位置
            if getattr(agent1, 'location') != getattr(agent2, 'location'):
                agent2.move_to(location)
                if hasattr(agent2, 'real_agent'):
                    agent2.real_agent.current_location = location
            
            # 获取当前关系强度
            current_relationship = self.behavior_manager.get_relationship_strength(agent1_name, agent2_name)
            
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
            
            # 更新社交网络并立即显示关系变化
            relationship_info = self.behavior_manager.update_social_network(
                agent1_name, agent2_name, interaction_type, 
                f"在{location}的{interaction_type}互动"
            )
            
            # 显示关系变化
            if relationship_info and relationship_info.get('change', 0) != 0:
                change_color = TerminalColors.GREEN if relationship_info['change'] > 0 else TerminalColors.RED
                change_symbol = "+" if relationship_info['change'] > 0 else ""
                
                # 根据互动类型显示不同的图标
                if interaction_type == 'friendly_chat':
                    icon = "💫"
                elif interaction_type == 'casual_meeting':
                    icon = "💭" 
                elif interaction_type == 'misunderstanding':
                    icon = "❓"
                elif interaction_type == 'argument':
                    icon = "💥"
                else:
                    icon = "🔄"
                
                print(f"  {icon} {relationship_info.get('relationship_emoji', '🤝')} "
                      f"{relationship_info.get('new_level', '普通')} "
                      f"({change_color}{change_symbol}{relationship_info['change']:.1f}{TerminalColors.END})")
                
                # 只在重大等级变化时显示详情
                if relationship_info.get('level_changed', False):
                    level_color = TerminalColors.GREEN if relationship_info['new_strength'] > relationship_info['old_strength'] else TerminalColors.YELLOW
                    print(f"    {level_color}🌟 {relationship_info.get('level_change_message', '关系等级发生变化')}{TerminalColors.END}")
            
            # 同时加入任务队列进行后台处理
            self._update_social_relationship(agent1_name, agent2_name, interaction_type, location)
            
            print()  # 空行分隔
            return True
            
        except Exception as e:
            logger.error(f"执行Agent对话异常: {e}")
            return False
    
    def _choose_interaction_type(self, relationship_strength: int) -> str:
        """根据关系强度选择互动类型"""
        if relationship_strength >= 70:
            # 关系很好：80%友好，15%中性，5%负面
            weights = [('friendly_chat', 80), ('casual_meeting', 15), ('misunderstanding', 4), ('argument', 1)]
        elif relationship_strength >= 50:
            # 关系一般：60%友好，25%中性，15%负面
            weights = [('friendly_chat', 60), ('casual_meeting', 25), ('misunderstanding', 12), ('argument', 3)]
        elif relationship_strength >= 30:
            # 关系较差：40%友好，35%中性，25%负面
            weights = [('friendly_chat', 40), ('casual_meeting', 35), ('misunderstanding', 20), ('argument', 5)]
        else:
            # 关系很差：25%友好，30%中性，45%负面
            weights = [('friendly_chat', 25), ('casual_meeting', 30), ('misunderstanding', 30), ('argument', 15)]
        
        # 根据权重随机选择
        interaction_types = []
        for interaction_type, weight in weights:
            interaction_types.extend([interaction_type] * weight)
        
        return random.choice(interaction_types)
    
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
            logger.error(f"生成{agent_name}回应失败: {e}")
            return "嗯..."
    
    def _generate_feedback_response(self, agent, agent_name: str, other_name: str, response: str, interaction_type: str) -> str:
        """生成反馈回应"""
        try:
            if interaction_type == 'friendly_chat':
                prompt = f"{other_name}回应：'{response}'，表示赞同："
            elif interaction_type in ['misunderstanding', 'argument']:
                prompt = f"{other_name}回应：'{response}'，坚持自己的立场，不要缓解气氛："
            else:
                prompt = f"{other_name}回应：'{response}'，简短回应："
            
            feedback = agent.think_and_respond(prompt)
            feedback = self.clean_response(feedback)
            
            # 验证负面互动的真实性
            if interaction_type in ['misunderstanding', 'argument']:
                feedback = self._ensure_negative_response(feedback, interaction_type, agent, prompt)
            
            return feedback
            
        except Exception as e:
            logger.error(f"生成{agent_name}反馈失败: {e}")
            return "好吧..."
    
    def _ensure_negative_response(self, response: str, interaction_type: str, agent, original_prompt: str) -> str:
        """确保负面互动的回应确实是负面的"""
        has_negative = any(keyword in response for keyword in self.negative_keywords)
        has_positive = any(keyword in response for keyword in self.positive_keywords)
        
        # 如果回复太积极或中性，重新生成
        if has_positive or (not has_negative and not has_positive):
            try:
                if interaction_type == 'argument':
                    retry_prompt = original_prompt + " 明确表达不同观点和反对意见："
                elif interaction_type == 'misunderstanding':
                    retry_prompt = original_prompt + " 表达困惑和不理解："
                else:
                    retry_prompt = original_prompt
                
                new_response = agent.think_and_respond(retry_prompt)
                new_response = self.clean_response(new_response)
                
                # 如果重新生成后仍然不够负面，添加自然前缀
                has_negative_new = any(keyword in new_response for keyword in self.negative_keywords)
                if not has_negative_new:
                    if interaction_type == 'argument':
                        response = "我不这么认为。" + new_response
                    else:
                        response = "我不太理解。" + new_response
                else:
                    response = new_response
                    
            except Exception as e:
                logger.error(f"重新生成负面回应失败: {e}")
                # 使用默认负面回应
                if interaction_type == 'argument':
                    response = "我觉得这个观点有问题。"
                else:
                    response = "我有点困惑，不太明白。"
        
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
    
    def _update_social_relationship(self, agent1_name: str, agent2_name: str, interaction_type: str, location: str):
        """更新社交关系"""
        try:
            # 构建互动上下文
            context = {
                'same_location': True,
                'location': location,
                'interaction_initiator': agent1_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # 异步更新关系
            interaction_data = {
                'agent1_name': agent1_name,
                'agent2_name': agent2_name,
                'interaction_type': interaction_type,
                'location': location,
                'context': context
            }
            
            self.thread_manager.add_interaction_task(interaction_data)
            
        except Exception as e:
            logger.error(f"更新社交关系失败: {e}")
    
    def _execute_solo_thinking(self, agent, agent_name: str, location: str) -> bool:
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
            except Exception:
                cleaned_thought = "在深度思考中..."
            
            print(f"\n{TerminalColors.BOLD}━━━ 💭 独自思考 ━━━{TerminalColors.END}")
            print(f"  {agent.emoji} {TerminalColors.YELLOW}{agent_name}{TerminalColors.END}: {cleaned_thought}")
            print()
            
            return True
            
        except Exception as e:
            logger.error(f"执行独自思考异常: {e}")
            return False
    
    def execute_group_discussion_safe(self, agents, agent, agent_name: str) -> bool:
        """安全执行群体讨论"""
        try:
            current_location = getattr(agent, 'location', '家')
            
            # 线程安全地找到同位置的Agent
            with self.thread_manager.agents_lock:
                agents_same_location = [
                    name for name, other_agent in agents.items()
                    if name != agent_name and getattr(other_agent, 'location', '家') == current_location
                ]
            
            if len(agents_same_location) < 1:
                # 没有足够的Agent，转为独自思考
                return self._execute_solo_thinking(agent, agent_name, current_location)
            
            # 选择参与者（最多3人）
            participants = random.sample(agents_same_location, min(2, len(agents_same_location)))
            all_participants = [agent_name] + participants
            
            # 生成讨论话题
            topics = [
                "最近的工作", "天气真不错", "这个地方很棒",
                "有什么新鲜事", "周末计划", "兴趣爱好", "生活感悟", "未来规划"
            ]
            topic = random.choice(topics)
            
            print(f"\n{TerminalColors.BOLD}━━━ 👥 群体讨论 ━━━{TerminalColors.END}")
            print(f"  📍 {current_location}: 关于'{topic}'的讨论")
            print(f"  🗣️  发起者: {agent.emoji} {agent_name}")
            print(f"  👥 参与者: {', '.join([f'{agents[p].emoji} {p}' for p in participants])}")
            
            # 发起者开始讨论
            start_prompt = f"在{current_location}和大家讨论'{topic}'，发起话题："
            try:
                initial_statement = agent.think_and_respond(start_prompt)
                initial_statement = self.clean_response(initial_statement)
            except Exception as e:
                logger.error(f"生成发起话题失败: {e}")
                initial_statement = f"大家觉得{topic}怎么样？"
            
            print(f"  💬 {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END}: {initial_statement}")
            
            # 其他参与者依次回应
            for i, participant_name in enumerate(participants):
                try:
                    participant_agent = agents[participant_name]
                    
                    # 生成回应
                    if i == 0:
                        # 第一个回应者对发起者的话题回应
                        response_prompt = f"{agent_name}说：'{initial_statement}'，在群体讨论中简短回应："
                    else:
                        # 后续回应者可以对前面的内容回应
                        response_prompt = f"在关于'{topic}'的群体讨论中，简短发表观点："
                    
                    response = participant_agent.think_and_respond(response_prompt)
                    response = self.clean_response(response)
                    
                    # 随机选择回应类型的颜色
                    response_colors = [TerminalColors.GREEN, TerminalColors.YELLOW, TerminalColors.CYAN]
                    color = random.choice(response_colors)
                    
                    print(f"  💬 {participant_agent.emoji} {color}{participant_name}{TerminalColors.END}: {response}")
                    
                except Exception as e:
                    logger.error(f"生成{participant_name}的群体讨论回应失败: {e}")
                    print(f"  💬 {agents[participant_name].emoji} {TerminalColors.YELLOW}{participant_name}{TerminalColors.END}: 我觉得挺好的。")
            
            # 发起者总结
            try:
                conclusion_prompt = f"听了大家关于'{topic}'的讨论，简短总结或回应："
                conclusion = agent.think_and_respond(conclusion_prompt)
                conclusion = self.clean_response(conclusion)
                print(f"  💬 {agent.emoji} {TerminalColors.BLUE}{agent_name}{TerminalColors.END}: {conclusion}")
            except Exception as e:
                logger.error(f"生成讨论总结失败: {e}")
                print(f"  💬 {agent.emoji} {TerminalColors.BLUE}{agent_name}{TerminalColors.END}: 大家说得都很有道理。")
            
            print()  # 空行分隔
            
            # 立即更新并显示所有参与者之间的关系变化
            print(f"  {TerminalColors.CYAN}💞 关系变化:{TerminalColors.END}")
            
            for participant in participants:
                try:
                    # 立即更新关系
                    relationship_info = self.behavior_manager.update_social_network(
                        agent_name, participant, 'group_discussion', 
                        f"群体讨论: {topic}"
                    )
                    
                    # 显示关系变化
                    if relationship_info and relationship_info.get('change', 0) != 0:
                        change_color = TerminalColors.GREEN if relationship_info['change'] > 0 else TerminalColors.RED
                        change_symbol = "+" if relationship_info['change'] > 0 else ""
                        
                        # 根据关系变化显示不同的图标
                        if relationship_info['change'] > 0:
                            icon = "💫"
                        else:
                            icon = "💔"
                        
                        print(f"    {icon} {agent.emoji}{agent_name} ↔ {agents[participant].emoji}{participant}: "
                              f"{relationship_info.get('relationship_emoji', '🤝')} "
                              f"{relationship_info.get('new_level', '普通')} "
                              f"({change_color}{change_symbol}{relationship_info['change']:.1f}{TerminalColors.END})")
                        
                        # 显示等级变化
                        if relationship_info.get('level_changed', False):
                            level_color = TerminalColors.GREEN if relationship_info['new_strength'] > relationship_info['old_strength'] else TerminalColors.YELLOW
                            print(f"      {level_color}🌟 {relationship_info.get('level_change_message', '关系等级发生变化')}{TerminalColors.END}")
                    
                except Exception as e:
                    logger.error(f"更新{agent_name}和{participant}的关系失败: {e}")
                
                # 同时添加到任务队列进行后台处理
                interaction_data = {
                    'agent1_name': agent_name,
                    'agent2_name': participant,
                    'interaction_type': 'group_discussion',
                    'location': current_location,
                    'context': {
                        'topic': topic,
                        'discussion_type': 'group',
                        'participants': all_participants,
                        'group_size': len(all_participants)
                    }
                }
                
                self.thread_manager.add_interaction_task(interaction_data)
            
            return True
            
        except Exception as e:
            logger.error(f"执行群体讨论异常: {e}")
            return False
