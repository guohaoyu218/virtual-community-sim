"""
向量数据库性能优化工具
提供数据库维护、优化和监控功能
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

from memory.vector_store import get_vector_store
from memory.memory_cleaner import get_memory_cleaner
from config.settings import VECTOR_DB_CONFIG

logger = logging.getLogger(__name__)

class VectorDatabaseOptimizer:
    """向量数据库优化器"""
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.memory_cleaner = get_memory_cleaner()
        
        # 优化配置
        self.optimization_config = {
            'max_collection_size': 50000,  # 每个集合最大记忆数
            'memory_retention_days': 90,   # 记忆保留天数
            'optimization_interval_hours': 24,  # 24小时优化一次
            'low_access_threshold': 0.1,   # 低访问频率阈值
            'importance_decay_rate': 0.001, # 重要性衰减率
            'memory_compression_ratio': 0.8, # 压缩比率
        }
        # 性能统计
        self.performance_stats = {
            # 最后一次优化操作的时间（通常是 datetime 对象）
            # 用于跟踪最近一次系统优化的时间点，判断是否需要触发新的优化
            'last_optimization': None,
    
            # 累计执行的优化操作总次数
                # 统计系统自启动以来共进行了多少次性能优化（如内存整理、索引优化等）
            'total_optimizations': 0,
    
    # 累计清理的记忆数据总条数
    # 记录所有清理操作中被删除的记忆条目总数，反映内存减负效果
            'total_memories_cleaned': 0,
    
    # 累计节省的存储空间（单位：MB）
    # 统计清理/优化操作释放的总存储空间，评估资源回收效率
            'total_space_saved_mb': 0,
    
    # 平均查询响应时间（单位：毫秒）
    # 记录数据查询操作的平均耗时，反映系统查询性能的整体表现
             'average_query_time_ms': 0,
    
    # 已优化的数据集/集合数量
    # 针对分库分表或多集合存储场景，统计已完成优化的集合数量
            'collections_optimized': 0
}
        
    def run_full_optimization(self) -> Dict[str, Any]:
        """运行完整的数据库优化"""
        logger.info("开始完整的向量数据库优化...")
        
        optimization_result = {
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'total_memories_before': 0,
            'total_memories_after': 0,
            'errors': [],
            'performance_improvements': {}
        }
        
        try:
            # 步骤1: 连接检查
            if not self._check_connection():
                optimization_result['errors'].append("数据库连接失败")
                return optimization_result
            
            optimization_result['steps_completed'].append("数据库连接检查")
            
            # 步骤2: 收集当前统计信息
            initial_stats = self._collect_database_statistics()
            optimization_result['total_memories_before'] = initial_stats['total_memories']
            optimization_result['initial_stats'] = initial_stats
            optimization_result['steps_completed'].append("收集初始统计信息")
            
            # 步骤3: 清理过期记忆
            cleanup_result = self._cleanup_expired_memories()
            optimization_result['cleanup_result'] = cleanup_result
            optimization_result['steps_completed'].append("清理过期记忆")
            
            # 步骤4: 压缩低重要性记忆
            compression_result = self._compress_low_importance_memories()
            optimization_result['compression_result'] = compression_result
            optimization_result['steps_completed'].append("压缩低重要性记忆")
            
            # 步骤5: 优化集合结构
            structure_result = self._optimize_collection_structures()
            optimization_result['structure_result'] = structure_result
            optimization_result['steps_completed'].append("优化集合结构")
            
            # 步骤6: 更新访问统计
            stats_result = self._update_access_statistics()
            optimization_result['stats_result'] = stats_result
            optimization_result['steps_completed'].append("更新访问统计")
            
            # 步骤7: 收集最终统计信息
            final_stats = self._collect_database_statistics()
            optimization_result['total_memories_after'] = final_stats['total_memories']
            optimization_result['final_stats'] = final_stats
            optimization_result['steps_completed'].append("收集最终统计信息")
            
            # 计算性能改进
            optimization_result['performance_improvements'] = self._calculate_improvements(
                initial_stats, final_stats
            )
            
            # 更新全局统计
            self._update_performance_stats(optimization_result)
            
            optimization_result['end_time'] = datetime.now().isoformat()
            optimization_result['success'] = True
            
            logger.info(f"向量数据库优化完成，清理了 {optimization_result['total_memories_before'] - optimization_result['total_memories_after']} 条记忆")
            
        except Exception as e:
            logger.error(f"向量数据库优化失败: {e}")
            optimization_result['errors'].append(str(e))
            optimization_result['success'] = False
        
        return optimization_result
    
    def _check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            return self.vector_store.is_connected()
        except Exception as e:
            logger.error(f"连接检查失败: {e}")
            return False
    
    def _collect_database_statistics(self) -> Dict[str, Any]:
        """收集数据库统计信息"""
        try:
            stats = {
                'total_collections': 0,
                'total_memories': 0,
                'collections_info': {},
                'memory_distribution': {},
                'importance_distribution': {},
                'access_frequency_distribution': {},
                'timestamp': datetime.now().isoformat()
            }
            
            if not self.vector_store.is_connected():
                return stats
            
            collections = self.vector_store.client.get_collections()
            stats['total_collections'] = len(collections.collections)
            
            for collection in collections.collections:
                try:
                    collection_stats = self.vector_store.get_collection_stats(collection.name)
                    
                    collection_info = {
                        'name': collection.name,
                        'memory_count': collection_stats.get('total_points', 0),
                        'average_importance': collection_stats.get('average_importance', 0),
                        'average_access_count': collection_stats.get('average_access_count', 0),
                        'memory_types': collection_stats.get('memory_types', {}),
                        'oldest_memory': collection_stats.get('oldest_memory'),
                        'newest_memory': collection_stats.get('newest_memory')
                    }
                    
                    stats['collections_info'][collection.name] = collection_info
                    stats['total_memories'] += collection_info['memory_count']
                    
                    # 统计分布
                    for mem_type, count in collection_info['memory_types'].items():
                        stats['memory_distribution'][mem_type] = stats['memory_distribution'].get(mem_type, 0) + count
                    
                except Exception as e:
                    logger.warning(f"收集集合 {collection.name} 统计失败: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"收集数据库统计失败: {e}")
            return {'error': str(e)}
    
    def _cleanup_expired_memories(self) -> Dict[str, Any]:
        """清理过期记忆"""
        cleanup_result = {
            'collections_processed': 0,
            'memories_deleted': 0,
            'errors': []
        }
        
        try:
            if not self.vector_store.is_connected():
                return cleanup_result
            
            collections = self.vector_store.client.get_collections()
            
            for collection in collections.collections:
                try:
                    # 使用向量存储的清理方法
                    result = self.vector_store.cleanup_old_memories(
                        collection.name,
                        max_age_days=self.optimization_config['memory_retention_days'],
                        max_memories=self.optimization_config['max_collection_size'],
                        min_importance=0.1
                    )
                    
                    cleanup_result['memories_deleted'] += result.get('deleted', 0)
                    cleanup_result['collections_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"清理集合 {collection.name} 失败: {e}"
                    logger.error(error_msg)
                    cleanup_result['errors'].append(error_msg)
            
        except Exception as e:
            logger.error(f"清理过期记忆失败: {e}")
            cleanup_result['errors'].append(str(e))
        
        return cleanup_result
    
    def _compress_low_importance_memories(self) -> Dict[str, Any]:
        """压缩低重要性记忆"""
        compression_result = {
            'collections_processed': 0,
            'memories_compressed': 0,
            'space_saved_estimate_mb': 0,
            'errors': []
        }
        
        try:
            # 这里可以实现记忆压缩逻辑
            # 例如：合并相似的低重要性记忆，减少存储空间
            
            if not self.vector_store.is_connected():
                return compression_result
            
            collections = self.vector_store.client.get_collections()
            
            for collection in collections.collections:
                try:
                    # 获取低重要性记忆
                    scroll_result = self.vector_store.client.scroll(
                        collection_name=collection.name,
                        with_payload=True,
                        limit=1000
                    )
                    
                    memories = scroll_result[0] if scroll_result else []
                    
                    # 找出低重要性且很少访问的记忆
                    low_importance_memories = []
                    for memory in memories:
                        importance = memory.payload.get('importance', 0.5)
                        access_count = memory.payload.get('access_count', 0)
                        
                        if importance < 0.2 and access_count < 2:
                            low_importance_memories.append(memory)
                    
                    # 这里可以实现压缩算法
                    # 目前只是标记为压缩候选
                    compression_result['memories_compressed'] += len(low_importance_memories)
                    compression_result['collections_processed'] += 1
                    
                    # 估算节省的空间
                    compression_result['space_saved_estimate_mb'] += len(low_importance_memories) * 0.001  # 假设每条记忆1KB
                    
                except Exception as e:
                    error_msg = f"压缩集合 {collection.name} 失败: {e}"
                    logger.error(error_msg)
                    compression_result['errors'].append(error_msg)
            
        except Exception as e:
            logger.error(f"压缩低重要性记忆失败: {e}")
            compression_result['errors'].append(str(e))
        
        return compression_result
    
    def _optimize_collection_structures(self) -> Dict[str, Any]:
        """优化集合结构"""
        optimization_result = {
            'collections_optimized': 0,
            'errors': []
        }
        
        try:
            if not self.vector_store.is_connected():
                return optimization_result
            
            collections = self.vector_store.client.get_collections()
            
            for collection in collections.collections:
                try:
                    # 优化集合
                    self.vector_store.optimize_collection(collection.name)
                    optimization_result['collections_optimized'] += 1
                    
                except Exception as e:
                    error_msg = f"优化集合 {collection.name} 失败: {e}"
                    logger.error(error_msg)
                    optimization_result['errors'].append(error_msg)
            
        except Exception as e:
            logger.error(f"优化集合结构失败: {e}")
            optimization_result['errors'].append(str(e))
        
        return optimization_result
    
    def _update_access_statistics(self) -> Dict[str, Any]:
        """更新访问统计"""
        stats_result = {
            'statistics_updated': True,
            'query_performance_measured': False,
            'errors': []
        }
        
        try:
            # 这里可以测量查询性能
            if self.vector_store.is_connected():
                start_time = time.time()
                
                # 执行一个测试查询来测量性能
                try:
                    collections = self.vector_store.client.get_collections()
                    if collections.collections:
                        test_collection = collections.collections[0].name
                        
                        # 执行测试搜索
                        search_result = self.vector_store.search_memories(
                            test_collection,
                            "测试查询",
                            limit=5
                        )
                        
                        query_time = (time.time() - start_time) * 1000
                        self.performance_stats['average_query_time_ms'] = query_time
                        stats_result['query_performance_measured'] = True
                        stats_result['query_time_ms'] = query_time
                        
                except Exception as e:
                    logger.warning(f"查询性能测试失败: {e}")
            
        except Exception as e:
            logger.error(f"更新访问统计失败: {e}")
            stats_result['errors'].append(str(e))
        
        return stats_result
    
    def _calculate_improvements(self, initial_stats: Dict, final_stats: Dict) -> Dict[str, Any]:
        """计算性能改进"""
        improvements = {}
        
        try:
            # 记忆数量变化
            initial_memories = initial_stats.get('total_memories', 0)
            final_memories = final_stats.get('total_memories', 0)
            
            improvements['memories_reduced'] = initial_memories - final_memories
            improvements['memory_reduction_percent'] = (
                (initial_memories - final_memories) / initial_memories * 100
                if initial_memories > 0 else 0
            )
            
            # 集合数量变化
            initial_collections = initial_stats.get('total_collections', 0)
            final_collections = final_stats.get('total_collections', 0)
            
            improvements['collections_change'] = final_collections - initial_collections
            
            # 估算性能提升
            if improvements['memories_reduced'] > 0:
                improvements['estimated_query_speedup_percent'] = min(
                    improvements['memory_reduction_percent'] * 0.1, 20
                )  # 最多20%的查询速度提升
            
        except Exception as e:
            logger.error(f"计算改进指标失败: {e}")
            improvements['error'] = str(e)
        
        return improvements
    
    def _update_performance_stats(self, optimization_result: Dict):
        """更新性能统计"""
        try:
            self.performance_stats['last_optimization'] = datetime.now().isoformat()
            self.performance_stats['total_optimizations'] += 1
            
            memories_cleaned = optimization_result.get('total_memories_before', 0) - optimization_result.get('total_memories_after', 0)
            self.performance_stats['total_memories_cleaned'] += memories_cleaned
            
            # 估算节省的空间
            space_saved = memories_cleaned * 0.001  # 假设每条记忆1KB
            self.performance_stats['total_space_saved_mb'] += space_saved
            
            cleanup_result = optimization_result.get('cleanup_result', {})
            self.performance_stats['collections_optimized'] += cleanup_result.get('collections_processed', 0)
            
        except Exception as e:
            logger.error(f"更新性能统计失败: {e}")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        try:
            # 收集当前状态
            current_stats = self._collect_database_statistics()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'database_status': self.vector_store.get_connection_status(),
                'current_statistics': current_stats,
                'performance_statistics': self.performance_stats,
                'optimization_config': self.optimization_config,
                'recommendations': self._generate_recommendations(current_stats)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成优化报告失败: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, current_stats: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        try:
            total_memories = current_stats.get('total_memories', 0)
            total_collections = current_stats.get('total_collections', 0)
            
            # 基于记忆数量的建议
            if total_memories > 100000:
                recommendations.append("记忆数量较多，建议增加清理频率")
            
            if total_collections > 20:
                recommendations.append("集合数量较多，考虑合并不活跃的Agent集合")
            
            # 基于性能统计的建议
            avg_query_time = self.performance_stats.get('average_query_time_ms', 0)
            if avg_query_time > 100:
                recommendations.append("查询速度较慢，建议进行集合优化")
            
            # 基于上次优化时间的建议
            last_optimization = self.performance_stats.get('last_optimization')
            if last_optimization:
                last_time = datetime.fromisoformat(last_optimization)
                hours_since_last = (datetime.now() - last_time).total_seconds() / 3600
                
                if hours_since_last > 48:
                    recommendations.append("建议执行全面优化，距离上次优化已超过48小时")
            else:
                recommendations.append("尚未执行过优化，建议执行首次全面优化")
            
            if not recommendations:
                recommendations.append("数据库状态良好，无需特殊优化")
            
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            recommendations.append(f"生成建议时出错: {e}")
        
        return recommendations
    
    def export_optimization_history(self, file_path: str) -> bool:
        """导出优化历史"""
        try:
            history_data = {
                'export_time': datetime.now().isoformat(),
                'performance_stats': self.performance_stats,
                'optimization_config': self.optimization_config,
                'database_status': self.vector_store.get_connection_status(),
                'current_statistics': self._collect_database_statistics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"优化历史已导出到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出优化历史失败: {e}")
            return False

# 全局实例
_vector_optimizer = None

def get_vector_optimizer() -> VectorDatabaseOptimizer:
    """获取全局向量数据库优化器实例"""
    global _vector_optimizer
    if _vector_optimizer is None:
        _vector_optimizer = VectorDatabaseOptimizer()
    return _vector_optimizer
