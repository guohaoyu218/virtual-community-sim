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
    
    def reconnect_if_needed(self):
        """在需要时重新连接"""
        if not self.is_connected():
            logger.warning("检测到连接断开，尝试重新连接...")
            self._connect_with_retry()
    
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
