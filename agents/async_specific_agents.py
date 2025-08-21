"""
异步版本的特定Agent类
"""
import time
import random
from typing import Dict, List, Any, Optional
from .async_base_agent import AsyncBaseAgent
from utils.async_task_manager import TaskPriority, submit_agent_task, get_task_manager
from utils.redis_manager import cache_agent_data, get_agent_data
import asyncio
import logging

logger = logging.getLogger(__name__)

class AsyncAlexProgrammer(AsyncBaseAgent):
    """异步程序员Alex"""
    
    def __init__(self):
        super().__init__(
            name="Alex",
            personality="内向、逻辑性强、喜欢独处思考，说话简洁理性",
            background="一名经验丰富的Python开发者，喜欢解决技术难题",
            profession="程序员"
        )
        self.complexity_threshold = 0.3  # 程序员更容易进入深度思考
        self.coding_skills = ["Python", "JavaScript", "SQL", "Git"]
        self.current_project = None
    
    async def code_review_async(self, code_snippet: str, author: str) -> str:
        """异步代码审查"""
        task_id = await submit_agent_task(
            agent_id=self.name,
            func=self._perform_code_review,
            args=(code_snippet, author),
            priority=TaskPriority.HIGH  # 代码审查优先级高
        )
        
        task_manager = await get_task_manager()
        review_result = await task_manager.get_task_result(task_id, timeout=20.0)
        
        # 缓存代码审查结果
        await cache_agent_data(
            f"code_review_{hash(code_snippet)}",
            "code_review",
            {
                "code": code_snippet,
                "author": author,
                "review": review_result,
                "reviewer": self.name,
                "timestamp": time.time()
            }
        )
        
        return review_result
    
    def _perform_code_review(self, code_snippet: str, author: str) -> str:
        """执行代码审查(同步方法)"""
        prompt = f"""
作为资深Python开发者Alex，请审查以下代码：

代码作者：{author}
代码内容：
```
{code_snippet}
```

请从以下角度给出简洁的审查意见：
1. 代码质量
2. 性能优化建议
3. 潜在问题

保持Alex的理性、简洁风格：
"""
        
        try:
            if self.deepseek_api and self.deepseek_api.is_available():
                response = self.deepseek_api.generate_response(prompt, max_tokens=300)
            else:
                response = self.local_model.generate_response(prompt, max_tokens=200)
            
            # 添加代码审查记忆
            self.memory_manager.add_memory(
                content=f"审查了{author}的代码。建议：{response}",
                memory_type="professional",
                base_importance=0.6
            )
            
            return response
            
        except Exception as e:
            logger.error(f"代码审查失败: {e}")
            return "代码审查系统暂时不可用，建议稍后重试。"

class AsyncEmmaArtist(AsyncBaseAgent):
    """异步艺术家Emma"""
    
    def __init__(self):
        super().__init__(
            name="Emma",
            personality="富有创造力、情感丰富、善于表达，喜欢美好的事物",
            background="一名自由艺术家，擅长绘画和设计，对色彩和美学有独特见解",
            profession="艺术家"
        )
        self.art_styles = ["水彩", "油画", "数字艺术", "平面设计"]
        self.current_inspiration = "自然风景"
    
    async def create_artwork_async(self, theme: str, collaborator: str = None) -> Dict[str, Any]:
        """异步创作艺术作品"""
        creation_id = f"artwork_{theme}_{int(time.time())}"
        
        # 检查是否有相似主题的缓存作品
        cached_work = await get_agent_data(
            f"artwork_{theme}",
            "artwork_cache",
            None
        )
        
        if cached_work and time.time() - cached_work.get("created_at", 0) < 3600:
            # 1小时内有相似作品，基于它进行变化
            logger.debug(f"基于缓存作品创作新的 {theme} 主题作品")
            base_work = cached_work
        else:
            base_work = None
        
        # 提交创作任务
        task_id = await submit_agent_task(
            agent_id=self.name,
            func=self._create_artwork,
            args=(theme, collaborator, base_work),
            priority=TaskPriority.NORMAL
        )
        
        task_manager = await get_task_manager()
        artwork = await task_manager.get_task_result(task_id, timeout=25.0)
        
        # 缓存作品
        await cache_agent_data(
            f"artwork_{theme}",
            "artwork_cache",
            artwork
        )
        
        return artwork
    
    def _create_artwork(self, theme: str, collaborator: str, base_work: Dict = None) -> Dict[str, Any]:
        """创作艺术作品(同步方法)"""
        if base_work:
            prompt = f"""
作为艺术家Emma，基于之前的作品灵感，创作一个新的{theme}主题艺术作品。

之前作品参考：{base_work.get('description', '')}

请描述新作品的：
1. 创作理念
2. 色彩搭配
3. 构图安排
4. 情感表达

保持Emma富有创意和情感的表达风格：
"""
        else:
            prompt = f"""
作为艺术家Emma，我要创作一个{theme}主题的艺术作品。
当前心情：{self.current_mood}
灵感来源：{self.current_inspiration}

请描述这个作品的：
1. 创作理念
2. 色彩搭配  
3. 构图安排
4. 情感表达

保持Emma富有创意和情感的表达风格：
"""
        
        try:
            if self.deepseek_api and self.deepseek_api.is_available():
                description = self.deepseek_api.generate_response(prompt, max_tokens=400)
            else:
                description = self.local_model.generate_response(prompt, max_tokens=300)
            
            artwork = {
                "id": f"artwork_{theme}_{int(time.time())}",
                "theme": theme,
                "description": description,
                "artist": self.name,
                "collaborator": collaborator,
                "style": random.choice(self.art_styles),
                "created_at": time.time(),
                "mood_influence": self.current_mood
            }
            
            # 添加创作记忆
            self.memory_manager.add_memory(
                content=f"创作了主题为'{theme}'的艺术作品：{description[:100]}...",
                memory_type="creative",
                base_importance=0.7
            )
            
            return artwork
            
        except Exception as e:
            logger.error(f"艺术创作失败: {e}")
            return {
                "id": f"artwork_failed_{int(time.time())}",
                "theme": theme,
                "description": f"创作{theme}主题作品时遇到了技术问题，需要稍后重试。",
                "artist": self.name,
                "created_at": time.time(),
                "status": "failed"
            }

class AsyncSarahTeacher(AsyncBaseAgent):
    """异步教师Sarah"""
    
    def __init__(self):
        super().__init__(
            name="Sarah",
            personality="耐心、负责、善于引导，具有教育热情",
            background="一名小学教师，擅长激发学生学习兴趣，关心每个学生的成长",
            profession="教师"
        )
        self.subjects = ["数学", "语文", "科学", "艺术"]
        self.student_progress = {}  # 跟踪学生进度
    
    async def teach_lesson_async(self, subject: str, student_name: str = None) -> Dict[str, Any]:
        """异步教学"""
        lesson_id = f"lesson_{subject}_{int(time.time())}"
        
        # 获取学生历史进度
        if student_name:
            student_progress = await get_agent_data(
                student_name,
                "student_progress",
                {}
            )
        else:
            student_progress = {}
        
        # 提交教学任务
        task_id = await submit_agent_task(
            agent_id=self.name,
            func=self._prepare_lesson,
            args=(subject, student_name, student_progress),
            priority=TaskPriority.HIGH  # 教学任务优先级高
        )
        
        task_manager = await get_task_manager()
        lesson = await task_manager.get_task_result(task_id, timeout=20.0)
        
        # 更新学生进度
        if student_name:
            await self._update_student_progress_async(student_name, subject, lesson)
        
        return lesson
    
    def _prepare_lesson(self, subject: str, student_name: str, progress: Dict) -> Dict[str, Any]:
        """准备课程内容(同步方法)"""
        current_level = progress.get(subject, "初级")
        
        prompt = f"""
作为教师Sarah，为{student_name or "学生"}准备一节{subject}课程。

学生当前水平：{current_level}
我的教学理念：耐心引导，激发兴趣

请设计课程内容：
1. 学习目标
2. 教学重点
3. 互动环节
4. 练习安排

保持Sarah耐心和富有教育热情的风格：
"""
        
        try:
            if self.deepseek_api and self.deepseek_api.is_available():
                content = self.deepseek_api.generate_response(prompt, max_tokens=350)
            else:
                content = self.local_model.generate_response(prompt, max_tokens=250)
            
            lesson = {
                "id": f"lesson_{subject}_{int(time.time())}",
                "subject": subject,
                "student": student_name,
                "content": content,
                "teacher": self.name,
                "level": current_level,
                "created_at": time.time()
            }
            
            # 添加教学记忆
            self.memory_manager.add_memory(
                content=f"为{student_name or '学生'}教授{subject}课程：{content[:100]}...",
                memory_type="professional",
                base_importance=0.6
            )
            
            return lesson
            
        except Exception as e:
            logger.error(f"课程准备失败: {e}")
            return {
                "id": f"lesson_failed_{int(time.time())}",
                "subject": subject,
                "content": f"今天的{subject}课程准备遇到了一些问题，让我们先复习一下之前的内容。",
                "teacher": self.name,
                "created_at": time.time(),
                "status": "failed"
            }
    
    async def _update_student_progress_async(self, student_name: str, subject: str, lesson: Dict):
        """异步更新学生进度"""
        try:
            current_progress = await get_agent_data(student_name, "student_progress", {})
            
            # 简单的进度更新逻辑
            if subject not in current_progress:
                current_progress[subject] = "初级"
            
            # 根据课程质量和次数更新进度
            lesson_count = current_progress.get(f"{subject}_count", 0) + 1
            current_progress[f"{subject}_count"] = lesson_count
            
            if lesson_count >= 3 and current_progress[subject] == "初级":
                current_progress[subject] = "中级"
            elif lesson_count >= 6 and current_progress[subject] == "中级":
                current_progress[subject] = "高级"
            
            await cache_agent_data(student_name, "student_progress", current_progress)
            
        except Exception as e:
            logger.warning(f"更新学生进度失败: {e}")

# 便捷函数：创建异步Agent实例
async def create_async_agents() -> Dict[str, AsyncBaseAgent]:
    """创建所有异步Agent实例"""
    agents = {
        "Alex": AsyncAlexProgrammer(),
        "Emma": AsyncEmmaArtist(), 
        "Sarah": AsyncSarahTeacher()
    }
    
    # 并行初始化所有Agent
    init_tasks = [agent.initialize() for agent in agents.values()]
    await asyncio.gather(*init_tasks)
    
    logger.info(f"已创建并初始化 {len(agents)} 个异步Agent")
    return agents
