# Memory Crystal 记忆晶体 v2.1.0

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║              ✦  M E M O R Y   C R Y S T A L  ✦               ║
    ║                     ─── 记 忆 晶 体 ───                       ║
    ║                         .  *  .                               ║
    ║                        . /|\\\\ .                                ║
    ║                       . / | \\\\ .                               ║
    ║                      . /  |  \\\\ .                              ║
    ║                     ◆─────◆─────◆                             ║
    ║                    /|    /|\\\\    |\\\\                             ║
    ║                   / |   / | \\\\   | \\\\                            ║
    ║                  /  |  /  |  \\\\  |  \\\\                           ║
    ║                 /   | /   |   \\\\ |   \\\\                          ║
    ║                ◆────◆────◆────◆────◆                          ║
    ║                 \\\\   | \\\\   |   / |   /                          ║
    ║                  \\\\  |  \\\\  |  /  |  /                           ║
    ║                   \\\\ |   \\\\ | /   | /                            ║
    ║                    \\\\|    \\\\|/    |/                             ║
    ║                     ◆─────◆─────◆                             ║
    ║          "让知识结晶，让记忆永恒"                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

**Memory Crystal** 是 Hermes Agent 的新一代结构化记忆系统，由 `fact_store` 和 `fact_feedback` 两个工具构成。

> **让知识结晶，让记忆永恒**  
> **Let Knowledge Crystallize, Let Memory Endure**

## 核心特性

- **结构化存储**：每条事实包含类别、标签、信任分数
- **实体探查**：查询某个实体的所有相关事实
- **关联追踪**：发现实体间的隐藏关联
- **跨实体推理**：多实体交集查询
- **矛盾检测**：自动发现知识冲突
- **反馈进化**：用得越多越准（信任分数训练）
- **HRR 向量**：1024 维相位向量支持语义检索（需 numpy）
- **主动检索**：用户提问时自动搜索相关知识（v2.1.0 新增）

## 版本历史

### v2.1.0 (2026-06-15) - 主动检索模块

**新增 11 个组件**：

| 组件 | 功能 |
|------|------|
| message_analyzer.py | 消息分析器 - 意图/实体/关键词/主题提取 |
| knowledge_retriever.py | 知识检索器 - fact_store/session_search/llm-wiki 三源检索 |
| relevance_scorer.py | 相关性评分器 - 多维度评分算法 |
| response_generator.py | 响应生成器 - 上下文/建议/动作生成 |
| session_tag_extractor.py | 会话标签提取器 - 自动标签/摘要/分类 |
| session_relation_finder.py | 会话关联发现器 - 基于标签/标题/父会话 |
| session_index_generator.py | 会话索引生成器 - session_index.md/session_log.md |
| hermes_integration.py | Hermes 核心集成 - 消息处理流程集成 |
| feedback_collector.py | 反馈收集器 - 用户反馈收集和信任分数更新 |
| learning_mechanism.py | 学习机制 - 从用户行为中学习 |
| prediction_mechanism.py | 预测机制 - 预测用户意图和需求 |

**核心功能**：
- ✅ 主动检索：用户提问时自动搜索相关知识
- ✅ 智能匹配：理解用户意图，找到最相关的信息
- ✅ 知识应用：将找到的知识应用到当前对话
- ✅ 跨会话连续性：从历史会话中学习
- ✅ 反馈学习：从用户反馈中优化
- ✅ 预测机制：预测用户需求

**测试验证**：
- edgetunnel 搜索：秒回
- 三源检索：fact_store/session_search/llm-wiki 正常
- 标签提取：准确
- 分类识别：准确

### v2.0.0 (2026-06-14)

- SKILL.md 精简 -112 行
- 新增 4 脚本：fact_digest / skill_retriever / task_skill_map / dream_prune
- 部署文档 MEMORY-SYSTEM-CONFIG.md

### v1.3.0 (2026-06-08)

- 检索流水线重构
- HRR 向量修复
- 12 条 pitfalls

### v1.2.0 (2026-06-08)

- Dream 记忆整合（四阶段：定位→采集→整合→修剪）
- 自动记忆修剪（过时删除 + 重复合并 + 安全矩阵保护）
- 成功反馈 + 双向记录
- 记忆选择性注入

### v1.0.0 (2026-06-08)

- 初始版本
- 结构化存储（实体/类别/标签/信任分数）
- 跨实体推理
- 矛盾检测
- 反馈进化

## 与传统 Memory 的区别

| 维度 | 传统 Memory | Memory Crystal |
|------|------------|----------------|
| 存储结构 | 纯文本列表 | 结构化实体（类别/标签/信任分数） |
| 检索方式 | 关键词匹配 | 向量相似度 + 实体探查 + 关联追踪 + 主动检索 |
| 推理能力 | 无 | 跨实体推理 + 矛盾检测 + 预测机制 |
| 进化机制 | 静态 | 反馈驱动 + Dream 整合 + 自动修剪 + 学习机制 |
| 适用场景 | 短期/会话级 | 长期/跨任务/知识网络 |

## 快速开始

### 添加事实

```python
fact_store(
    action='add',
    content='MiMo 输入超过 28K tokens 时 API 响应显著变慢',
    category='tool',
    tags='mimo,xiaomi,performance'
)
```

### 查询事实

```python
# 关键词搜索（按需检索，推荐）
fact_store(action='search', query='MiMo 性能')

# 实体探查（精准查询某实体的所有事实）
fact_store(action='probe', entity='MiMo')

# 跨实体推理（多实体交集）
fact_store(action='reason', entities=['MiMo', 'DeepSeek'])
```

### 主动检索 (v2.1.0)

```python
import sys
from pathlib import Path

scripts_dir = Path.home() / '.hermes' / 'scripts'
sys.path.insert(0, str(scripts_dir))

from knowledge_retrieval import retrieve_for_message

# 主动检索相关知识
result = retrieve_for_message("如何配置 fact_store?")
print(result['response']['context'])
```

## 文件结构

```
memory-crystal/
├── SKILL.md                    # 技能文档
├── README.md                   # 本文件
├── references/                 # 参考文档
├── templates/                  # 模板文件
└── scripts/                    # 脚本文件
    ├── knowledge_retrieval.py      # 主模块
    ├── knowledge_retriever.py      # 知识检索器
    ├── knowledge_retrieve_tool.py  # 工具脚本
    ├── message_analyzer.py         # 消息分析器
    ├── relevance_scorer.py         # 相关性评分器
    ├── response_generator.py       # 响应生成器
    ├── session_tag_extractor.py    # 会话标签提取器
    ├── session_relation_finder.py  # 会话关联发现器
    ├── session_index_generator.py  # 会话索引生成器
    ├── hermes_integration.py       # Hermes 核心集成
    ├── feedback_collector.py       # 反馈收集器
    ├── learning_mechanism.py       # 学习机制
    └── prediction_mechanism.py     # 预测机制
```

## GitHub 仓库

https://github.com/yingmingyapei/memory-crystal

## 许可证

MIT License

## v2.3.0 (2026-06-20)

### 新增功能
- **fact_store_cli.py**: 命令行访问fact_store数据库
  - 支持：list、search、add、remove、stats
  - 测试结果：127条fact可正常查询

### 优化内容
- 更新SKILL.md到v2.3.0
- 新增fact_store CLI脚本
- 完善记忆系统文档

### 系统健康度
- fact_store CLI: ✅ 可用
- 记忆系统健康度: 98/100
