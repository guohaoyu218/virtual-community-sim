"""
终端UI显示模块
负责所有终端界面的显示逻辑
"""

import os
from .terminal_colors import TerminalColors

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

{TerminalColors.YELLOW}🎮 可用命令：{TerminalColors.END}
  📍 map          - 查看小镇地图
  👥 agents       - 查看所有Agent状态  
  💬 chat <name>  - 与Agent对话
  🚶 move <name> <place> - 移动Agent
  🤖 auto         - 开启/关闭自动模拟
  💾 save         - 手动保存系统状态
  📊 status       - 查看持久化状态
  🏥 health       - 查看系统健康状态
  🧠 memory       - 显示内存状态
  🗄️  vector      - 显示向量数据库状态
  🧹 cleanup      - 执行内存清理 [normal|emergency|vector|all]
  � optimize     - 数据库优化 [vector|report]
  �🔄 reset errors - 重置错误统计
  
  🧠 智能命令：
  👫 social       - 查看社交网络
  🎪 event        - 创建小镇事件
  🎯 group <location> - 组织群体活动
  📊 stats        - 详细统计信息
  🔥 popular      - 查看热门地点
  
  📜 history      - 查看对话历史
  🆘 help         - 显示帮助
  🚪 quit         - 退出程序

{TerminalColors.CYAN}💡 快速开始：输入 'map' 查看小镇布局，或 'memory' 查看系统状态{TerminalColors.END}
""")
    
    def show_map(self, buildings, agents):
        """显示小镇地图"""
        print(f"\n{TerminalColors.BOLD}🗺️  小镇地图{TerminalColors.END}")
        print("=" * 50)
        
        # 创建6x6网格
        grid = [['⬜' for _ in range(6)] for _ in range(6)]
        
        # 放置建筑
        for name, building in buildings.items():
            x, y = building['x'], building['y']
            grid[y][x] = building['emoji']
        
        # 放置Agent
        agent_positions = {}
        for name, agent in agents.items():
            location = agent.location
            if location in buildings:
                x, y = buildings[location]['x'], buildings[location]['y']
                if (x, y) not in agent_positions:
                    agent_positions[(x, y)] = []
                agent_positions[(x, y)].append(f"{agent.color}{agent.emoji}{TerminalColors.END}")
        
        # 显示地图
        for y in range(6):
            row = ""
            for x in range(6):
                if (x, y) in agent_positions:
                    # 显示Agent
                    agents_here = agent_positions[(x, y)]
                    row += agents_here[0] + " "  # 只显示第一个Agent
                else:
                    # 显示建筑或空地
                    row += grid[y][x] + " "
            print(f"  {row}")
        
        print("\n📍 建筑说明:")
        for name, building in buildings.items():
            occupants = [f"{agents[agent_name].emoji}{agent_name}" 
                        for agent_name in agents.keys() 
                        if agents[agent_name].location == name]
            occupant_count = len(occupants)
            count_display = f"[{occupant_count}人]" if occupant_count > 0 else "[空]"
            occupant_text = f" {count_display} ({', '.join(occupants)})" if occupants else f" {count_display}"
            print(f"  {building['emoji']} {name}{occupant_text}")
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
