# 🏘️ AI Agent 虚拟社区模拟系统

## 📖 项目简介

这是一个基于先进AI技术的虚拟社区模拟系统，支持多个智能Agent在虚拟环境中进行真实的社交互动、工作生活和情感交流。系统采用了先进的上下文工程技术和智能关系管理，能够模拟真实的人际关系动态。

## ✨ 核心特性

### 🧠 先进AI技术
- **上下文工程**: 比传统Prompt工程更智能的动态上下文构建
- **Few-shot学习**: 提供优质示例，确保高质量对话
- **智能响应清理**: 杜绝模型训练残留和垃圾输出
- **多层质量过滤**: 确保角色一致性和对话自然度

### 💫 真实关系动态
- **智能冲突系统**: 基于关系强度的多层级冲突模拟
- **自然关系衰减**: 模拟真实的人际关系变化
- **情感状态管理**: Agent具有动态的情绪和心理状态
- **社交网络分析**: 实时关系强度和社交活跃度统计

### 🏗️ 模块化架构
- **分层设计**: 核心逻辑、显示层、交互层清晰分离
- **线程安全**: 支持并发操作和异步处理
- **插件化扩展**: 易于添加新的Agent类型和行为模式
- **智能内存管理**: 自动清理和性能优化

### 🎮 丰富交互方式
- **终端界面**: 快速响应的命令行交互
- **实时模拟**: Agent自主行动和社交互动
- **用户对话**: 与任意Agent进行个性化对话
- **系统监控**: 全面的状态监控和性能分析

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Windows/Linux/macOS
- 内存: 建议8GB+
- 存储: 建议2GB+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/guohaoyu218/virtual-community-sim.git
cd virtual-community-sim
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置API（可选）**
```bash
# 复制配置文件
cp .env.example .env
# 编辑 .env 文件，添加API密钥
```

4. **启动系统**
```bash
# Web界面版本（推荐）
python main.py

# 终端界面版本
python main.py --terminal

# 直接启动终端版本
python terminal_town_refactored.py
```

## 🎯 使用指南

### 基础命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `map` | 查看小镇地图和Agent位置 | `map` |
| `agents` | 显示所有Agent状态 | `agents` |
| `chat <name>` | 与指定Agent对话 | `chat Alex` |
| `move <name> <place>` | 移动Agent到指定地点 | `move Emma 咖啡厅` |
| `auto` | 开启/关闭自动模拟 | `auto` |
| `social` | 查看社交网络关系 | `social` |

### 智能功能

| 命令 | 功能 | 示例 |
|------|------|------|
| `stats` | 系统统计信息 | `stats` |
| `history` | 交互历史记录 | `history` |
| `popular` | 热门位置与活动 | `popular` |
| `events` | 系统事件概览 | `events` |
| `memory` | 内存状态监控 | `memory` |
| `health` | 系统健康状态 | `health` |

### 系统管理

| 命令 | 功能 | 示例 |
|------|------|------|
| `save` | 手动保存系统状态 | `save` |
| `cleanup [type]` | 内存清理 | `cleanup smart` |
| `strategy [type]` | 调整清理策略 | `strategy performance` |
| `optimize vector` | 向量数据库优化 | `optimize vector` |
| `reset errors` | 重置错误统计 | `reset errors` |

## 🏗️ 系统架构

```
virtual-community-sim/
├── core/                    # 核心模块
│   ├── context_engine.py    # 上下文工程引擎
│   ├── relationship_manager.py # 关系管理器
│   ├── thread_manager.py    # 线程管理
│   └── smart_cleanup_manager.py # 智能清理
├── agents/                  # Agent相关
│   ├── base_agent.py        # 基础Agent类
│   ├── specific_agents.py   # 具体Agent实现
│   └── behavior_manager.py  # 行为管理器
├── memory/                  # 记忆系统
│   ├── vector_store.py      # 向量存储
│   ├── memory_manager.py    # 记忆管理
│   └── memory_cleaner.py    # 内存清理
├── simulation/              # 模拟引擎
│   ├── simulation_engine.py # 模拟引擎
│   └── social_interaction.py # 社交互动
├── display/                 # 显示层
│   ├── terminal_ui.py       # 终端UI
│   └── terminal_colors.py   # 颜色定义
├── chat/                    # 对话系统
│   └── chat_handler.py      # 对话处理器
└── config/                  # 配置文件
    ├── settings.py          # 系统设置
    └── relationship_config.py # 关系配置
```

## 🔧 配置说明

### API配置
支持多种AI模型后端：
- **Qwen本地模型**: 无需API，本地运行
- **DeepSeek API**: 在线API，需要配置密钥
- **自定义模型**: 可扩展支持其他模型

### 内存管理配置
```python
# 智能清理阈值
MEMORY_WARNING = 65%      # 内存警告阈值
MEMORY_CLEANUP = 75%      # 自动清理阈值
MEMORY_EMERGENCY = 85%    # 紧急清理阈值

# 向量数据库配置
MAX_MEMORIES_PER_AGENT = 300  # 每个Agent最大记忆数
CLEANUP_INTERVAL = 4          # 清理间隔（小时）
```

## 📊 系统特性详解

### 上下文工程 vs 传统Prompt

**传统Prompt工程问题:**
- 简单文本模板拼接
- 容易产生垃圾输出
- 响应质量不稳定
- 角色一致性差

**我们的上下文工程:**
- ✅ Few-shot学习示例
- ✅ 动态角色模板
- ✅ 多层质量过滤
- ✅ 智能响应清理

### 智能关系动态

**关系变化机制:**
- **友好互动**: +3~8分（同地点+1，同职业+1）
- **深度交流**: +5~12分（高关系基础+2）
- **误解冲突**: -5~15分（关系越好，失望越大）
- **自然衰减**: 长期不互动会缓慢下降

**冲突触发系统:**
```
关系强度70+: 冲突概率×1.8 (好朋友容易失望)
关系强度40-70: 冲突概率×1.3 (中等关系有分歧)
频繁互动: 冲突概率×1.5 (接触多摩擦多)
```

## 🎨 Agent角色类型

### 内置Agent
- **👨‍💻 Alex**: 程序员，理性思维，技术导向
- **🎨 Emma**: 艺术家，感性创造，美学追求
- **👩‍🏫 Sarah**: 老师，耐心教导，知识分享
- **👨‍⚕️ David**: 医生，严谨专业，关注健康
- **👨‍💼 Michael**: 商人，商业思维，效率优先
- **👩‍🍳 Lisa**: 厨师，生活气息，热情好客
- **🔧 Tom**: 机械师，实用主义，解决问题
- **👴 Frank**: 退休人员，人生阅历，智慧分享

### 自定义扩展
支持添加新的Agent类型：
```python
class CustomAgent(BaseAgent):
    def __init__(self, name, profession, personality):
        super().__init__(name, profession)
        self.personality = personality
        # 自定义初始化逻辑
```

## 📈 性能监控

### 系统健康指标
- **内存使用率**: 实时监控，智能清理
- **响应时间**: 对话和操作响应速度
- **错误率**: 系统稳定性指标
- **Agent活跃度**: 社交互动频率

### 优化建议
- 定期执行 `optimize vector` 清理向量数据库
- 根据硬件配置调整清理策略
- 监控内存使用，及时处理异常

## 🛠️ 开发指南

### 添加新功能
1. 在相应模块目录创建新文件
2. 继承基础类实现自定义逻辑
3. 在主程序中注册新功能
4. 添加相应的测试用例

### 调试技巧
- 使用 `health` 命令查看系统状态
- 查看 `logs/` 目录下的日志文件
- 使用 `memory` 命令监控资源使用

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add some amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 问题反馈

如果遇到问题或有建议，请通过以下方式联系：

- 创建 [GitHub Issue](https://github.com/guohaoyu218/virtual-community-sim/issues)
- 发送邮件到: [your-email@example.com]

## 🎯 路线图

### 已完成
- ✅ 基础Agent系统
- ✅ 先进上下文工程
- ✅ 智能关系管理
- ✅ 模块化重构
- ✅ 智能内存管理

### 开发中
- 🚧 Web界面支持
- 🚧 更多AI模型集成
- 🚧 群体活动系统
- 🚧 长期记忆机制

### 计划中
- 📋 移动端应用
- 📋 多语言支持
- 📋 云端部署方案
- 📋 API接口开放

---

*感谢使用AI Agent虚拟社区模拟系统！这是一个展示先进AI技术在社会模拟中应用的开源项目。*
