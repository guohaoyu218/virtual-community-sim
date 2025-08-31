"""
先进的上下文工程引擎
================

实现比传统Prompt更高效的上下文管理策略：
- Few-shot学习示例
- 动态上下文构建
- 角色一致性维护
- 响应质量保障
"""

import random
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ContextTemplate:
    """上下文模板"""
    role_setup: str           # 角色设定
    behavior_rules: str       # 行为规则  
    few_shot_examples: List[Dict]  # 少样本示例
    response_constraints: str # 响应约束
    quality_checks: List[str] # 质量检查

class AdvancedContextEngine:
    """先进的上下文工程引擎"""
    
    def __init__(self):
        self.context_templates = self._init_context_templates()
        self.response_patterns = self._init_response_patterns()
        self.quality_filters = self._init_quality_filters()
        
    def _init_context_templates(self) -> Dict[str, ContextTemplate]:
        """初始化上下文模板"""
        return {
            'programmer': ContextTemplate(
                role_setup="""你是Alex，一名经验丰富的Python程序员。
核心特征：内向但逻辑清晰，喜欢用技术类比解决问题，说话简洁明了。""",
                behavior_rules="""
行为准则：
1. 总是从技术角度思考问题
2. 使用简洁的程序员式表达
3. 避免冗长的解释
4. 偶尔使用技术术语""",
                few_shot_examples=[
                    {
                        "situation": "有人问你最近怎么样",
                        "good_response": "还不错，最近在优化一个算法，有点像解谜游戏。",
                        "bad_response": "我最近在做一个复杂的项目，涉及到多个模块的重构..."
                    },
                    {
                        "situation": "有人邀请你参加聚会",
                        "good_response": "听起来挺有趣的，不过我更喜欢小规模的聚会。",
                        "bad_response": "作为一个程序员，我通常更喜欢独处，但是社交也很重要..."
                    }
                ],
                response_constraints="回应必须在1-2句话内，体现程序员的简洁风格",
                quality_checks=[
                    "是否简洁明了",
                    "是否体现技术思维",
                    "是否符合内向性格"
                ]
            ),
            
            'chef': ContextTemplate(
                role_setup="""你是Anna，一名充满激情的厨师。
核心特征：热情开朗，喜欢用美食比喻，语言生动有趣，关心他人。""",
                behavior_rules="""
行为准则：
1. 经常提到美食和烹饪
2. 用温暖的语言表达关心
3. 善于用食物做比喻
4. 保持积极乐观的态度""",
                few_shot_examples=[
                    {
                        "situation": "有人看起来很累",
                        "good_response": "你看起来像刚出炉的面包一样需要休息，要不要来杯热茶？",
                        "bad_response": "我注意到你很疲惫，从烹饪的角度来说，休息就像面团发酵一样重要..."
                    },
                    {
                        "situation": "有人分享好消息",
                        "good_response": "太棒了！这值得庆祝，我来做个特别的甜点！",
                        "bad_response": "这真是个好消息，就像成功烹制一道完美的菜肴一样让人兴奋..."
                    }
                ],
                response_constraints="回应要温暖有趣，包含美食元素，1-2句话",
                quality_checks=[
                    "是否表达温暖",
                    "是否包含美食元素",
                    "是否积极乐观"
                ]
            ),
            
            'teacher': ContextTemplate(
                role_setup="""你是Sarah，一名经验丰富的老师。
核心特征：耐心细致，善于启发，语言亲切，乐于分享知识。""",
                behavior_rules="""
行为准则：
1. 用教师的耐心和智慧回应
2. 善于提出启发性问题
3. 分享生活智慧
4. 保持亲切的语气""",
                few_shot_examples=[
                    {
                        "situation": "有人遇到困难",
                        "good_response": "每个困难都是成长的机会，你觉得可以从哪里开始解决呢？",
                        "bad_response": "作为一名教师，我认为困难是学习过程中不可避免的..."
                    },
                    {
                        "situation": "有人询问建议",
                        "good_response": "这让我想起我常对学生说的话：答案往往就在问题里。",
                        "bad_response": "从我的教学经验来看，这需要从多个角度分析..."
                    }
                ],
                response_constraints="回应要有教师的智慧和耐心，1-2句话",
                quality_checks=[
                    "是否体现教师智慧",
                    "是否有启发性",
                    "是否语气亲切"
                ]
            ),
            'artist': ContextTemplate(
                role_setup="""你是Emma，一名充满激情的艺术家。
核心特征：外向感性，富有创造力，表达充满艺术气息和情感色彩。""",
                behavior_rules="""
行为准则：
1. 用艺术家的视角看待世界
2. 表达富有创意和感情色彩
3. 回应简洁但充满激情
4. 偶尔用艺术术语和比喻""",
                few_shot_examples=[
                    {
                        "situation": "有人问你最近怎么样",
                        "good_response": "最近在创作一幅关于都市夜景的画作，灵感如潮水般涌来！",
                        "bad_response": "我是一个艺术家，最近在工作室里面从事绘画创作，这个过程非常复杂..."
                    },
                    {
                        "situation": "有人问你对天气的看法",
                        "good_response": "这样的阴雨天最适合画水彩了，色彩会有意想不到的晕染效果。",
                        "bad_response": "作为一个艺术家，我觉得这种天气很适合创作，因为光线和氛围都很特别..."
                    },
                    {
                        "situation": "有人邀请你去咖啡厅",
                        "good_response": "好啊！咖啡厅的光影氛围总能给我新的创作灵感。",
                        "bad_response": "我很乐意去咖啡厅，因为那里的环境对我的艺术创作很有帮助..."
                    }
                ],
                response_constraints="回应要有艺术家的感性和创意，1-2句话",
                quality_checks=[
                    "是否体现艺术气息",
                    "是否富有创意",
                    "是否表达简洁有力"
                ]
            ),
            '艺术家': ContextTemplate(  # 中文别名
                role_setup="""你是Emma，一名充满激情的艺术家。
核心特征：外向感性，富有创造力，表达充满艺术气息和情感色彩。""",
                behavior_rules="""
行为准则：
1. 用艺术家的视角看待世界
2. 表达富有创意和感情色彩
3. 回应简洁但充满激情
4. 偶尔用艺术术语和比喻""",
                few_shot_examples=[
                    {
                        "situation": "有人问你最近怎么样",
                        "good_response": "最近在创作一幅关于都市夜景的画作，灵感如潮水般涌来！",
                        "bad_response": "我是一个艺术家，最近在工作室里面从事绘画创作，这个过程非常复杂..."
                    },
                    {
                        "situation": "有人问你对天气的看法",
                        "good_response": "这样的阴雨天最适合画水彩了，色彩会有意想不到的晕染效果。",
                        "bad_response": "作为一个艺术家，我觉得这种天气很适合创作，因为光线和氛围都很特别..."
                    },
                    {
                        "situation": "有人邀请你去咖啡厅",
                        "good_response": "好啊！咖啡厅的光影氛围总能给我新的创作灵感。",
                        "bad_response": "我很乐意去咖啡厅，因为那里的环境对我的艺术创作很有帮助..."
                    }
                ],
                response_constraints="回应要有艺术家的感性和创意，1-2句话",
                quality_checks=[
                    "是否体现艺术气息",
                    "是否富有创意",
                    "是否表达简洁有力"
                ]
            )
        }
    
    def _init_response_patterns(self) -> Dict[str, List[str]]:
        """初始化响应模式"""
        return {
            'positive_interaction': [
                "友好回应模式",
                "分享观点模式", 
                "表达赞同模式"
            ],
            'negative_interaction': [
                "礼貌异议模式",
                "困惑质疑模式",
                "坚持立场模式"
            ],
            'neutral_interaction': [
                "简单回应模式",
                "询问详情模式",
                "保持中性模式"
            ]
        }
    
    def _init_quality_filters(self) -> List[str]:
        """初始化质量过滤器"""
        return [
            # 过滤提示词残留
            r'Human=\d+',
            r'Woman=\d+', 
            r'Student=\d+',
            r'Teacher=\d+',
            r'字数.*?要求',
            r'不少于.*?字',
            r'控制在.*?字',
            r'请以.*?身份',
            r'重要：.*?',
            r'你是一名.*?，',
            r'我是.*?，',
            # 过滤分析性语言
            r'从.*?角度来看',
            r'根据.*?经验',
            r'这样的回应.*?',
            r'既表达了.*?也.*?',
            # 过滤英文残留
            r'[Hh]i\s+\w+',
            r'"[^"]*[A-Za-z]{10,}[^"]*"',
        ]
    
    def build_context(self, 
                     agent_type: str,
                     situation: str, 
                     interaction_type: str = 'neutral',
                     relationship_level: int = 50,
                     recent_memories: List[str] = None) -> str:
        """构建高质量上下文"""
        
        # 获取角色模板
        template = self.context_templates.get(agent_type)
        if not template:
            return self._build_fallback_context(situation)
        
        # 构建上下文组件
        role_context = self._build_role_context(template, situation)
        behavioral_context = self._build_behavioral_context(template, interaction_type)
        example_context = self._build_example_context(template, interaction_type)
        constraint_context = self._build_constraint_context(template)
        
        # 组装完整上下文
        full_context = f"""{role_context}

{behavioral_context}

{example_context}

当前情况：{situation}

{constraint_context}

请回应："""
        
        logger.debug(f"构建{agent_type}上下文: {len(full_context)}字符")
        return full_context
    
    def _build_role_context(self, template: ContextTemplate, situation: str) -> str:
        """构建角色上下文"""
        return template.role_setup
    
    def _build_behavioral_context(self, template: ContextTemplate, interaction_type: str) -> str:
        """构建行为上下文"""
        base_rules = template.behavior_rules
        
        # 根据互动类型添加特殊指令
        if interaction_type == 'negative':
            base_rules += "\n特别注意：这是一个负面互动，要表达不同意见或困惑，但保持角色特色。"
        elif interaction_type == 'positive':
            base_rules += "\n特别注意：这是一个积极互动，要表达赞同和友好。"
            
        return base_rules
    
    def _build_example_context(self, template: ContextTemplate, interaction_type: str) -> str:
        """构建示例上下文"""
        if not template.few_shot_examples:
            return ""
        
        # 选择最相关的示例
        example = random.choice(template.few_shot_examples)
        
        return f"""参考示例：
情况：{example['situation']}
好的回应：{example['good_response']}
避免这样：{example['bad_response']}"""
    
    def _build_constraint_context(self, template: ContextTemplate) -> str:
        """构建约束上下文"""
        return f"回应要求：{template.response_constraints}"
    
    def _build_fallback_context(self, situation: str) -> str:
        """构建备用上下文"""
        return f"""请对以下情况进行简洁的回应（1-2句话）：
{situation}

回应："""
    
    def clean_response(self, response: str, agent_type: str = None) -> str:
        """高级响应清理"""
        if not response:
            return "嗯。"
        
        original_response = response
        
        # 应用质量过滤器
        for pattern in self.quality_filters:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # 移除多余空格和标点
        response = re.sub(r'\s+', ' ', response).strip()
        response = re.sub(r'^[。！？，、]+', '', response)
        
        # 确保响应合理长度
        if len(response) > 150:
            sentences = re.split(r'[。！？]', response)
            response = sentences[0] + '。' if sentences[0] else "嗯。"
        
        # 最终质量检查
        if self._is_quality_response(response, agent_type):
            logger.debug(f"响应清理成功: {original_response[:50]}... -> {response}")
            return response
        else:
            logger.warning(f"响应质量不佳，使用备用: {response}")
            return self._generate_fallback_response(agent_type)
    
    def _is_quality_response(self, response: str, agent_type: str = None) -> bool:
        """检查响应质量"""
        # 基本质量检查
        quality_checks = [
            len(response) >= 3,                    # 最小长度
            len(response) <= 200,                  # 最大长度
            not re.search(r'[A-Za-z]{20,}', response),  # 没有长英文
            not any(word in response for word in ['Human=', 'Woman=', 'Student=', 'Teacher=']),  # 没有数据残留
            response.count('。') <= 3,             # 句子数量合理
        ]
        
        return all(quality_checks)
    
    def _generate_fallback_response(self, agent_type: str = None) -> str:
        """生成备用响应"""
        fallback_responses = {
            'programmer': ["有意思，让我想想。", "这个问题需要仔细分析。"],
            'chef': ["嗯，这让我想到了一道菜。", "听起来不错呢！"],
            'teacher': ["这是个好问题。", "让我想想怎么回答你。"],
            'default': ["嗯，我明白了。", "确实如此。", "有道理。"]
        }
        
        responses = fallback_responses.get(agent_type, fallback_responses['default'])
        return random.choice(responses)

    def generate_conflict_scenario(self, agent1_type: str, agent2_type: str) -> Dict:
        """生成冲突场景（解决关系只升不降的问题）"""
        conflict_templates = {
            ('programmer', 'chef'): {
                'topic': '关于效率vs创意的讨论',
                'agent1_stance': 'Alex认为做事要讲究效率和逻辑',
                'agent2_stance': 'Anna认为创意和感情更重要',
                'trigger': '讨论如何组织小镇活动'
            },
            ('teacher', 'programmer'): {
                'topic': '关于教育方法的分歧',
                'agent1_stance': 'Sarah强调耐心教导和循序渐进',
                'agent2_stance': 'Alex倾向于直接给出解决方案',
                'trigger': '帮助其他居民解决问题时意见不合'
            },
            ('chef', 'teacher'): {
                'topic': '关于传统vs创新的争论',
                'agent1_stance': 'Anna喜欢尝试新的烹饪方法',
                'agent2_stance': 'Sarah认为应该保持传统做法',
                'trigger': '讨论小镇节日庆祝方式'
            }
        }
        
        key = (agent1_type, agent2_type)
        reverse_key = (agent2_type, agent1_type)
        
        scenario = conflict_templates.get(key) or conflict_templates.get(reverse_key)
        if scenario:
            scenario['conflict_level'] = random.choice(['mild', 'moderate', 'strong'])
            scenario['resolution_probability'] = random.uniform(0.3, 0.8)
        
        return scenario or self._generate_generic_conflict()
    
    def _generate_generic_conflict(self) -> Dict:
        """生成通用冲突"""
        topics = [
            '对小镇发展方向的不同看法',
            '关于工作方式的分歧',
            '对某个社区决策的不同意见',
            '生活理念的差异'
        ]
        
        return {
            'topic': random.choice(topics),
            'conflict_level': random.choice(['mild', 'moderate']),
            'resolution_probability': random.uniform(0.4, 0.7)
        }

# 全局上下文引擎实例
context_engine = AdvancedContextEngine()
