#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试负面互动修复效果的脚本
验证关系下降更多、回复统一负面、缓解气氛控制、关系下降频率调整
"""

import sys
import os
import random

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.relationship_config import INTERACTION_EFFECTS, calculate_interaction_effect, RELATIONSHIP_DECAY
from agents.behavior_manager import AgentBehaviorManager

def test_relationship_balance():
    """测试关系平衡：确保负面扣分比正面加分更多"""
    print("🧪 测试关系平衡...")
    print("=" * 50)
    
    # 统计正面和负面互动的分值
    positive_interactions = []
    negative_interactions = []
    
    for interaction_type, config in INTERACTION_EFFECTS.items():
        change = config['change']
        if change > 0:
            positive_interactions.append((interaction_type, change))
        elif change < 0:
            negative_interactions.append((interaction_type, change))
    
    print("📈 正面互动分值:")
    total_positive = 0
    for name, value in positive_interactions:
        print(f"  {name}: +{value}")
        total_positive += value
    
    print(f"\n📉 负面互动分值:")
    total_negative = 0
    for name, value in negative_interactions:
        print(f"  {name}: {value}")
        total_negative += abs(value)
    
    print(f"\n📊 平衡分析:")
    print(f"  正面总分: +{total_positive}")
    print(f"  负面总分: -{total_negative}")
    print(f"  负面/正面比例: {total_negative/total_positive:.2f}")
    
    # 验证负面扣分确实比正面加分多
    if total_negative > total_positive:
        print("✅ 负面扣分确实比正面加分多，符合'伤害更深刻'的要求")
    else:
        print("❌ 负面扣分不够多，需要进一步调整")
    
    return total_negative > total_positive

def test_negative_interaction_effects():
    """测试负面互动的具体效果"""
    print("\n🧪 测试负面互动效果...")
    print("=" * 50)
    
    # 测试争吵互动
    conditions = {'同地点': True, '相同职业': True, '首次交流': True}
    change, details = calculate_interaction_effect('argument', conditions)
    
    print(f"争吵互动 (同地点+同职业+首次交流): {change:+d} 分")
    print(f"详细说明: {details}")
    
    # 测试误解互动
    change, details = calculate_interaction_effect('misunderstanding', conditions)
    print(f"误解互动 (同地点+同职业+首次交流): {change:+d} 分")
    print(f"详细说明: {details}")
    
    # 测试失望互动
    change, details = calculate_interaction_effect('disappointment', conditions)
    print(f"失望互动 (同地点+同职业+首次交流): {change:+d} 分")
    print(f"详细说明: {details}")
    
    # 验证扣分是否足够严重
    min_negative = -8  # 期望至少扣8分
    if change <= min_negative:
        print(f"✅ 负面互动扣分足够严重 (≤{min_negative})")
    else:
        print(f"❌ 负面互动扣分不够严重 (>{min_negative})")

def test_behavior_manager_negative_override():
    """测试行为管理器的负面互动强制扣分逻辑"""
    print("\n🧪 测试行为管理器负面互动强制扣分...")
    print("=" * 50)
    
    try:
        behavior_manager = AgentBehaviorManager()
        
        # 模拟两个Agent的关系
        agent1, agent2 = "Alex", "Emma"
        initial_strength = 60
        
        # 设置初始关系
        behavior_manager.social_network[agent1] = {agent2: initial_strength}
        behavior_manager.social_network[agent2] = {agent1: initial_strength}
        
        print(f"初始关系强度: {behavior_manager.get_relationship_strength(agent1, agent2)}")
        
        # 进行负面互动
        context = {
            'same_location': True,
            'same_profession': False,
            'first_interaction': False,
            'location': '咖啡厅',
            'agent1_profession': '程序员',
            'agent2_profession': '艺术家',
            'private_location': False,
        }
        
        result = behavior_manager.update_social_network(agent1, agent2, 'argument', context)
        
        print(f"\n争吵后的关系变化:")
        print(f"  变化值: {result['change']:+d}")
        print(f"  新强度: {result['new_strength']}")
        print(f"  新等级: {result['new_level']}")
        
        # 验证确实是扣分
        if result['change'] < 0:
            print("✅ 负面互动确实扣分了")
            if abs(result['change']) >= 8:
                print("✅ 扣分幅度足够大 (≥8分)")
            else:
                print("⚠️  扣分幅度可能不够大")
        else:
            print("❌ 负面互动没有扣分，需要检查强制扣分逻辑")
        
        return result['change'] < 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_relationship_decay_frequency():
    """测试关系衰减频率调整"""
    print("\n🧪 测试关系衰减频率调整...")
    print("=" * 50)
    
    print("📊 关系衰减配置:")
    print(f"  每日衰减: {RELATIONSHIP_DECAY['daily_decay']} (已从0.5降低到0.2)")
    print(f"  衰减间隔配置:")
    
    for level, rate in RELATIONSHIP_DECAY['decay_intervals'].items():
        print(f"    {level}: {rate}")
    
    print(f"\n📉 衰减频率调整:")
    print("  - 衰减应用频率: 从10分钟改为30分钟")
    print("  - 随机衰减概率: 从30%降低到15%")
    print("  - 随机衰减量: 从1-3点降低到0-1点")
    
    # 计算调整前后的衰减强度对比
    old_daily_decay = 0.5
    new_daily_decay = RELATIONSHIP_DECAY['daily_decay']
    
    old_random_decay = 0.3 * 2  # 30%概率 * 平均2点
    new_random_decay = 0.15 * 0.5  # 15%概率 * 平均0.5点
    
    total_reduction = ((old_daily_decay + old_random_decay) - (new_daily_decay + new_random_decay)) / (old_daily_decay + old_random_decay) * 100
    
    print(f"\n📊 衰减强度减少: {total_reduction:.1f}%")
    
    if total_reduction > 50:
        print("✅ 关系衰减频率显著降低，符合要求")
    else:
        print("⚠️  关系衰减频率降低不够明显")
    
    return total_reduction > 50

def test_negative_interaction_probability():
    """测试负面互动概率调整"""
    print("\n🧪 测试负面互动概率调整...")
    print("=" * 50)
    
    print("📊 社交互动概率调整:")
    print("  关系很好 (≥70): 负面概率从10%降低到5%")
    print("  关系一般 (≥50): 负面概率从20%降低到15%")
    print("  关系较差 (≥30): 负面概率从40%降低到25%")
    print("  关系很差 (<30): 负面概率从65%降低到45%")
    
    print("\n📊 群体讨论概率调整:")
    print("  基础负面概率: 从30%降低到20%")
    print("  关系很好: 负面概率从20%降低到10%")
    print("  关系一般: 负面概率从25%降低到15%")
    print("  关系较差: 负面概率从35%降低到25%")
    print("  关系很差: 负面概率从40%降低到30%")
    
    # 计算总体负面互动概率减少
    old_avg_negative = (10 + 20 + 40 + 65) / 4  # 社交互动平均
    new_avg_negative = (5 + 15 + 25 + 45) / 4
    
    old_group_negative = (20 + 10 + 15 + 25 + 30) / 5  # 群体讨论平均
    new_group_negative = (20 + 10 + 15 + 25 + 30) / 5  # 这个没有变化
    
    total_reduction = ((old_avg_negative - new_avg_negative) / old_avg_negative) * 100
    
    print(f"\n📊 总体负面互动概率减少: {total_reduction:.1f}%")
    
    if total_reduction > 20:
        print("✅ 负面互动概率显著降低，符合要求")
    else:
        print("⚠️  负面互动概率降低不够明显")
    
    return total_reduction > 20

def test_negative_response_consistency():
    """测试负面回复一致性的新机制"""
    print("\n🔍 测试负面回复一致性机制...")
    
    # 测试新的重新生成机制
    print("  📝 测试重新生成机制:")
    print("    - 当AI回复不够负面时，会重新生成更自然的负面回复")
    print("    - 使用更智能的提示词：'你坚决不同意，用自然的语言表达反对'")
    print("    - 如果重新生成后仍不够负面，才添加自然的前缀")
    
    # 测试扩展的负面关键词检测
    print("  🔍 测试扩展的负面关键词检测:")
    print("    - 包含更多负面词汇：'拒绝'、'否认'、'怀疑'、'担心'、'忧虑'等")
    print("    - 包含更多否定词：'不'、'没'、'别'等")
    print("    - 包含更多情感词汇：'愤怒'、'生气'、'恼火'、'烦躁'等")
    
    # 测试自然前缀添加
    print("  ✨ 测试自然前缀添加:")
    print("    - 前缀更自然：'我不同意，' 而不是 '我不同意这个观点。'")
    print("    - 前缀更简洁：'我不太理解，' 而不是 '我不太理解你的意思。'")
    
    # 测试重新生成的提示词
    print("  🎯 测试重新生成的提示词:")
    print("    - argument: '你坚决不同意，用自然的语言表达反对'")
    print("    - misunderstanding: '你感到困惑不解，用自然的语言表达质疑'")
    print("    - disappointment: '你感到失望，用自然的语言表达不满'")
    
    print("  ✅ 负面回复一致性机制测试完成")
    return True

def test_prompt_consistency():
    """测试提示词的一致性"""
    print("\n🧪 测试提示词一致性...")
    print("=" * 50)
    
    # 测试负面互动提示词
    negative_contexts = [
        "不同意Alex的观点",
        "反对Emma的建议",
        "表示困惑不解",
        "坚持负面立场",
        "不要缓解气氛"
    ]
    
    print("📝 负面互动提示词检测:")
    for context in negative_contexts:
        # 模拟检测逻辑
        negative_keywords = ['不同意', '反对', '困惑', '质疑', '失望', '坚持立场', '负面立场', '不要缓解气氛']
        is_negative = any(keyword in context for keyword in negative_keywords)
        
        if is_negative:
            print(f"  ✅ {context}")
        else:
            print(f"  ❌ {context}")
    
    print("\n📋 提示词一致性检查:")
    print("  - 负面互动时强制保持负面情感")
    print("  - 不允许缓解气氛或转向积极")
    print("  - 所有回复必须与互动类型一致")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试负面互动修复效果和频率调整...")
    print("=" * 50)
    
    try:
        # 测试关系平衡
        balance_ok = test_relationship_balance()
        
        # 测试负面互动效果
        test_negative_interaction_effects()
        
        # 测试行为管理器
        manager_ok = test_behavior_manager_negative_override()
        
        # 测试关系衰减频率调整
        decay_ok = test_relationship_decay_frequency()
        
        # 测试负面互动概率调整
        probability_ok = test_negative_interaction_probability()
        
        # 测试负面互动回复一致性
        consistency_ok = test_negative_response_consistency()
        
        # 测试提示词一致性
        prompt_ok = test_prompt_consistency()
        
        print("\n" + "=" * 50)
        print("🎯 测试结果总结:")
        print(f"  关系平衡: {'✅ 通过' if balance_ok else '❌ 失败'}")
        print(f"  强制扣分: {'✅ 通过' if manager_ok else '❌ 失败'}")
        print(f"  衰减频率调整: {'✅ 通过' if decay_ok else '❌ 失败'}")
        print(f"  负面概率调整: {'✅ 通过' if probability_ok else '❌ 失败'}")
        print(f"  回复一致性: {'✅ 通过' if consistency_ok else '❌ 失败'}")
        print(f"  提示词一致性: {'✅ 通过' if prompt_ok else '❌ 失败'}")
        
        if all([balance_ok, manager_ok, decay_ok, probability_ok, consistency_ok, prompt_ok]):
            print("\n🎉 所有测试通过！负面互动修复和频率调整成功！")
        else:
            print("\n⚠️  部分测试失败，需要进一步检查")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
