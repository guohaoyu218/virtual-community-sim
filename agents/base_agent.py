import time
import random
from datetime import datetime
from typing import List, Dict, Any
from model_interface.qwen_interface import get_qwen_model
from model_interface.deepseek_api import get_deepseek_api
from memory.memory_manager import get_memory_manager
from config.settings import API_CONFIG
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, name: str, personality: str, background: str, profession: str = "通用"):
        self.name = name
        self.personality = personality
        self.background = background
        self.profession = profession
        
        # 状态信息
        self.current_location = "家"
        self.location = "家"  # 兼容性属性
        self.current_mood = "平静"
        self.energy_level = 80
        
        # 关系系统
        self.relationships = {}
        
        # 高级记忆系统
        self.memory_manager = get_memory_manager(self.name.lower())
        
        # 模型接口
        self.local_model = get_qwen_model()
        self.deepseek_api = get_deepseek_api() if API_CONFIG.get("use_api_fallback", False) else None
        
        # 任务复杂度阈值 - 降低阈值让更多任务使用API
        self.complexity_threshold = 0.3
        
        # 添加初始记忆
        self._initialize_memories()
        
        logger.info(f"Agent {self.name} ({self.profession}) 创建成功")
        if self.deepseek_api and self.deepseek_api.is_available():
            logger.info(f"{self.name} 具备DeepSeek高级推理能力")
    
    def _initialize_memories(self):
        """初始化基础记忆"""
        # 添加基本身份记忆
        self.memory_manager.add_memory(
            content=f"我是{self.name}，一名{self.profession}。{self.background}",
            memory_type="identity",
            base_importance=0.9
        )
        
        # 添加个性记忆
        self.memory_manager.add_memory(
            content=f"我的个性特点：{self.personality}",
            memory_type="identity", 
            base_importance=0.8
        )
    
    def add_memory(self, memory: str, importance: int = 5, memory_type: str = "experience"):
        """添加记忆 (统一接口)"""
        # 转换重要性到0-1范围
        base_importance = min(1.0, importance / 10.0)
        
        # 添加到向量记忆系统
        memory_id = self.memory_manager.add_memory(
            content=memory,
            memory_type=memory_type,
            base_importance=base_importance
        )
        
        logger.debug(f"{self.name} 添加记忆: {memory}")
        return memory_id
    
    def get_recent_memories(self, count: int = 5) -> List[str]:
        """获取最近的记忆"""
        try:
            recent_experiences = self.memory_manager.get_recent_experiences(
                hours=24, limit=count
            )
            return [mem["content"] for mem in recent_experiences]
        except Exception as e:
            logger.error(f"获取最近记忆失败: {e}")
            return []
    
    def retrieve_relevant_memories(self, context: str, limit: int = 3) -> List[str]:
        """检索与当前情况相关的记忆"""
        try:
            # 简单的本地缓存，避免频繁查询相同内容
            cache_key = f"{context[:50]}_{limit}"
            if hasattr(self, '_memory_cache') and cache_key in self._memory_cache:
                cache_time, cached_memories = self._memory_cache[cache_key]
                if time.time() - cache_time < 120:  # 2分钟缓存
                    return cached_memories
            
            relevant_memories = self.memory_manager.retrieve_memories(
                query=context,
                limit=limit,
                min_importance=0.2
            )
            result = [mem["content"] for mem in relevant_memories]
            
            # 更新缓存
            if not hasattr(self, '_memory_cache'):
                self._memory_cache = {}
            self._memory_cache[cache_key] = (time.time(), result)
            
            return result
        except Exception as e:
            logger.error(f"检索相关记忆失败: {e}")
            return self.get_recent_memories(limit)
    
    def build_personality_prompt(self, context: str) -> str:
        """构建更自然的个性化prompt"""
        # 检测是否是负面互动，如果是则添加特殊指令
        negative_keywords = ['不同意', '反对', '困惑', '质疑', '失望', '坚持立场', '负面立场', '不要缓解气氛']
        is_negative_interaction = any(keyword in context for keyword in negative_keywords)
        
        if is_negative_interaction:
            # 负面互动时，强制保持负面，不允许缓解气氛
            prompt = f"""{self.name}是一名{self.profession}，{self.personality}。
现在{context}
重要：这是负面互动，必须保持负面情感，不允许缓解气氛或转向积极。
{self.name}："""
        else:
            # 正常互动
            prompt = f"""{self.name}是一名{self.profession}，{self.personality}。
现在{context}
{self.name}："""
        return prompt
    
    def analyze_task_complexity(self, situation: str) -> float:
        """分析任务复杂度"""
        complexity_indicators = [
            len(situation.split()) > 15,  # 降低长文本阈值
            any(word in situation for word in ["为什么", "怎么办", "分析", "设计", "介绍", "详细", "发展", "趋势"]),  # 需要分析
            any(word in situation for word in ["创作", "创意", "想象"]),  # 创意任务
            any(word in situation for word in ["复杂", "深入", "详细", "强化学习", "算法", "技术"]),  # 明确要求复杂回应
            "?" in situation or "？" in situation,  # 问题类型
        ]
        
        complexity = sum(complexity_indicators) / len(complexity_indicators)
        logger.debug(f"任务复杂度分析: {situation[:30]}... -> {complexity}")
        return complexity
    
    def should_use_advanced_model(self, situation: str) -> bool:
        """判断是否需要使用高级模型"""
        # 检查是否有可用的高级模型
        if not self.deepseek_api or not self.deepseek_api.is_available():
            return False
        
        complexity = self.analyze_task_complexity(situation)
        return complexity > self.complexity_threshold
    
    def think_and_respond(self, situation: str) -> str:
        """思考并回应情况"""
        try:
            # 智能路由：根据复杂度选择模型
            if self.should_use_advanced_model(situation):
                logger.debug(f"{self.name} 使用DeepSeek高级推理")
                response = self._advanced_thinking_with_api(situation)
            else:
                logger.debug(f"{self.name} 使用本地模型回应")
                response = self._simple_thinking(situation)
            
            # 记录这次交互
            memory_content = f"面对'{situation}'时，我回应：{response}"
            self.add_memory(memory_content, importance=6, memory_type="experience")
            
            return response
            
        except Exception as e:
            logger.error(f"{self.name} 回应时出错: {e}")
            return f"*{self.name}似乎在思考什么，暂时没有说话*"
    
    def _simple_thinking(self, situation: str) -> str:
        """简单思考模式 - 使用本地模型"""
        prompt = self.build_personality_prompt(situation)
        return self.local_model.chat(prompt, max_tokens=120)  # 从800降到120
    
    def _advanced_thinking_with_api(self, situation: str) -> str:
        """高级思考模式 - 使用DeepSeek API"""
        if not self.deepseek_api or not self.deepseek_api.is_available():
            # 回退到本地模型
            return self._advanced_thinking_local(situation)
        
        # 构建更自然的prompt用于API
        enhanced_prompt = f"""
        {self.name}是一名{self.profession}。
        
        个性特点：{self.personality}
        背景：{self.background}

        状态：在{self.current_location}，心情{self.current_mood}，精力{self.energy_level}%

        相关经历：{self.retrieve_relevant_memories(situation, limit=3)}

        遇到的情况：{situation}

        {self.name}："""
        
        return self.deepseek_api.chat(enhanced_prompt, max_tokens=180)  # 从1200降到180
    
    def _advanced_thinking_local(self, situation: str) -> str:
        """高级思考模式 - 本地模型备用"""
        prompt = f"""
        {self.build_personality_prompt(situation)}
        
        {self.name}：
        """
        return self.local_model.chat(prompt, max_tokens=150)  # 从800降到150
    
    def interact_with(self, other_agent, message: str) -> str:
        """与另一个Agent交互"""
        # 构建社交情境
        relationship_context = ""
        if other_agent.name in self.relationships:
            relationship_level = self.relationships[other_agent.name]
            if relationship_level > 70:
                relationship_context = f"我和{other_agent.name}是好朋友"
            elif relationship_level > 50:
                relationship_context = f"我对{other_agent.name}有好感"
            elif relationship_level < 30:
                relationship_context = f"我对{other_agent.name}不太熟悉"
        
        situation = f"{other_agent.name}对我说：'{message}'。{relationship_context}"
        response = self.think_and_respond(situation)
        
        # 更新关系
        if other_agent.name not in self.relationships:
            self.relationships[other_agent.name] = 50
        
        # 根据交互内容微调关系
        positive_words = ["你好", "谢谢", "很棒", "同意", "喜欢"]
        negative_words = ["不对", "讨厌", "烦人", "错误"]
        
        if any(word in message.lower() for word in positive_words):
            self.relationships[other_agent.name] += 5
        elif any(word in message.lower() for word in negative_words):
            self.relationships[other_agent.name] -= 3
        
        # 限制关系值范围
        self.relationships[other_agent.name] = max(0, min(100, self.relationships[other_agent.name]))
        
        # 记录社交互动
        social_memory = f"与{other_agent.name}的对话：他们说'{message}'，我回应'{response}'，关系度：{self.relationships[other_agent.name]}"
        self.add_memory(social_memory, importance=7, memory_type="social")
        
        return response
    
    def update_status(self):
        """更新Agent状态"""
        # 同步location属性
        if hasattr(self, 'location') and self.location != self.current_location:
            self.current_location = self.location
        elif hasattr(self, 'current_location') and not hasattr(self, 'location'):
            self.location = self.current_location
        
        # 随机变化心情和精力
        from config.settings import AVAILABLE_MOODS
        
        if random.random() < 0.3:  # 30%概率改变心情
            self.current_mood = random.choice(AVAILABLE_MOODS)
        
        # 精力随时间消耗
        self.energy_level = max(10, self.energy_level - random.randint(1, 5))
        
        if self.energy_level < 30:
            self.current_mood = "疲惫"
    
    def get_memory_summary(self) -> str:
        """获取记忆摘要"""
        try:
            summary = self.memory_manager.get_memory_summary()
            return summary.get("summary", "暂无记忆摘要")
        except Exception as e:
            logger.error(f"获取记忆摘要失败: {e}")
            return "记忆系统暂时不可用"
    
    def get_model_status(self) -> Dict[str, bool]:
        """获取模型可用状态"""
        return {
            "local_model": self.local_model is not None,
            "deepseek_api": self.deepseek_api is not None and self.deepseek_api.is_available(),
            "memory_system": self.memory_manager is not None
        }
    
    def __str__(self):
        status = self.get_model_status()
        api_status = "🚀" if status["deepseek_api"] else "🏠"
        return f"{self.name} {api_status} (位置: {self.current_location}, 心情: {self.current_mood})"