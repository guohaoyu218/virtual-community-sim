# 🏘️ AI Agent 虚拟社区模拟系统

> � 一个基于大语言模型的智能社区模拟系统，支持多个AI Agent的真实社交互动与情感交流

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/guohaoyu218/virtual-community-sim.svg)](https://github.com/guohaoyu218/virtual-community-sim/stargazers)

## 🌟 项目亮点

**🤖 智能Agent系统** - 9个具有独特个性的AI Agent，支持真实的社交互动和情感表达

**🧠 先进AI技术** - 集成Few-shot学习、上下文工程和智能响应清理，确保高质量对话

**💫 动态关系网络** - 真实的关系变化、冲突解决和社交网络演化，支持数据持久化

**🎮 丰富交互体验** - 终端UI、自动模拟、用户对话和实时监控等多种交互方式

## 🚀 快速开始

### 💻 环境要求
- **Python**: 3.8+ 
- **系统**: Windows/Linux/macOS
- **内存**: 推荐 8GB+
- **存储**: 推荐 2GB+

### ⚡ 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/guohaoyu218/virtual-community-sim.git
cd virtual-community-sim

# 2. 安装依赖
pip install -r requirements.txt

# 3. 直接启动（自动初始化）
python terminal_town_refactored.py
```

### 🛠️ 可选配置

如需使用在线AI模型，创建 `.env` 文件：
```bash
# DeepSeek API配置（可选）
DEEPSEEK_API_KEY=your_api_key_here
```

---

## 🎯 功能指南

### 🎮 基础操作

| 命令 | 功能 | 示例 |
|------|------|------|
| `map` | 查看小镇地图和Agent位置 | `map` |
| `agents` | 显示所有Agent状态 | `agents` |
| `social` | 查看社交网络关系矩阵 | `social` |
| `chat Alex` | 与指定Agent对话 | `chat Alex` |
| `move Emma 咖啡厅` | 移动Agent到指定地点 | `move Emma 咖啡厅` |
| `auto` | 开启/关闭自动模拟 | `auto` |

### 📊 系统监控

| 命令 | 功能 | 说明 |
|------|------|------|
| `stats` | 系统综合统计信息 | 显示Agent、关系、性能等统计 |
| `health` | 系统健康状态 | 错误统计、熔断器状态等 |
| `memory` | 内存使用情况 | 系统内存、向量数据库状态 |
| `save` | 手动保存系统状态 | 保存社交网络和系统数据 |

### 🤖 AI Agent 角色

| Agent | 职业 | 个性特点 | Emoji |
|-------|------|----------|--------|
| **Alex** | 程序员 | 理性思维，技术导向 | 👨‍💻 |
| **Emma** | 艺术家 | 感性创造，美学追求 | 👩‍🎨 |
| **Sarah** | 老师 | 耐心教导，知识分享 | 👩‍🏫 |
| **David** | 商人 | 商业思维，效率优先 | 👨‍💼 |
| **Lisa** | 学生 | 好奇活泼，学习热情 | 👩‍🎓 |
| **Mike** | 退休人员 | 人生阅历，智慧分享 | 👴 |
| **John** | 医生 | 严谨专业，关注健康 | 👨‍⚕️ |
| **Anna** | 厨师 | 生活气息，热情好客 | 👩‍🍳 |
| **Tom** | 机械师 | 实用主义，解决问题 | 👨‍🔧 |

---

## ✨ 核心特性

### 🧠 先进AI技术
- **上下文工程**: Few-shot学习 + 动态角色模板，确保高质量对话
- **智能响应清理**: 多层过滤去除垃圾输出，保持对话自然度
- **角色一致性**: 每个Agent都有独特的个性和专业背景
- **自动初始化**: 首次启动自动生成真实的社交网络数据

### 💫 动态关系系统
- **真实关系演化**: 关系值范围10-90，支持友谊、冲突、和解
- **智能冲突机制**: 基于性格和职业的冲突触发和解决
- **数据持久化**: 社交网络状态自动保存，重启后保持关系状态
- **关系可视化**: 彩色关系矩阵，直观显示Agent间的情感状态

### 🏗️ 技术架构
- **模块化设计**: 核心逻辑、显示层、交互层清晰分离
- **线程安全**: 支持并发操作和异步处理
- **向量数据库**: 基于Qdrant的长期记忆存储
- **智能内存管理**: 自动监控和多级清理策略

### 🎮 交互体验
- **终端UI**: 彩色界面，实时状态显示
- **自动模拟**: Agent自主社交互动，观察关系演化
- **用户对话**: 与任意Agent进行个性化对话
- **系统监控**: 全面的性能和健康状态监控

---

## 🔧 系统配置

### 🤖 AI模型配置
系统支持多种AI后端，自动选择可用模型：

1. **Qwen本地模型** (推荐)
   - 无需API密钥，完全本地运行
   - 自动下载模型文件
   - 隐私安全，响应稳定

2. **DeepSeek API** (可选)
   - 需要API密钥配置
   - 在线调用，响应快速
   - 创建 `.env` 文件配置：
   ```env
   DEEPSEEK_API_KEY=your_api_key_here
   ```

### 💾 数据存储
- **自动初始化**: 首次启动自动生成社交网络数据
- **持久化存储**: 关系状态、对话历史、Agent状态自动保存
- **数据恢复**: 系统重启后自动恢复所有状态
- **文件位置**: `data/cache/` 目录下

### ⚡ 性能优化
- **智能内存管理**: 自动监控和清理
- **向量数据库**: 高效的长期记忆存储
- **异步处理**: 多线程安全的并发操作
- **错误恢复**: 自动错误处理和系统自愈

---

## 🎬 使用示例

### 🚀 基础体验流程

```bash
# 1. 启动系统
python terminal_town_refactored.py

# 2. 查看小镇地图
🏘️ 小镇> map

# 3. 查看Agent状态
🏘️ 小镇> agents

# 4. 查看社交网络
🏘️ 小镇> social

# 5. 与Agent对话
🏘️ 小镇> chat Alex
你好Alex，最近在做什么项目？

# 6. 开启自动模拟，观察Agent互动
🏘️ 小镇> auto
```

### 💫 社交网络示例

启动后，系统会自动生成真实的关系网络：

```
━━━ 👥 社交网络状态 ━━━

🔗 Agent关系矩阵:
   Agent    Alex    Emma   Sarah   David    Lisa    Mike    John    Anna     Tom
────────────────────────────────────────────────────────────────────────────────
    Alex       ─    💖75    😊62    🙂45    😞18    🙂52    😐38    🙂48    😐35
    Emma    💖72       ─    😊65    🙂43    🙂51    😞22    🙂44    😊67    🙂41
   Sarah    😊61    😊63       ─    💖85    🙂47    🙂39    😊69    💖88    🙂42
   ...
```

### 🤖 Agent对话示例

```
🏘️ 小镇> chat Emma
👩‍🎨 Emma: 你好！我正在画一幅关于小镇生活的作品，你觉得什么最能代表我们的社区？

> 我觉得可以画Agent们在咖啡厅聊天的场景

👩‍🎨 Emma: 太棒的想法了！咖啡厅确实是大家交流的中心，我可以捕捉那种温馨的社交氛围。
```

---

## 🏗️ 项目架构

```
virtual-community-sim/
├── 🏠 core/                     # 核心模块
│   ├── agent_manager.py         # Agent生命周期管理
│   ├── thread_manager.py        # 多线程安全管理
│   ├── context_engine.py        # 先进上下文工程 ✨
│   └── relationship_manager.py  # 高级关系管理 ✨
│
├── 🤖 agents/                   # AI Agent系统
│   ├── base_agent.py           # Agent基础类
│   ├── specific_agents.py      # 9个具体Agent实现
│   └── behavior_manager.py     # 社交行为管理 ✨
│
├── 🧠 memory/                   # 智能记忆系统
│   ├── vector_store.py         # Qdrant向量数据库
│   ├── memory_manager.py       # 长期记忆管理
│   └── memory_cleaner.py       # 智能内存清理 ✨
│
├── 🎮 simulation/               # 模拟引擎
│   ├── simulation_engine.py    # 自动模拟核心
│   └── social_interaction.py   # 社交互动逻辑 ✨
│
├── 🎨 display/                  # 用户界面
│   ├── terminal_ui.py          # 彩色终端UI
│   └── terminal_colors.py      # 颜色主题
│
└── 💬 chat/                     # 对话系统
    └── chat_handler.py         # 智能对话处理
```

---

## 🛠️ 开发指南

### 🔧 本地开发
```bash
# 开发环境设置
git clone https://github.com/guohaoyu218/virtual-community-sim.git
cd virtual-community-sim
pip install -r requirements.txt

# 调试和监控
python terminal_town_refactored.py
🏘️ 小镇> health    # 查看系统健康状态
🏘️ 小镇> memory    # 监控内存使用
🏘️ 小镇> stats     # 系统统计信息
```

### 📁 重要文件说明
- `terminal_town_refactored.py` - 主程序入口
- `agents/behavior_manager.py` - 社交网络核心逻辑
- `data/cache/social_network.json` - 社交关系数据存储
- `logs/agent_system.log` - 系统运行日志

### 🧪 自定义扩展
```python
# 添加新的Agent类型
class CustomAgent(BaseAgent):
    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.custom_trait = "特殊技能"
        
    def custom_behavior(self):
        return "执行自定义行为"
```

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### � 快速贡献
1. **Fork** 本项目
2. **创建**功能分支: `git checkout -b feature/amazing-feature`
3. **提交**更改: `git commit -m 'Add amazing feature'`
4. **推送**分支: `git push origin feature/amazing-feature`
5. **创建** Pull Request

### 💡 贡献方向
- 🐛 **Bug修复**: 报告或修复系统问题
- ✨ **新功能**: 添加新的Agent类型或交互方式
- 📖 **文档改进**: 完善使用说明和代码注释
- 🎨 **UI优化**: 改进终端界面和用户体验
- 🧪 **测试用例**: 增加单元测试和集成测试

---

## �📄 许可证

本项目采用 **MIT 许可证** - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 问题反馈

遇到问题或有建议？欢迎联系：

- 📧 **GitHub Issues**: [提交问题](https://github.com/guohaoyu218/virtual-community-sim/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/guohaoyu218/virtual-community-sim/discussions)
- ⭐ **给项目点星**: 如果这个项目对你有帮助，请给我们一个星标！

---

## 🎯 开发路线图

### ✅ 已完成
- 🤖 基础Agent系统和社交网络
- 🧠 先进上下文工程和智能对话
- 💫 动态关系管理和冲突解决
- 💾 数据持久化和自动初始化
- 🛡️ 智能内存管理和错误处理

### 🚧 开发中
- 🌐 Web界面版本
- � 更多AI模型集成
- � 数据可视化面板
- 🎮 群体活动系统

### 📋 计划中
- � 移动端应用
- 🌍 多语言支持
- ☁️ 云端部署方案
- � 开放API接口

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个星标！⭐**

*感谢使用 AI Agent 虚拟社区模拟系统！*

</div>
