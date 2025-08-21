"""
异步任务管理器 - 支持高并发Agent操作
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Task:
    """任务数据类"""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    created_at: datetime
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # 优先级队列
        self.task_queues = {
            TaskPriority.URGENT: asyncio.Queue(maxsize=100),
            TaskPriority.HIGH: asyncio.Queue(maxsize=200),
            TaskPriority.NORMAL: asyncio.Queue(maxsize=500),
            TaskPriority.LOW: asyncio.Queue(maxsize=200)
        }
        
        # 任务状态跟踪
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, Any] = {}
        self.failed_tasks: Dict[str, Exception] = {}
        
        # 工作线程池
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        
        # 性能统计
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0
        }
        
        logger.info(f"异步任务管理器初始化完成: {max_workers}个工作线程")
    
    async def start(self):
        """启动任务管理器"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 创建工作线程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"任务管理器已启动，{len(self.workers)}个工作线程运行中")
    
    async def stop(self):
        """停止任务管理器"""
        self.is_running = False
        
        # 等待所有任务完成
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("任务管理器已停止")
    
    async def submit_task(self, 
                         task_id: str,
                         func: Callable,
                         args: tuple = (),
                         kwargs: dict = None,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: Optional[float] = None) -> str:
        """提交异步任务"""
        kwargs = kwargs or {}
        
        # 检查队列是否已满
        queue = self.task_queues[priority]
        if queue.qsize() >= queue.maxsize:
            raise asyncio.QueueFull(f"优先级 {priority.name} 的任务队列已满")
        
        # 创建任务
        task = Task(
            id=task_id,
            name=func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            created_at=datetime.now(),
            timeout=timeout
        )
        
        # 添加到队列
        await queue.put(task)
        self.stats["total_tasks"] += 1
        
        logger.debug(f"任务已提交: {task_id} ({priority.name})")
        return task_id
    
    async def get_task_result(self, task_id: str, timeout: float = 10.0) -> Any:
        """获取任务结果"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查是否完成
            if task_id in self.completed_tasks:
                return self.completed_tasks.pop(task_id)
            
            # 检查是否失败
            if task_id in self.failed_tasks:
                exc = self.failed_tasks.pop(task_id)
                raise exc
            
            # 等待一小段时间
            await asyncio.sleep(0.1)
        
        raise asyncio.TimeoutError(f"任务 {task_id} 在 {timeout}s 内未完成")
    
    async def _worker(self, worker_name: str):
        """工作线程"""
        logger.info(f"工作线程 {worker_name} 已启动")
        
        while self.is_running:
            task = None
            try:
                # 按优先级获取任务
                task = await self._get_next_task()
                if task is None:
                    await asyncio.sleep(0.1)
                    continue
                
                logger.debug(f"{worker_name} 开始执行任务: {task.id}")
                
                # 执行任务
                start_time = time.time()
                
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        # 异步函数
                        if task.timeout:
                            result = await asyncio.wait_for(
                                task.func(*task.args, **task.kwargs),
                                timeout=task.timeout
                            )
                        else:
                            result = await task.func(*task.args, **task.kwargs)
                    else:
                        # 同步函数，在线程池中执行
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None, 
                            lambda: task.func(*task.args, **task.kwargs)
                        )
                    
                    # 记录成功结果
                    execution_time = time.time() - start_time
                    self.completed_tasks[task.id] = result
                    self.stats["completed_tasks"] += 1
                    self._update_average_time(execution_time)
                    
                    logger.debug(f"任务完成: {task.id} (耗时: {execution_time:.2f}s)")
                
                except Exception as e:
                    # 任务执行失败
                    task.retry_count += 1
                    
                    if task.retry_count <= task.max_retries:
                        # 重试
                        logger.warning(f"任务 {task.id} 失败，第 {task.retry_count} 次重试: {e}")
                        await self.task_queues[task.priority].put(task)
                    else:
                        # 彻底失败
                        self.failed_tasks[task.id] = e
                        self.stats["failed_tasks"] += 1
                        logger.error(f"任务 {task.id} 最终失败: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程 {worker_name} 发生错误: {e}")
                if task:
                    self.failed_tasks[task.id] = e
                    self.stats["failed_tasks"] += 1
        
        logger.info(f"工作线程 {worker_name} 已停止")
    
    async def _get_next_task(self) -> Optional[Task]:
        """按优先级获取下一个任务"""
        # 按优先级顺序检查队列
        for priority in [TaskPriority.URGENT, TaskPriority.HIGH, 
                        TaskPriority.NORMAL, TaskPriority.LOW]:
            queue = self.task_queues[priority]
            try:
                return queue.get_nowait()
            except asyncio.QueueEmpty:
                continue
        
        return None
    
    def _update_average_time(self, execution_time: float):
        """更新平均执行时间"""
        total_completed = self.stats["completed_tasks"]
        current_avg = self.stats["average_execution_time"]
        
        # 计算新的平均值
        new_avg = ((current_avg * (total_completed - 1)) + execution_time) / total_completed
        self.stats["average_execution_time"] = new_avg
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "queue_sizes": {
                priority.name: queue.qsize() 
                for priority, queue in self.task_queues.items()
            },
            "running_tasks": len(self.running_tasks),
            "workers_count": len(self.workers),
            "is_running": self.is_running
        }

# 全局任务管理器实例
_task_manager = None

async def get_task_manager() -> AsyncTaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
        await _task_manager.start()
    return _task_manager

async def submit_agent_task(agent_id: str, 
                          func: Callable, 
                          args: tuple = (),
                          kwargs: dict = None,
                          priority: TaskPriority = TaskPriority.NORMAL) -> str:
    """提交Agent相关任务的便捷函数"""
    task_manager = await get_task_manager()
    task_id = f"agent_{agent_id}_{int(time.time() * 1000)}"
    
    await task_manager.submit_task(
        task_id=task_id,
        func=func,
        args=args,
        kwargs=kwargs or {},
        priority=priority,
        timeout=30.0  # Agent任务默认30秒超时
    )
    
    return task_id
