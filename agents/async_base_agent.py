"""
异步Agent基类 - 支持并发执行和缓存优化
"""
import asyncio
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from model_interface.qwen_interface import get_qwen_model
from model_interface.deepseek_api import get_deepseek_api
from memory.memory_manager import get_memory_manager
from utils.async_task_manager import get_task_manager, TaskPriority, submit_agent_task
from utils.redis_manager import get_redis_manager, cache_agent_data, get_agent_data
from config.settings import API_CONFIG
import logging

logger = logging.getLogger(__name__)

class AsyncBaseAgent:
    """异步Agent基类"""
    
    def __init__(self, name: str, personality: str, background: str, profession: str = "通用"):
        self.name = name
        self.personality = personality
        self.background = background
        self.profession = profession
        
        # 状态信息
        self.current_location = "家"
        self.location = "家"
        self.current_mood = "平静"
        self.energy_level = 80
        
        # 关系系统
        self.relationships = {}
        
        # 缓存最近的状态更新时间
        self._last_status_update = 0
        self._status_cache_interval = 60  # 60秒更新一次状态缓存
        
        # 异步锁，防止并发操作冲突
        self._operation_lock = asyncio.Lock()
        
        # 高级记忆系统
        self.memory_manager = get_memory_manager(self.name.lower())
        
        # 模型接口
        self.local_model = get_qwen_model()
        self.deepseek_api = get_deepseek_api() if API_CONFIG.get("use_api_fallback", False) else None
        
        # 任务复杂度阈值
        self.complexity_threshold = 0.3
        
        logger.info(f"异步Agent {self.name} ({self.profession}) 创建成功")
    
    async def initialize(self):
        """异步初始化方法"""
        # 初始化基础记忆
        await self._initialize_memories_async()
        
        # 从缓存恢复状态
        await self._restore_from_cache()
        
        logger.info(f"异步Agent {self.name} 初始化完成")
    
    async def _initialize_memories_async(self):
        """异步初始化基础记忆"""
        # 添加基本身份记忆
        await self._add_memory_async(
            content=f"我是{self.name}，一名{self.profession}。{self.background}",
            memory_type="identity",
            base_importance=0.9
        )
        
        # 添加性格记忆
        await self._add_memory_async(
            content=f"我的性格特点：{self.personality}",
            memory_type="identity",
            base_importance=0.8
        )
    
    async def _restore_from_cache(self):
        """从Redis缓存恢复Agent状态"""
        try:
            cached_status = await get_agent_data(self.name, "agent_status", {})
            if cached_status:
                self.current_location = cached_status.get("location", self.current_location)
                self.current_mood = cached_status.get("mood", self.current_mood)
                self.energy_level = cached_status.get("energy", self.energy_level)
                self.relationships = cached_status.get("relationships", {})
                
                logger.debug(f"从缓存恢复Agent {self.name} 状态")
        except Exception as e:
            logger.warning(f"恢复Agent {self.name} 缓存状态失败: {e}")
    
    async def _save_to_cache(self):
        """保存Agent状态到Redis缓存"""
        try:
            status_data = {
                "location": self.current_location,
                "mood": self.current_mood,
                "energy": self.energy_level,
                "relationships": self.relationships,
                "last_update": time.time()
            }
            
            await cache_agent_data(self.name, "agent_status", status_data)
            self._last_status_update = time.time()
            
        except Exception as e:
            logger.warning(f"保存Agent {self.name} 状态到缓存失败: {e}")
    
    async def _add_memory_async(self, 
                              content: str,
                              memory_type: str = "experience",
                              base_importance: float = 0.5,
                              metadata: Dict[str, Any] = None) -> str:
        """异步添加记忆"""
        # 在线程池中执行同步的记忆操作
        loop = asyncio.get_event_loop()
        memory_id = await loop.run_in_executor(
            None,
            self.memory_manager.add_memory,
            content,
            memory_type,
            base_importance,
            metadata
        )
        
        # 缓存重要记忆
        if base_importance >= 0.7:
            await self._cache_important_memory(content, memory_type, base_importance)
        
        return memory_id
    
    async def _cache_important_memory(self, content: str, memory_type: str, importance: float):
        """缓存重要记忆"""
        try:
            memory_data = {
                "content": content,
                "type": memory_type,
                "importance": importance,
                "timestamp": datetime.now().isoformat()
            }
            
            # 获取现有重要记忆缓存
            cached_memories = await get_agent_data(self.name, "important_memories", [])
            
            # 添加新记忆
            cached_memories.append(memory_data)
            
            # 保持最多10条重要记忆
            if len(cached_memories) > 10:
                cached_memories = sorted(cached_memories, 
                                       key=lambda x: x["importance"], 
                                       reverse=True)[:10]
            
            await cache_agent_data(self.name, "important_memories", cached_memories)
            
        except Exception as e:
            logger.warning(f"缓存重要记忆失败: {e}")
    
    async def think_async(self, situation: str, context: Dict[str, Any] = None) -> str:
        """异步思考方法"""
        async with self._operation_lock:
            # 提交思考任务到任务管理器
            task_id = await submit_agent_task(
                agent_id=self.name,
                func=self._perform_thinking,
                args=(situation, context or {}),
                priority=TaskPriority.NORMAL
            )
            
            # 等待任务完成
            task_manager = await get_task_manager()
            result = await task_manager.get_task_result(task_id, timeout=15.0)
            
            return result
    
    def _perform_thinking(self, situation: str, context: Dict[str, Any]) -> str:
        """执行思考逻辑(同步方法，由任务管理器调用)"""
        # 检查任务复杂度
        complexity = self._assess_complexity(situation)
        
        # 构建提示词
        prompt = self._build_thinking_prompt(situation, context)
        
        try:
            if complexity > self.complexity_threshold and self.deepseek_api and self.deepseek_api.is_available():
                # 使用API处理复杂任务
                response = self.deepseek_api.generate_response(prompt, max_tokens=200)
            else:
                # 使用本地模型
                response = self.local_model.generate_response(prompt, max_tokens=150)
            
            # 添加思考记忆
            self.memory_manager.add_memory(
                content=f"思考情况：{situation}。想法：{response}",
                memory_type="thinking",
                base_importance=0.4
            )
            
            return response
            
        except Exception as e:
            logger.error(f"思考过程失败: {e}")
            return f"我需要仔细思考这个问题：{situation}"
    
    async def interact_async(self, other_agent: 'AsyncBaseAgent', context: str = "") -> Dict[str, Any]:
        """异步交互方法"""
        interaction_id = f"{self.name}_{other_agent.name}_{int(time.time())}"
        
        # 检查缓存的最近交互
        cached_interaction = await get_agent_data(
            interaction_id[:50],  # 限制键长度
            "recent_interaction",
            None
        )
        
        if cached_interaction and time.time() - cached_interaction.get("timestamp", 0) < 300:
            # 5分钟内有缓存交互，直接返回
            logger.debug(f"使用缓存交互: {self.name} -> {other_agent.name}")
            return cached_interaction
        
        # 并行执行双方的思考
        my_task = submit_agent_task(
            agent_id=self.name,
            func=self._prepare_interaction,
            args=(other_agent.name, context),
            priority=TaskPriority.HIGH
        )
        
        other_task = submit_agent_task(
            agent_id=other_agent.name,
            func=other_agent._prepare_interaction,
            args=(self.name, context),
            priority=TaskPriority.HIGH
        )
        
        # 等待双方准备完成
        task_manager = await get_task_manager()
        
        my_preparation = await task_manager.get_task_result(await my_task, timeout=10.0)
        other_preparation = await task_manager.get_task_result(await other_task, timeout=10.0)
        
        # 生成交互结果
        interaction_result = {
            "participants": [self.name, other_agent.name],
            "context": context,
            "my_approach": my_preparation,
            "other_approach": other_preparation,
            "timestamp": time.time(),
            "location": self.current_location
        }
        
        # 缓存交互结果
        await cache_agent_data(
            interaction_id[:50],
            "recent_interaction", 
            interaction_result
        )
        
        # 更新关系
        await self._update_relationship_async(other_agent.name, "interaction")
        await other_agent._update_relationship_async(self.name, "interaction")
        
        return interaction_result
    
    def _prepare_interaction(self, other_agent_name: str, context: str) -> str:
        """准备交互的内容(同步方法)"""
        # 获取相关记忆
        memories = self.memory_manager.retrieve_memories(
            query=f"与{other_agent_name}的交往经历",
            memory_types=["social", "experience"],
            limit=3
        )
        
        memory_context = "\n".join([mem["content"] for mem in memories])
        
        prompt = f"""
作为{self.name}({self.profession})，性格：{self.personality}
当前心情：{self.current_mood}，位置：{self.current_location}

相关记忆：
{memory_context}

现在要与{other_agent_name}交流，情况：{context}

请用一句话描述你的交流方式：
"""
        
        try:
            response = self.local_model.generate_response(prompt, max_tokens=100)
            return response.strip()
        except Exception as e:
            logger.error(f"准备交互失败: {e}")
            return f"我准备与{other_agent_name}进行友好交流"
    
    async def _update_relationship_async(self, other_agent: str, interaction_type: str):
        """异步更新关系"""
        async with self._operation_lock:
            if other_agent not in self.relationships:
                self.relationships[other_agent] = {"familiarity": 0, "last_interaction": 0}
            
            # 更新关系数据
            self.relationships[other_agent]["familiarity"] += 1
            self.relationships[other_agent]["last_interaction"] = time.time()
            
            # 如果需要，保存到缓存
            current_time = time.time()
            if current_time - self._last_status_update > self._status_cache_interval:
                await self._save_to_cache()
    
    async def move_to_async(self, location: str, reason: str = ""):
        """异步移动到新位置"""
        if location == self.current_location:
            return
        
        async with self._operation_lock:
            old_location = self.current_location
            self.current_location = location
            self.location = location  # 兼容性
            
            # 添加移动记忆
            await self._add_memory_async(
                content=f"从{old_location}移动到{location}。原因：{reason}",
                memory_type="experience",
                base_importance=0.3
            )
            
            # 更新缓存
            await self._save_to_cache()
            
            logger.debug(f"{self.name} 移动到 {location}")
    
    def _assess_complexity(self, text: str) -> float:
        """评估文本复杂度"""
        # 简单的复杂度评估
        factors = 0
        
        # 长度因子
        if len(text) > 100:
            factors += 0.2
        if len(text) > 200:
            factors += 0.2
        
        # 问题复杂度
        complex_keywords = ["为什么", "如何", "分析", "解释", "计划", "策略", "方案"]
        for keyword in complex_keywords:
            if keyword in text:
                factors += 0.1
        
        return min(factors, 1.0)
    
    def _build_thinking_prompt(self, situation: str, context: Dict[str, Any]) -> str:
        """构建思考提示词"""
        return f"""
作为{self.name}({self.profession})，我的性格是{self.personality}。
当前状态：心情{self.current_mood}，位置{self.current_location}，精力{self.energy_level}。

面对情况：{situation}

结合我的背景和性格，我会如何思考和应对？请简洁回答。
"""
    
    async def get_status_async(self) -> Dict[str, Any]:
        """异步获取Agent状态"""
        return {
            "name": self.name,
            "profession": self.profession,
            "personality": self.personality,
            "location": self.current_location,
            "mood": self.current_mood,
            "energy": self.energy_level,
            "relationships_count": len(self.relationships),
            "last_update": self._last_status_update
        }
    
    async def cleanup(self):
        """清理资源"""
        # 最后保存状态到缓存
        await self._save_to_cache()
        logger.info(f"异步Agent {self.name} 清理完成")
