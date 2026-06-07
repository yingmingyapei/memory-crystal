# Memory Crystal 记忆晶体 v2.0.0

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║              ✦  M E M O R Y   C R Y S T A L  ✦               ║
    ║                     ─── 记 忆 晶 体 ───                       ║
    ║                         .  *  .                               ║
    ║                        . /|\ .                                ║
    ║                       . / | \ .                               ║
    ║                      . /  |  \ .                              ║
    ║                     ◆─────◆─────◆                             ║
    ║          "让知识结晶，让记忆永恒"                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

**Memory Crystal** 是 Hermes Agent 的新一代结构化记忆系统，由 `fact_store` 和 `fact_feedback` 两个工具构成。基于全息缩减表示（HRR）的相位向量代数，实现结构化存储、实体解析、信任分数进化、跨实体推理。

> **让知识结晶，让记忆永恒 — Let Knowledge Crystallize, Let Memory Endure**

## 核心特性

| 特性 | 说明 |
|------|------|
| **结构化存储** | 每条事实包含类别、标签、信任分数、创建/更新时间 |
| **HRR 向量代数** | 1024 维相位向量，bind/unbind/bundle 代数运算 |
| **实体探查** | 查询某个实体的所有相关事实（HRR 代数检索） |
| **关联追踪** | 发现实体间的结构关联 |
| **跨实体推理** | 多实体交集查询（向量空间 JOIN） |
| **矛盾检测** | 自动发现实体重叠但内容冲突的事实 |
| **反馈进化** | 用得多越准（helpful +0.05, unhelpful -0.10） |
| **混合检索** | FTS5 全文 + Jaccard 重排序 + HRR 向量相似度 |
| **中文友好** | 中文搜索 LIKE 兜底 + 实体提取支持中文 |
| **回填恢复** | `backfill_all()` 一键恢复向量和实体 |

## v2.0 新增

- **插件化架构**：完整的 MemoryProvider 实现 + `plugin.yaml`
- **回填机制**：`backfill_all()` 一次修复实体/向量/banks
- **已知术语表**：30+ 中文/英文技术术语自动实体提取
- **Lint 验证**：所有 Python 文件通过语法检查
- **SNR 预警**：HRR 存储容量接近极限时自动告警

## 与传统 Memory 的区别

| 维度 | 传统 Memory | Memory Crystal |
|------|------------|----------------|
| 存储结构 | 纯文本列表 | SQLite + 实体 + 信任分数 + HRR 向量 |
| 检索方式 | 关键词匹配 | FTS5 + Jaccard + HRR 代数 + 信任加权 |
| 推理能力 | 无 | 跨实体推理 + 矛盾检测 + 关联追踪 |
| 进化机制 | 静态 | 反馈驱动 + backfill 恢复 + 信任训练 |
| 适用场景 | 短期/会话级 | 长期/跨任务/知识网络 |

## 仓库结构

```
memory-crystal/
├── plugin.yaml                     # Hermes 插件注册
├── SKILL.md                        # 完整操作指南
├── README.md                       # 本文件
├── plugins/memory/holographic/     # 核心实现代码
│   ├── __init__.py                 # MemoryCrystalProvider 插件入口
│   ├── store.py                    # SQLite 存储层（实体解析、信任评分）
│   ├── retrieval.py                # 混合检索引擎（FTS5 + Jaccard + HRR）
│   └── holographic.py              # HRR 相位向量代数库
├── references/
│   ├── architecture.md             # 系统架构详解
│   ├── dream-consolidation.md      # Dream 记忆整合流程
│   ├── auto-pruning-rules.md       # 自动修剪规则
│   ├── selective-injection.md      # 记忆选择性注入
│   ├── holographic-debugging-guide.md  # HRR 调试指南
│   ├── fts5-chinese-fix.md         # FTS5 中文修复记录
│   └── logo.txt                    # ASCII logo
└── templates/
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

### 添加事实

```python
fact_store(
    action='add',
    content='MiMo 输入超过 28K tokens 时 API 响应显著变慢。根因：服务器容量有限',
    category='tool',
    tags='mimo,xiaomi,performance'
)
```

### 查询

```python
# 混合搜索
fact_store(action='search', query='MiMo 性能')

# 实体探查
fact_store(action='probe', entity='MiMo')

# 跨实体推理（AND 语义）
fact_store(action='reason', entities=['MiMo', '性能', 'token'])

# 关联追踪
fact_store(action='related', entity='A股')

# 矛盾检测
fact_store(action='contradict')
```

### 反馈进化

```python
# 标记有用（trust +0.05）
fact_feedback(action='helpful', fact_id=41)

# 标记过时（trust -0.10）
fact_feedback(action='unhelpful', fact_id=7)
```

### 回填恢复（安装 numpy 后）

```python
from plugins.memory.holographic.store import MemoryStore
store = MemoryStore(db_path="~/.hermes/memory_store.db")
result = store.backfill_all()
# {'facts_processed': N, 'entities_added': M, 'vectors_computed': N, 'banks_rebuilt': K}
```

## 文档

| 文档 | 说明 |
|------|------|
| [SKILL.md](SKILL.md) | 完整操作指南（v2.0.0） |
| [架构详解](references/architecture.md) | 系统架构和数据模型 |
| [Dream 记忆整合](references/dream-consolidation.md) | 四阶段整合流程 |
| [自动修剪规则](references/auto-pruning-rules.md) | 过时删除+重复合并+安全矩阵 |
| [选择性注入](references/selective-injection.md) | 按需检索替代全量注入 |
| [FTS5 中文修复](references/fts5-chinese-fix.md) | 中文搜索问题修复记录 |
| [HRR 调试指南](references/holographic-debugging-guide.md) | 向量系统调试 |
| [添加事实模板](templates/add-fact.md) | 按类别/场景的添加示例 |
| [推理查询模板](templates/reasoning.md) | 跨实体推理示例 |
| [实体探查模板](templates/probe-entity.md) | 实体探查示例 |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-06-08 | 初始发布：SKILL.md + 模板 |
| v1.1.0 | 2026-06-08 | +FTS5 中文修复 + HRR 调试指南 + 12 条 pitfalls |
| v1.2.0 | 2026-06-08 | +Dream 整合 + 自动修剪 + 成功反馈 + 选择性注入 |
| **v2.0.0** | **2026-06-08** | **+插件源码（__init__/store/retrieval/holographic）+ plugin.yaml + 回填 + 实体提取增强 + SNR 预警** |

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
