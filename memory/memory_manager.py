from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import time
from .vector_store import get_vector_store
from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

class MemoryManager:
    """Agent记忆管理器"""
    
    def __init__(self, agent_id: str):
        """
        初始化记忆管理器
        Args:
            agent_id: Agent唯一标识
        """
        self.agent_id = agent_id
        self.vector_store = get_vector_store()
        self.collection_name = f"agent_{agent_id}_memories"
        
        # 添加简单缓存机制
        self._memory_cache = {}
        self._cache_timeout = 300  # 5分钟缓存
        self._last_query_time = 0
        self._query_interval = 10  # 至少间隔10秒才能查询
        
        # 创建该Agent的记忆集合
        self.vector_store.create_collection(self.collection_name)
        
        # 记忆重要性权重
        self.importance_weights = {
            "recency": 0.3,      # 时间近期性
            "relevance": 0.4,    # 与当前情况的相关性
            "importance": 0.2,   # 原始重要性分数
            "access_frequency": 0.1  # 访问频率
        }
        
        logger.info(f"记忆管理器初始化完成: {agent_id}")
    
    def add_memory(self, 
                   content: str, 
                   memory_type: str = "experience",
                   base_importance: float = 0.5,
                   metadata: Dict[str, Any] = None) -> str:
        """
        添加新记忆
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (experience, learning, social, goal)
            base_importance: 基础重要性 (0-1)
            metadata: 额外元数据
        Returns:
            记忆ID
        """
        # 评估记忆重要性
        importance = self._evaluate_importance(content, memory_type, base_importance)
        
        # 添加到向量存储
        memory_id = self.vector_store.add_memory(
            collection_name=self.collection_name,
            content=content,
            agent_id=self.agent_id,
            importance=importance,
            memory_type=memory_type,
            metadata=metadata or {}
        )
        
        logger.debug(f"添加记忆: {memory_type} - {content[:50]}...")
        return memory_id
    
    def retrieve_memories(self, 
                         query: str, 
                         memory_types: List[str] = None,
                         limit: int = 5,
                         min_importance: float = 0.1) -> List[Dict[str, Any]]:
        """
        检索相关记忆
        Args:
            query: 查询内容
            memory_types: 记忆类型过滤
            limit: 返回数量
            min_importance: 最小重要性阈值
        Returns:
            相关记忆列表
        """
        # 检查缓存和查询频率限制
        current_time = time.time()
        cache_key = f"{query}_{memory_types}_{limit}_{min_importance}"
        
        # 如果太频繁查询，返回缓存或简单结果
        if current_time - self._last_query_time < self._query_interval:
            if cache_key in self._memory_cache:
                cache_data = self._memory_cache[cache_key]
                if current_time - cache_data['timestamp'] < self._cache_timeout:
                    logger.debug(f"使用缓存记忆: {query[:20]}...")
                    return cache_data['memories']
            
            # 返回简单的默认记忆
            return []
        
        self._last_query_time = current_time
        
        all_memories = []
        
        try:
            if memory_types:
                # 分别搜索不同类型的记忆
                for mem_type in memory_types:
                    memories = self.vector_store.search_memories(
                        collection_name=self.collection_name,
                        query=query,
                        agent_id=self.agent_id,
                        limit=limit,
                        min_importance=min_importance,
                        memory_type=mem_type
                    )
                    all_memories.extend(memories)
            else:
                # 搜索所有类型
                all_memories = self.vector_store.search_memories(
                    collection_name=self.collection_name,
                    query=query,
                    agent_id=self.agent_id,
                    limit=limit * 2,  # 搜索更多然后重新排序
                    min_importance=min_importance
                )
            
            # 重新计算记忆分数并排序
            scored_memories = self._score_memories(all_memories, query)
            
            # 缓存结果
            self._memory_cache[cache_key] = {
                'memories': scored_memories[:limit],
                'timestamp': current_time
            }
            
            # 返回前N个最相关的记忆
            return scored_memories[:limit]
            
        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            return []
    
    def get_recent_experiences(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的经历"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        memories = self.vector_store.search_memories(
            collection_name=self.collection_name,
            query="最近的经历和活动",
            agent_id=self.agent_id,
            limit=limit,
            memory_type="experience"
        )
        
        # 过滤时间并按时间排序
        recent_memories = []
        for memory in memories:
            memory_time = datetime.fromisoformat(memory["timestamp"])
            if memory_time >= cutoff_time:
                recent_memories.append(memory)
        
        return sorted(recent_memories, key=lambda x: x["timestamp"], reverse=True)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        stats = self.vector_store.get_agent_memory_stats(
            self.collection_name, 
            self.agent_id
        )
        
        if stats["total_memories"] == 0:
            return {"summary": "暂无记忆", "stats": stats}
        
        # 获取重要记忆
        important_memories = self.vector_store.search_memories(
            collection_name=self.collection_name,
            query="重要的经历和学习",
            agent_id=self.agent_id,
            limit=3,
            min_importance=0.7
        )
        
        summary = {
            "stats": stats,
            "important_memories": [m["content"] for m in important_memories],
            "summary": f"共有{stats['total_memories']}条记忆，平均重要性{stats.get('average_importance', 0):.2f}"
        }
        
        return summary
    
    def _evaluate_importance(self, 
                           content: str, 
                           memory_type: str, 
                           base_importance: float) -> float:
        """评估记忆重要性"""
        importance = base_importance
        
        # 根据记忆类型调整
        type_multipliers = {
            "goal": 0.9,        # 目标相关很重要
            "social": 0.8,      # 社交互动重要
            "learning": 0.7,    # 学习内容重要
            "experience": 0.6,  # 一般经历
            "routine": 0.3      # 日常琐事
        }
        
        importance *= type_multipliers.get(memory_type, 0.5)
        
        # 根据内容关键词调整
        important_keywords = ["决定", "学会", "发现", "重要", "第一次", "成功", "失败", "朋友"]
        for keyword in important_keywords:
            if keyword in content:
                importance *= 1.2
                break
        
        # 限制在0-1范围内
        return max(0.0, min(1.0, importance))
    
    def _score_memories(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """重新计算记忆综合分数"""
        current_time = datetime.now()
        
        for memory in memories:
            memory_time = datetime.fromisoformat(memory["timestamp"])
            hours_ago = (current_time - memory_time).total_seconds() / 3600
            
            # 计算时间衰减分数 (24小时内为1.0，之后指数衰减)
            recency_score = max(0.1, 1.0 / (1 + hours_ago / 24))
            
            # 综合分数
            final_score = (
                memory["similarity"] * self.importance_weights["relevance"] +
                memory["importance"] * self.importance_weights["importance"] +
                recency_score * self.importance_weights["recency"]
            )
            
            memory["final_score"] = final_score
        
        # 按综合分数排序
        return sorted(memories, key=lambda x: x["final_score"], reverse=True)

# 全局记忆管理器缓存
_memory_managers = {}

def get_memory_manager(agent_id: str) -> MemoryManager:
    """获取Agent的记忆管理器"""
    global _memory_managers
    if agent_id not in _memory_managers:
        _memory_managers[agent_id] = MemoryManager(agent_id)
    return _memory_managers[agent_id]
