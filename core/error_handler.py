"""
错误处理和监控系统
统一管理系统异常、监控和恢复
"""

import logging
import traceback
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误分类"""
    AGENT = "agent"
    SOCIAL = "social"
    PERSISTENCE = "persistence"
    THREAD = "thread"
    UI = "ui"
    MODEL = "model"
    SYSTEM = "system"

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 错误统计
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'recent_errors': [],
            'system_health': 'healthy'
        }
        
        # 错误处理策略
        self.error_handlers = {}
        self.recovery_strategies = {}
        self.circuit_breakers = {}
        
        # 监控配置
        self.max_recent_errors = 100
        self.critical_error_threshold = 5  # 5分钟内5个严重错误触发熔断
        self.health_check_interval = 30  # 30秒健康检查
        
        # 线程控制
        self._monitoring_thread = None
        self._shutdown_event = threading.Event()
        self._error_lock = threading.RLock()
        
        # 启动监控
        self._start_monitoring()
        
        # 注册默认错误处理器
        self._register_default_handlers()
        
        logger.info("错误处理系统初始化完成")
    
    def _start_monitoring(self):
        """启动错误监控线程"""
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="ErrorMonitoring",
            daemon=True
        )
        self._monitoring_thread.start()
    
    def _monitoring_loop(self):
        """监控循环"""
        while not self._shutdown_event.is_set():
            try:
                self._check_system_health()
                self._cleanup_old_errors()
                self._check_circuit_breakers()
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        # Agent相关错误
        self.register_error_handler(
            ErrorCategory.AGENT,
            self._handle_agent_error
        )
        
        # 社交网络错误
        self.register_error_handler(
            ErrorCategory.SOCIAL,
            self._handle_social_error
        )
        
        # 持久化错误
        self.register_error_handler(
            ErrorCategory.PERSISTENCE,
            self._handle_persistence_error
        )
        
        # 线程相关错误
        self.register_error_handler(
            ErrorCategory.THREAD,
            self._handle_thread_error
        )
        
        # UI错误
        self.register_error_handler(
            ErrorCategory.UI,
            self._handle_ui_error
        )
        
        # 模型接口错误
        self.register_error_handler(
            ErrorCategory.MODEL,
            self._handle_model_error
        )
        
        # 系统级错误
        self.register_error_handler(
            ErrorCategory.SYSTEM,
            self._handle_system_error
        )
    
    def register_error_handler(self, category: ErrorCategory, handler: Callable):
        """注册错误处理器"""
        self.error_handlers[category] = handler
        logger.debug(f"注册错误处理器: {category.value}")
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """注册恢复策略"""
        self.recovery_strategies[category] = strategy
        logger.debug(f"注册恢复策略: {category.value}")
    
    @contextmanager
    def error_context(self, operation: str, category: ErrorCategory = ErrorCategory.SYSTEM, 
                     severity: ErrorSeverity = ErrorSeverity.MEDIUM, **context):
        """错误处理上下文管理器"""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            # 记录错误
            error_info = {
                'operation': operation,
                'category': category,
                'severity': severity,
                'exception': e,
                'context': context,
                'duration': time.time() - start_time
            }
            
            self.handle_error(error_info)
            raise  # 重新抛出异常
    
    def handle_error(self, error_info: Dict[str, Any]) -> bool:
        """处理错误"""
        try:
            with self._error_lock:
                # 记录错误
                self._log_error(error_info)
                
                # 更新统计
                self._update_error_stats(error_info)
                
                # 执行错误处理策略
                recovery_successful = self._execute_error_handler(error_info)
                
                # 检查是否需要熔断
                self._check_circuit_breaker(error_info)
                
                return recovery_successful
                
        except Exception as e:
            logger.critical(f"错误处理器本身发生异常: {e}")
            return False
    
    def _log_error(self, error_info: Dict[str, Any]):
        """记录错误日志"""
        try:
            timestamp = datetime.now()
            
            # 构建详细的错误信息
            error_record = {
                'timestamp': timestamp.isoformat(),
                'operation': error_info.get('operation', 'Unknown'),
                'category': error_info.get('category', ErrorCategory.SYSTEM).value,
                'severity': error_info.get('severity', ErrorSeverity.MEDIUM).value,
                'error_type': type(error_info.get('exception', Exception())).__name__,
                'error_message': str(error_info.get('exception', '')),
                'context': error_info.get('context', {}),
                'duration': error_info.get('duration', 0),
                'traceback': traceback.format_exc() if error_info.get('exception') else None
            }
            
            # 写入日志文件
            log_file = self.log_dir / f"errors_{timestamp.strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_record, ensure_ascii=False) + '\\n')
            
            # 记录到系统日志
            severity = error_info.get('severity', ErrorSeverity.MEDIUM)
            if severity == ErrorSeverity.CRITICAL:
                logger.critical(f"严重错误: {error_record['operation']} - {error_record['error_message']}")
            elif severity == ErrorSeverity.HIGH:
                logger.error(f"高级错误: {error_record['operation']} - {error_record['error_message']}")
            elif severity == ErrorSeverity.MEDIUM:
                logger.warning(f"中级错误: {error_record['operation']} - {error_record['error_message']}")
            else:
                logger.info(f"低级错误: {error_record['operation']} - {error_record['error_message']}")
            
        except Exception as e:
            logger.critical(f"记录错误日志失败: {e}")
    
    def _update_error_stats(self, error_info: Dict[str, Any]):
        """更新错误统计"""
        try:
            category = error_info.get('category', ErrorCategory.SYSTEM).value
            severity = error_info.get('severity', ErrorSeverity.MEDIUM).value
            
            # 更新总错误数
            self.error_stats['total_errors'] += 1
            
            # 更新分类统计
            if category not in self.error_stats['errors_by_category']:
                self.error_stats['errors_by_category'][category] = 0
            self.error_stats['errors_by_category'][category] += 1
            
            # 更新严重程度统计
            if severity not in self.error_stats['errors_by_severity']:
                self.error_stats['errors_by_severity'][severity] = 0
            self.error_stats['errors_by_severity'][severity] += 1
            
            # 添加到最近错误列表
            recent_error = {
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'severity': severity,
                'operation': error_info.get('operation', 'Unknown'),
                'message': str(error_info.get('exception', ''))
            }
            
            self.error_stats['recent_errors'].append(recent_error)
            
            # 限制最近错误列表长度
            if len(self.error_stats['recent_errors']) > self.max_recent_errors:
                self.error_stats['recent_errors'] = self.error_stats['recent_errors'][-self.max_recent_errors:]
            
        except Exception as e:
            logger.error(f"更新错误统计失败: {e}")
    
    def _execute_error_handler(self, error_info: Dict[str, Any]) -> bool:
        """执行错误处理策略"""
        try:
            category = error_info.get('category', ErrorCategory.SYSTEM)
            
            # 执行注册的错误处理器
            if category in self.error_handlers:
                handler = self.error_handlers[category]
                return handler(error_info)
            else:
                # 使用默认处理策略
                return self._default_error_handler(error_info)
                
        except Exception as e:
            logger.error(f"执行错误处理策略失败: {e}")
            return False
    
    def _check_circuit_breaker(self, error_info: Dict[str, Any]):
        """检查熔断器"""
        try:
            category = error_info.get('category', ErrorCategory.SYSTEM)
            severity = error_info.get('severity', ErrorSeverity.MEDIUM)
            
            # 只对严重错误进行熔断检查
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                now = datetime.now()
                
                if category not in self.circuit_breakers:
                    self.circuit_breakers[category] = []
                
                # 添加错误时间
                self.circuit_breakers[category].append(now)
                
                # 清理5分钟前的错误记录
                cutoff_time = now - timedelta(minutes=5)
                self.circuit_breakers[category] = [
                    t for t in self.circuit_breakers[category] if t > cutoff_time
                ]
                
                # 检查是否达到熔断阈值
                if len(self.circuit_breakers[category]) >= self.critical_error_threshold:
                    self._trigger_circuit_breaker(category)
                    
        except Exception as e:
            logger.error(f"检查熔断器失败: {e}")
    
    def _trigger_circuit_breaker(self, category: ErrorCategory):
        """触发熔断器"""
        try:
            logger.critical(f"触发熔断器: {category.value} - 短时间内严重错误过多")
            
            # 更新系统健康状态
            self.error_stats['system_health'] = 'degraded'
            
            # 执行恢复策略
            if category in self.recovery_strategies:
                strategy = self.recovery_strategies[category]
                recovery_result = strategy()
                
                if recovery_result:
                    logger.info(f"恢复策略执行成功: {category.value}")
                    # 清理熔断器
                    self.circuit_breakers[category] = []
                else:
                    logger.error(f"恢复策略执行失败: {category.value}")
                    
        except Exception as e:
            logger.critical(f"触发熔断器异常: {e}")
    
    def _check_system_health(self):
        """检查系统健康状态"""
        try:
            # 检查最近5分钟的错误情况
            now = datetime.now()
            cutoff_time = now - timedelta(minutes=5)
            
            recent_critical_errors = 0
            recent_high_errors = 0
            
            for error in self.error_stats['recent_errors']:
                error_time = datetime.fromisoformat(error['timestamp'])
                if error_time > cutoff_time:
                    if error['severity'] == ErrorSeverity.CRITICAL.value:
                        recent_critical_errors += 1
                    elif error['severity'] == ErrorSeverity.HIGH.value:
                        recent_high_errors += 1
            
            # 更新健康状态
            if recent_critical_errors > 0:
                self.error_stats['system_health'] = 'critical'
            elif recent_high_errors > 3:
                self.error_stats['system_health'] = 'degraded'
            elif recent_high_errors > 0:
                self.error_stats['system_health'] = 'warning'
            else:
                self.error_stats['system_health'] = 'healthy'
                
        except Exception as e:
            logger.error(f"检查系统健康状态失败: {e}")
    
    def _cleanup_old_errors(self):
        """清理旧错误记录"""
        try:
            # 清理7天前的日志文件
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in self.log_dir.glob("errors_*.jsonl"):
                try:
                    file_date_str = log_file.stem.split('_')[1]
                    file_date = datetime.strptime(file_date_str, '%Y%m%d')
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        logger.debug(f"删除旧错误日志: {log_file}")
                        
                except Exception as e:
                    logger.warning(f"清理日志文件失败 {log_file}: {e}")
                    
        except Exception as e:
            logger.error(f"清理旧错误记录失败: {e}")
    
    def _check_circuit_breakers(self):
        """定期检查熔断器状态"""
        try:
            now = datetime.now()
            cutoff_time = now - timedelta(minutes=10)  # 10分钟后自动恢复
            
            for category in list(self.circuit_breakers.keys()):
                # 清理过期的熔断记录
                self.circuit_breakers[category] = [
                    t for t in self.circuit_breakers[category] if t > cutoff_time
                ]
                
                # 如果没有最近的错误，自动恢复
                if not self.circuit_breakers[category]:
                    if self.error_stats['system_health'] in ['degraded', 'critical']:
                        self.error_stats['system_health'] = 'recovering'
                        logger.info(f"系统健康状态恢复中: {category.value}")
                        
        except Exception as e:
            logger.error(f"检查熔断器状态失败: {e}")
    
    # 默认错误处理器
    def _handle_agent_error(self, error_info: Dict[str, Any]) -> bool:
        """处理Agent相关错误"""
        try:
            logger.info("执行Agent错误恢复策略")
            
            # 可以在这里添加Agent重置逻辑
            # 例如：重置Agent状态、重新初始化等
            
            return True
            
        except Exception as e:
            logger.error(f"Agent错误处理失败: {e}")
            return False
    
    def _handle_social_error(self, error_info: Dict[str, Any]) -> bool:
        """处理社交网络错误"""
        try:
            logger.info("执行社交网络错误恢复策略")
            
            # 可以在这里添加社交网络修复逻辑
            # 例如：重建社交关系、清理异常数据等
            
            return True
            
        except Exception as e:
            logger.error(f"社交网络错误处理失败: {e}")
            return False
    
    def _handle_persistence_error(self, error_info: Dict[str, Any]) -> bool:
        """处理持久化错误"""
        try:
            logger.info("执行持久化错误恢复策略")
            
            # 可以在这里添加持久化恢复逻辑
            # 例如：重试保存、备份恢复等
            
            return True
            
        except Exception as e:
            logger.error(f"持久化错误处理失败: {e}")
            return False
    
    def _handle_thread_error(self, error_info: Dict[str, Any]) -> bool:
        """处理线程相关错误"""
        try:
            logger.info("执行线程错误恢复策略")
            
            # 可以在这里添加线程恢复逻辑
            # 例如：重启工作线程、清理死锁等
            
            return True
            
        except Exception as e:
            logger.error(f"线程错误处理失败: {e}")
            return False
    
    def _handle_ui_error(self, error_info: Dict[str, Any]) -> bool:
        """处理UI错误"""
        try:
            logger.info("执行UI错误恢复策略")
            
            # 可以在这里添加UI恢复逻辑
            # 例如：重置显示状态、清理界面等
            
            return True
            
        except Exception as e:
            logger.error(f"UI错误处理失败: {e}")
            return False
    
    def _handle_model_error(self, error_info: Dict[str, Any]) -> bool:
        """处理模型接口错误"""
        try:
            logger.info("执行模型接口错误恢复策略")
            
            # 可以在这里添加模型恢复逻辑
            # 例如：重试请求、切换模型等
            
            return True
            
        except Exception as e:
            logger.error(f"模型接口错误处理失败: {e}")
            return False
    
    def _handle_system_error(self, error_info: Dict[str, Any]) -> bool:
        """处理系统级错误"""
        try:
            logger.info("执行系统错误恢复策略")
            
            # 可以在这里添加系统恢复逻辑
            # 例如：清理资源、重启组件等
            
            return True
            
        except Exception as e:
            logger.error(f"系统错误处理失败: {e}")
            return False
    
    def _default_error_handler(self, error_info: Dict[str, Any]) -> bool:
        """默认错误处理策略"""
        try:
            logger.info("执行默认错误恢复策略")
            
            # 基本的错误恢复逻辑
            # 记录日志，但不进行特殊处理
            
            return True
            
        except Exception as e:
            logger.error(f"默认错误处理失败: {e}")
            return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        try:
            with self._error_lock:
                return {
                    **self.error_stats,
                    'circuit_breaker_status': {
                        category.value: len(errors) for category, errors in self.circuit_breakers.items()
                    },
                    'health_check_time': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"获取错误统计失败: {e}")
            return {}
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的错误记录"""
        try:
            with self._error_lock:
                return self.error_stats['recent_errors'][-limit:]
        except Exception as e:
            logger.error(f"获取最近错误记录失败: {e}")
            return []
    
    def reset_error_stats(self):
        """重置错误统计"""
        try:
            with self._error_lock:
                self.error_stats = {
                    'total_errors': 0,
                    'errors_by_category': {},
                    'errors_by_severity': {},
                    'recent_errors': [],
                    'system_health': 'healthy'
                }
                self.circuit_breakers.clear()
                
                logger.info("错误统计已重置")
                
        except Exception as e:
            logger.error(f"重置错误统计失败: {e}")
    
    def shutdown(self):
        """关闭错误处理系统"""
        try:
            logger.info("开始关闭错误处理系统...")
            
            # 停止监控线程
            self._shutdown_event.set()
            
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=5.0)
            
            logger.info("错误处理系统已关闭")
            
        except Exception as e:
            logger.critical(f"关闭错误处理系统失败: {e}")

# 全局错误处理器实例
global_error_handler = None

def initialize_error_handler(log_dir: str = "logs") -> ErrorHandler:
    """初始化全局错误处理器"""
    global global_error_handler
    if global_error_handler is None:
        global_error_handler = ErrorHandler(log_dir)
    return global_error_handler

def get_error_handler() -> Optional[ErrorHandler]:
    """获取全局错误处理器"""
    return global_error_handler

def handle_error(operation: str, category: ErrorCategory = ErrorCategory.SYSTEM, 
                severity: ErrorSeverity = ErrorSeverity.MEDIUM, exception: Exception = None, **context):
    """便捷的错误处理函数"""
    if global_error_handler:
        error_info = {
            'operation': operation,
            'category': category,
            'severity': severity,
            'exception': exception,
            'context': context
        }
        return global_error_handler.handle_error(error_info)
    return False
