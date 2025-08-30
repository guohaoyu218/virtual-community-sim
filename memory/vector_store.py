from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import logging
import time
from .embedding_service import get_embedding_service
from config.settings import VECTOR_DB_CONFIG, DOCKER_CONFIG

logger = logging.getLogger(__name__)

class VectorStore:
    """Qdrant向量数据库接口 - Docker服务器模式"""
    
    def __init__(self):
        """初始化向量数据库连接"""
        self.client = None
        self.embedding_service = None
        self.dimension = None
        self._connect_with_retry()
        
    def _connect_with_retry(self):
        """带重试的连接方法"""
        for attempt in range(VECTOR_DB_CONFIG["retry_attempts"]):
            try:
                self._establish_connection()
                self._test_connection()
                logger.info("Qdrant连接成功建立")
                return
            except Exception as e:
                logger.warning(f"连接尝试 {attempt + 1} 失败: {e}")
                if attempt < VECTOR_DB_CONFIG["retry_attempts"] - 1:
                    time.sleep(VECTOR_DB_CONFIG["retry_delay"])
                else:
                    logger.error("所有连接尝试都失败，使用内存模式作为备用")
                    self._fallback_to_memory()
    
    def _establish_connection(self):
        """建立Qdrant连接"""
        host = VECTOR_DB_CONFIG["host"]
        port = VECTOR_DB_CONFIG["port"]
        timeout = VECTOR_DB_CONFIG["timeout"]
        
        logger.info(f"尝试连接到Qdrant服务器: {host}:{port}")
        
        # 创建客户端连接
        self.client = QdrantClient(
            host=host,
            port=port,
            timeout=timeout,
            https=VECTOR_DB_CONFIG.get("https", False),
            api_key=VECTOR_DB_CONFIG.get("api_key")
        )
        
        # 初始化嵌入服务
        self.embedding_service = get_embedding_service()
        self.dimension = self.embedding_service.get_dimension()
        
        logger.info(f"连接配置: {host}:{port}, 向量维度: {self.dimension}")
    
    def _test_connection(self):
        """测试连接是否正常"""
        try:
            # 尝试获取集合列表来测试连接
            collections = self.client.get_collections()
            logger.info(f"连接测试成功，当前集合数量: {len(collections.collections)}")
            
            # 如果启用健康检查，进行更详细的测试
            if DOCKER_CONFIG.get("check_health_on_startup", True):
                self._health_check()
                
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            raise
    
    def _health_check(self):
        """健康检查"""
        try:
            # 创建测试集合
            test_collection = "health_check_test"
            
            # 检查是否存在，如果存在则删除
            collections = self.client.get_collections().collections
            if any(col.name == test_collection for col in collections):
                self.client.delete_collection(test_collection)
            
            # 创建测试集合
            self.client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
            )
            
            # 插入测试数据 - 使用UUID格式的ID
            test_vector = [0.1] * self.dimension
            test_point_id = str(uuid.uuid4())  # 使用UUID格式
            
            self.client.upsert(
                collection_name=test_collection,
                points=[PointStruct(
                    id=test_point_id,  # 修复：使用UUID格式
                    vector=test_vector,
                    payload={"test": True}
                )]
            )
            
            # 搜索测试
            search_result = self.client.search(
                collection_name=test_collection,
                query_vector=test_vector,
                limit=1
            )
            
            # 清理测试集合
            self.client.delete_collection(test_collection)
            
            logger.info("健康检查通过")
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            raise
    
    def _fallback_to_memory(self):
        """回退到内存模式"""
        try:
            logger.warning("使用内存模式Qdrant (数据不会持久化)")
            self.client = QdrantClient(":memory:")
            self.embedding_service = get_embedding_service()
            self.dimension = self.embedding_service.get_dimension()
        except Exception as e:
            logger.error(f"内存模式初始化也失败: {e}")
            raise RuntimeError("无法初始化任何向量数据库模式")
    
    def is_connected(self) -> bool:
        """检查是否连接正常"""
        try:
            if self.client is None:
                return False
            self.client.get_collections()
            return True
        except:
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取详细的连接状态信息"""
        try:
            if self.client is None:
                return {
                    'connected': False,
                    'error': 'Client not initialized'
                }
            
            # 测试连接
            collections = self.client.get_collections()
            
            # 获取数据库信息
            total_collections = len(collections.collections)
            total_points = 0
            
            for collection in collections.collections:
                try:
                    info = self.client.get_collection(collection.name)
                    if hasattr(info, 'points_count'):
                        total_points += info.points_count
                except:
                    continue
            
            return {
                'connected': True,
                'host': VECTOR_DB_CONFIG.get("host", "unknown"),
                'port': VECTOR_DB_CONFIG.get("port", "unknown"),
                'total_collections': total_collections,
                'total_points': total_points,
                'embedding_dimension': self.dimension,
                'client_type': 'persistent' if ':memory:' not in str(self.client) else 'memory'
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def reconnect_if_needed(self):
        """在需要时重新连接"""
        if not self.is_connected():
            logger.warning("检测到连接断开，尝试重新连接...")
            self._connect_with_retry()
    
    def cleanup_old_memories(self, 
                           collection_name: str,
                           max_age_days: int = 30,
                           max_memories: int = 10000,
                           min_importance: float = 0.3) -> Dict[str, int]:
        """清理旧记忆"""
        try:
            # 获取所有记忆
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                with_payload=True,
                limit=max_memories + 1000  # 稍微多获取一些
            )
            
            memories = scroll_result[0] if scroll_result else []
            if not memories:
                return {'deleted': 0, 'total': 0}
            
            # 找出需要删除的记忆
            to_delete = []
            current_time = datetime.now()
            
            for memory in memories:
                should_delete = False
                
                # 检查年龄
                timestamp_str = memory.payload.get('timestamp', '')
                if timestamp_str:
                    try:
                        memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        age_days = (current_time - memory_time.replace(tzinfo=None)).days
                        
                        # 删除过旧且低重要性的记忆
                        importance = memory.payload.get('importance', 0.5)
                        if age_days > max_age_days and importance < min_importance:
                            should_delete = True
                    except:
                        # 无法解析时间戳，认为是旧记忆
                        should_delete = True
                
                # 检查访问频率
                access_count = memory.payload.get('access_count', 0)
                importance = memory.payload.get('importance', 0.5)
                
                # 删除从未访问且重要性极低的记忆
                if access_count == 0 and importance < 0.1:
                    should_delete = True
                
                if should_delete:
                    to_delete.append(memory.id)
            
            # 如果记忆总数超过限制，删除最旧的
            if len(memories) > max_memories:
                # 按时间戳和重要性排序
                sorted_memories = sorted(memories, 
                                       key=lambda m: (
                                           m.payload.get('timestamp', ''),
                                           m.payload.get('importance', 0.5)
                                       ))
                
                excess_count = len(memories) - max_memories
                for memory in sorted_memories[:excess_count]:
                    if memory.id not in to_delete:
                        to_delete.append(memory.id)
            
            # 执行删除
            deleted_count = 0
            if to_delete:
                # 批量删除，避免一次删除过多
                batch_size = 1000
                for i in range(0, len(to_delete), batch_size):
                    batch = to_delete[i:i+batch_size]
                    self.client.delete(
                        collection_name=collection_name,
                        points_selector=batch
                    )
                    deleted_count += len(batch)
                
                logger.info(f"从 {collection_name} 删除了 {deleted_count} 条旧记忆")
            
            return {
                'deleted': deleted_count,
                'total': len(memories),
                'remaining': len(memories) - deleted_count
            }
            
        except Exception as e:
            logger.error(f"清理旧记忆失败: {e}")
            return {'deleted': 0, 'total': 0, 'error': str(e)}
    
    def optimize_collection(self, collection_name: str):
        """优化集合性能"""
        try:
            # 如果支持优化操作
            if hasattr(self.client, 'optimize'):
                self.client.optimize(collection_name)
                logger.info(f"集合 {collection_name} 优化完成")
        except Exception as e:
            logger.warning(f"优化集合 {collection_name} 失败: {e}")
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            info = self.client.get_collection(collection_name)
            
            # 获取详细统计
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                with_payload=True,
                limit=1000  # 样本数量
            )
            
            memories = scroll_result[0] if scroll_result else []
            
            if not memories:
                return {
                    'total_points': 0,
                    'dimension': getattr(info, 'config', {}).get('params', {}).get('size', 0)
                }
            
            # 分析样本
            importance_sum = 0
            access_count_sum = 0
            memory_types = {}
            oldest_timestamp = None
            newest_timestamp = None
            
            for memory in memories:
                importance_sum += memory.payload.get('importance', 0.5)
                access_count_sum += memory.payload.get('access_count', 0)
                
                mem_type = memory.payload.get('memory_type', 'unknown')
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
                
                timestamp = memory.payload.get('timestamp', '')
                if timestamp:
                    if oldest_timestamp is None or timestamp < oldest_timestamp:
                        oldest_timestamp = timestamp
                    if newest_timestamp is None or timestamp > newest_timestamp:
                        newest_timestamp = timestamp
            
            # 安全获取配置信息
            config = getattr(info, 'config', None)
            dimension = self.dimension or 0
            if config:
                if hasattr(config, 'params') and hasattr(config.params, 'vectors'):
                    # 新版本Qdrant的结构
                    if hasattr(config.params.vectors, 'size'):
                        dimension = config.params.vectors.size
                    elif isinstance(config.params.vectors, dict) and 'size' in config.params.vectors:
                        dimension = config.params.vectors['size']
                elif hasattr(config, 'params') and hasattr(config.params, 'size'):
                    # 兼容旧版本
                    dimension = config.params.size

            stats = {
                'total_points': getattr(info, 'points_count', len(memories)),
                'dimension': dimension,
                'sample_size': len(memories),
                'average_importance': importance_sum / len(memories) if memories else 0,
                'average_access_count': access_count_sum / len(memories) if memories else 0,
                'memory_types': memory_types,
                'oldest_memory': oldest_timestamp,
                'newest_memory': newest_timestamp,
                'collection_info': {
                    'name': collection_name,
                    'status': getattr(info, 'status', 'unknown')
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {'error': str(e)}
    
    def create_collection(self, collection_name: str, recreate: bool = False):
        """创建集合"""
        try:
            # 确保连接正常
            self.reconnect_if_needed()
            
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_exists = any(col.name == collection_name for col in collections)
            
            if collection_exists and recreate:
                self.client.delete_collection(collection_name)
                logger.info(f"删除已存在的集合: {collection_name}")
            
            if not collection_exists or recreate:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"创建集合成功: {collection_name}")
                
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            # 尝试重新连接
            self.reconnect_if_needed()
            raise
    
    def add_memory(self, 
                   collection_name: str, 
                   content: str, 
                   agent_id: str,
                   importance: float = 0.5,
                   memory_type: str = "general",
                   metadata: Dict[str, Any] = None) -> str:
        """添加记忆"""
        try:
            # 确保连接正常
            self.reconnect_if_needed()
            
            # 生成记忆ID
            memory_id = str(uuid.uuid4())
            
            # 获取嵌入向量
            embedding = self.embedding_service.encode_single(content)
            
            # 构建payload
            payload = {
                "content": content,
                "agent_id": agent_id,
                "importance": importance,
                "memory_type": memory_type,
                "timestamp": datetime.now().isoformat(),
                "access_count": 0
            }
            
            if metadata:
                payload.update(metadata)
            
            # 插入向量
            self.client.upsert(
                collection_name=collection_name,
                points=[PointStruct(
                    id=memory_id,
                    vector=embedding.tolist(),
                    payload=payload
                )]
            )
            
            logger.debug(f"添加记忆成功: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            # 尝试重新连接后再试一次
            try:
                self.reconnect_if_needed()
                # 这里可以重试一次添加操作
                logger.info("重新连接后重试添加记忆...")
                # 为了避免无限递归，这里返回None表示失败
            except:
                pass
            return None
    
    def search_memories(self, 
                       collection_name: str,
                       query: str,
                       agent_id: str = None,
                       limit: int = 5,
                       min_importance: float = 0.0,
                       memory_type: str = None) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        Args:
            collection_name: 集合名称
            query: 查询文本
            agent_id: 特定Agent ID (可选)
            limit: 返回数量限制
            min_importance: 最小重要性阈值
            memory_type: 记忆类型过滤
        Returns:
            相关记忆列表
        """
        try:
            # 获取查询向量
            query_embedding = self.embedding_service.encode_single(query)
            
            # 构建过滤条件
            filter_conditions = []
            
            if agent_id:
                filter_conditions.append(
                    FieldCondition(key="agent_id", match=MatchValue(value=agent_id))
                )
            
            if min_importance > 0:
                filter_conditions.append(
                    FieldCondition(key="importance", range={"gte": min_importance})
                )
            
            if memory_type:
                filter_conditions.append(
                    FieldCondition(key="memory_type", match=MatchValue(value=memory_type))
                )
            
            # 执行搜索
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=search_filter,
                limit=limit,
                with_payload=True
            )
            
            # 更新访问次数
            self._update_access_counts(collection_name, [r.id for r in results])
            
            # 格式化结果
            memories = []
            for result in results:
                memory = {
                    "id": result.id,
                    "content": result.payload["content"],
                    "similarity": result.score,
                    "importance": result.payload["importance"],
                    "timestamp": result.payload["timestamp"],
                    "memory_type": result.payload.get("memory_type", "general"),
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["content", "agent_id", "importance", "timestamp", "memory_type", "access_count"]}
                }
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []
    
    def _update_access_counts(self, collection_name: str, memory_ids: List[str]):
        """更新记忆访问次数"""
        try:
            for memory_id in memory_ids:
                # 获取当前记录
                result = self.client.retrieve(
                    collection_name=collection_name,
                    ids=[memory_id],
                    with_payload=True
                )
                
                if result:
                    current_count = result[0].payload.get("access_count", 0)
                    # 更新访问次数
                    self.client.set_payload(
                        collection_name=collection_name,
                        points=[memory_id],
                        payload={"access_count": current_count + 1}
                    )
        except Exception as e:
            logger.debug(f"更新访问次数失败: {e}")
    
    def get_agent_memory_stats(self, collection_name: str, agent_id: str) -> Dict[str, Any]:
        """获取Agent记忆统计信息"""
        try:
            # 查询该Agent的所有记忆
            results = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="agent_id", match=MatchValue(value=agent_id))]
                ),
                with_payload=True,
                limit=1000
            )
            
            memories = results[0] if results else []
            
            if not memories:
                return {"total_memories": 0}
            
            total_memories = len(memories)
            avg_importance = sum(m.payload["importance"] for m in memories) / total_memories
            memory_types = {}
            
            for memory in memories:
                mem_type = memory.payload.get("memory_type", "general")
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            return {
                "total_memories": total_memories,
                "average_importance": avg_importance,
                "memory_types": memory_types,
                "oldest_memory": min(m.payload["timestamp"] for m in memories),
                "newest_memory": max(m.payload["timestamp"] for m in memories)
            }
            
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {"total_memories": 0}

# 全局向量存储实例
_vector_store = None

def get_vector_store() -> VectorStore:
    """获取全局向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
