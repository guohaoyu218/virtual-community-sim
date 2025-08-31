"""
聊天处理器模块
专门处理与Agent的对话逻辑
"""

import time
import logging
import concurrent.futures
from datetime import datetime
from display.terminal_colors import TerminalColors

logger = logging.getLogger(__name__)

class ChatHandler:
    """聊天处理器"""
    
    def __init__(self, thread_manager, response_cleaner_func, context_engine=None):
        self.thread_manager = thread_manager
        self.clean_response = response_cleaner_func
        self.context_engine = context_engine  # 先进上下文引擎
    
    def chat_with_agent(self, agents, agent_name: str, message: str = None):
        """与Agent对话 - 线程安全版本"""
        try:
            with self.thread_manager.safe_agent_access(agents, agent_name) as agent:
                print(f"\n{TerminalColors.BOLD}💬 与 {agent.color}{agent.emoji} {agent_name}{TerminalColors.END}{TerminalColors.BOLD} 对话{TerminalColors.END}")
                print("=" * 40)
                print(f"{TerminalColors.CYAN}💡 输入 'exit' 结束对话{TerminalColors.END}\n")
                
                if message:
                    self._process_chat_message_safe(agent, agent_name, message)
                else:
                    # 进入对话循环
                    self._enter_chat_loop(agent, agent_name)
                    
        except ValueError as e:
            print(f"{TerminalColors.RED}❌ {e}{TerminalColors.END}")
            print(f"可用的Agent: {', '.join(agents.keys())}")
        except Exception as e:
            logger.error(f"聊天系统异常: {e}")
            print(f"{TerminalColors.RED}❌ 聊天系统暂时不可用{TerminalColors.END}")
    
    def _enter_chat_loop(self, agent, agent_name: str):
        """进入安全的对话循环"""
        while not self.thread_manager.is_shutdown():
            try:
                user_input = input(f"{TerminalColors.YELLOW}🧑 你: {TerminalColors.END}").strip()
                
                if user_input.lower() in ['exit', '退出', 'quit']:
                    print(f"{TerminalColors.GREEN}👋 结束与{agent_name}的对话{TerminalColors.END}\n")
                    break
                
                if user_input:
                    self._process_chat_message_safe(agent, agent_name, user_input)
                    
            except KeyboardInterrupt:
                print(f"\n{TerminalColors.YELLOW}⚠️ 对话被中断{TerminalColors.END}")
                break
            except EOFError:
                break
            except Exception as e:
                logger.error(f"对话循环异常: {e}")
                print(f"{TerminalColors.RED}❌ 对话出现异常，请重试{TerminalColors.END}")
    
    def _process_chat_message_safe(self, agent, agent_name: str, message: str):
        """线程安全的聊天消息处理"""
        start_time = time.time()
        response_future = None
        
        try:
            # 使用线程池异步处理AI回应，避免阻塞
            response_future = self.thread_manager.submit_task(
                self._get_agent_response, agent, agent_name, message
            )
            
            # 显示思考状态
            print(f"  {agent.color}{agent.emoji} {agent_name}: {TerminalColors.END}{TerminalColors.YELLOW}思考中...{TerminalColors.END}")
            
            # 等待回应，设置超时
            try:
                response = response_future.result(timeout=30.0)  # 30秒超时
            except Exception as e:
                response = f"*{agent_name}思考了很久，似乎在深度思考中...*"
                logger.warning(f"{agent_name}回应超时: {e}")
            
            # 清除思考状态显示
            print(f"\033[1A\033[K", end="")  # 上移一行并清除
            
            # 显示最终回应
            print(f"  {agent.color}{agent.emoji} {agent_name}: {TerminalColors.END}{response}")
            
            # 计算响应时间
            response_time = time.time() - start_time
            if response_time > 5.0:
                print(f"  {TerminalColors.YELLOW}⏱️  响应时间: {response_time:.1f}秒{TerminalColors.END}")
            
            # 异步保存对话记录
            self._async_save_chat_record(agent_name, message, response, response_time)
            
            print()  # 空行分隔
            
        except Exception as e:
            logger.error(f"处理{agent_name}聊天消息异常: {e}")
            print(f"  {agent.color}{agent.emoji} {agent_name}: {TerminalColors.END}{TerminalColors.RED}*系统异常，无法回应*{TerminalColors.END}")
        finally:
            # 确保取消未完成的future
            if response_future and not response_future.done():
                response_future.cancel()
    
    def _get_agent_response(self, agent, agent_name: str, message: str) -> str:
        """获取Agent回应（在线程池中执行）"""
        try:
            # 构建情境
            current_location = getattr(agent, 'location', '未知位置')
            situation = f"用户对我说：'{message}'"
            
            # 如果有上下文引擎，使用先进的上下文构建
            if self.context_engine:
                profession = getattr(agent, 'profession', 'general')
                context = self.context_engine.build_context(
                    agent_type=profession,  # 使用职业作为agent_type
                    situation=situation,
                    interaction_type='user_chat',  # 用户对话类型
                    relationship_level=80,  # 用户与Agent关系通常较好
                    recent_memories=[]  # 可以传入最近的记忆
                )
                # 使用上下文增强的情况
                enhanced_situation = f"{situation}\n\n上下文信息：{context}"
                response = agent.think_and_respond(enhanced_situation)
            else:
                # 使用默认回应方式
                response = agent.think_and_respond(situation)
            
            # 清理回应
            cleaned_response = self.clean_response(response)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"{agent_name}生成回应异常: {e}")
            return f"*{agent_name}遇到了技术问题，暂时无法回应*"
    
    def _async_save_chat_record(self, agent_name: str, user_message: str, 
                              agent_response: str, response_time: float):
        """异步保存聊天记录"""
        try:
            # 异步保存到向量数据库
            memory_task = {
                'type': 'user_chat',
                'agent_name': agent_name,
                'user_message': user_message,
                'agent_response': agent_response,
                'timestamp': datetime.now().isoformat(),
                'response_time': response_time
            }
            
            # 非阻塞地添加到队列
            self.thread_manager.add_memory_task(memory_task)
                
        except Exception as e:
            logger.error(f"异步保存聊天记录失败: {e}")
    
    def save_chat_to_history(self, chat_history, agent_name: str, user_message: str, 
                           agent_response: str, response_time: float):
        """保存聊天记录到历史"""
        try:
            # 创建聊天记录
            chat_entry = {
                'time': datetime.now().strftime("%H:%M:%S"),
                'agent': agent_name,
                'user': user_message,
                'response': agent_response,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # 线程安全地添加到历史记录
            self.thread_manager.safe_chat_append(chat_history, chat_entry)
                
        except Exception as e:
            logger.error(f"保存聊天历史失败: {e}")
