---
name: memory-crystal
description: Memory Crystal 记忆晶体 — Hermes Agent 结构化记忆系统操作指南。封装 fact_store + fact_feedback 的最佳实践、常用模板、pitfalls。
version: 1.3.0
author: yingming
tags: [memory, fact-store, knowledge-graph, reasoning, hermes-core]
category: hermes
created: 2026-06-08
---

# Memory Crystal 记忆晶体

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║              ✦  M E M O R Y   C R Y S T A L  ✦               ║
    ║                     ─── 记 忆 晶 体 ───                       ║
    ║                         .  *  .                               ║
    ║                        . /|\ .                                ║
    ║                       . / | \ .                               ║
    ║                      . /  |  \ .                              ║
    ║                     ◆─────◆─────◆                             ║
    ║                    /|    /|\    |\                             ║
    ║                   / |   / | \   | \                            ║
    ║                  /  |  /  |  \  |  \                           ║
    ║                 /   | /   |   \ |   \                          ║
    ║                ◆────◆────◆────◆────◆                          ║
    ║                 \   | \   |   / |   /                          ║
    ║                  \  |  \  |  /  |  /                           ║
    ║                   \ |   \ | /   | /                            ║
    ║                    \|    \|/    |/                             ║
    ║                     ◆─────◆─────◆                             ║
    ║          "让知识结晶，让记忆永恒"                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

## 触发条件

当用户说以下关键词时加载此技能：
- "记忆晶体" / "Memory Crystal"
- "fact_store" / "fact_feedback"
- "存储事实" / "查询事实" / "记忆系统"
- "实体探查" / "关联推理" / "矛盾检测"
- "信任分数"

## 核心概念

Memory Crystal **不是**"文件写满了就拆分建索引"。它是基于**全息缩减表示（Holographic Reduced Representations）**的向量记忆系统——每条事实不是一段文字，而是一个 1024 维的相位向量。概念之间通过向量代数绑定（bind）、解绑（unbind）、叠加（bundle），从而支持跨实体推理。

底层实现在 `plugins/memory/holographic/holographic.py`，基于 numpy 的相位向量运算。

### 两套系统的本质区别

```
memory 工具 ≈ 一个不断追加的 .txt 文件
    → 每次会话全量注入 system prompt
    → 写满了就截断，没有查询能力
    → 适合短期偏好/临时状态

fact_store ≈ 一个带向量索引的结构化数据库
    → 每条事实有类别、标签、信任分数
    → 支持 search/probe/reason/contradict
    → 信任分数随使用反馈自动进化
    → 适合长期环境配置/工作教训/知识网络
```

| 维度 | memory 工具 | Memory Crystal (fact_store) |
|------|------------|----------------|
| 存储结构 | 纯文本列表 | 结构化实体（类别/标签/信任分数）+ HRR 向量 |
| 检索方式 | 关键词匹配 | 向量相似度 + 实体探查 + 关联追踪 |
| 推理能力 | 无 | 跨实体推理 + 矛盾检测 |
| 进化机制 | 静态 | 反馈驱动（信任分数训练） |
| 适用场景 | 短期/会话级 | 长期/跨任务/知识网络 |

### 两个工具

| 工具 | 功能 | 类比 |
|------|------|------|
| `fact_store` | 结构化存储 + 推理（add/search/probe/reason/contradict/list） | 晶体的切面 |
| `fact_feedback` | 反馈进化（helpful/unhelpful → 训练信任分数） | 晶体的光泽度 |

### 何时用哪个

| 信息类型 | 存储位置 | 示例 |
|---------|---------|------|
| 用户偏好 | memory | "用户对自动化失败容忍度低" |
| 环境配置 | fact_store | "WSL 代理端口 10808" |
| 工作教训 | fact_store | "cron job prompt 必须用 update 命令" |
| 临时状态 | memory | "当前正在分析 MiMo 性能问题" |
| 持久技能 | skill | "热点刀锋六阶段流程" |

## 操作指南

### 1. 添加事实 (add)

**何时添加**：
- 用户纠正 → 立即存储（高信任）
- 踩坑教训 → 立即存储（标签: lesson）
- 环境发现 → 存储（类别: tool/general）

**模板**：
```python
fact_store(
    action='add',
    content='[具体事实描述，包含条件、根因、解决方案]',
    category='general',  # user_pref / project / tool / general
    tags='[标签1],[标签2],[标签3]'
)
```

**示例**：
```python
# 好的事实 ✅
fact_store(
    action='add',
    content='MiMo 输入超过 28K tokens 时 API 响应显著变慢。根因：服务器容量有限，KV-cache 处理能力不足。缓解：context_length=50000, compression.threshold=0.25',
    category='tool',
    tags='mimo,xiaomi,performance,bottleneck'
)

# 坏的事实 ❌（缺乏具体条件和根因）
fact_store(action='add', content='MiMo 很慢')
```

### 2. 搜索事实 (search)

**检索流水线**（2026-06-08 重构）：
```
Stage 1: FTS5 前缀匹配（"WSL" → "WSL*"，速度快）
    ↓ 无结果
Stage 2: LIKE 子串匹配（"网络" → LIKE '%网络%'，中文兜底）
    ↓ 候选集
Stage 3: Jaccard 重排序（query tokens ↔ fact tokens 重叠度）
Stage 4: 信任分数加权（relevance × trust_score）
```

**模板**：
```python
fact_store(action='search', query='[关键词1] [关键词2]')
```

**示例**：
```python
fact_store(action='search', query='cron 超时')
fact_store(action='search', query='MiMo 性能')
fact_store(action='search', query='WSL')       # FTS5 前缀 → 找到 "WSL网络"
fact_store(action='search', query='网络')      # FTS5 失败 → LIKE 兜底 → 找到
fact_store(action='search', query='记忆')      # LIKE 子串匹配
```

**注意**：多词查询用 OR 连接（自动），返回结果按相关度排序。中文词无需特殊处理，LIKE 兜底自动覆盖。

### 3. 实体探查 (probe)

**何时使用**：查询某个实体的所有相关事实。

**模板**：
```python
fact_store(action='probe', entity='[实体名称]')
```

**示例**：
```python
fact_store(action='probe', entity='MiMo')
# → 返回所有提到 MiMo 的事实

fact_store(action='probe', entity='WSL')
# → 返回所有提到 WSL 的事实
```

### 4. 关联追踪 (related)

**何时使用**：查找与某实体关联的其他实体。

**模板**：
```python
fact_store(action='related', entity='[实体名称]')
```

**示例**：
```python
fact_store(action='related', entity='A股')
# → 返回与 A股 相关的数据源、技能、方法论等
```

### 5. 跨实体推理 (reason)

**何时使用**：需要同时查询多个实体的交集。

**模板**：
```python
fact_store(action='reason', entities=['[实体1]', '[实体2]', '[实体3]'])
```

**示例**：
```python
fact_store(action='reason', entities=['WSL', '网络', 'cron'])
# → 发现 WSL 网络是 cron 超时的根因

fact_store(action='reason', entities=['MiMo', '性能', 'token'])
# → 发现 MiMo 在长 token 下的性能瓶颈
```

### 6. 矛盾检测 (contract)

**何时使用**：定期检查知识一致性，或发现信息冲突时。

**模板**：
```python
fact_store(action='contract')
```

**处理矛盾**：
1. 检查哪条事实更准确
2. 更新或删除过时的事实
3. 用 `fact_feedback(action='unhelpful', fact_id=xxx)` 标记错误事实

### 7. 反馈进化 (feedback)

**何时反馈**：
- 使用事实后发现准确 → `helpful`
- 使用事实后发现过时/错误 → `unhelpful`

**模板**：
```python
# 标记有用（trust_score +0.1）
fact_feedback(action='helpful', fact_id=[fact_id])

# 标记过时（trust_score -0.1）
fact_feedback(action='unhelpful', fact_id=[fact_id])
```

### 8. 列出所有事实 (list)

**模板**：
```python
fact_store(action='list')
```

## 最佳实践

### 存储质量标准

✅ **好的事实**：
- 包含具体条件（"输入超过 28K tokens"）
- 包含根因分析（"服务器容量有限"）
- 包含解决方案（"context_length=50000"）
- 使用标签分类（"mimo,performance"）

❌ **坏的事实**：
- 过于笼统（"MiMo 很慢"）
- 缺乏条件（"这个工具不好用"）
- 临时状态（"正在调试中"）

### 信任分数管理

- 新事实默认 0.5
- 被标记 helpful → +0.1
- 被标记 unhelpful → -0.1
- 高频检索 → 间接提升
- 定期清理低信任（<0.3）的事实

### 定期维护

建议每周执行一次：
```python
# 1. 列出所有事实
fact_store(action='list')

# 2. 检查矛盾
fact_store(action='contract')

# 3. 清理过时事实（trust_score < 0.3）
fact_store(action='remove', fact_id=[id])

# 4. 标记常用事实为 helpful
fact_feedback(action='helpful', fact_id=[id])
```

## Pitfalls（常见错误）

### 1. 把临时状态存入 Crystal

❌ **错误**：
```python
fact_store(action='add', content='正在调试 cron job 超时问题')
```

✅ **正确**：用 `memory` 工具存储临时状态。

### 2. 存储过于笼统的事实

❌ **错误**：
```python
fact_store(action='add', content='opencli 有问题')
```

✅ **正确**：
```python
fact_store(action='add', 
    content='opencli daemon start 命令不存在，正确命令是 opencli daemon restart',
    category='tool',
    tags='opencli,daemon,command')
```

### 3. 忘记设置标签

❌ **错误**：
```python
fact_store(action='add', content='...', category='general')
```

✅ **正确**：
```python
fact_store(action='add', content='...', category='general', tags='tag1,tag2,tag3')
```

### 4. 不反馈导致信任分数失真

❌ **错误**：使用事实后不反馈。

✅ **正确**：每次使用后反馈。
```python
# 使用事实后
fact_feedback(action='helpful', fact_id=41)
```

### 5. 用 search 代替 probe

❌ **错误**：想查询某实体的所有事实，却用关键词搜索。

✅ **正确**：用 `probe` 查询实体。
```python
# 错误
fact_store(action='search', query='MiMo')

# 正确
fact_store(action='probe', entity='MiMo')
```

### 6. FTS5 中文搜索失败（已修复 2026-06-08）

**问题**：`search('WSL')` 返回空，但 `list` 能看到包含 "WSL" 的事实。

**根因**：FTS5 的 `unicode61` 分词器将中英文混合文本合并成一个 token：
```
存储: "WSL网络关键事实"
分词: ["WSL网络关键事实"]  ← "WSL" 和 "网络" 被合并
搜索 "WSL": 找不到单独的 "WSL" 词 → 返回空
搜索 "WSL*": 前缀匹配 "WSL网络" → 成功
```

**修复**（`plugins/memory/holographic/retrieval.py`）：
- `_build_fts_query()` 自动加前缀通配符（query → query*）
- 纯中文词跳过 FTS5（前缀匹配对中文无效）
- `_fts_candidates()` 增加 LIKE 子串降级：FTS5 无结果时用 `LIKE '%关键词%'`
- `_tokenize_for_like()` 中文↔拉丁文边界分词："WSL网络" → ["WSL", "网络"]

**修复后验证**：
```python
fact_store(action='search', query='WSL')      # FTS5 前缀 → 1 条 ✅
fact_store(action='search', query='网络')     # LIKE 兜底 → 1 条 ✅
fact_store(action='search', query='记忆')     # LIKE 兜底 → 3 条 ✅
fact_store(action='search', query='热点刀锋')  # LIKE 兜底 → 2 条 ✅
```

### 7. numpy 未安装 → 整个向量检索链断裂

**症状**：probe/related/reason 全部降级为 search，search 对中文又返回空。

**根因**：`plugins/memory/holographic/holographic.py` 用 numpy 做相位向量运算。如果 numpy 不可用（`hrr._HAS_NUMPY = False`）：
- `_compute_hrr_vector()` 静默跳过（不报错）
- probe/related/reason 的 SQL `WHERE hrr_vector IS NOT NULL` 过滤掉所有无向量的事实
- 降级为 search → 如果 FTS5 也失败 → 返回空

**诊断**：
```python
# 在 execute_code 中检查
import sys; sys.path.insert(0, "/home/yingming/.hermes/hermes-agent")
from plugins.memory.holographic import holographic as hrr
print(f"hrr._HAS_NUMPY: {hrr._HAS_NUMPY}")  # 必须为 True
```

**修复**：`uv pip install numpy`（在 .venv 中安装）

**回填数据**：安装 numpy 后，已有事实缺少 HRR 向量，需要回填：
```python
from plugins.memory.holographic.store import MemoryStore
store = MemoryStore(db_path="~/.hermes/memory_store.db")
result = store.backfill_all()
# → {'facts_processed': 19, 'vectors_computed': 19, 'entities_added': 87, 'banks_rebuilt': 3}
```

### 8. 实体提取不认中文

**症状**：`probe('WSL')` 返回空，因为事实没有实体关联。

**根因**：`store.py` 的 `_extract_entities()` 只用英文正则：
- `\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)` — 只认英文大写词
- `"xxx"` / `'xxx'` — 只认引号

中文文本 "WSL网络关键事实" 中的 "WSL" 后面直接跟中文，正则不认。

**修复**（2026-06-08）：
- 新增 `_RE_CN_PAREN_TERM` 正则：提取 "MiMo (小米大模型)" 模式
- 新增 `_KNOWN_ENTITIES` 集合：30+ 个已知技术术语（WSL/MiMo/问财/A股/numpy 等）
- `_extract_entities()` 新增括号术语提取 + 已知术语子串匹配

**回填**：同 Pitfall #7，`store.backfill_all()` 会同时修复实体和向量。

### 9. HRR 向量静默缺失

**症状**：部分事实有 HRR 向量，部分没有。有向量的能被 probe 找到，没有的只能靠 FTS5。

**根因**：numpy 安装时间晚于事实创建时间。`_compute_hrr_vector()` 在 numpy 不可用时直接 `return`，不报错不标记。

**诊断**：
```python
# 检查哪些事实缺少向量
store._conn.execute("SELECT fact_id FROM facts WHERE hrr_vector IS NULL").fetchall()
```

**修复**：`store.backfill_all()` 一次性补全所有缺失向量。

### 10. Memory Bank 计数虚高

**症状**：`memory_banks` 表的 `fact_count` 远大于实际事实数。

**根因**：删除事实时 bank 没正确重建，或 bank 是累积计算而非实时同步。

**修复**：`store.backfill_all()` 会重建所有 bank 并清理孤儿 bank。

### 11. 代码修改后需要重启 Hermes

**症状**：修改了 `plugins/memory/holographic/*.py` 但 `fact_store` 工具行为不变。

**根因**：Python 模块缓存。Hermes 启动时加载插件代码到内存，运行期间不会重新加载。

**解决**：修改插件代码后必须重启 Hermes 才能生效。在 execute_code 中直接 import 可以绕过缓存（用于验证），但 agent 的 fact_store 工具走的是已缓存的旧代码。

### 12. 先写文档后测试（流程错误）

**教训**（2026-06-08）：创建了完整的 SKILL.md + Wiki + GitHub 仓库 + 模板，但没有验证 fact_store 的 search/probe/reason 是否正常工作。用户发现后指出："这套系统并没有经过测试这个环节？"

**正确流程**：
1. **先验证核心功能** → 测试 add/search/probe/reason/contradict
2. **发现问题立即修复** → 不要继续写文档
3. **修复后重新测试** → 确认所有操作正常
4. **然后才写文档和技能** → 文档反映真实行为

**原则**：工具能用 > 文档好看。没有经过测试的文档是误导。

## 与 memory 工具的配合

```
┌─────────────────────────────────────────────────────────────┐
│                    记忆系统分层                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐     ┌──────────────┐                     │
│   │    memory     │     │    Crystal    │                     │
│   │  (短期/会话)   │     │  (长期/结构化) │                    │
│   └──────┬───────┘     └──────┬───────┘                     │
│          │                     │                             │
│          ▼                     ▼                             │
│   ┌──────────────┐     ┌──────────────┐                     │
│   │ 用户偏好      │     │ 环境配置      │                     │
│   │ 临时状态      │     │ 工作教训      │                     │
│   │ 会话上下文    │     │ 知识网络      │                     │
│   └──────────────┘     └──────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 参考文档

- [架构详解](references/architecture.md)
- [ASCII Logo](references/logo.txt)
- [FTS5 中文搜索修复记录](references/fts5-chinese-fix.md) — 2026-06-08 修复 search 对中文返回空的问题
- [Holographic 调试指南](references/holographic-debugging-guide.md) — 诊断脚本、修复步骤、检索流水线详解
- [Wiki 文档](/mnt/c/Users/yingm/wiki/systems/hermes/2026-06-08-Memory-Crystal-记忆晶体系统.md)

## 口号

> **让知识结晶，让记忆永恒**  
> **Let Knowledge Crystallize, Let Memory Endure**

---

*Memory Crystal — 不是存储，是结晶。*
