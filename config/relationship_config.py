"""
关系系统配置文件
定义Agent之间关系的详细规则和阈值
"""

# 关系等级配置
RELATIONSHIP_LEVELS = {
    "敌对": {"min": -20, "max": -1, "emoji": "😠", "description": "关系很差，经常冲突"},
    "陌生": {"min": 0, "max": 20, "emoji": "�", "description": "不熟悉，初次见面"},
    "认识": {"min": 21, "max": 40, "emoji": "🙂", "description": "有过几次交流，算是认识"},
    "熟人": {"min": 41, "max": 60, "emoji": "😊", "description": "比较熟悉，偶尔聊天"},
    "好朋友": {"min": 61, "max": 80, "emoji": "😄", "description": "关系很好，经常交流"},
    "亲密朋友": {"min": 81, "max": 100, "emoji": "🥰", "description": "非常亲密，无话不谈"}
}

# 互动类型和对应的关系变化值
INTERACTION_EFFECTS = {
    "friendly_chat": {
        "change": 3,  # 友好聊天基础分数
        "description": "友好聊天",
        "conditions": {
            "同地点": +2,  # 在同一地点聊天额外加分
            "相同职业": +2,  # 相同职业有共同话题
            "首次交流": +5,  # 首次交流加分，从陌生到认识
        }
    },
    "disagreement": {
        "change": -6,  # 轻度不同意见
        "description": "意见不合",
        "conditions": {
            "不同观点": -3,  # 观点不同
            "价值观差异": -2,  # 价值观差异
            "态度强硬": -2,   # 态度比较强硬
        }
    },
    "argument": {
        "change": -12,  # 从-8增加到-12，确保争吵扣分明显
        "description": "发生争吵",
        "conditions": {
            "价值观冲突": -6,  # 从-4增加到-6
            "工作压力": -5,   # 从-3增加到-5
            "公共场所": -5,   # 从-3增加到-5，公开争吵更伤感情
        }
    },
    "misunderstanding": {
        "change": -10,  # 从-6增加到-10，确保误解扣分明显
        "description": "产生误解",
        "conditions": {
            "沟通不良": -5,  # 从-3增加到-5
            "第一印象差": -6,  # 从-4增加到-6
        }
    },
    "conflict": {
        "change": -10,  # 从-8增加到-10，确保冲突扣分明显
        "description": "严重冲突",
        "conditions": {
            "原则分歧": -5,  # 从-4增加到-5
            "公开对立": -4,  # 从-3增加到-4
        }
    },
    "disappointment": {
        "change": -8,  # 从-5增加到-8，确保失望扣分明显
        "description": "感到失望",
        "conditions": {
            "期望落空": -5,  # 从-3增加到-5
            "被忽视": -5,    # 从-3增加到-5
        }
    },
    "deep_conversation": {
        "change": 3,  # 从5降低到3，减少正面加分
        "description": "深度交流",
        "conditions": {
            "高关系基础": +1,  # 从+2降低到+1
            "私密场所": +1,  # 在家或安静地方
        }
    },
    "collaboration": {
        "change": 4,  # 从6降低到4，减少正面加分
        "description": "合作共事",
        "conditions": {
            "成功合作": +2,  # 从+3降低到+2
            "相同专业": +1,  # 从+2降低到+1
        }
    },
    "help_assistance": {
        "change": 3,  # 从4降低到3，减少正面加分
        "description": "帮助协助",
        "conditions": {
            "紧急帮助": +2,  # 从+3降低到+2
            "专业帮助": +1,  # 从+2降低到+1
        }
    },
    "reconciliation": {
        "change": 2,  # 从4降低到2，进一步减弱和解效果
        "description": "和解",
        "conditions": {
            "主动道歉": +1,  # 从+2降低到+1
            "第三方调解": +1,  # 保持+1
        }
    },
    "casual_meeting": {
        "change": 1,
        "description": "偶然相遇",
        "conditions": {
            "意外惊喜": +1,
        }
    },
    "group_activity": {
        "change": 1,  # 从2降低到1，减少正面加分
        "description": "群体活动",
        "conditions": {
            "活动领导": +1,  # 保持+1
            "积极参与": +0,  # 从+1降低到+0
        }
    },
    "ignore": {
        "change": -3,  # 从-2增加到-3，确保忽视扣分明显
        "description": "忽视冷淡",
        "conditions": {
            "长期忽视": -4,  # 从-3增加到-4
            "故意冷落": -3,  # 从-2增加到-3
        }
    },
    "public_humiliation": {  # 新增：公开羞辱
        "change": -12,  # 从-10增加到-12，确保羞辱扣分明显
        "description": "公开羞辱",
        "conditions": {
            "恶意中伤": -6,  # 从-5增加到-6
            "众人围观": -4,  # 从-3增加到-4
        }
    },
    "betrayal": {  # 新增：背叛
        "change": -15,  # 从-12增加到-15，确保背叛扣分明显
        "description": "背叛信任",
        "conditions": {
            "破坏承诺": -5,  # 从-4增加到-5
            "出卖秘密": -8,  # 从-6增加到-8
        }
    }
}

# 关系衰减配置
RELATIONSHIP_DECAY = {
    "enabled": True,
    "daily_decay": 0.5,  # 每天自然衰减
    "min_threshold": 20,  # 最低不会衰减到20以下
    "max_level": 100,  # 最高关系值
    "decay_intervals": {
        "陌生": 0.1,      # 陌生关系衰减很慢
        "认识": 0.3,
        "熟人": 0.5,
        "好朋友": 0.7,    # 好朋友不联系会衰减较快
        "亲密朋友": 0.4,  # 亲密朋友有一定抗衰减性
    }
}

# 特殊关系修正
PERSONALITY_MODIFIERS = {
    "外向": {"social_bonus": 1.2, "first_meeting": 1.5},
    "内向": {"social_bonus": 0.8, "deep_talk": 1.3},
    "友善": {"positive_interactions": 1.3, "conflict_resistance": 1.2},
    "严肃": {"professional_bonus": 1.4, "casual_penalty": 0.8},
    "幽默": {"group_activity": 1.3, "tension_relief": 1.5},
    "谨慎": {"trust_building": 0.7, "long_term": 1.2},
}

# 职业相性配置
PROFESSION_COMPATIBILITY = {
    "程序员": {
        "程序员": 1.3,     # 同行相性好
        "艺术家": 0.9,     # 理性vs感性稍有差异
        "老师": 1.1,       # 都需要逻辑思维
        "医生": 1.0,
        "学生": 1.2,       # 喜欢教学生
        "商人": 0.8,       # 价值观可能不同
        "厨师": 1.0,
        "机械师": 1.2,     # 都是技术工作
        "退休人员": 0.9,
    },
    "艺术家": {
        "程序员": 0.9,
        "艺术家": 1.4,     # 同行惺惺相惜
        "老师": 1.2,       # 都关注表达和创造
        "医生": 1.0,
        "学生": 1.3,       # 启发创造力
        "商人": 0.7,       # 商业化vs艺术理想
        "厨师": 1.3,       # 都是创造美的工作
        "机械师": 0.8,
        "退休人员": 1.1,
    },
    # ... 其他职业组合
    
}

# 地点对关系的影响
LOCATION_EFFECTS = {
    "咖啡厅": {"casual_boost": 1.2, "atmosphere": "轻松"},
    "图书馆": {"deep_talk": 1.3, "atmosphere": "安静"},
    "公园": {"relax_boost": 1.1, "atmosphere": "自然"},
    "办公室": {"professional": 1.2, "atmosphere": "正式"},
    "家": {"intimate": 1.4, "atmosphere": "私密"},
    "医院": {"serious": 1.0, "atmosphere": "严肃"},
    "餐厅": {"social": 1.2, "atmosphere": "社交"},
    "修理店": {"practical": 1.1, "atmosphere": "实用"},
}

# 时间对关系的影响
TIME_EFFECTS = {
    "晨间": {"energy": 1.1, "mood": "清新"},
    "午间": {"social": 1.2, "mood": "活跃"},
    "傍晚": {"relaxed": 1.2, "mood": "放松"},
    "夜间": {"intimate": 1.3, "mood": "私密"},
}

# 关系阈值变化提醒
RELATIONSHIP_CHANGE_MESSAGES = {
    "升级": {
        "陌生→认识": "从陌生人变成了认识的朋友",
        "认识→熟人": "关系更进一步，成为了熟人",
        "熟人→好朋友": "友谊加深，成为了好朋友",
        "好朋友→亲密朋友": "成为了无话不谈的亲密朋友",
    },
    "降级": {
        "亲密朋友→好朋友": "关系有所疏远，但仍是好朋友",
        "好朋友→熟人": "友谊淡化，回到熟人关系",
        "熟人→认识": "关系变淡，只是一般认识",
        "认识→陌生": "关系疏远，变得陌生",
    }
}

def get_relationship_level(strength: int) -> str:
    """根据关系强度获取关系等级"""
    # 确保strength在合理范围内
    strength = max(-20, min(100, strength))
    
    for level, config in RELATIONSHIP_LEVELS.items():
        if config["min"] <= strength <= config["max"]:
            return level
    
    # 如果没有匹配到，根据数值返回合适等级
    if strength < 0:
        return "敌对"
    elif strength <= 20:
        return "冷淡"
    else:
        return "认识"

def get_level_info(level: str) -> dict:
    """获取关系等级详细信息"""
    return RELATIONSHIP_LEVELS.get(level, {})

def calculate_interaction_effect(
    interaction_type: str, 
    conditions: dict = None
) -> tuple:
    """
    计算互动效果
    返回 (变化值, 详细说明)
    """
    if interaction_type not in INTERACTION_EFFECTS:
        return 1, f"未知互动类型: {interaction_type}"
    
    base_effect = INTERACTION_EFFECTS[interaction_type]
    base_change = base_effect["change"]
    description = base_effect["description"]
    
    total_change = base_change
    details = [f"基础{description}: {base_change:+d}"]
    
    # 应用条件修正
    if conditions:
        for condition, active in conditions.items():
            if active and condition in base_effect["conditions"]:
                modifier = base_effect["conditions"][condition]
                total_change += modifier
                details.append(f"{condition}: {modifier:+d}")
    
    return total_change, " | ".join(details)
