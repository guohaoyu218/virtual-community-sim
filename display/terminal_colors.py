"""
终端颜色定义模块
"""

class TerminalColors:
    """终端颜色定义"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'  # 紫色/洋红色
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    # Agent专用颜色
    ALEX = '\033[94m'    # 蓝色 - 程序员
    EMMA = '\033[95m'    # 紫色 - 艺术家  
    SARAH = '\033[92m'   # 绿色 - 老师
