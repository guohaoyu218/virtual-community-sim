"""
智能清理管理器
自动监控系统资源并执行合理的清理策略
"""
import time
import threading
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CleanupThresholds:
    """清理阈值配置"""
    # 内存阈值 (%)
    memory_warning: float = 70.0    # 内存使用率超过70%时警告
    memory_cleanup: float = 80.0    # 内存使用率超过80%时自动清理
    memory_emergency: float = 90.0  # 内存使用率超过90%时紧急清理
    
    # 向量数据库阈值
    vector_memories_per_agent: int = 500     # 每个Agent最多保留500条记忆
    vector_cleanup_interval: int = 6 * 3600  # 6小时清理一次
    
    # 交互历史阈值
    chat_history_max: int = 1000      # 最多保留1000条聊天记录
    interaction_history_max: int = 500 # 最多保留500条交互记录
    
    # 时间阈值
    old_memory_days: int = 7          # 7天前的记忆视为过期
    cache_timeout_hours: int = 2      # 缓存2小时后过期


class SmartCleanupManager:
    """智能清理管理器"""
    
    def __init__(self, 
                 memory_cleaner,
                 vector_optimizer,
                 thresholds: Optional[CleanupThresholds] = None):
        self.memory_cleaner = memory_cleaner
        self.vector_optimizer = vector_optimizer
        self.thresholds = thresholds or CleanupThresholds()
        
        # 运行状态
        self.is_running = False
        self.cleanup_thread = None
        self.last_cleanup_times = {
            'memory': 0,
            'vector': 0,
            'emergency': 0
        }
        
        # 统计信息
        self.cleanup_stats = {
            'auto_cleanups': 0,
            'memory_cleanups': 0,
            'vector_cleanups': 0,
            'emergency_cleanups': 0,
            'last_cleanup_time': None
        }
        
        logger.info("智能清理管理器初始化完成")
    
    def start_monitoring(self, check_interval: int = 60):
        """开始监控系统资源"""
        if self.is_running:
            logger.warning("智能清理监控已在运行")
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            name="SmartCleanupMonitor",
            daemon=True
        )
        self.cleanup_thread.start()
        logger.info(f"智能清理监控已启动，检查间隔: {check_interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("智能清理监控已停止")
    
    def _monitoring_loop(self, check_interval: int):
        """监控循环"""
        while self.is_running:
            try:
                # 检查系统资源状态
                self._check_and_cleanup()
                
                # 等待下次检查
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"智能清理监控异常: {e}")
                time.sleep(60)  # 发生异常时等待更长时间
    
    def _check_and_cleanup(self):
        """检查并执行清理"""
        try:
            # 获取系统资源状态
            memory_percent = psutil.virtual_memory().percent
            current_time = time.time()
            
            # 1. 内存检查和清理
            self._check_memory_cleanup(memory_percent, current_time)
            
            # 2. 向量数据库检查和清理
            self._check_vector_cleanup(current_time)
            
            # 3. 定期优化
            self._check_periodic_optimization(current_time)
            
        except Exception as e:
            logger.error(f"资源检查失败: {e}")
    
    def _check_memory_cleanup(self, memory_percent: float, current_time: float):
        """检查内存使用并执行清理"""
        
        # 紧急清理 (90%+)
        if memory_percent >= self.thresholds.memory_emergency:
            # 限制紧急清理频率（最多每10分钟一次）
            if current_time - self.last_cleanup_times['emergency'] > 600:
                logger.warning(f"内存使用率过高({memory_percent:.1f}%)，执行紧急清理")
                self._execute_emergency_cleanup()
                self.last_cleanup_times['emergency'] = current_time
                
        # 常规清理 (80%+)
        elif memory_percent >= self.thresholds.memory_cleanup:
            # 限制常规清理频率（最多每30分钟一次）
            if current_time - self.last_cleanup_times['memory'] > 1800:
                logger.info(f"内存使用率较高({memory_percent:.1f}%)，执行自动清理")
                self._execute_memory_cleanup()
                self.last_cleanup_times['memory'] = current_time
                
        # 内存警告 (70%+)
        elif memory_percent >= self.thresholds.memory_warning:
            # 轻量级清理（缓存清理）
            self._execute_light_cleanup()
    
    def _check_vector_cleanup(self, current_time: float):
        """检查向量数据库并执行清理"""
        # 每6小时检查一次向量数据库
        if current_time - self.last_cleanup_times['vector'] > self.thresholds.vector_cleanup_interval:
            try:
                # 获取向量数据库状态
                memory_status = self.memory_cleaner.get_memory_status()
                vector_db = memory_status.get('vector_database', {})
                
                if vector_db.get('connected', False):
                    total_memories = vector_db.get('total_memories', 0)
                    
                    # 如果记忆数量过多，执行向量数据库清理
                    if total_memories > self.thresholds.vector_memories_per_agent * 10:  # 假设10个Agent
                        logger.info(f"向量数据库记忆过多({total_memories}条)，执行自动清理")
                        self._execute_vector_cleanup()
                        self.last_cleanup_times['vector'] = current_time
                        
            except Exception as e:
                logger.error(f"向量数据库检查失败: {e}")
    
    def _check_periodic_optimization(self, current_time: float):
        """定期优化检查"""
        # 每天凌晨3点执行一次全面优化
        now = datetime.now()
        if now.hour == 3 and now.minute < 5:  # 3:00-3:05之间
            last_optimization = self.cleanup_stats.get('last_optimization_date')
            today = now.date()
            
            if last_optimization != today:
                logger.info("执行每日定期优化")
                self._execute_periodic_optimization()
                self.cleanup_stats['last_optimization_date'] = today
    
    def _execute_emergency_cleanup(self):
        """执行紧急清理"""
        try:
            # 1. 强制垃圾回收
            import gc
            collected = gc.collect()
            
            # 2. 紧急内存清理
            result = self.memory_cleaner.emergency_cleanup()
            
            # 3. 清理向量数据库中的低重要性记忆
            vector_result = self.memory_cleaner.cleanup_vector_database()
            
            # 更新统计
            self.cleanup_stats['emergency_cleanups'] += 1
            self.cleanup_stats['last_cleanup_time'] = datetime.now().isoformat()
            
            logger.info(f"紧急清理完成: GC回收{collected}个对象, 清理结果: {result}")
            
        except Exception as e:
            logger.error(f"紧急清理失败: {e}")
    
    def _execute_memory_cleanup(self):
        """执行常规内存清理"""
        try:
            result = self.memory_cleaner.cleanup_system_memory()
            
            # 更新统计
            self.cleanup_stats['memory_cleanups'] += 1
            self.cleanup_stats['auto_cleanups'] += 1
            self.cleanup_stats['last_cleanup_time'] = datetime.now().isoformat()
            
            logger.info(f"自动内存清理完成: {result}")
            
        except Exception as e:
            logger.error(f"自动内存清理失败: {e}")
    
    def _execute_light_cleanup(self):
        """执行轻量级清理"""
        try:
            import gc
            # 只执行垃圾回收，不做重量级操作
            collected = gc.collect()
            if collected > 0:
                logger.debug(f"轻量级清理: 垃圾回收{collected}个对象")
                
        except Exception as e:
            logger.error(f"轻量级清理失败: {e}")
    
    def _execute_vector_cleanup(self):
        """执行向量数据库清理"""
        try:
            result = self.memory_cleaner.cleanup_vector_database()
            
            # 更新统计
            self.cleanup_stats['vector_cleanups'] += 1
            self.cleanup_stats['auto_cleanups'] += 1
            self.cleanup_stats['last_cleanup_time'] = datetime.now().isoformat()
            
            logger.info(f"自动向量数据库清理完成: {result}")
            
        except Exception as e:
            logger.error(f"自动向量数据库清理失败: {e}")
    
    def _execute_periodic_optimization(self):
        """执行定期优化"""
        try:
            # 1. 向量数据库优化
            result = self.vector_optimizer.run_full_optimization()
            
            # 2. 全面内存清理
            memory_result = self.memory_cleaner.force_cleanup_all()
            
            logger.info(f"定期优化完成: 向量优化={result.get('success', False)}, 内存清理={memory_result}")
            
        except Exception as e:
            logger.error(f"定期优化失败: {e}")
    
    def get_cleanup_status(self) -> Dict[str, Any]:
        """获取清理状态"""
        memory_percent = psutil.virtual_memory().percent
        
        return {
            'is_monitoring': self.is_running,
            'current_memory_usage': f"{memory_percent:.1f}%",
            'memory_status': self._get_memory_status_description(memory_percent),
            'thresholds': {
                'warning': f"{self.thresholds.memory_warning}%",
                'cleanup': f"{self.thresholds.memory_cleanup}%", 
                'emergency': f"{self.thresholds.memory_emergency}%"
            },
            'statistics': self.cleanup_stats.copy(),
            'last_cleanup_times': {
                k: datetime.fromtimestamp(v).isoformat() if v > 0 else '从未清理'
                for k, v in self.last_cleanup_times.items()
            }
        }
    
    def _get_memory_status_description(self, memory_percent: float) -> str:
        """获取内存状态描述"""
        if memory_percent >= self.thresholds.memory_emergency:
            return "🔴 紧急状态"
        elif memory_percent >= self.thresholds.memory_cleanup:
            return "🟡 需要清理"
        elif memory_percent >= self.thresholds.memory_warning:
            return "🟠 警告状态"
        else:
            return "🟢 正常状态"
    
    def adjust_thresholds(self, **kwargs):
        """动态调整清理阈值"""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                logger.info(f"清理阈值已调整: {key} = {value}")
            else:
                logger.warning(f"未知的阈值参数: {key}")
    
    def force_cleanup(self, cleanup_type: str = 'all'):
        """手动触发清理"""
        logger.info(f"手动触发清理: {cleanup_type}")
        
        if cleanup_type == 'emergency':
            self._execute_emergency_cleanup()
        elif cleanup_type == 'memory':
            self._execute_memory_cleanup()
        elif cleanup_type == 'vector':
            self._execute_vector_cleanup()
        elif cleanup_type == 'all':
            self._execute_memory_cleanup()
            self._execute_vector_cleanup()
        else:
            raise ValueError(f"未知的清理类型: {cleanup_type}")


def get_smart_cleanup_manager(memory_cleaner, vector_optimizer, 
                            custom_thresholds: Optional[Dict] = None) -> SmartCleanupManager:
    """获取智能清理管理器实例"""
    thresholds = CleanupThresholds()
    
    if custom_thresholds:
        for key, value in custom_thresholds.items():
            if hasattr(thresholds, key):
                setattr(thresholds, key, value)
    
    return SmartCleanupManager(memory_cleaner, vector_optimizer, thresholds)
