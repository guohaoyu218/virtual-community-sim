"""
简化的Redis管理器 - 支持fallback到内存缓存
"""
import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SimpleRedisManager:
    """简化的Redis缓存管理器，支持内存fallback"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None):
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        # 内存缓存作为fallback
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # Redis客户端
        self.redis_client = None
        self.is_connected = False
        
        # 缓存键前缀
        self.key_prefixes = {
            "agent_memory": "agent:memory:",
            "agent_status": "agent:status:",
            "interaction": "interaction:",
            "location": "location:",
            "system": "system:",
            "task_result": "task:result:",
            "session": "session:"
        }
        
        # 默认TTL设置(秒)
        self.default_ttl = {
            "agent_memory": 3600,
            "agent_status": 300,
            "interaction": 1800,
            "location": 600,
            "system": 86400,
            "task_result": 1800,
            "session": 7200
        }
    
    async def connect(self):
        """尝试连接Redis，失败时使用内存缓存"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # 测试连接
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.redis_client.ping)
            
            self.is_connected = True
            logger.info(f"✅ Redis连接成功: {self.host}:{self.port}")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败，使用内存缓存: {e}")
            self.redis_client = None
            self.is_connected = False
    
    async def disconnect(self):
        """断开连接"""
        if self.redis_client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.redis_client.close)
            except:
                pass
        self.is_connected = False
        logger.info("Redis连接已断开")
    
    def _get_full_key(self, category: str, key: str) -> str:
        """获取完整的缓存键"""
        prefix = self.key_prefixes.get(category, "misc:")
        return f"{prefix}{key}"
    
    def _cleanup_memory_cache(self):
        """清理过期的内存缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp > 3600:  # 1小时过期
                expired_keys.append(key)
        
        for key in expired_keys:
            self._memory_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
    
    async def set_cache(self, 
                       category: str,
                       key: str, 
                       value: Any,
                       ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        full_key = self._get_full_key(category, key)
        
        # 序列化值
        if isinstance(value, (dict, list)):
            serialized_value = json.dumps(value, ensure_ascii=False)
        else:
            serialized_value = str(value)
        
        # 设置TTL
        if ttl is None:
            ttl = self.default_ttl.get(category, 3600)
        
        try:
            if self.is_connected and self.redis_client:
                # 使用Redis
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.redis_client.setex,
                    full_key,
                    ttl,
                    serialized_value
                )
                logger.debug(f"Redis缓存已设置: {full_key}")
            else:
                # 使用内存缓存
                self._memory_cache[full_key] = {
                    "value": serialized_value,
                    "ttl": ttl,
                    "timestamp": time.time()
                }
                self._cache_timestamps[full_key] = time.time()
                logger.debug(f"内存缓存已设置: {full_key}")
                
                # 定期清理
                if len(self._memory_cache) % 100 == 0:
                    self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    async def get_cache(self, 
                       category: str,
                       key: str,
                       default: Any = None) -> Any:
        """获取缓存"""
        full_key = self._get_full_key(category, key)
        
        try:
            if self.is_connected and self.redis_client:
                # 从Redis获取
                loop = asyncio.get_event_loop()
                value = await loop.run_in_executor(
                    None,
                    self.redis_client.get,
                    full_key
                )
            else:
                # 从内存缓存获取
                cache_entry = self._memory_cache.get(full_key)
                if cache_entry:
                    # 检查是否过期
                    current_time = time.time()
                    if current_time - cache_entry["timestamp"] > cache_entry["ttl"]:
                        # 过期，删除
                        self._memory_cache.pop(full_key, None)
                        self._cache_timestamps.pop(full_key, None)
                        value = None
                    else:
                        value = cache_entry["value"]
                else:
                    value = None
            
            if value is None:
                return default
            
            # 尝试反序列化JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return default
    
    async def delete_cache(self, category: str, key: str) -> bool:
        """删除缓存"""
        full_key = self._get_full_key(category, key)
        
        try:
            if self.is_connected and self.redis_client:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.redis_client.delete,
                    full_key
                )
                return result > 0
            else:
                # 从内存缓存删除
                deleted = full_key in self._memory_cache
                self._memory_cache.pop(full_key, None)
                self._cache_timestamps.pop(full_key, None)
                return deleted
                
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            if self.is_connected and self.redis_client:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, self.redis_client.info)
                
                db_keys = 0
                if 'db0' in info:
                    db_info = info['db0']
                    if isinstance(db_info, dict):
                        db_keys = db_info.get('keys', 0)
                    else:
                        import re
                        match = re.search(r'keys=(\d+)', str(db_info))
                        if match:
                            db_keys = int(match.group(1))
                
                return {
                    "connected": True,
                    "backend": "Redis",
                    "total_keys": db_keys,
                    "used_memory": info.get("used_memory_human", "0B"),
                    "connected_clients": info.get("connected_clients", 0),
                    "uptime": info.get("uptime_in_seconds", 0)
                }
            else:
                return {
                    "connected": False,
                    "backend": "Memory",
                    "total_keys": len(self._memory_cache),
                    "used_memory": f"{len(self._memory_cache) * 100}B (估算)",
                    "connected_clients": 1,
                    "uptime": 0
                }
                
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {"connected": False, "error": str(e)}
    
    # Agent专用缓存方法
    async def cache_agent_memory(self, agent_id: str, memory_data: Dict[str, Any]) -> bool:
        """缓存Agent记忆"""
        return await self.set_cache("agent_memory", agent_id, memory_data)
    
    async def get_agent_memory(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent记忆缓存"""
        return await self.get_cache("agent_memory", agent_id, {})
    
    async def cache_agent_status(self, agent_id: str, status: Dict[str, Any]) -> bool:
        """缓存Agent状态"""
        return await self.set_cache("agent_status", agent_id, status, ttl=300)
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent状态缓存"""
        return await self.get_cache("agent_status", agent_id, {})

# 全局Redis管理器实例
_redis_manager = None

async def get_redis_manager() -> SimpleRedisManager:
    """获取全局Redis管理器实例"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = SimpleRedisManager()
        await _redis_manager.connect()
    return _redis_manager

# 便捷函数
async def cache_agent_data(agent_id: str, data_type: str, data: Any) -> bool:
    """缓存Agent数据的便捷函数"""
    redis_manager = await get_redis_manager()
    return await redis_manager.set_cache(data_type, agent_id, data)

async def get_agent_data(agent_id: str, data_type: str, default: Any = None) -> Any:
    """获取Agent数据的便捷函数"""
    redis_manager = await get_redis_manager()
    return await redis_manager.get_cache(data_type, agent_id, default)
