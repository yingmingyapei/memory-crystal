# Memory Crystal 记忆晶体 v2.3.0

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║              ✦  M E M O R Y   C R Y S T A L  ✦               ║
    ║                     ─── 记 忆 晶 体 ───                       ║
    ║                         .  *  .                               ║
    ║                        . /|\\ .                                ║
    ║                       . / | \\ .                               ║
    ║                      . /  |  \\ .                              ║
    ║                     ◆─────◆─────◆                             ║
    ║          "让知识结晶，让记忆永恒"                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

**Memory Crystal** 是 Hermes Agent 的新一代结构化记忆系统，基于全息缩减表示（HRR）的相位向量代数，实现结构化存储、实体解析、信任分数进化、跨实体推理和主动检索。

> **让知识结晶，让记忆永恒 — Let Knowledge Crystallize, Let Memory Endure**

## 核心架构：两套系统协同工作

Memory Crystal 是**两套系统协同工作**：

| 系统 | 定位 | 存储方式 | 检索能力 | 适用场景 |
|------|------|----------|----------|----------|
| **memory 工具** | 短期/会话级 | 纯文本文件（MEMORY.md/USER.md） | 无查询能力，全量注入system prompt | 用户偏好、临时状态 |
| **fact_store** | 长期/结构化 | SQLite数据库 + HRR向量 | 向量相似度 + 实体探查 + 关联追踪 | 环境配置、工作教训、知识网络 |

## 运作流程详解

### 1. 存储阶段

```python
# 添加事实到fact_store
fact_store(action='add', 
    content='opencli daemon start 命令不存在，正确命令是 opencli daemon restart',
    category='tool',
    tags='opencli,daemon,command')
```

**自动处理**：
- 提取**实体**（技术术语、工具名等）
- 计算**HRR向量**（1024维相位向量，用于相似度计算）
- 设置**信任分数**（初始0.5，通过反馈进化）

### 2. 检索阶段（四步工作流程）

```
① skills_list 扫描 → ② fact_store search + 读fact_digest.md → ③ 评估最佳匹配 → ④ 执行
```

**三种检索方式**：

| 方式 | 用途 | 示例 |
|------|------|------|
| **search** | 关键词搜索（FTS5 + LIKE降级） | `fact_store(action='search', query='WSL IP')` |
| **probe** | 实体探查（查询某实体的所有事实） | `fact_store(action='probe', entity='WSL')` |
| **reason** | 跨实体推理（多实体交叉查询） | `fact_store(action='reason', entities=['WSL', 'network', 'SSH'])` |

### 3. 反馈阶段（信任分数进化）

```python
# 使用事实后反馈
fact_feedback(action='helpful', fact_id=41)  # trust +0.1
fact_feedback(action='unhelpful', fact_id=42)  # trust -0.1
```

**信任分数规则**：
- helpful_count ≥ 3 → 强化（永不自动删除）
- trust ≥ 0.5 → 永不自动删除
- 创建 <7 天 → 永不自动删除

### 4. 主动检索机制（v2.1.0新增）

```
用户消息 → 消息分析器 → 知识检索器 → 相关性评分器 → 响应生成器
              ↓              ↓              ↓              ↓
         意图/实体/关键词  fact_store     多维度评分     上下文/建议
                          session_search
                          llm-wiki
```

**11个组件协同**：

| 组件 | 功能 |
|------|------|
| 消息分析器 | 提取意图、实体、关键词、同义词扩展 |
| 知识检索器 | 三源并行搜索（fact_store + session_search + llm-wiki） |
| 相关性评分器 | 6维度评分（关键词30% + 实体25% + 信任15% + 新鲜10% + 频率10% + 位置10%） |
| 响应生成器 | 构建上下文、建议、动作 |

### 5. 维护机制

#### 自动修剪规则

| 条件 | 动作 |
|------|------|
| trust < 0.3 且创建 >30 天 | 删除 |
| trust < 0.2 且创建 >7 天 | 删除 |
| content_similarity > 0.8 | 合并（保留较新的） |
| helpful_count ≥ 3 | 强化（永不自动删除） |

#### Dream记忆整合（每日22:00自动触发）

1. **定位**：扫描所有事实，建立基线
2. **采集**：从会话/任务中提取新信号
3. **整合**：合并重复、更新过时、补充标签
4. **修剪**：清理低信任、合并近似、生成报告

## 核心特性

| 特性 | 说明 |
|------|------|
| **结构化存储** | 每条事实包含类别、标签、信任分数、创建/更新时间 |
| **HRR 向量代数** | 1024 维相位向量，bind/unbind/bundle 代数运算 |
| **实体探查** | 查询某个实体的所有相关事实（HRR 代数检索） |
| **关联追踪** | 发现实体间的结构关联 |
| **跨实体推理** | 多实体交集查询（向量空间 JOIN） |
| **矛盾检测** | 自动发现实体重叠但内容冲突的事实 |
| **反馈进化** | 用得多越准（helpful +0.1, unhelpful -0.1） |
| **混合检索** | FTS5 全文 + Jaccard 重排序 + HRR 向量相似度 |
| **中文友好** | 中文搜索 LIKE 兜底 + 实体提取支持中文 |
| **主动检索** | 消息分析→知识检索→相关性评分→响应生成 |
| **搜索优化** | 并行搜索（8.99ms）+ 缓存 + 高亮 + 排序 + 分页 + 过滤 + 导出 |

## 与传统 Memory 的区别

| 维度 | 传统 Memory | Memory Crystal |
|------|------------|----------------|
| 存储结构 | 纯文本列表 | SQLite + 实体 + 信任分数 + HRR 向量 |
| 检索方式 | 关键词匹配 | FTS5 + Jaccard + HRR 代数 + 信任加权 |
| 推理能力 | 无 | 跨实体推理 + 矛盾检测 + 关联追踪 |
| 进化机制 | 静态 | 反馈驱动 + backfill 恢复 + 信任训练 |
| 适用场景 | 短期/会话级 | 长期/跨任务/知识网络 |

## 使用示例

### 存储知识

```python
fact_store(action='add', 
    content='WSL网络配置：IP 192.168.3.33，用户 yingming',
    category='environment',
    tags='WSL,network,config')
```

### 检索知识

```python
# 关键词搜索
result = fact_store(action='search', query='WSL IP')

# 实体探查
result = fact_store(action='probe', entity='WSL')

# 跨实体推理
result = fact_store(action='reason', entities=['WSL', 'network', 'SSH'])
```

### 反馈训练

```python
# 使用事实后反馈
fact_feedback(action='helpful', fact_id=result['results'][0]['fact_id'])
```

### 回填恢复（安装 numpy 后）

```python
from plugins.memory.holographic.store import MemoryStore
store = MemoryStore(db_path="~/.hermes/memory_store.db")
result = store.backfill_all()
# {'facts_processed': N, 'entities_added': M, 'vectors_computed': N, 'banks_rebuilt': K}
```

## 诊断与优化

### 诊断脚本

```python
import sqlite3
conn = sqlite3.connect('/home/yingming/.hermes/memory_store.db')
total = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
never_used = conn.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count=0").fetchone()[0]
avg_trust = conn.execute("SELECT AVG(trust_score) FROM facts").fetchone()[0]
print(f"Total: {total}, Never used: {never_used} ({never_used/total*100:.1f}%), Avg trust: {avg_trust:.2f}")
```

### 核心洞察

**问题不是"搜索速度慢"，而是"搜索根本没有被使用"**。速度优化无意义——如果功能根本没在被使用的话。

**解决方案**：四层主动检索架构（消息分析器→知识检索器→相关性评分器→响应生成器）

## 仓库结构

```
memory-crystal/
├── plugin.yaml                     # Hermes 插件注册
├── SKILL.md                        # 完整操作指南（v2.3.0）
├── README.md                       # 本文件
├── plugins/memory/holographic/     # 核心实现代码
│   ├── __init__.py                 # MemoryCrystalProvider 插件入口
│   ├── store.py                    # SQLite 存储层（实体解析、信任评分）
│   ├── retrieval.py                # 混合检索引擎（FTS5 + Jaccard + HRR）
│   └── holographic.py              # HRR 相位向量代数库
├── scripts/                        # 22个功能组件
│   ├── knowledge_retrieval.py      # 主动检索主模块
│   ├── message_analyzer.py         # 消息分析器
│   ├── knowledge_retriever.py      # 知识检索器
│   ├── relevance_scorer.py         # 相关性评分器
│   ├── response_generator.py       # 响应生成器
│   ├── chinese_tokenizer.py        # 中文分词器
│   ├── entity_extractor.py         # 实体提取器
│   ├── parallel_search.py          # 并行搜索
│   ├── search_cache.py             # 搜索缓存
│   ├── search_highlight.py         # 搜索高亮
│   ├── search_sorter.py            # 搜索排序
│   ├── search_paginator.py         # 搜索分页
│   ├── search_filter.py            # 搜索过滤
│   ├── search_exporter.py          # 搜索导出
│   ├── search_suggest.py           # 搜索建议
│   ├── search_history.py           # 搜索历史
│   ├── fact_digest.py              # 每日摘要生成
│   ├── dream_prune.py              # Dream修剪
│   └── ...                         # 其他组件
├── references/                     # 参考文档
│   ├── architecture.md             # 系统架构详解
│   ├── dream-consolidation.md      # Dream 记忆整合流程
│   ├── auto-pruning-rules.md       # 自动修剪规则
│   ├── selective-injection.md      # 记忆选择性注入
│   ├── proactive-retrieval-architecture.md  # 主动检索架构详解
│   ├── actual-api-signatures.md    # 实际API签名速查
│   ├── test-suite.md               # 完整测试套件
│   └── ...                         # 其他参考文档
└── templates/                      # 模板文件
    ├── add-fact.md                 # 添加事实模板
    ├── reasoning.md                # 推理查询模板
    └── probe-entity.md             # 实体探查模板
```

## 快速开始

### 安装

```bash
# 作为 Hermes 插件安装
hermes plugin install github.com/yingmingyapei/memory-crystal

# 或手动安装
git clone https://github.com/yingmingyapei/memory-crystal.git
cp -r memory-crystal/plugins/memory/holographic ~/.hermes/plugins/memory/
cp memory-crystal/plugin.yaml ~/.hermes/plugins/
```

### 依赖

```bash
pip install numpy>=1.24
```

## 文档

| 文档 | 说明 |
|------|------|
| [SKILL.md](SKILL.md) | 完整操作指南（v2.3.0） |
| [架构详解](references/architecture.md) | 系统架构和数据模型 |
| [主动检索架构](references/proactive-retrieval-architecture.md) | v2.1.0-v2.3.0 完整18组件架构 |
| [Dream 记忆整合](references/dream-consolidation.md) | 四阶段整合流程 |
| [自动修剪规则](references/auto-pruning-rules.md) | 过时删除+重复合并+安全矩阵 |
| [选择性注入](references/selective-injection.md) | 按需检索替代全量注入 |
| [实际API签名](references/actual-api-signatures.md) | 25个模块的实际API签名速查 |
| [完整测试套件](references/test-suite.md) | 40个测试覆盖全部25个模块 |
| [FTS5 中文修复](references/fts5-chinese-fix.md) | 中文搜索问题修复记录 |
| [HRR 调试指南](references/holographic-debugging-guide.md) | 向量系统调试 |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-06-08 | 初始发布：SKILL.md + 模板 |
| v1.1.0 | 2026-06-08 | +FTS5 中文修复 + HRR 调试指南 + 12 条 pitfalls |
| v1.2.0 | 2026-06-08 | +Dream 整合 + 自动修剪 + 成功反馈 + 选择性注入 |
| v2.0.0 | 2026-06-08 | +插件源码 + 回填 + 实体提取增强 + SNR 预警 |
| v2.1.0 | 2026-06-15 | +主动检索模块（11个组件）+ 三源检索 + 中文分词 |
| v2.1.1 | 2026-06-15 | +搜索缓存 + 结果高亮 |
| v2.1.2 | 2026-06-15 | +并行搜索 + 搜索建议 + 搜索历史 |
| v2.1.3 | 2026-06-15 | +中文分词优化 + 同义词扩展 |
| v2.1.4 | 2026-06-15 | +评分算法优化（6维度） |
| v2.1.5 | 2026-06-15 | +实体提取增强（10种类型） |
| **v2.3.0** | **2026-06-15** | **+搜索排序+分页+过滤+导出+完整22组件** |

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Memory Crystal 架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   fact_store / fact_feedback (工具入口)                         │
│          │                                                       │
│          ▼                                                       │
│   MemoryCrystalProvider (__init__.py)                           │
│          │                                                       │
│     ┌────┴────┐                                                  │
│     ▼         ▼                                                   │
│  store.py   retrieval.py                                         │
│  (SQLite)   (FTS5+Jaccard+HRR)                                   │
│     │         │                                                   │
│     └────┬────┘                                                   │
│          ▼                                                         │
│   holographic.py (HRR 相位向量代数)                               │
│                                                                  │
│   数据层: SQLite (facts/entities/fact_entities/memory_banks)    │
│   向量层: numpy float64 (1024-dim phase vectors)                 │
└─────────────────────────────────────────────────────────────────┘
```

### 检索流水线

```
search(query):
  query → FTS5 MATCH（前缀通配）
    ↓ 无结果
  LIKE '%term%'（中文兜底）
    ↓ 候选集
  Jaccard(query_tokens, fact_tokens) 重排序
    ↓
  HRR 向量相似度（若 numpy 可用）
    ↓
  relevance × trust_score → 最终分数
    ↓
  返回 top-N

probe(entity):
  entity → encode_atom → bind(entity, ROLE_ENTITY)
    ↓
  unbind(fact_vector, probe_key) → residual
    ↓
  similarity(residual, content_vector) × trust_score

reason([e1, e2]):
  ∀ entity: bind(entity, ROLE_ENTITY) → probe_key
    ↓
  ∀ fact: min(unbind(fact, probe_key) similarity) → AND 语义
```

### 主动检索流水线

```
用户消息 → 消息分析器 → 知识检索器 → 相关性评分器 → 响应生成器
              ↓              ↓              ↓              ↓
         意图/实体/关键词  并行搜索三源    6维度评分     上下文/建议
                          (8.99ms)        (30%+25%+     (缓存+高亮
                                          15%+10%+      +排序+分页
                                          10%+10%)      +过滤+导出)
```

## 配置

在 `config.yaml` 的 `plugins.hermes-memory-store` 下配置：

```yaml
plugins:
  hermes-memory-store:
    db_path: "~/.hermes/memory_store.db"
    auto_extract: false
    default_trust: 0.5
    hrr_dim: 1024
    hrr_weight: 0.3
    min_trust_threshold: 0.3
    temporal_decay_half_life: 0
```

## 许可证

MIT License

---

*Memory Crystal — 不是存储，是结晶。*
