"""
增强版终端主程序
==============

整合了先进的上下文工程和高级关系管理的智能Agent系统
"""

import sys
import os

# 确保能够导入所有模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from terminal_town import TerminalTown
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnhancedTerminalTown(TerminalTown):
    """增强版终端小镇"""
    
    def __init__(self):
        super().__init__()
        logger.info("初始化增强版AI小镇系统")
        
        # 导入增强模块
        try:
            from core.context_engine import context_engine
            from core.relationship_manager import relationship_manager
            self.context_engine = context_engine
            self.relationship_manager = relationship_manager
            logger.info("成功加载先进的上下文工程和关系管理模块")
        except ImportError as e:
            logger.warning(f"无法加载增强模块: {e}")
            self.context_engine = None
            self.relationship_manager = None
    
    def show_welcome(self):
        """显示增强版欢迎界面"""
        print(f"""
{self.TerminalColors.BOLD}{self.TerminalColors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                🏘️  AI Agent 虚拟小镇 - 增强版               ║
║                      终端交互模式                             ║
║                                                              ║
║  ✨ 先进上下文工程 + 高级关系动态管理                        ║
║  🔥 真实冲突模拟 + 智能响应清理                              ║
╚══════════════════════════════════════════════════════════════╝
{self.TerminalColors.END}

{self.TerminalColors.GREEN}🎯 增强版特性：{self.TerminalColors.END}
  ✅ 先进的上下文工程 - 比传统Prompt更智能
  ✅ 高级关系动态管理 - 真实的社交冲突和和解
  ✅ 智能响应质量控制 - 杜绝"Human=16"等输出问题
  ✅ 多层级冲突系统 - 轻微分歧到激烈争论
  ✅ 自然关系衰减 - 模拟真实的人际关系变化

{self.TerminalColors.YELLOW}💡 关于上下文工程：{self.TerminalColors.END}
  传统Prompt工程只是简单的文本模板，而我们使用的上下文工程包含：
  • Few-shot学习示例
  • 动态角色模板  
  • 响应质量过滤
  • 多层级约束系统
  
  这确实比基础的Prompt工程更先进有效！

{self.TerminalColors.CYAN}🚀 现在就体验增强版的智能对话和真实关系动态！{self.TerminalColors.END}
输入 '{self.TerminalColors.BOLD}help{self.TerminalColors.END}' 查看所有命令
""")

    def _enhanced_clean_response(self, response: str, agent_type: str = None) -> str:
        """使用增强版响应清理"""
        if self.context_engine:
            return self.context_engine.clean_response(response, agent_type)
        else:
            return self._clean_response(response)
    
    def show_system_status(self):
        """显示增强版系统状态"""
        super().show_system_status()
        
        print(f"\n{self.TerminalColors.BOLD}🚀 增强功能状态{self.TerminalColors.END}")
        print("=" * 50)
        
        # 上下文引擎状态
        context_status = "✅ 已启用" if self.context_engine else "❌ 未加载"
        print(f"🧠 上下文工程引擎: {context_status}")
        
        # 关系管理器状态
        relationship_status = "✅ 已启用" if self.relationship_manager else "❌ 未加载"
        print(f"💫 高级关系管理器: {relationship_status}")
        
        if self.relationship_manager:
            # 显示活跃冲突
            active_conflicts = len(self.relationship_manager.active_conflicts)
            print(f"⚔️  当前活跃冲突: {active_conflicts}个")
            
            if active_conflicts > 0:
                print(f"   冲突详情:")
                for pair, scenario in self.relationship_manager.active_conflicts.items():
                    agent1, agent2 = pair
                    print(f"   • {agent1} vs {agent2}: {scenario.topic} ({scenario.intensity})")
        
        print()

if __name__ == "__main__":
    try:
        enhanced_town = EnhancedTerminalTown()
        enhanced_town.run()
    except KeyboardInterrupt:
        print("\n👋 感谢使用增强版AI Agent虚拟小镇！")
    except Exception as e:
        logger.error(f"增强版系统运行异常: {e}")
        print(f"❌ 系统异常: {e}")
