"""
内存清理和维护管理器
负责向量数据库和系统内存的清理、压缩和优化
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import gc
import psutil
import os

from .vector_store import get_vector_store
from config.settings import VECTOR_DB_CONFIG

logger = logging.getLogger(__name__)

class MemoryCleaner:
    """内存清理管理器"""
    
    def __init__(self):
        self.vector_store = get_vector_store()
        
        # 清理配置
        self.cleanup_config = {
            'memory_threshold_percent': 80,  # 内存使用率阈值
            'vector_db_size_limit_mb': 1000,  # 向量数据库大小限制
            'memory_cleanup_interval': 1800,  # 30分钟清理一次
            'vector_cleanup_interval': 3600,  # 1小时清理一次向量数据库
            'old_memory_days': 30,  # 删除30天前的低重要性记忆
            'low_importance_threshold': 0.3,  # 低重要性阈值
            'max_memories_per_agent': 10000,  # 每个Agent最大记忆数
        }
        
        # 状态跟踪
        self._last_memory_cleanup = 0
        self._last_vector_cleanup = 0
        self._cleanup_stats = {
            'total_cleanups': 0,
            'memories_cleaned': 0,
            'space_freed_mb': 0,
            'last_cleanup_time': None
        }
        
        # 线程控制
        self._cleanup_thread = None
        self._shutdown_event = threading.Event()
        self._cleanup_lock = threading.RLock()
        
        logger.info("内存清理管理器初始化完成")
    
    def start_background_cleanup(self):
        """启动后台清理任务"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            logger.warning("清理线程已在运行")
            return
        
        self._shutdown_event.clear()
        self._cleanup_thread = threading.Thread(
            target=self._background_cleanup_worker,
            name="MemoryCleanupWorker",
            daemon=True
        )
        self._cleanup_thread.start()
        logger.info("后台内存清理已启动")
    
    def stop_background_cleanup(self):
        """停止后台清理任务"""
        if self._shutdown_event:
            self._shutdown_event.set()
        
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
            logger.info("后台内存清理已停止")
    
    def _background_cleanup_worker(self):
        """后台清理工作线程"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # 检查是否需要内存清理
                if (current_time - self._last_memory_cleanup) >= self.cleanup_config['memory_cleanup_interval']:
                    self.cleanup_system_memory()
                    self._last_memory_cleanup = current_time
                
                # 检查是否需要向量数据库清理
                if (current_time - self._last_vector_cleanup) >= self.cleanup_config['vector_cleanup_interval']:
                    self.cleanup_vector_database()
                    self._last_vector_cleanup = current_time
                
                # 检查内存使用率
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > self.cleanup_config['memory_threshold_percent']:
                    logger.warning(f"内存使用率过高: {memory_percent}%, 执行紧急清理")
                    self.emergency_cleanup()
                
            except Exception as e:
                logger.error(f"后台清理任务异常: {e}")
            
            # 等待一段时间后再次检查
            self._shutdown_event.wait(300)  # 5分钟检查一次
    
    def cleanup_system_memory(self) -> Dict[str, Any]:
        """清理系统内存"""
        logger.info("开始系统内存清理...")
        
        with self._cleanup_lock:
            stats = {
                'before_memory_mb': psutil.virtual_memory().used / 1024 / 1024,
                'cleaned_items': 0,
                'errors': []
            }
            
            try:
                # 1. Python垃圾回收
                collected = gc.collect()
                stats['gc_collected'] = collected
                logger.debug(f"垃圾回收清理了 {collected} 个对象")
                
                # 2. 清理过期缓存
                stats['cache_cleaned'] = self._cleanup_expired_caches()
                
                # 3. 强制内存整理
                if psutil.virtual_memory().percent > 70:
                    # 在高内存使用时进行更积极的清理
                    for generation in range(3):
                        gc.collect(generation)
                
                stats['after_memory_mb'] = psutil.virtual_memory().used / 1024 / 1024
                stats['memory_freed_mb'] = stats['before_memory_mb'] - stats['after_memory_mb']
                
                self._cleanup_stats['total_cleanups'] += 1
                self._cleanup_stats['space_freed_mb'] += stats['memory_freed_mb']
                self._cleanup_stats['last_cleanup_time'] = datetime.now().isoformat()
                
                logger.info(f"系统内存清理完成，释放 {stats['memory_freed_mb']:.2f} MB")
                return stats
                
            except Exception as e:
                logger.error(f"系统内存清理失败: {e}")
                stats['errors'].append(str(e))
                return stats
    
    def cleanup_vector_database(self) -> Dict[str, Any]:
        """清理向量数据库"""
        logger.info("开始向量数据库清理...")
        
        with self._cleanup_lock:
            stats = {
                'collections_processed': 0,
                'memories_deleted': 0,
                'space_freed_mb': 0,
                'errors': []
            }
            
            try:
                if not self.vector_store.is_connected():
                    logger.warning("向量数据库未连接，跳过清理")
                    return stats
                
                # 获取所有集合
                collections = self.vector_store.client.get_collections()
                
                for collection in collections.collections:
                    collection_name = collection.name
                    try:
                        # 清理每个集合
                        collection_stats = self._cleanup_collection(collection_name)
                        stats['memories_deleted'] += collection_stats.get('deleted_count', 0)
                        stats['collections_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"清理集合 {collection_name} 失败: {e}"
                        logger.error(error_msg)
                        stats['errors'].append(error_msg)
                
                # 压缩数据库
                try:
                    self._compress_vector_database()
                    stats['database_compressed'] = True
                except Exception as e:
                    logger.warning(f"数据库压缩失败: {e}")
                
                self._cleanup_stats['memories_cleaned'] += stats['memories_deleted']
                
                logger.info(f"向量数据库清理完成，删除 {stats['memories_deleted']} 条记忆")
                return stats
                
            except Exception as e:
                logger.error(f"向量数据库清理失败: {e}")
                stats['errors'].append(str(e))
                return stats
    
    def _cleanup_collection(self, collection_name: str) -> Dict[str, Any]:
        """清理单个集合"""
        stats = {'deleted_count': 0, 'agent_id': None}
        
        try:
            # 提取agent_id
            if collection_name.startswith('agent_') and collection_name.endswith('_memories'):
                agent_id = collection_name.replace('agent_', '').replace('_memories', '')
                stats['agent_id'] = agent_id
            
            # 获取集合中的所有记忆
            scroll_result = self.vector_store.client.scroll(
                collection_name=collection_name,
                with_payload=True,
                limit=10000  # 一次处理最多10000条
            )
            
            memories = scroll_result[0] if scroll_result else []
            if not memories:
                return stats
            
            # 分析记忆，找出需要删除的
            to_delete = []
            current_time = datetime.now()
            
            for memory in memories:
                should_delete = False
                
                # 检查时间
                timestamp_str = memory.payload.get('timestamp', '')
                if timestamp_str:
                    try:
                        memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        memory_age = (current_time - memory_time.replace(tzinfo=None)).days
                        
                        # 删除过老的低重要性记忆
                        importance = memory.payload.get('importance', 0.5)
                        if memory_age > self.cleanup_config['old_memory_days'] and importance < self.cleanup_config['low_importance_threshold']:
                            should_delete = True
                    except:
                        # 无法解析时间戳的记忆也删除
                        should_delete = True
                
                # 检查重要性
                importance = memory.payload.get('importance', 0.5)
                access_count = memory.payload.get('access_count', 0)
                
                # 删除从未被访问且重要性很低的记忆
                if importance < 0.1 and access_count == 0:
                    should_delete = True
                
                if should_delete:
                    to_delete.append(memory.id)
            
            # 检查Agent记忆总数，如果超过限制则删除最旧的
            if len(memories) > self.cleanup_config['max_memories_per_agent']:
                # 按时间戳排序，删除最旧的
                sorted_memories = sorted(memories, 
                                       key=lambda m: m.payload.get('timestamp', ''))
                excess_count = len(memories) - self.cleanup_config['max_memories_per_agent']
                for memory in sorted_memories[:excess_count]:
                    if memory.id not in to_delete:
                        to_delete.append(memory.id)
            
            # 执行删除
            if to_delete:
                self.vector_store.client.delete(
                    collection_name=collection_name,
                    points_selector=to_delete
                )
                stats['deleted_count'] = len(to_delete)
                logger.debug(f"从 {collection_name} 删除了 {len(to_delete)} 条记忆")
            
            return stats
            
        except Exception as e:
            logger.error(f"清理集合 {collection_name} 失败: {e}")
            return stats
    
    def _cleanup_expired_caches(self) -> int:
        """清理过期缓存"""
        cleaned_count = 0
        
        try:
            # 这里可以添加具体的缓存清理逻辑
            # 例如清理Agent的内存缓存、UI缓存等
            
            # 清理全局缓存
            if hasattr(self.vector_store, '_memory_cache'):
                cache = self.vector_store._memory_cache
                current_time = time.time()
                
                expired_keys = []
                for key, data in cache.items():
                    if isinstance(data, dict) and 'timestamp' in data:
                        if current_time - data['timestamp'] > 300:  # 5分钟过期
                            expired_keys.append(key)
                
                for key in expired_keys:
                    del cache[key]
                    cleaned_count += 1
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
        
        return cleaned_count
    
    def _compress_vector_database(self):
        """压缩向量数据库"""
        try:
            # Qdrant的优化操作
            if hasattr(self.vector_store.client, 'optimize'):
                collections = self.vector_store.client.get_collections()
                for collection in collections.collections:
                    # 优化每个集合
                    self.vector_store.client.optimize(collection.name)
                logger.info("向量数据库优化完成")
        except Exception as e:
            logger.warning(f"向量数据库压缩失败: {e}")
    
    def emergency_cleanup(self) -> Dict[str, Any]:
        """紧急清理 - 在内存使用率过高时调用"""
        logger.warning("执行紧急内存清理...")
        
        stats = {
            'emergency_cleanup': True,
            'actions_taken': []
        }
        
        try:
            # 1. 强制垃圾回收
            collected = 0
            for generation in range(3):
                collected += gc.collect(generation)
            stats['gc_collected'] = collected
            stats['actions_taken'].append('强制垃圾回收')
            
            # 2. 清理所有缓存
            cache_cleaned = self._cleanup_expired_caches()
            stats['cache_cleaned'] = cache_cleaned
            stats['actions_taken'].append('清理缓存')
            
            # 3. 限制向量数据库查询
            if hasattr(self.vector_store, '_emergency_mode'):
                self.vector_store._emergency_mode = True
                stats['actions_taken'].append('启用数据库紧急模式')
            
            # 4. 清理最不重要的记忆
            emergency_vector_stats = self._emergency_vector_cleanup()
            stats.update(emergency_vector_stats)
            
            logger.info(f"紧急清理完成，采取行动: {stats['actions_taken']}")
            return stats
            
        except Exception as e:
            logger.error(f"紧急清理失败: {e}")
            stats['error'] = str(e)
            return stats
    
    def _emergency_vector_cleanup(self) -> Dict[str, Any]:
        """紧急向量数据库清理"""
        stats = {'emergency_deleted': 0}
        
        try:
            if not self.vector_store.is_connected():
                return stats
            
            collections = self.vector_store.client.get_collections()
            
            for collection in collections.collections:
                collection_name = collection.name
                
                # 删除最不重要的记忆
                scroll_result = self.vector_store.client.scroll(
                    collection_name=collection_name,
                    with_payload=True,
                    limit=1000
                )
                
                memories = scroll_result[0] if scroll_result else []
                
                # 按重要性排序，删除最低的20%
                if len(memories) > 100:  # 只有当记忆数量较多时才删除
                    sorted_memories = sorted(memories, 
                                           key=lambda m: m.payload.get('importance', 0.5))
                    
                    delete_count = len(memories) // 5  # 删除20%
                    to_delete = [m.id for m in sorted_memories[:delete_count]]
                    
                    if to_delete:
                        self.vector_store.client.delete(
                            collection_name=collection_name,
                            points_selector=to_delete
                        )
                        stats['emergency_deleted'] += len(to_delete)
        
        except Exception as e:
            logger.error(f"紧急向量清理失败: {e}")
        
        return stats
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存状态信息"""
        try:
            # 系统内存状态
            memory = psutil.virtual_memory()
            
            # 进程内存状态
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # 向量数据库状态
            vector_status = self._get_vector_db_status()
            
            status = {
                'system_memory': {
                    'total_gb': memory.total / 1024 / 1024 / 1024,
                    'used_gb': memory.used / 1024 / 1024 / 1024,
                    'available_gb': memory.available / 1024 / 1024 / 1024,
                    'percent_used': memory.percent
                },
                'process_memory': {
                    'rss_mb': process_memory.rss / 1024 / 1024,
                    'vms_mb': process_memory.vms / 1024 / 1024
                },
                'vector_database': vector_status,
                'cleanup_stats': self._cleanup_stats,
                'cleanup_config': self.cleanup_config,
                'last_check': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"获取内存状态失败: {e}")
            return {'error': str(e)}
    
    def _get_vector_db_status(self) -> Dict[str, Any]:
        """获取向量数据库状态"""
        try:
            if not self.vector_store.is_connected():
                return {'connected': False}
            
            collections = self.vector_store.client.get_collections()
            
            total_memories = 0
            collections_info = []
            
            for collection in collections.collections:
                try:
                    info = self.vector_store.client.get_collection(collection.name)
                    memories_count = info.points_count if hasattr(info, 'points_count') else 0
                    total_memories += memories_count
                    
                    collections_info.append({
                        'name': collection.name,
                        'memories_count': memories_count
                    })
                except:
                    continue
            
            return {
                'connected': True,
                'total_collections': len(collections.collections),
                'total_memories': total_memories,
                'collections': collections_info
            }
            
        except Exception as e:
            logger.error(f"获取向量数据库状态失败: {e}")
            return {'connected': False, 'error': str(e)}
    
    def force_cleanup_all(self) -> Dict[str, Any]:
        """强制清理所有内容"""
        logger.info("开始强制全面清理...")
        
        results = {
            'memory_cleanup': self.cleanup_system_memory(),
            'vector_cleanup': self.cleanup_vector_database(),
            'emergency_cleanup': self.emergency_cleanup()
        }
        
        logger.info("强制全面清理完成")
        return results
    
    def shutdown(self):
        """关闭清理管理器"""
        logger.info("正在关闭内存清理管理器...")
        self.stop_background_cleanup()
        logger.info("内存清理管理器已关闭")

# 全局实例
_memory_cleaner = None

def get_memory_cleaner() -> MemoryCleaner:
    """获取全局内存清理器实例"""
    global _memory_cleaner
    if _memory_cleaner is None:
        _memory_cleaner = MemoryCleaner()
    return _memory_cleaner
