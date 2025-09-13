"""
终端UI显示模块
负责所有终端界面的显示逻辑
"""

import os
from display.terminal_colors import TerminalColors

class TerminalUI:
    """终端UI显示器"""
    
    def __init__(self):
        pass
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_welcome(self):
        """显示欢迎界面"""
        print(f"""
{TerminalColors.BOLD}{TerminalColors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                    🏘️  AI Agent 虚拟小镇                     ║
║                      终端交互模式                             ║
║                                                              ║
║  快速 • 流畅 • 直观的命令行体验                              ║
╚══════════════════════════════════════════════════════════════╝
{TerminalColors.END}

{TerminalColors.GREEN}✨ 欢迎来到AI Agent虚拟小镇！{TerminalColors.END}

{TerminalColors.YELLOW}🎮 基础命令：{TerminalColors.END}
  📍 map          - 查看小镇地图
  👥 agents       - 查看所有Agent状态  
  💬 chat <name>  - 与Agent对话
  🚶 move <name> <place> - 移动Agent
  🤖 auto         - 开启/关闭自动模拟
  💾 save         - 手动保存系统状态
  
{TerminalColors.CYAN}📊 信息查看：{TerminalColors.END}
  👫 social       - 查看社交网络 (network/advanced)
  📜 history      - 查看历史记录 (chat/interactions/movements)
  🧠 memory       - 显示内存状态
  🔧 status       - 查看系统状态
  📊 stats        - 详细统计信息 (system/errors/memory/agents/social)
  
{TerminalColors.MAGENTA}🎪 互动功能：{TerminalColors.END}
  🎉 event        - 事件管理 (list/create/clear)
  💡 dev          - 开发者工具
  
{TerminalColors.RED}🆘 系统命令：{TerminalColors.END}
  🆘 help         - 显示帮助
  🚪 quit         - 退出程序

{TerminalColors.CYAN}💡 快速开始：输入 'map' 查看小镇布局，或 'agents' 查看所有角色{TerminalColors.END}
""")
    
    def show_map(self, buildings, agents):
        """显示小镇地图"""
        print(f"\n{TerminalColors.BOLD}🗺️  小镇地图{TerminalColors.END}")
        print("=" * 50)
        
        # 创建6x6网格
        grid = [['⬜' for _ in range(6)] for _ in range(6)]
        
        # 放置建筑到网格
        for name, building in buildings.items():
            x, y = building['x'], building['y']
            if 0 <= x < 6 and 0 <= y < 6:  # 确保坐标在范围内
                grid[y][x] = building['emoji']
        
        # 获取Agent位置信息
        agent_positions = {}
        for agent_name, agent in agents.items():
            location = agent.location
            if location in buildings:
                x, y = buildings[location]['x'], buildings[location]['y']
                if 0 <= x < 6 and 0 <= y < 6:  # 确保坐标在范围内
                    if (x, y) not in agent_positions:
                        agent_positions[(x, y)] = []
                    agent_positions[(x, y)].append(f"{agent.emoji}{agent_name}")
        
        # 显示地图网格 - 使用固定宽度格式化
        print(f"\n🗺️  地图网格 (X坐标: 0-5, Y坐标: 0-5):")
        print("   " + "".join([f"{i:^4}" for i in range(6)]))  # X轴坐标
        print("   " + "─" * 24)
        
        for y in range(6):
            row_cells = []
            for x in range(6):
                if (x, y) in agent_positions:
                    # 如果该位置有Agent，显示Agent数量或首个Agent emoji
                    agents_here = agent_positions[(x, y)]
                    if len(agents_here) == 1:
                        cell = agents_here[0][0]  # 只显示emoji
                    else:
                        cell = f"{len(agents_here)}"  # 显示数量
                else:
                    # 显示建筑或空地
                    cell = grid[y][x]
                
                # 每个格子固定宽度为4个字符
                row_cells.append(f"{cell:^4}")
            
            print(f"{y} │" + "".join(row_cells))
        
        print("   " + "─" * 24)
        
        # 显示建筑说明（更整齐的格式）
        print(f"\n📍 建筑分布:")
        print(f"{'位置':^8} {'建筑':^8} {'人数':^6} {'居住者':^20}")
        print("─" * 50)
        
        # 按坐标排序显示建筑
        sorted_buildings = sorted(buildings.items(), key=lambda x: (x[1]['y'], x[1]['x']))
        
        for name, building in sorted_buildings:
            x, y = building['x'], building['y']
            
            # 统计该建筑的Agent
            occupants = []
            for agent_name, agent in agents.items():
                if agent.location == name:
                    occupants.append(f"{agent.emoji}{agent_name}")
            
            occupant_count = len(occupants)
            if occupant_count > 0:
                if occupant_count <= 2:
                    occupant_text = ', '.join(occupants)
                else:
                    occupant_text = f"{', '.join(occupants[:2])}... +{occupant_count-2}"
            else:
                occupant_text = "空"
            
            # 格式化输出，确保对齐
            pos_str = f"({x},{y})"
            building_str = f"{building['emoji']}{name}"
            count_str = f"[{occupant_count}人]" if occupant_count > 0 else "[空]"
            
            print(f"{pos_str:^8} {building_str:<8} {count_str:^6} {occupant_text:<20}")
        print()
    
    def show_agents_status(self, agents):
        """显示所有Agent状态"""
        print(f"\n{TerminalColors.BOLD}👥 Agent状态总览{TerminalColors.END}")
        print("=" * 60)
        
        for name, agent in agents.items():
            status = agent.get_status()
            print(f"{agent.color}{agent.emoji} {name}{TerminalColors.END}")
            print(f"  📍 位置: {status['location']}")
            print(f"  😊 心情: {status['mood']}")
            print(f"  ⚡ 能量: {status['energy']}%")
            print(f"  🎯 行为: {status['current_action']}")
            
            if hasattr(agent, 'real_agent'):
                print(f"  🧠 类型: 真实AI Agent")
            else:
                print(f"  🤖 类型: 简化Agent")
            print()
    
    def show_simulation_action(self, action_type, agent, agent_name, details=None):
        """显示模拟行动"""
        action_headers = {
            'social': '💬 社交互动',
            'group_discussion': '👥 群体讨论',
            'move': '🚶 移动',
            'think': '💭 思考',
            'work': '💼 工作',
            'relax': '🌸 放松',
            'solo_thinking': '💭 独自思考'
        }
        
        header = action_headers.get(action_type, '🎯 行动')
        print(f"\n{TerminalColors.BOLD}━━━ {header} ━━━{TerminalColors.END}")
        
        if details:
            for detail in details:
                print(f"  {detail}")
        else:
            print(f"  {agent.emoji} {TerminalColors.CYAN}{agent_name}{TerminalColors.END}")
        print()
    
    def show_movement(self, agent, agent_name, old_location, new_location):
        """显示移动信息"""
        print(f"{TerminalColors.GREEN}🚶 {agent.emoji} {agent_name} 从 {old_location} 移动到 {new_location}{TerminalColors.END}")
    
    def show_error(self, message):
        """显示错误信息"""
        print(f"{TerminalColors.RED}❌ {message}{TerminalColors.END}")
    
    def show_success(self, message):
        """显示成功信息"""
        print(f"{TerminalColors.GREEN}✅ {message}{TerminalColors.END}")
    
    def show_warning(self, message):
        """显示警告信息"""
        print(f"{TerminalColors.YELLOW}⚠️ {message}{TerminalColors.END}")
    
    def show_info(self, message):
        """显示信息"""
        print(f"{TerminalColors.CYAN}ℹ️ {message}{TerminalColors.END}")
