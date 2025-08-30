"""
线程管理器模块
统一管理所有线程和并发控制
"""

import threading
import queue
import logging
from threading import RLock, Lock, Event, Condition
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ThreadManager:
    """线程管理器 - 统一管理所有线程和并发控制"""
    
    def __init__(self):
        # 线程安全控制
        self._agents_lock = RLock()          # Agent状态的读写锁
        self._chat_lock = Lock()             # 聊天历史的保护锁
        self._social_lock = Lock()           # 社交网络的保护锁
        self._simulation_lock = Lock()       # 自动模拟的控制锁
        self._vector_db_lock = Lock()        # 向量数据库写入锁
        self._buildings_lock = Lock()        # 建筑物状态锁
        
        # 并发控制
        self._shutdown_event = Event()       # 优雅关闭信号
        self._simulation_condition = Condition(self._simulation_lock)
        self._thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="TownAgent")
        
        # 异步操作队列
        self._memory_save_queue = queue.Queue(maxsize=100)
        self._interaction_queue = queue.Queue(maxsize=50)
        
        # 工作线程
        self._memory_worker = None
        self._interaction_worker = None
        
    def start_background_workers(self, memory_save_func, interaction_process_func):
        """启动后台工作线程"""
        # 内存保存工作线程
        self._memory_worker = threading.Thread(
            target=self._memory_save_worker,
            args=(memory_save_func,),
            name="MemoryWorker",
            daemon=True
        )
        self._memory_worker.start()
        
        # 交互处理工作线程
        self._interaction_worker = threading.Thread(
            target=self._interaction_worker_func,
            args=(interaction_process_func,),
            name="InteractionWorker", 
            daemon=True
        )
        self._interaction_worker.start()
        
        logger.info("后台工作线程已启动")
    
    def _memory_save_worker(self, memory_save_func):
        """后台内存保存工作线程"""
        while not self._shutdown_event.is_set():
            try:
                # 阻塞等待任务，超时1秒
                task = self._memory_save_queue.get(timeout=1.0)
                if task is None:  # 关闭信号
                    break
                    
                # 批量处理内存保存任务
                memory_save_func([task])
                self._memory_save_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"内存保存工作线程异常: {e}")
    
    def _interaction_worker_func(self, interaction_process_func):
        """交互处理工作线程"""
        while not self._shutdown_event.is_set():
            try:
                interaction_data = self._interaction_queue.get(timeout=1.0)
                if interaction_data is None:
                    break
                    
                interaction_process_func(interaction_data)
                self._interaction_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"交互处理工作线程异常: {e}")
    
    @contextmanager
    def safe_agent_access(self, agents, agent_name: str):
        """安全的Agent访问上下文管理器"""
        with self._agents_lock:
            if agent_name not in agents:
                raise ValueError(f"Agent {agent_name} 不存在")
            yield agents[agent_name]
    
    def safe_chat_append(self, chat_history, chat_entry: dict):
        """线程安全的聊天历史添加"""
        with self._chat_lock:
            chat_history.append(chat_entry)
            # 限制历史记录长度，防止内存溢出
            if len(chat_history) > 1000:
                chat_history[:] = chat_history[-800:]  # 保留最近800条
    
    def safe_social_update(self, behavior_manager, agent1_name: str, agent2_name: str, 
                          interaction_type: str, context: dict = None):
        """线程安全的社交网络更新"""
        with self._social_lock:
            return behavior_manager.update_social_network(
                agent1_name, agent2_name, interaction_type, context
            )
    
    def safe_building_update(self, buildings, agent_name: str, old_location: str, new_location: str):
        """线程安全的建筑物状态更新"""
        with self._buildings_lock:
            # 从旧位置移除
            if old_location in buildings:
                occupants = buildings[old_location]['occupants']
                if agent_name in occupants:
                    occupants.remove(agent_name)
            
            # 添加到新位置
            if new_location in buildings:
                occupants = buildings[new_location]['occupants']
                if agent_name not in occupants:
                    occupants.append(agent_name)
    
    def submit_task(self, func, *args, **kwargs):
        """向线程池提交任务"""
        return self._thread_pool.submit(func, *args, **kwargs)
    
    def add_memory_task(self, task):
        """添加内存保存任务"""
        try:
            self._memory_save_queue.put_nowait(task)
        except queue.Full:
            logger.warning("内存保存队列已满，跳过此次保存")
    
    def add_interaction_task(self, interaction_data: dict):
        """添加社交交互任务到队列"""
        try:
            if not self._shutdown_event.is_set():
                self._interaction_queue.put_nowait(interaction_data)
        except queue.Full:
            logger.warning("社交交互队列已满，忽略新任务")
    
    def add_memory_save_task(self, memory_data: dict):
        """添加内存保存任务到队列"""
        try:
            if not self._shutdown_event.is_set():
                self._memory_save_queue.put_nowait(memory_data)
        except queue.Full:
            logger.warning("内存保存队列已满，忽略新任务")

    def get_simulation_condition(self):
        """获取模拟条件变量"""
        return self._simulation_condition
    
    def is_shutdown(self):
        """检查是否正在关闭"""
        return self._shutdown_event.is_set()
    
    def shutdown(self):
        """优雅关闭线程管理器"""
        logger.info("开始关闭线程管理器...")
        
        # 设置关闭信号
        self._shutdown_event.set()
        
        # 停止后台工作线程
        try:
            self._memory_save_queue.put_nowait(None)  # 发送关闭信号
            self._interaction_queue.put_nowait(None)
        except queue.Full:
            pass
        
        # 等待工作线程结束
        if self._memory_worker and self._memory_worker.is_alive():
            self._memory_worker.join(timeout=5.0)
        
        if self._interaction_worker and self._interaction_worker.is_alive():
            self._interaction_worker.join(timeout=5.0)
        
        # 关闭线程池
        try:
            self._thread_pool.shutdown(wait=True)
        except Exception as e:
            logger.warning(f"关闭线程池异常: {e}")
        
        logger.info("线程管理器已安全关闭")
    
    # 属性访问器
    @property
    def agents_lock(self):
        return self._agents_lock
    
    @property
    def chat_lock(self):
        return self._chat_lock
    
    @property
    def social_lock(self):
        return self._social_lock
    
    @property
    def buildings_lock(self):
        return self._buildings_lock
    
    @property
    def vector_db_lock(self):
        return self._vector_db_lock
