---
name: memory-crystal
description: Memory Crystal 记忆晶体——Hermes Agent 结构化记忆系统。v2.4.0 新增搜索排序+分页+过滤+导出+主动检索+并行搜索+缓存+高亮+建议+历史+中文分词+实体提取。22个组件，19项功能。
version: 2.4.0
author: yingming
tags: [memory, fact-store, knowledge-graph, reasoning, hermes-core, proactive-retrieval, chinese-tokenizer, entity-extraction, search-sort, search-pagination, search-filter, search-export]
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

## 跨对话知识共享

fact_store 是 SQLite 数据库，跨对话共享。但新对话不会自动知道里面有什么。

**解决方案**：四步工作流程
```
① skills_list 扫描
② fact_store search 相关事实 + 读 ~/.hermes/fact_digest.md
③ 评估最佳匹配
④ 执行
```

`fact_digest.py` 每天 7:00 cron 自动生成摘要，写入 `~/.hermes/fact_digest.md`。

## Pitfalls

### 0. fact_store add 返回 success 但数据未持久化（2026-06-14）

**症状**：`fact_store(action='add', ...)` 返回 `{"fact_id": 97, "status": "added"}`，但后续 `fact_store(action='list')` 看不到该条目，`fact_store(action='search')` 也搜不到。

**根因**：不确定，可能与并发写入、FTS5 索引同步、或 session 上下文有关。

**防御**：每次 add 后必须 search 验证。
```python
fact_store(action='add', content='...', tags='...')
# 验证
result = fact_store(action='search', query='关键词')
assert len(result['results']) > 0, "fact_store add failed silently!"
```

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

### 13. memories/memory/*.md 文件的实际读取机制 + MEMORY.md 文件位置

**MEMORY.md 文件位置**：`/home/yingming/.hermes/memories/MEMORY.md`
**USER.md 文件位置**：`/home/yingming/.hermes/memories/USER.md`

⚠️ 注意：路径是 `~/.hermes/memories/MEMORY.md`，不是 `~/.hermes/MEMORY.md`。`memory` 工具的 replace/add 操作写入的就是这个文件。

**症状**：看到 `~/.hermes/memories/memory/` 目录下有 90+ 个独立 .md 文件，但不确定系统是否读取它们。

**事实**：
- `memory_tool.py` 的 `load_from_disk()` 只读 `MEMORY.md` 和 `USER.md` 两个文件
- 但 `agent/memory_optimization` 技能描述了三层知识架构，其中 Layer 1 是"memories/memory/*.md，一个事实一个文件，auto-injected top-N per turn"
- 这两条信息看似矛盾，实际可能是**两条不同的注入路径**：memory_tool 是显式路径，memory_optimization 是隐式路径
- **未验证**：目前没有确认 memory_optimization 描述的 Layer 1 注入是否在当前版本实际生效

**教训**：不要断言 `memories/memory/*.md` 是"孤儿文件"——它们可能有隐式读取路径。如果需要确认，检查 `agent/memory_optimization.py` 和 `agent/system_prompt.py` 的实际注入逻辑。

### 12. 先写文档后测试（流程错误）

**教训**（2026-06-08）：创建了完整的 SKILL.md + Wiki + GitHub 仓库 + 模板，但没有验证 fact_store 的 search/probe/reason 是否正常工作。用户发现后指出："这套系统并没有经过测试这个环节？"

**正确流程**：
1. **先验证核心功能** → 测试 add/search/probe/reason/contradict
2. **发现问题立即修复** → 不要继续写文档
3. **修复后重新测试** → 确认所有操作正常
4. **然后才写文档和技能** → 文档反映真实行为

**原则**：工具能用 > 文档好看。没有经过测试的文档是误导。

## v2.0 新增：Dream 记忆整合

> 脚本：`scripts/fact_digest.py`（每日摘要）、`scripts/skill_retriever.py`（三层技能检索）、`scripts/task_skill_map.json`（90+技能映射）、`scripts/dream_prune.py`（Dream修剪）
> 部署文档：`references/MEMORY-SYSTEM-CONFIG.md`

借鉴 Claude Code 的 Dream Memory Consolidation，Memory Crystal 现在支持四阶段记忆整合：

```
Phase 1 — 定位：扫描所有事实，建立基线
Phase 2 — 采集：从会话/任务中提取新信号（成功+失败）
Phase 3 — 整合：合并重复、更新过时、补充标签
Phase 4 — 修剪：清理低信任、合并近似、生成报告
```

**触发时机**：每日 22:00 由 Phoenix Protocol 深度进化任务自动触发，或用户说"记忆整合"时手动触发。

**详细流程**：参考 `references/dream-consolidation.md`

## v2.0 新增：自动记忆修剪

Memory Crystal 现在支持自动修剪规则：

| 条件 | 动作 |
|------|------|
| trust < 0.3 且创建 >30 天 | 删除 |
| trust < 0.2 且创建 >7 天 | 删除 |
| content_similarity > 0.8 | 合并（保留较新的） |
| 内容 <10 字且 trust < 0.5 | 增强或删除 |
| helpful_count ≥ 3 | 强化（永不自动删除） |

**安全矩阵**：
- 创建 <7 天的事实 → 永不自动删除
- trust ≥ 0.5 的事实 → 永不自动删除
- 被标记 helpful ≥3 次 → 永不自动删除

**详细规则**：参考 `references/auto-pruning-rules.md`

## v2.0 新增：成功反馈 + 双向记录

借鉴 Claude Code 的洞察：
> "如果只保存纠正，会避免过去的错误，但会偏离用户已验证过的方法，变得过于谨慎。"

**新增反馈类型**：

| 场景 | 反馈 | 效果 |
|------|------|------|
| 事实被使用且正确 | `fact_feedback(action='helpful')` | trust +0.1 |
| 事实被使用但错误 | `fact_feedback(action='unhelpful')` | trust -0.1 |
| 修复验证通过 | `fact_store(action='add', tags='verified-fix')` | 记录成功模式 |
| 工作模式有效 | `fact_store(action='add', tags='success-pattern')` | 记录成功方法 |

**关键改变**：不只在犯错时记录，在做对时也要记录。成功的模式和失败的教训同样有价值。

## v2.0 新增：记忆选择性注入

借鉴 Claude Code 的 Memory Synthesis 机制，Memory Crystal 现在推荐按需检索而非全量注入：

| 场景 | 推荐策略 | 工具 |
|------|---------|------|
| 简单查询 | search(关键词) top-3 | `fact_store(action='search')` |
| 涉及特定实体 | probe(实体名) | `fact_store(action='probe')` |
| 多实体交叉 | reason([实体列表]) | `fact_store(action='reason')` |
| 全量巡检 | list（全部） | `fact_store(action='list')` |

**原则**：搜索优于全量，top-N 优于全部，实体感知优于关键词，推理优于检索。

**详细指南**：参考 `references/selective-injection.md`

### 14. list 只返回 10 条，实际可能有 60+ 条

**症状**：`fact_store(action='list')` 只显示 10 条，误以为只有 10 条事实。

**根因**：list 工具有默认 limit，不代表实际总数。直接查 SQLite 可见完整数据。

**诊断**：
```python
import sqlite3, os
db = sqlite3.connect(os.path.expanduser("~/.hermes/memory_store.db"))
count = db.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
print(f"Total facts: {count}")  # 可能 60+
db.close()
```

**正确做法**：需要全量数据时用 `search` 或直接查数据库，不要依赖 `list` 的输出数量。

### 15. procedures 属于 skills，不属于 memory

**教训**（2026-06-14）：把工作流程写成祈使句存入 memory（"每次执行任务必须走三步"），被用户指出违规。

**规则**：
- memory 存**声明式事实**（"用户偏好X"、"环境是Y"）
- skills 存**流程方法论**（"做X的步骤是1→2→3"）
- fact_store 存**跨对话知识**（"API key 在某日轮换"、"某工具的坑"）

**判断标准**：如果一条记忆读起来像"给自己的指令"，它应该在 skill 里，不在 memory 里。

### 16. memory 条目数量由用户控制，核心规则存第一条

**用户规则**（2026-06-14 确立，2026-06-15 更新）：MEMORY.md 只保留 3 条高频行为规则，具体工具/技能信息存 fact_store。第一条（操作习惯）是最重要的，包含四步工作流程 + wiki-work-logger 强制记录规则。

**memory 文件位置**：`/home/yingming/.hermes/memories/MEMORY.md`（不是 `~/.hermes/MEMORY.md`）
**user 文件位置**：`/home/yingming/.hermes/memories/USER.md`（不是 `~/.hermes/USER.md`）

**当前 MEMORY.md 三条**：
```
1. 操作习惯：四步工作流程 + wiki-work-logger 强制记录
2. 工作习惯+备份：Wiki + GitHub
3. 信息时效性：验证时效性
```

**跨对话知识共享闭环**：
```
对话A 存入 fact_store → 每天7:00 自动生成 fact_digest.md → 对话B 启动时读摘要 + search fact_store → 共享知识
```

**摘要文件**：`~/.hermes/fact_digest.md`（由 `~/.hermes/scripts/fact_digest.py` 生成，cron job ID: 5cfcea0df50d）

### 17. MEMORY.md 膨胀防护——只放 3 条，多余的存 fact_store

**症状**：MEMORY.md 从 3 条膨胀到 8 条，因为每次完成工作后都往里追加新条目（video-converter、内容创作理念等）。

**根因**：没有明确的"什么该存 MEMORY.md，什么该存 fact_store"的判断规则。

**规则**：
- MEMORY.md 只存**每次会话都需要的行为规则**（操作习惯、工作习惯、信息时效性）
- 具体工具信息（video-converter、ffmpeg 参数）→ fact_store
- 用户偏好（内容创作风格、输出格式）→ USER.md 或 fact_store
- 一次性事件（模型切换、API key 轮换）→ fact_store

**判断标准**：问自己"这个信息是不是每次对话都需要？"如果不是，存 fact_store。

**修复**：如果 MEMORY.md 超过 3 条，立即把多余的移到 fact_store 并从 MEMORY.md 删除。

### 18. USER.md 维护——定期清理过时内容

**症状**：USER.md 条目只增不减，过时信息（如一个月前的模型切换记录）一直保留。

**规则**：
- 每周检查一次 USER.md
- 清理过时内容（超过一个月的事件记录）
- 合并重复条目（如多个"保存路径"合并为一条）
- 添加新发现的用户习惯

**判断标准**：如果一条 USER.md 条目描述的是"某天发生了某事"而不是"用户的稳定偏好"，它应该在 fact_store 而不是 USER.md。

### 19. 记忆系统架构速查——什么存在哪里

**每次会话自动注入（不需要读取文件）**：
```
MEMORY.md (3条) → system prompt 中的 "MEMORY (your personal notes)" 部分
USER.md (14条) → system prompt 中的 "USER PROFILE (who the user is)" 部分
```

**按需检索（需要主动调用工具）**：
```
fact_store (50+条) → fact_store(action='search') 或 fact_store(action='probe')
~/.hermes/fact_digest.md → read_file（每日摘要，cron 自动生成）
skills (122个) → skill_view(name)
```

**历史遗留（不主动读取）**：
```
memories/memory/*.md (84个) → 历史记忆文件，可能有隐式读取路径（未验证）
memories/user/*.md (41个) → 历史用户偏好文件
```

**关键区分**：
- "自动注入" = 系统把内容放到 system prompt 中，我不需要读文件
- "按需检索" = 我需要主动调用工具才能获取内容
- "历史遗留" = 文件存在但不确定是否被读取

### 20. fact_store 100% 从未被检索——检索激活问题（2026-06-15）

**症状**：fact_store 有 76 条记录，但 `retrieval_count` 全部为 0。知识存储了但从未被使用。

**诊断方法**：
```python
import sqlite3
conn = sqlite3.connect('/home/yingming/.hermes/memory_store.db')
total = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
never_used = conn.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count=0").fetchone()[0]
print(f"Total: {total}, Never used: {never_used} ({never_used/total*100:.1f}%)")
```

**根因分析**：
- **没有主动检索触发器** - 用户提问时不会自动搜索相关知识
- **没有智能匹配算法** - 无法理解用户意图，找到最相关的信息
- **没有知识应用机制** - 找到的信息无法自动应用到当前对话

**核心洞察**：问题不是"搜索速度慢"，而是"搜索根本没有被使用"。

**用户核心需求**："无论在哪个对话中提出问题或执行操作，都能及时做出正确的反应"

**解决方案**：需要四层架构：
1. **消息分析器** - 分析用户消息，提取意图、实体、关键词
2. **知识检索器** - 从 fact_store、session_search、llm-wiki 检索相关知识
3. **相关性评分器** - 对检索结果进行多维度评分
4. **响应生成器** - 基于检索结果生成响应

**详细方案**：`C:\Users\yingm\wiki\systems\hermes\2026-06-15-记忆系统完整改造方案.md`

### 21. session_search sessions 表可能不存在（2026-06-15）

**症状**：调用 `session_search` 时报错 `no such table: sessions`

**诊断方法**：
```python
import sqlite3
conn = sqlite3.connect('/home/yingming/.hermes/sessions/state.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
exists = cursor.fetchone() is not None
print(f"sessions table exists: {exists}")
```

**根因**：session_search 的数据库可能没有正确初始化，或者 sessions 表被意外删除。

**防御**：使用 session_search 前先验证表是否存在：
```python
# 验证 sessions 表
try:
    result = session_search(query='test')
    # 如果返回正常，表存在
except Exception as e:
    if 'no such table' in str(e):
        # 表不存在，需要修复
        print("sessions table missing, need to initialize")
```

**修复**：如果表不存在，需要重新创建或从备份恢复。

### 22. fact_store vs session_search 混淆陷阱

**症状**：用 `session_search` 查询知识事实，或用 `fact_store` 查询对话历史。

**根因**：两者都是 SQLite 数据库，容易混淆用途。

**正确用法**：
- `fact_store`：存储**知识事实**（环境配置、工作教训、用户偏好、工具用法）
- `session_search`：存储**对话历史**（会话内容、对话上下文、历史记录）

**判断标准**：问自己"这个信息是知识还是对话记录？"
- 知识 → `fact_store`
- 对话记录 → `session_search`

**示例**：
```python
# ✅ 正确：查询知识
fact_store(action='search', query='WSL 网络配置')

# ✅ 正确：查询对话历史
session_search(query='昨天讨论的 memory.md 写入限制')

# ❌ 错误：用 fact_store 查询对话历史
fact_store(action='search', query='昨天讨论了什么')  # fact_store 不存储对话历史

# ❌ 错误：用 session_search 查询知识
session_search(query='WSL 网络配置')  # session_search 不存储结构化知识
```

**补充**：llm-wiki 作为第三种知识存储，适合需要目录结构和文档化的场景。三者各有侧重，不要混用。

### 21. memory.md 文件写入限制调查方法

**症状**：用户提到"昨天的记忆系统更新中已经设置"，但 `fact_store` 搜索无结果。

**调查步骤**：
1. 用 `session_search` 查找昨天的对话记录
2. 搜索关键词如"memory.md 写入 限制 记忆系统 更新"
3. 如果找到相关会话，用 `session_search(session_id=..., around_message_id=...)` 查看具体内容
4. 如果 `session_search` 也找不到，检查 `~/.hermes/memories/memory/` 目录下的历史文件

**注意**：`fact_store` 存储知识事实，不存储对话历史。用户提到的"昨天的设置"可能在对话历史中，而不是在知识事实中。

### 22. MEMORY.md 文件位置确认

**症状**：不确定 MEMORY.md 文件的实际位置。

**正确位置**：
- MEMORY.md：`/home/yingming/.hermes/memories/MEMORY.md`
- USER.md：`/home/yingming/.hermes/memories/USER.md`

**错误位置**：
- ❌ `~/.hermes/MEMORY.md`（不存在）
- ❌ `~/.hermes/USER.md`（不存在）

**验证方法**：
```bash
ls -la ~/.hermes/memories/MEMORY.md
ls -la ~/.hermes/memories/USER.md
```

**教训**：不要假设文件位置，用 `ls` 或 `file` 命令验证实际路径。

### 23. 存储≠检索——诊断记忆系统必须检查两端（2026-06-15 核心教训）

**症状**：fact_store 有 76 条记录，但 100% 从未被检索过（retrieval_count 全部为 0）。

**根因**：只关注了存储侧（数据是否完整、结构是否合理），没有检查检索侧（检索是否在发生）。

**诊断公式**：
```
系统有效性 = 存储完整性 × 检索触发率 × 检索准确率 × 知识应用率
```

**诊断脚本**：
```python
import sqlite3
conn = sqlite3.connect('/home/yingming/.hermes/memory_store.db')
total = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
never_used = conn.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count=0").fetchone()[0]
avg_trust = conn.execute("SELECT AVG(trust_score) FROM facts").fetchone()[0]
print(f"Total: {total}, Never used: {never_used} ({never_used/total*100:.1f}%), Avg trust: {avg_trust:.2f}")
```

**核心洞察**：问题不是"搜索速度慢"，而是"搜索根本没有被使用"。速度优化无意义——如果功能根本没在被使用的话。

**解决方案**：创建 knowledge-retrieval 技能，实现主动检索触发器。详见 `hermes/knowledge-retrieval/SKILL.md`。

## v2.1.0 新增：主动检索模块（2026-06-15）

> 脚本：`scripts/knowledge_retrieval.py`（主模块）、`scripts/message_analyzer.py`、`scripts/knowledge_retriever.py`、`scripts/relevance_scorer.py`、`scripts/response_generator.py`、`scripts/session_tag_extractor.py`、`scripts/session_relation_finder.py`、`scripts/session_index_generator.py`、`scripts/hermes_integration.py`、`scripts/feedback_collector.py`、`scripts/learning_mechanism.py`、`scripts/prediction_mechanism.py`
> GitHub: https://github.com/yingmingyapei/memory-crystal (commit 8e99ba7)

**核心问题**：fact_store 有 76 条记录但 100% 从未被检索（retrieval_count 全部为 0）。知识存储了但从未被使用。

**用户核心需求**："无论在哪个对话中提出问题或执行操作，都能及时做出正确的反应"

**解决方案**：四层主动检索架构

```
用户消息 → 消息分析器 → 知识检索器 → 相关性评分器 → 响应生成器
              ↓              ↓              ↓              ↓
         意图/实体/关键词  fact_store     多维度评分     上下文/建议
                          session_search
                          llm-wiki
```

### 11 个组件

| 组件 | 文件 | 功能 |
|------|------|------|
| 消息分析器 | message_analyzer.py | 意图分类、实体提取、关键词提取、主题识别、同义词扩展 |
| 知识检索器 | knowledge_retriever.py | 三源检索（fact_store FTS5 + session_search + llm-wiki），支持同义词扩展 |
| 相关性评分器 | relevance_scorer.py | 关键词匹配(35%) + 实体匹配(30%) + 信任分数(15%) + 新鲜度(10%) + 检索频率(10%) |
| 响应生成器 | response_generator.py | 上下文构建、建议生成、动作生成 |
| 会话标签提取器 | session_tag_extractor.py | 自动标签（主题/情感/优先级/工具）、摘要生成、会话分类 |
| 会话关联发现器 | session_relation_finder.py | 基于标签/标题/父会话发现相关会话 |
| 会话索引生成器 | session_index_generator.py | 生成 session_index.md 和 session_log.md |
| Hermes 核心集成 | hermes_integration.py | 消息处理流程集成，自动检索+注入上下文 |
| 反馈收集器 | feedback_collector.py | 收集用户反馈，更新信任分数 |
| 学习机制 | learning_mechanism.py | 从用户行为中学习，优化检索算法 |
| 预测机制 | prediction_mechanism.py | 预测用户意图和需求，提供主动建议 |

### 使用方法

```python
import sys
from pathlib import Path
scripts_dir = Path.home() / '.hermes' / 'scripts'
sys.path.insert(0, str(scripts_dir))

from knowledge_retrieval import retrieve_for_message

# 主动检索
result = retrieve_for_message("如何配置 fact_store?")
print(result['response']['context'])      # 上下文
print(result['response']['suggestions'])  # 建议
print(result['response']['actions'])      # 动作
```

### 测试验证

- edgetunnel 搜索：秒回 ✅
- 微信收费 搜索：秒回 ✅
- 三源检索：fact_store(7条) + session_search(0条) + llm-wiki(5条) ✅
- 标签提取：准确 ✅
- 分类识别：准确 ✅

## v2.1.1 新增：搜索缓存 + 结果高亮（2026-06-15）

> 脚本：`scripts/search_cache.py`、`scripts/search_highlight.py`

**搜索缓存**（search_cache.py）：
- SQLite 缓存数据库 `~/.hermes/search_cache.db`
- 自动过期（TTL 300秒）
- 缓存大小限制（1000条）
- LRU 淘汰策略

**搜索结果高亮**（search_highlight.py）：
- 5种高亮样式：bold(`**X**`)、underline(`__X__`)、mark(`==X==`)、bracket(`【X】`)、tag(`<mark>X</mark>`)
- 片段提取：从长文本中提取包含关键词的片段
- 批量高亮支持

## v2.1.2 新增：并行搜索 + 搜索建议 + 搜索历史（2026-06-15）

> 脚本：`scripts/parallel_search.py`、`scripts/search_suggest.py`、`scripts/search_history.py`

**并行搜索**（parallel_search.py）：
- 使用 `concurrent.futures.ThreadPoolExecutor` 并行搜索三源
- 总时间 8.99ms（fact_store 5.65ms + session_search 1.05ms + llm-wiki 3.65ms）
- 超时控制（10秒）

**搜索建议**（search_suggest.py）：
- 自动补全：从 fact_store/session_search/llm-wiki 提取关键词
- 热门搜索：预定义的常见搜索词
- 相关搜索：基于部分查询匹配

**搜索历史**（search_history.py）：
- SQLite 历史数据库 `~/.hermes/search_history.db`
- 记录搜索查询、关键词、结果数、搜索时间
- 最近搜索、频繁搜索、统计信息
- 自动清理（保留30天）

### 知识检索器 v1.3 集成

knowledge_retriever.py 已集成所有优化：
```
用户消息 → 检查缓存 → 并行搜索三源 → 高亮结果 → 添加建议/历史 → 缓存结果 → 返回
```

### 性能基准

| 指标 | 值 |
|------|-----|
| 并行搜索总时间 | 8.99ms |
| fact_store 搜索 | 5.65ms |
| session_search 搜索 | 1.05ms |
| llm-wiki 搜索 | 3.65ms |
| 缓存命中 | <1ms |

## v2.1.3 新增：中文分词优化（2026-06-15）

> 脚本：`scripts/chinese_tokenizer.py`

**中文分词器**（chinese_tokenizer.py）：
- 基于词典的正向最大匹配算法
- 内置词典：技术词汇、投资词汇、AI词汇、系统词汇、动作词汇
- 同义词映射：配置→设置/设定/调整，搜索→查找/查询/检索
- 停用词过滤：中文+英文停用词
- 关键词提取：按词频排序，返回前N个

**集成到 message_analyzer.py v1.2**：
- `_extract_keywords()` 使用中文分词器
- `_expand_synonyms()` 使用同义词映射
- 分词更准确，同义词扩展更全面

## v2.1.4 新增：评分算法优化（2026-06-15）

> 脚本：`scripts/relevance_scorer.py` v1.2

**评分权重优化**：

| 维度 | 权重 | 说明 |
|------|------|------|
| keyword_match | 30% | 关键词匹配 |
| entity_match | 25% | 实体匹配 |
| trust_score | 15% | 信任分数 |
| recency | 10% | 新鲜度 |
| retrieval_count | 10% | 检索频率 |
| keyword_position | 10% | 关键词位置（越靠前权重越高） |

**新增：关键词位置权重**：
- 关键词在文本中越靠前，权重越高
- 位置分数 = max(0, 1 - avg_position / text_length)

## v2.1.5 新增：实体提取增强（2026-06-15）

> 脚本：`scripts/entity_extractor.py`

**支持 10 种实体类型**：

| 类型 | 说明 | 示例 |
|------|------|------|
| stock | 股票、基金、ETF | 600519, A股, ETF |
| tool | 工具、配置文件 | fact_store, MEMORY.md |
| file | 文件类型 | .py, .md, .json |
| platform | 社交媒体、平台 | Telegram, GitHub |
| concept | 技术概念 | LLM, Agent, RAG |
| technology | 编程语言、技术栈 | Python, Docker |
| person | 人名 | 张三, John |
| organization | 公司、组织 | OpenAI, Google |
| time | 时间、日期 | 2026-06-15, 今天 |
| location | 地点 | 北京, 硅谷 |

**集成到 message_analyzer.py v1.3**：
- `_extract_entities()` 使用实体提取器
- 实体提取更全面，支持实体关系发现

## v2.4.0 新增：搜索排序+分页+过滤+导出（2026-06-15）

> 脚本：`scripts/search_sorter.py`、`scripts/search_paginator.py`、`scripts/search_filter.py`、`scripts/search_exporter.py`
> GitHub: https://github.com/yingmingyapei/memory-crystal (commit 8e99ba7)

### 搜索结果排序（search_sorter.py）

5种排序方式：
- `relevance` — 按相关性分数排序（默认）
- `date` — 按日期排序（created_at/started_at）
- `trust` — 按信任分数排序
- `frequency` — 按检索频率排序
- `alphabetical` — 按字母顺序排序

### 搜索结果分页（search_paginator.py）

- 自动分页（默认每页10条）
- 分页元数据：当前页、总页数、总数、是否有上下页
- 支持自定义 page_size

### 搜索结果过滤（search_filter.py）

5种过滤器：
- `min_score` — 最小分数过滤
- `max_age_days` — 最大年龄过滤（天）
- `category` — 按类别过滤
- `tags` — 按标签过滤
- `source` — 按来源过滤

### 搜索结果导出（search_exporter.py）

3种导出格式：
- `json` — JSON 格式（含元数据）
- `csv` — CSV 格式（表格）
- `markdown` — Markdown 格式（可读）

### 知识检索器 v1.4 集成

knowledge_retriever.py 已集成所有优化：
```
用户消息 → 检查缓存 → 并行搜索三源 → 高亮结果 → 过滤 → 排序 → 分页 → 添加建议/历史 → 缓存结果 → 返回
```

### 完整组件列表（22个）

| 组件 | 文件 | 功能 |
|------|------|------|
| 消息分析器 | message_analyzer.py | 意图分类、实体提取、关键词提取、主题识别、同义词扩展 |
| 知识检索器 | knowledge_retriever.py | 三源检索（fact_store FTS5 + session_search + llm-wiki），支持并行搜索、缓存、高亮、过滤、排序、分页 |
| 相关性评分器 | relevance_scorer.py | 6维度评分：关键词匹配(30%) + 实体匹配(25%) + 信任分数(15%) + 新鲜度(10%) + 检索频率(10%) + 关键词位置(10%) |
| 响应生成器 | response_generator.py | 上下文构建、建议生成、动作生成 |
| 会话标签提取器 | session_tag_extractor.py | 自动标签（主题/情感/优先级/工具）、摘要生成、会话分类 |
| 会话关联发现器 | session_relation_finder.py | 基于标签/标题/父会话发现相关会话 |
| 会话索引生成器 | session_index_generator.py | 生成 session_index.md 和 session_log.md |
| Hermes 核心集成 | hermes_integration.py | 消息处理流程集成，自动检索+注入上下文 |
| 反馈收集器 | feedback_collector.py | 收集用户反馈，更新信任分数 |
| 学习机制 | learning_mechanism.py | 从用户行为中学习，优化检索算法 |
| 预测机制 | prediction_mechanism.py | 预测用户意图和需求，提供主动建议 |
| 中文分词器 | chinese_tokenizer.py | 正向最大匹配，同义词扩展，停用词过滤 |
| 实体提取器 | entity_extractor.py | 10种实体类型，实体关系发现 |
| 并行搜索 | parallel_search.py | ThreadPoolExecutor 并行搜索三源，8.99ms |
| 搜索建议 | search_suggest.py | 自动补全，热门搜索，相关搜索 |
| 搜索历史 | search_history.py | 记录/查询/统计搜索历史，自动清理30天 |
| 搜索缓存 | search_cache.py | SQLite 缓存，自动过期(TTL 300s)，LRU 淘汰 |
| 搜索高亮 | search_highlight.py | 5种高亮样式，片段提取 |
| 搜索排序 | search_sorter.py | 5种排序方式，多维度排序 |
| 搜索分页 | search_paginator.py | 自动分页，分页元数据 |
| 搜索过滤 | search_filter.py | 5种过滤器，多条件过滤 |
| 搜索导出 | search_exporter.py | JSON/CSV/Markdown 格式导出 |

### 用户偏好：继续直到完成

**用户说"继续优化，直到完成为止，不要询问我"时**：
- 执行所有优化任务
- 不要每步都询问确认
- 完成后统一汇报

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

## 知识管理系统对比：fact_store vs session_search vs llm-wiki

### 存储方式对比

| 系统 | 存储方式 | 目录结构 | 标注系统 | 检索能力 |
|------|---------|---------|---------|---------|
| fact_store | SQLite 数据库 | ❌ 无 | ✅ 有（ID、类别、标签、信任分数） | 向量相似度 + 实体探查 + 关联追踪 |
| session_search | SQLite 数据库 | ❌ 无 | ❌ 无（只有 FTS5 全文搜索） | 全文搜索（FTS5） |
| llm-wiki | 文件系统 | ✅ 有 | ✅ 有（index.md、log.md、frontmatter） | 文件系统遍历 + 全文搜索 |

### 改造方案评估（2026-06-15）

**问题**：如何用 llm-wiki 模式改进 fact_store 和 session_search 的搜索速度和用户体验？

**三种方案对比**：

| 方案 | 思路 | 工作量 | 性能 | 功能 | 推荐度 |
|------|------|--------|------|------|--------|
| **A: 混合架构** | SQLite + llm-wiki索引 | 2.5天 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **推荐** |
| B: 完全迁移 | 全部迁移到文件系统 | 1-2周 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 不推荐 |
| C: 增强SQLite | 保持现有架构 | 1-2天 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 备选 |

**推荐方案 A: 混合架构**

核心思路：保持 SQLite 作为主存储，增加 llm-wiki 风格的索引层。

**实施步骤**：

阶段 1: fact_store 索引化 (1天)
- 创建索引生成脚本：读取 fact_store 数据库，按 category 分区，生成 index.md
- 创建时间线日志：记录所有 fact 操作，生成 memory_log.md
- 集成到 cron job：每天自动更新索引

阶段 2: session_search 索引化 (1天)
- 创建会话索引生成脚本：读取 session_search 数据库，按日期/主题分区，生成 session_index.md
- 增加会话标签系统：为会话自动提取标签，存储在 sessions 表的 tags 字段
- 集成到会话结束流程：会话结束时自动更新索引

阶段 3: 交叉引用系统 (0.5天)
- 为 fact_store 增加关联：增加 related_facts 字段，自动生成关联建议
- 为 session_search 增加关联：增加 related_sessions 字段，基于内容相似度自动关联

**预期收益**：
- 搜索速度：提升 2-3 倍（索引查询 10-50ms → 5-20ms）
- 用户体验：可视化导航 + 交叉引用 + 时间线日志
- 知识网络：Obsidian 集成，图形化视图

**详细报告**：`C:\Users\yingm\wiki\systems\hermes\2026-06-15-fact-store-session-search改造评估报告.md`

### 使用场景对比

| 场景 | 推荐系统 | 原因 |
|------|---------|------|
| 查询特定事实（如 API 密钥位置） | fact_store | 结构化查询，支持实体探查 |
| 查找历史对话内容 | session_search | FTS5 全文搜索，支持对话上下文 |
| 查看知识库整体结构 | llm-wiki | 文件系统目录结构，可视化索引 |
| 跨对话知识共享 | fact_store | SQLite 数据库，跨会话持久化 |
| 回忆具体对话细节 | session_search | 包含完整对话历史和上下文 |
| 知识文档化 | llm-wiki | 文件系统，支持 Markdown 格式 |

### 目录结构对比

**fact_store**：
- 无目录结构，所有事实存储在单一 SQLite 数据库中
- 通过标签系统实现分类（如 `tags='WSL,网络,配置'`）
- 支持实体探查（`probe`）和关联推理（`reason`）

**session_search**：
- 无目录结构，所有会话存储在 SQLite 数据库中
- 只有 FTS5 全文搜索，无标注系统
- 支持会话发现（`discover`）和会话滚动（`scroll`）

**llm-wiki**：
- 文件系统目录结构（如 `/wiki/systems/hermes/`）
- 每个知识条目是独立的 Markdown 文件
- 支持 frontmatter 元数据（标题、标签、日期等）
- 有 index.md（索引）和 log.md（变更日志）

### 选择指南

1. **短期/会话级信息** → 使用 `memory` 工具
2. **长期/跨任务知识** → 使用 `fact_store`
3. **历史对话回忆** → 使用 `session_search`
4. **知识文档化** → 使用 `llm-wiki`
5. **需要目录结构和可视化索引** → 使用 `llm-wiki`
6. **需要结构化查询和推理** → 使用 `fact_store`

### 混合使用策略

```
对话A 存入 fact_store → 每天7:00 自动生成 fact_digest.md → 对话B 启动时读摘要 + search fact_store → 共享知识
```

- fact_store 作为核心知识库，存储结构化事实
- llm-wiki 作为文档化层，存储完整知识文档
- session_search 作为历史层，存储对话历史
- memory 工具作为临时层，存储会话级信息

## 参考文档

- [架构详解](references/architecture.md)
- [ASCII Logo](references/logo.txt)
- [FTS5 中文搜索修复记录](references/fts5-chinese-fix.md) — 2026-06-08 修复 search 对中文返回空的问题
- [Holographic 调试指南](references/holographic-debugging-guide.md) — 诊断脚本、修复步骤、检索流水线详解
- [Dream 记忆整合](references/dream-consolidation.md) — v2.0 四阶段整合流程（定位→采集→整合→修剪）
- [自动修剪规则](references/auto-pruning-rules.md) — v2.0 过时删除+重复合并+低信任清理
- [选择性注入](references/selective-injection.md) — v2.0 按需检索替代全量注入
- [每日摘要脚本](scripts/fact_digest.py) — 从 SQLite 生成 `~/.hermes/fact_digest.md`，cron 每天 7:00 运行
- [记忆系统诊断脚本](scripts/diagnose_memory_system.py) — 诊断 fact_store 检索率和 session_search sessions 表状态
- [知识管理系统对比](references/knowledge-system-comparison.md) — fact_store vs session_search vs llm-wiki 详细对比
- [改造方案评估](references/fact-store-session-search-evaluation.md) — 2026-06-15 基于 llm-wiki 模式的搜索加速方案评估
- [session_search 改造设计](references/session-search-redesign.md) — 2026-06-15 session_search 改造详细设计
- [记忆系统完整改造方案](references/memory-system-complete-redesign.md) — 2026-06-15 主动检索+智能匹配+知识应用
- [记忆系统主动检索模块](references/proactive-retrieval-module.md) — v2.1.0 主动检索系统架构、11个组件详解、使用方法
- [主动检索架构详解](references/proactive-retrieval-architecture.md) — v2.1.0-v2.1.5 完整18组件架构、数据流、性能基准
- [Wiki 文档](/mnt/c/Users/yingm/wiki/systems/hermes/2026-06-08-Memory-Crystal-记忆晶体系统.md)

### v2.1.2 新增脚本

- [搜索缓存](scripts/search_cache.py) — SQLite 缓存，自动过期，LRU 淘汰
- [搜索高亮](scripts/search_highlight.py) — 5种高亮样式，片段提取
- [并行搜索](scripts/parallel_search.py) — ThreadPoolExecutor 并行搜索三源，8.99ms
- [搜索建议](scripts/search_suggest.py) — 自动补全，热门搜索
- [搜索历史](scripts/search_history.py) — 记录/查询/统计搜索历史

### v2.1.3-v2.1.5 新增脚本

- [中文分词器](scripts/chinese_tokenizer.py) — 正向最大匹配，同义词扩展，停用词过滤
- [实体提取器](scripts/entity_extractor.py) — 10种实体类型，实体关系发现

### v2.4.0 新增脚本

- [搜索排序](scripts/search_sorter.py) — 5种排序方式（relevance/date/trust/frequency/alphabetical）
- [搜索分页](scripts/search_paginator.py) — 自动分页，分页元数据（当前页/总页数/总数）
- [搜索过滤](scripts/search_filter.py) — 5种过滤器（min_score/max_age/category/tags/source）
- [搜索导出](scripts/search_exporter.py) — JSON/CSV/Markdown 格式导出

### 24. 新模块必须使用 Memory Crystal 版本体系（2026-06-15）

**症状**：创建了 knowledge-retrieval 技能，版本号独立为 v1.0.0 / v1.1.0，用户指出"这套不是记忆系统吗？"

**根因**：没有将新模块纳入 Memory Crystal 品牌和版本体系。

**规则**：
- 所有记忆系统相关的新功能都属于 Memory Crystal，使用其版本号
- 不要创建独立版本体系（如 knowledge-retrieval v1.0.0）
- 版本号规则：MAJOR(架构变更).MINOR(新功能).PATCH(修复)
- 当前版本：v2.1.0（主动检索模块）

**正确做法**：
```
Memory Crystal v2.1.0 ← 新功能
knowledge-retrieval 是 v2.1.0 的模块名，不是独立产品
```

**错误做法**：
```
knowledge-retrieval v1.0.0 ← 独立版本，用户不认可
knowledge-retrieval v1.1.0 ← 仍然独立
```

### 25. session_search 数据库初始化检查（2026-06-15）

**症状**：session_search 数据库文件存在但表是空的（`SELECT name FROM sqlite_master WHERE type='table'` 返回空列表）。

**诊断**：
```python
import sqlite3
conn = sqlite3.connect('/home/yingming/.hermes/sessions/state.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables: {tables}")  # 可能为空 []
```

**修复**：使用 hermes_state.py 中的 SCHEMA_SQL 初始化：
```python
import sqlite3
conn = sqlite3.connect('/home/yingming/.hermes/sessions/state.db')
# 使用 Hermes 的 SCHEMA_SQL 创建表
conn.executescript(SCHEMA_SQL)
conn.commit()
```

**SCHEMA_SQL 关键表**：
- `schema_version` - 版本追踪
- `sessions` - 会话表（id, source, title, started_at, message_count 等）
- `messages` - 消息表（id, session_id, role, content, timestamp 等）

### 26. 三源检索策略——fact_store + session_search + llm-wiki（2026-06-15）

**用户需求**：无论在哪个对话中提出问题，都能及时做出正确的反应。

**三源检索策略**：

| 数据源 | 适用场景 | 搜索方式 | 示例 |
|--------|---------|---------|------|
| fact_store | 知识事实 | FTS5 + LIKE | "edgetunnel 是什么" |
| session_search | 对话历史 | LIKE + FTS5 | "之前讨论过 edgetunnel 吗" |
| llm-wiki | 文档知识 | index.md 匹配 | "edgetunnel 的 wiki 页面" |

**检索流程**：
1. 消息分析 → 提取关键词、实体、意图
2. 并行检索三源 → 各自返回结果
3. 相关性评分 → 多维度打分
4. 合并排序 → 去重、按分数排序
5. 生成响应 → 上下文 + 建议 + 动作

**关键点**：
- 同义词扩展提升召回率（配置→设置/设定/调整）
- FTS5 搜索失败时降级到 LIKE
- session_search 表可能不存在，需要先检查

### 27. session_search FTS5 需要手动创建（2026-06-15）

**症状**：session_search 数据库已初始化（sessions/messages 表存在），但没有 FTS5 虚拟表。

**修复**：手动创建 sessions_fts 表和触发器：
```python
import sqlite3
conn = sqlite3.connect('/home/yingming/.hermes/sessions/state.db')
conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(title, source, content=sessions, content_rowid=rowid)")
conn.execute("CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN INSERT INTO sessions_fts(rowid, title, source) VALUES (new.rowid, new.title, new.source); END")
conn.commit()
```

### 28. 优化顺序：先诊断后优化（2026-06-15 核心方法论）

**错误做法**：直接开始优化搜索速度（加索引、加缓存、加并行）

**正确做法**：
1. 先诊断系统状态（检索触发率、表是否存在、数据是否完整）
2. 找到真正的瓶颈（搜索没在用 vs 搜索慢）
3. 针对性解决（创建触发器 vs 优化性能）

**诊断脚本**：
```python
import sqlite3
# fact_store 检索率
conn = sqlite3.connect('/home/yingming/.hermes/memory_store.db')
total = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
never = conn.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count=0").fetchone()[0]
print(f"fact_store: {total} total, {never} never used ({never/total*100:.0f}%)")

# session_search 表状态
conn2 = sqlite3.connect('/home/yingming/.hermes/sessions/state.db')
tables = [r[0] for r in conn2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"session_search tables: {tables}")
```

**教训**：速度优化无意义——如果功能根本没在被使用的话。

## 口号

> **让知识结晶，让记忆永恒**  
> **Let Knowledge Crystallize, Let Memory Endure**

---

*Memory Crystal — 不是存储，是结晶。*
