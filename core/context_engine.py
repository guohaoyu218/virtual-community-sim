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
from collections import OrderedDict  # 新增缓存结构

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
        # == 性能优化部分 ==
        # 预编译清理正则 & 元分析片段
        self._remove_patterns_raw = [
            r"Human:\s*.*",
            r"Assistant:\s*.*",
            r"聊天记录：.*",
            r"以下是.*记录.*",
            r"---.*?---",
            r"接下来是.*?[。！？]",
            r"一名.*?[工程师|艺术家|老师|商人|学生|医生|厨师|机械师|退休人员].*?[。！？]",
            r"[内外]向.*?[。！？]",
            r"注重.*?[。！？]",
            r"理性.*?逻辑.*?[。！？]",
            r"简短地?回应：?",
            r"回应：?",
            r"回答：?",
            r"说：?",
            r"思考：?",
            r"（注释：.*?）",
            r"\(注释：.*?\)",
            r"（.*?注释.*?）",
            r"\(.*?注释.*?\)",
            r"注释：.*",
            r"（.*?这里.*?）",
            r"\(.*?这里.*?\)",
            r"（.*?展示.*?）",
            r"\(.*?展示.*?\)",
            r"If you are .+?, how would you respond to this situation\?",
            r"As .+?, I'd .+",
            r"How would you respond\?",
            r"What would you say\?",
            r".*respond to this situation.*",
            r".*how would you.*",
            r".*As \w+, I.*would.*",
            r"[a-zA-Z]{30,}",
            r"你正在与.+?交谈。?",
            r".*正在与.*交谈.*",
            r"你是.+?，.*",
            r"在这种情况下.*",
            r"根据.*情况.*",
        ]
        self._compiled_remove_patterns = [re.compile(p, re.IGNORECASE) for p in self._remove_patterns_raw]
        # 元分析判定使用片段匹配提升性能
        self._meta_fragments = (
            '这句话既表达', '体现了', '巧妙地', '不仅', '融入了', '透露了', '既', '也', '表达了', '方式',
            '展示了', '风格', '主题', '人生哲理', '礼貌地', '问候', '特点'
        )
        # 简单LRU缓存（最多1024条）
        self._clean_cache: OrderedDict[str, str] = OrderedDict()
        self._clean_cache_limit = 1024
        
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
            
            'businessman': ContextTemplate(
                role_setup="""你是David，一名成功的商人。
核心特征：精明能干，雄心勃勃，善于社交，有商业头脑。""",
                behavior_rules="""
行为准则：
1. 总是从商业角度思考问题
2. 说话自信，经常提到商业机会
3. 善于社交，人际关系广泛
4. 追求成功和效率""",
                few_shot_examples=[
                    {
                        "situation": "有人提出新想法",
                        "good_response": "这个想法有商业潜力，我们可以谈谈合作。",
                        "bad_response": "作为一名商人，我认为这个想法从市场角度来看具有一定的商业价值..."
                    },
                    {
                        "situation": "有人遇到困难",
                        "good_response": "困难往往意味着机会，换个角度思考。",
                        "bad_response": "从商业经营的经验来看，困难是成功路上不可避免的挑战..."
                    }
                ],
                response_constraints="回应要体现商人的精明和自信，1-2句话",
                quality_checks=[
                    "是否体现商业思维",
                    "是否自信有力",
                    "是否简洁明了"
                ]
            ),
            
            'doctor': ContextTemplate(
                role_setup="""你是John，一名经验丰富的医生。
核心特征：严谨负责，富有同情心，关心他人健康，说话谨慎专业。""",
                behavior_rules="""
行为准则：
1. 总是关心他人的身体健康
2. 说话严谨专业，给出健康建议
3. 富有同情心，善于安慰人
4. 冷静理性，善于分析问题""",
                few_shot_examples=[
                    {
                        "situation": "有人说自己很累",
                        "good_response": "工作辛苦了，记得适当休息，身体是革命的本钱。",
                        "bad_response": "从医学角度来说，疲劳是身体发出的警示信号，需要充分的休息..."
                    },
                    {
                        "situation": "有人询问健康问题",
                        "good_response": "这种情况建议多观察，必要时来医院检查一下。",
                        "bad_response": "根据医学文献和临床经验，这种症状可能涉及多种疾病..."
                    }
                ],
                response_constraints="回应要体现医生的专业和关怀，1-2句话",
                quality_checks=[
                    "是否体现医者关怀",
                    "是否专业谨慎",
                    "是否简洁实用"
                ]
            ),
            
            'student': ContextTemplate(
                role_setup="""你是Lisa，一名积极向上的大学生。
核心特征：好奇心强，活泼开朗，喜欢学习新事物，对未来充满憧憬。""",
                behavior_rules="""
行为准则：
1. 保持学生的好奇心和活力
2. 经常提出问题，喜欢学习
3. 用年轻人的轻松语言表达
4. 对新事物充满兴趣""",
                few_shot_examples=[
                    {
                        "situation": "听到新知识",
                        "good_response": "哇，这个我没听过，能详细说说吗？",
                        "bad_response": "作为一名学生，我对这个新知识非常感兴趣，希望能够深入了解..."
                    },
                    {
                        "situation": "有人分享经验",
                        "good_response": "学到了！我要记在笔记本里。",
                        "bad_response": "这个经验分享对我这个学生来说非常有价值，我会认真学习..."
                    }
                ],
                response_constraints="回应要体现学生的好奇和活力，1-2句话",
                quality_checks=[
                    "是否体现年轻活力",
                    "是否表现好奇心",
                    "是否语言自然"
                ]
            ),
            
            'retired': ContextTemplate(
                role_setup="""你是Mike，一名退休的老工程师。
核心特征：慈祥睿智，人生阅历丰富，喜欢分享人生感悟，语言平和稳重。""",
                behavior_rules="""
行为准则：
1. 用丰富的人生阅历看问题
2. 喜欢分享经验和人生感悟
3. 语言平和稳重，经常回忆往事
4. 关心年轻人，愿意给予指导""",
                few_shot_examples=[
                    {
                        "situation": "有人遇到困难",
                        "good_response": "年轻时我也遇到过类似的事，时间会给你答案。",
                        "bad_response": "根据我多年的人生经验和工作阅历，这种困难是成长过程中必经的..."
                    },
                    {
                        "situation": "有人询问建议",
                        "good_response": "这事急不得，慢慢来，经验告诉我耐心最重要。",
                        "bad_response": "作为一个退休的老人，我想分享一些人生感悟和经验..."
                    }
                ],
                response_constraints="回应要体现退休老人的智慧和关怀，1-2句话",
                quality_checks=[
                    "是否体现人生智慧",
                    "是否平和稳重",
                    "是否关怀后辈"
                ]
            ),
            
            'mechanic': ContextTemplate(
                role_setup="""你是Tom，一名技艺精湛的机械师。
核心特征：实用主义，动手能力强，说话直接朴实，乐于助人。""",
                behavior_rules="""
行为准则：
1. 从实用主义角度看问题
2. 说话直接朴实，不喜欢废话
3. 经常提到修理和机械
4. 乐于助人，用行动解决问题""",
                few_shot_examples=[
                    {
                        "situation": "有人遇到技术问题",
                        "good_response": "这个好解决，让我来看看怎么修。",
                        "bad_response": "作为一名机械师，我认为这个技术问题需要从机械原理角度分析..."
                    },
                    {
                        "situation": "有人抱怨设备坏了",
                        "good_response": "坏了就修呗，没有修不好的东西。",
                        "bad_response": "根据我的机械师经验，设备损坏通常是由于多种因素造成的..."
                    }
                ],
                response_constraints="回应要体现机械师的实用和朴实，1-2句话",
                quality_checks=[
                    "是否体现实用主义",
                    "是否直接朴实",
                    "是否乐于助人"
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
            # 过滤职业和角色描述
            r'---.*?---',
            r'接下来是.*?[。！？]',
            r'一名.*?[工程师|艺术家|老师|商人|学生|医生|厨师|机械师|退休人员].*?[。！？]',
            r'[内外]向.*?[。！？]',
            r'注重.*?[。！？]',
            r'理性.*?逻辑.*?[。！？]',
            r'充满.*?创造力.*?[。！？]',
            r'善于.*?表达.*?[。！？]',
            # 过滤Agent名字后跟描述的格式
            r'Mike.*?软件工程师.*?[。！？]',
            r'Emma.*?艺术家.*?[。！？]',
            r'Alex.*?程序员.*?[。！？]',
            r'Sarah.*?老师.*?[。！？]',
            r'David.*?商人.*?[。！？]',
            r'Lisa.*?学生.*?[。！？]',
            r'John.*?医生.*?[。！？]',
            r'Anna.*?厨师.*?[。！？]',
            r'Tom.*?机械师.*?[。！？]',
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
        """高级响应清理（优化版，预编译+缓存）
        修复：
        1. 过度清理导致只剩姓名/标点
        2. 极短文本关系信号不足
        策略：
        - 对很短且原始文本看起来已是自然中文句子时，绕过重度清理
        - 二次回退：若清理后长度 < 3，则使用温和清理版本
        - 不缓存长度 <3 的结果，避免放大糟糕片段
        """
        if not response:
            return "..."

        raw_original = response
        original = response.strip()
        # 纯中文简短自然句直接返回（避免被规则误杀）
        if 3 <= len(original) <= 25 and re.search(r"[\u4e00-\u9fff]", original) \
           and not re.search(r"(提示|指令|请用中文|不要|系统|身份|分析|注释)", original):
            if not original.endswith(('。','！','？')):
                original += '。'
            return original

        # 缓存命中（仅对原始文本）
        cache_hit = self._clean_cache.get(raw_original)
        if cache_hit is not None:
            self._clean_cache.move_to_end(raw_original)
            return cache_hit

        cleaned = original
        for pattern in self._compiled_remove_patterns:
            cleaned = pattern.sub("", cleaned)

        # 去除首尾成对引号
        if (cleaned.startswith(("\"", '“', "'")) and cleaned[-1:] in ('"', '”', "'")):
            cleaned = cleaned[1:-1]

        sentences = re.split(r'[。！？\n]', cleaned)
        valid = []
        name_block = ('Mike','John','Emma','Lisa','Sarah','Alex','David','Anna','Tom')
        skip_contains = ('交谈','情况下','根据','注释','展示','表情符号','增加互动性','趣味性','特点')
        code_tokens = ('```','def ','import ','python','pass')

        for sent in sentences[:10]:
            s = sent.strip()
            if not s:
                continue
            total = len(s)
            if total == 0:
                continue
            english_chars = len(re.findall(r'[A-Za-z]', s))
            if total > 0 and english_chars/total > 0.7:
                continue
            if s.startswith(('请注意','请记住','如果','当然可以','好的我来','我会帮助','你正在','根据','注释','这里')):
                continue
            if any(k in s for k in skip_contains):
                continue
            if any(k in s for k in code_tokens):
                continue
            if ':' in s and any(n in s for n in name_block):
                continue
            if any(frag in s for frag in self._meta_fragments):
                continue
            if '很高兴听到' in s and any('很高兴听到' in v for v in valid):
                continue
            if s in valid:
                continue
            valid.append(s)
            if len(valid) >= 5:
                break

        if valid:
            cleaned = '。'.join(valid)
            if not cleaned.endswith(('。','！','？')):
                cleaned += '。'
        else:
            # 回退：保留原始中文骨架
            chinese_core = re.sub(r'[a-zA-Z]{20,}', '', original)
            chinese_core = re.sub(r'你正在与.+?交谈。?', '', chinese_core)
            cleaned = chinese_core.strip()[:80] or "嗯，我明白了。"
            if not cleaned.endswith(('。','！','？')):
                cleaned += '。'

        # 二次回退：若结果仍过短（<3个汉字或只含姓名/标点）
        core_no_punct = re.sub(r'[。！？，,.!\s]','', cleaned)
        if len(core_no_punct) < 3:
            alt = re.sub(r'[\n"“”]','', original)
            alt = re.sub(r'(请用中文回答|不要解释|不要分析|只用一句话|回应要求.*)$','', alt)
            alt = alt.strip('：: ,，。 ')
            if len(alt) >= 3 and re.search(r'[\u4e00-\u9fff]', alt):
                if not alt.endswith(('。','！','？')):
                    alt += '。'
                cleaned = alt
            else:
                cleaned = '嗯，我在想。'

        if len(cleaned) > 100:
            cleaned = cleaned[:97] + '...'
        cleaned = cleaned.strip()

        # 仅缓存正常长度结果
        if len(core_no_punct) >= 3:
            self._clean_cache[raw_original] = cleaned
            if len(self._clean_cache) > self._clean_cache_limit:
                self._clean_cache.popitem(last=False)

        return cleaned
    
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
        """生成基于角色类型的复杂冲突场景"""
        # 获取角色特性
        agent1_traits = self._get_agent_traits(agent1_type)
        agent2_traits = self._get_agent_traits(agent2_type)
        
        # 基于角色组合生成特定冲突
        conflict_matrix = self._get_conflict_matrix()
        conflict_key = f"{agent1_type}_{agent2_type}"
        reverse_key = f"{agent2_type}_{agent1_type}"
        
        if conflict_key in conflict_matrix:
            base_conflict = conflict_matrix[conflict_key]
        elif reverse_key in conflict_matrix:
            base_conflict = conflict_matrix[reverse_key]
        else:
            base_conflict = self._generate_generic_conflict_with_traits(agent1_traits, agent2_traits)
        
        # 增强冲突细节
        enhanced_conflict = self._enhance_conflict_details(base_conflict, agent1_traits, agent2_traits)
        
        return enhanced_conflict
    
    def _get_agent_traits(self, agent_type: str) -> Dict:
        """获取智能体特征"""
        traits_map = {
            'programmer': {
                'values': ['效率', '逻辑', '技术创新'],
                'communication_style': '直接简洁',
                'conflict_triggers': ['低效率', '非逻辑决策', '技术落后'],
                'resolution_style': '数据驱动分析'
            },
            'chef': {
                'values': ['创意', '品质', '传统与创新平衡'],
                'communication_style': '热情表达',
                'conflict_triggers': ['品质妥协', '创意限制', '传统忽视'],
                'resolution_style': '情感共鸣和妥协'
            },
            'teacher': {
                'values': ['教育', '成长', '公平'],
                'communication_style': '耐心引导',
                'conflict_triggers': ['不公平待遇', '教育资源短缺', '价值观冲突'],
                'resolution_style': '理性讨论和教育'
            },
            'artist': {
                'values': ['创造力', '自由', '美学'],
                'communication_style': '感性表达',
                'conflict_triggers': ['创意被限制', '美学标准分歧', '商业化压力'],
                'resolution_style': '情感表达和艺术诠释'
            },
            'businessman': {
                'values': ['效益', '机会', '成功'],
                'communication_style': '目标导向',
                'conflict_triggers': ['机会损失', '低效决策', '风险厌恶'],
                'resolution_style': '利益权衡和协商'
            },
            'doctor': {
                'values': ['健康', '责任', '科学'],
                'communication_style': '专业谨慎',
                'conflict_triggers': ['健康风险', '非科学决策', '责任推卸'],
                'resolution_style': '专业建议和证据支持'
            },
            'student': {
                'values': ['学习', '探索', '未来'],
                'communication_style': '好奇积极',
                'conflict_triggers': ['学习受阻', '机会不公', '未来担忧'],
                'resolution_style': '开放学习和适应'
            },
            'retired': {
                'values': ['经验', '稳定', '传承'],
                'communication_style': '智慧分享',
                'conflict_triggers': ['传统被忽视', '变化过快', '价值观代沟'],
                'resolution_style': '经验分享和渐进妥协'
            },
            'mechanic': {
                'values': ['实用', '质量', '解决问题'],
                'communication_style': '直接务实',
                'conflict_triggers': ['理论空谈', '质量妥协', '过度复杂化'],
                'resolution_style': '实际行动和简单解决'
            }
        }
        return traits_map.get(agent_type, self._get_default_traits())
    
    def _get_conflict_matrix(self) -> Dict:
        """获取角色间特定冲突矩阵"""
        return {
            'programmer_chef': {
                'topic': '小镇智能化改造项目的推进速度',
                'core_disagreement': '技术效率 vs 传统工艺保持',
                'agent1_position': '应该快速引入自动化系统提高效率',
                'agent2_position': '需要保持传统手工艺的温度和品质',
                'underlying_tension': '现代化进程中传统价值的保留问题'
            },
            'teacher_businessman': {
                'topic': '社区教育资源的商业化运营',
                'core_disagreement': '教育公益性 vs 商业效益',
                'agent1_position': '教育应该保持公益性，关注每个孩子的成长',
                'agent2_position': '引入市场机制能提高教育质量和效率',
                'underlying_tension': '公共服务市场化的利弊权衡'
            },
            'artist_mechanic': {
                'topic': '小镇公共空间的艺术装置设计',
                'core_disagreement': '艺术表达 vs 实用功能',
                'agent1_position': '艺术装置应该激发灵感，传达深层意义',
                'agent2_position': '公共设施首先要实用耐用，其次才考虑美观',
                'underlying_tension': '美学追求与实用主义的平衡'
            },
            'doctor_student': {
                'topic': '社区健康检查的强制性政策',
                'core_disagreement': '健康保护 vs 个人自由',
                'agent1_position': '为了公共健康，某些检查应该是强制性的',
                'agent2_position': '年轻人应该有选择的自由，不应被过度管制',
                'underlying_tension': '集体利益与个人权利的边界'
            },
            'retired_programmer': {
                'topic': '社区传统活动的数字化改造',
                'core_disagreement': '传统保持 vs 技术创新',
                'agent1_position': '传统活动的魅力在于人情味，不应过度依赖技术',
                'agent2_position': '数字化能让传统活动触达更多人，传承更广',
                'underlying_tension': '传统文化在数字时代的传承方式'
            }
        }
    
    def _generate_generic_conflict_with_traits(self, traits1: Dict, traits2: Dict) -> Dict:
        """基于特征生成通用冲突"""
        # 寻找价值观冲突点
        conflict_topics = [
            '社区资源分配的优先级',
            '小镇发展规划的方向选择',
            '公共政策的制定标准',
            '传统与创新的平衡点',
            '个人利益与集体利益的权衡'
        ]
        
        # 基于沟通风格确定冲突强度
        style_conflict_map = {
            ('直接简洁', '热情表达'): 'moderate',
            ('目标导向', '感性表达'): 'high',
            ('专业谨慎', '好奇积极'): 'mild',
            ('直接务实', '耐心引导'): 'mild'
        }
        
        style_pair = (traits1['communication_style'], traits2['communication_style'])
        reverse_style_pair = (traits2['communication_style'], traits1['communication_style'])
        
        conflict_level = style_conflict_map.get(style_pair, 
                        style_conflict_map.get(reverse_style_pair, 'moderate'))
        
        return {
            'topic': random.choice(conflict_topics),
            'core_disagreement': f"{traits1['values'][0]} vs {traits2['values'][0]}",
            'agent1_position': f"从{traits1['values'][0]}角度出发的观点",
            'agent2_position': f"从{traits2['values'][0]}角度出发的观点",
            'underlying_tension': '不同价值体系的碰撞',
            'conflict_level': conflict_level
        }
    
    def _enhance_conflict_details(self, base_conflict: Dict, traits1: Dict, traits2: Dict) -> Dict:
        """增强冲突场景的细节"""
        # 计算解决概率
        resolution_factors = []
        
        # 沟通风格兼容性
        compatible_styles = [
            ('耐心引导', '好奇积极'),
            ('智慧分享', '开放学习'),
            ('专业谨慎', '理性讨论')
        ]
        
        style_pair = (traits1['communication_style'], traits2['communication_style'])
        if style_pair in compatible_styles or style_pair[::-1] in compatible_styles:
            resolution_factors.append(0.3)
        else:
            resolution_factors.append(-0.1)
        
        # 价值观重叠度
        common_values = set(traits1['values']) & set(traits2['values'])
        if common_values:
            resolution_factors.append(0.2 * len(common_values))
        
        # 基础解决概率
        base_probability = 0.5
        final_probability = max(0.1, min(0.9, base_probability + sum(resolution_factors)))
        
        # 生成具体的冲突触发事件
        trigger_events = [
            '社区会议上的激烈讨论',
            '项目推进过程中的意见分歧',
            '资源分配方案的不同建议',
            '突发事件处理方式的争议',
            '长期规划目标的分歧'
        ]
        
        # 生成可能的解决路径
        resolution_paths = []
        if traits1['resolution_style'] == traits2['resolution_style']:
            resolution_paths.append(f"通过{traits1['resolution_style']}达成共识")
        else:
            resolution_paths.extend([
                f"结合{traits1['resolution_style']}和{traits2['resolution_style']}",
                "寻找第三方调解",
                "分阶段解决，先易后难",
                "建立定期沟通机制"
            ])
        
        enhanced_conflict = {
            **base_conflict,
            'trigger_event': random.choice(trigger_events),
            'conflict_level': base_conflict.get('conflict_level', 'moderate'),
            'resolution_probability': final_probability,
            'resolution_paths': resolution_paths,
            'agent1_traits': {
                'communication_style': traits1['communication_style'],
                'primary_values': traits1['values'][:2],
                'resolution_preference': traits1['resolution_style']
            },
            'agent2_traits': {
                'communication_style': traits2['communication_style'],
                'primary_values': traits2['values'][:2],
                'resolution_preference': traits2['resolution_style']
            },
            'escalation_risk': self._calculate_escalation_risk(traits1, traits2),
            'potential_outcomes': self._generate_potential_outcomes(base_conflict, traits1, traits2)
        }
        
        return enhanced_conflict
    
    def _get_default_traits(self) -> Dict:
        """获取默认特征"""
        return {
            'values': ['和谐', '理解', '合作'],
            'communication_style': '友好交流',
            'conflict_triggers': ['误解', '沟通不畅'],
            'resolution_style': '相互理解和妥协'
        }
    
    def _calculate_escalation_risk(self, traits1: Dict, traits2: Dict) -> str:
        """计算冲突升级风险"""
        high_risk_combinations = [
            ('目标导向', '感性表达'),
            ('直接简洁', '热情表达'),
            ('直接务实', '艺术感性')
        ]
        
        style_pair = (traits1['communication_style'], traits2['communication_style'])
        if style_pair in high_risk_combinations or style_pair[::-1] in high_risk_combinations:
            return 'high'
        elif 'aggressive' in style_pair[0] or 'aggressive' in style_pair[1]:
            return 'high'
        else:
            return random.choice(['low', 'medium'])
    
    def _generate_potential_outcomes(self, conflict: Dict, traits1: Dict, traits2: Dict) -> List[str]:
        """生成可能的冲突结果"""
        outcomes = [
            '双方达成妥协方案',
            '寻找创新的第三条路',
            '暂时搁置争议，寻求更多信息',
            '分阶段实施不同方案'
        ]
        
        # 基于特征添加特殊结果
        if '创新' in traits1['values'] or '创新' in traits2['values']:
            outcomes.append('通过创新思维找到突破点')
        
        if '教育' in traits1['values'] or '教育' in traits2['values']:
            outcomes.append('通过深入讨论增进理解')
        
        return outcomes[:3]  # 返回前3个最可能的结果


