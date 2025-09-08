"""
状态显示模块
负责各种系统状态的显示逻辑
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from display.terminal_colors import TerminalColors

logger = logging.getLogger(__name__)

class StatusDisplay:
    """状态显示管理器"""
    
    def __init__(self):
        pass
    
    def show_social_network_basic(self, agents: Dict, behavior_manager, show_recent_interactions_func):
        """显示基础社交网络状态"""
        print(f"\n{TerminalColors.BOLD}━━━ 👥 社交网络状态 ━━━{TerminalColors.END}")
        
        # 获取所有Agent名称
        agent_names = list(agents.keys())
        if not agent_names:
            print(f"❌ 暂无Agent")
            return
        
        # 创建关系矩阵表格
        print(f"\n{TerminalColors.CYAN}🔗 Agent关系矩阵:{TerminalColors.END}")
        
        # 准备关系数据
        relationships = {}
        
        # 统一从behavior_manager获取关系数据
        if hasattr(behavior_manager, 'social_network') and behavior_manager.social_network:
            for agent1_name in agent_names:
                for agent2_name in agent_names:
                    if agent1_name != agent2_name:
                        # 获取关系强度（默认50）
                        strength = behavior_manager.social_network.get(agent1_name, {}).get(agent2_name, 50)
                        # 转换为0-1分数（原来是0-100）
                        score = strength / 100.0
                        relationships[(agent1_name, agent2_name)] = score
        
        # 如果没有关系数据，使用默认值
        if not relationships:
            for agent1_name in agent_names:
                for agent2_name in agent_names:
                    if agent1_name != agent2_name:
                        relationships[(agent1_name, agent2_name)] = 0.5  # 默认中性关系
        
        # 表格头部
        header = f"{'Agent':>8}"
        for name in agent_names:
            header += f"{name[:6]:>8}"  # 截断长名称
        print(header)
        print("─" * (8 + len(agent_names) * 8))
        
        # 表格内容
        for agent1 in agent_names:
            row = f"{agent1[:8]:>8}"
            for agent2 in agent_names:
                if agent1 == agent2:
                    # 自己对自己显示为 -
                    row += f"{'─':>8}"
                else:
                    # 获取关系分数
                    score = relationships.get((agent1, agent2), 0.5)
                    
                    # 转换为整数分数显示（0-100）
                    int_score = int(score * 100)
                    
                    # 根据分数选择颜色和符号
                    if score >= 0.8:
                        symbol = f"{TerminalColors.GREEN}💖{TerminalColors.END}"
                    elif score >= 0.6:
                        symbol = f"{TerminalColors.GREEN}😊{TerminalColors.END}"
                    elif score >= 0.4:
                        symbol = f"{TerminalColors.CYAN}🙂{TerminalColors.END}"
                    elif score >= 0.2:
                        symbol = f"{TerminalColors.YELLOW}😐{TerminalColors.END}"
                    else:
                        symbol = f"{TerminalColors.RED}😞{TerminalColors.END}"
                    
                    # 显示整数分数
                    row += f"{symbol}{int_score:>4}"
            
            print(row)
        
        # 图例说明
        print(f"\n{TerminalColors.YELLOW}📋 关系等级说明:{TerminalColors.END}")
        print(f"  💖 亲密 (80+)   😊 友好 (60+)   🙂 中性 (40+)")
        print(f"  😐 冷淡 (20+)   😞 敌对 (<20)")
        
        # 显示统计信息
        self._show_relationship_statistics(relationships)
        show_recent_interactions_func()
        print()
    
    def _show_relationship_statistics(self, relationships):
        """显示关系统计信息"""
        if relationships:
            scores = [score for (a1, a2), score in relationships.items() if a1 != a2]
            if scores:
                # 转换为整数分数进行统计
                int_scores = [int(score * 100) for score in scores]
                avg_score = sum(int_scores) / len(int_scores)
                max_score = max(int_scores)
                min_score = min(int_scores)
                
                print(f"\n{TerminalColors.CYAN}📊 关系统计:{TerminalColors.END}")
                print(f"  • 平均关系值: {avg_score:.0f}")
                print(f"  • 最高关系值: {max_score}")
                print(f"  • 最低关系值: {min_score}")
                print(f"  • 关系对数: {len(scores)//2}")
    
    def show_social_network_file_status(self):
        """显示社交网络文件状态"""
        print(f"\n{TerminalColors.BOLD}━━━ 📁 社交网络文件状态 ━━━{TerminalColors.END}")
        
        try:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            file_path = os.path.join(data_dir, 'social_network.json')
            
            if os.path.exists(file_path):
                # 文件存在，显示详细信息
                file_stat = os.stat(file_path)
                file_size = file_stat.st_size
                modification_time = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"📄 文件路径: {file_path}")
                print(f"📊 文件大小: {file_size} 字节")
                print(f"🕒 修改时间: {modification_time}")
                
                # 尝试读取文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"✅ 文件状态: 可读取")
                    print(f"📈 社交网络大小: {len(data.get('social_network', {}))} 个Agent")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ 文件格式错误: {e}")
                except Exception as e:
                    print(f"❌ 读取文件失败: {e}")
            else:
                print(f"❌ 文件不存在: {file_path}")
                print(f"💡 提示: 使用 'save' 命令创建社交网络文件")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取社交网络文件状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示社交网络文件状态失败: {e}")
    
    def show_social_network_detailed(self, agents: Dict, behavior_manager, chat_history: List):
        """显示详细的社交网络分析"""
        print(f"\n{TerminalColors.BOLD}━━━ 📊 详细社交网络分析 ━━━{TerminalColors.END}")
        
        agent_names = list(agents.keys())
        if not agent_names:
            print(f"❌ 暂无Agent")
            return
        
        # 社交活跃度排行
        print(f"\n{TerminalColors.CYAN}🏆 社交活跃度排行:{TerminalColors.END}")
        social_scores = {}
        
        # 计算每个Agent的社交分数
        for agent_name in agent_names:
            score = 0
            interaction_count = 0
            
            # 统一从behavior_manager获取关系数据
            if hasattr(behavior_manager, 'social_network'):
                agent_relationships = behavior_manager.social_network.get(agent_name, {})
                for other_agent, strength in agent_relationships.items():
                    score += strength
                    interaction_count += 1
            
            # 从聊天历史统计用户交互
            user_chats = 0
            if chat_history:
                user_chats = len([chat for chat in chat_history if chat.get('agent_name') == agent_name])
                score += user_chats * 5  # 用户交互加分
            
            social_scores[agent_name] = {
                'total_score': score,
                'interaction_count': interaction_count,
                'user_chats': user_chats
            }
        
        # 排序并显示
        sorted_agents = sorted(social_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        for i, (agent_name, stats) in enumerate(sorted_agents, 1):
            agent = agents.get(agent_name)
            if agent:
                emoji = getattr(agent, 'emoji', '🤖')
                profession = getattr(agent, 'profession', '未知')
                location = getattr(agent, 'location', '未知')
                
                print(f"  {i:2d}. {emoji} {agent_name} ({profession})")
                print(f"      📍 {location} | 💯 {stats['total_score']:.1f} | 🤝 {stats['interaction_count']} | 💬 {stats['user_chats']}")
        
        # 显示关系网络分析
        print(f"\n{TerminalColors.CYAN}🕸️ 关系网络分析:{TerminalColors.END}")
        
        # 统计关系强度分布
        if hasattr(behavior_manager, 'social_network'):
            strength_distribution = {'敌对': 0, '冷淡': 0, '中性': 0, '友好': 0, '亲密': 0}
            total_relationships = 0
            
            for agent_name, relationships in behavior_manager.social_network.items():
                for other_agent, strength in relationships.items():
                    total_relationships += 1
                    if strength >= 80:
                        strength_distribution['亲密'] += 1
                    elif strength >= 60:
                        strength_distribution['友好'] += 1
                    elif strength >= 40:
                        strength_distribution['中性'] += 1
                    elif strength >= 20:
                        strength_distribution['冷淡'] += 1
                    else:
                        strength_distribution['敌对'] += 1
            
            print(f"  📊 关系分布 (总计 {total_relationships//2} 对关系):")
            for level, count in strength_distribution.items():
                if count > 0:
                    percentage = (count / total_relationships) * 100 if total_relationships > 0 else 0
                    print(f"     {level}: {count//2} 对 ({percentage/2:.1f}%)")
        
        print()
    
    def show_persistence_status(self, persistence_manager):
        """显示持久化状态"""
        try:
            stats = persistence_manager.get_system_statistics()
            
            print(f"\n{TerminalColors.BOLD}━━━ 💾 持久化状态 ━━━{TerminalColors.END}")
            print(f"📁 数据目录: {stats.get('data_directory', 'Unknown')}")
            print(f"📄 缓存文件: {stats.get('cache_files', 0)} 个")
            print(f"💿 备份文件: {stats.get('backup_files', 0)} 个") 
            print(f"💬 交互记录: {stats.get('interaction_files', 0)} 个")
            print(f"👤 Agent档案: {stats.get('agent_profiles', 0)} 个")
            print(f"💽 数据总大小: {stats.get('total_data_size_mb', 0)} MB")
            print(f"🤖 自动保存: {'✅ 已启用' if stats.get('auto_save_enabled', False) else '❌ 未启用'}")
            
            if stats.get('last_save_times'):
                print(f"⏰ 最近保存时间:")
                for component, save_time in stats['last_save_times'].items():
                    print(f"   • {component}: {save_time}")
            
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取持久化状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示持久化状态失败: {e}")
    
    def show_system_health(self, error_handler):
        """显示系统健康状态"""
        try:
            stats = error_handler.get_error_statistics()
            recent_errors = error_handler.get_recent_errors(10)
            
            print(f"\n{TerminalColors.BOLD}━━━ 🏥 系统健康状态 ━━━{TerminalColors.END}")
            
            # 系统健康状态
            health = stats.get('system_health', 'unknown')
            health_colors = {
                'healthy': TerminalColors.GREEN,
                'warning': TerminalColors.YELLOW,
                'degraded': TerminalColors.RED,
                'critical': TerminalColors.RED,
                'recovering': TerminalColors.CYAN
            }
            health_color = health_colors.get(health, TerminalColors.WHITE)
            print(f"💊 系统状态: {health_color}{health.upper()}{TerminalColors.END}")
            
            # 错误统计
            print(f"📊 错误统计:")
            print(f"  • 总错误数: {stats.get('total_errors', 0)}")
            
            # 按类别统计
            category_stats = stats.get('errors_by_category', {})
            if category_stats:
                print(f"  • 按类别:")
                for category, count in category_stats.items():
                    print(f"     {category}: {count}")
            
            # 按严重程度统计
            severity_stats = stats.get('errors_by_severity', {})
            if severity_stats:
                print(f"  • 按严重程度:")
                for severity, count in severity_stats.items():
                    print(f"     {severity}: {count}")
            
            # 熔断器状态
            circuit_breaker_status = stats.get('circuit_breaker_status', {})
            if circuit_breaker_status:
                print(f"🔥 熔断器状态:")
                for category, count in circuit_breaker_status.items():
                    print(f"   • {category}: {count}")
            
            # 最近错误
            if recent_errors:
                print(f"🚨 最近错误 (最多10条):")
                for error in recent_errors[-10:]:
                    timestamp = error.get('timestamp', 'Unknown')[:19]
                    category = error.get('category', 'Unknown')
                    message = error.get('message', 'No message')[:50]
                    print(f"   • [{timestamp}] {category}: {message}")
            
            print(f"⏰ 检查时间: {stats.get('health_check_time', 'Unknown')[:19]}")
            print()
            
        except Exception as e:
            print(f"{TerminalColors.RED}❌ 获取系统健康状态失败: {e}{TerminalColors.END}")
            logger.error(f"显示系统健康状态失败: {e}")
