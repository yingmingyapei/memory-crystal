# Holographic Memory 调试指南

## 系统架构

```
fact_store tool
    → HolographicMemoryProvider.handle_tool_call()
        → FactRetriever (retrieval.py) — 检索引擎
            → MemoryStore (store.py) — SQLite 存储层
                → holographic.py — HRR 向量代数（numpy）
```

数据库位置：`~/.hermes/memory_store.db`

## 快速诊断脚本

```python
import sqlite3, sys
sys.path.insert(0, "/home/yingming/.hermes/hermes-agent")

db = "/home/yingming/.hermes/memory_store.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

# 1. 基础统计
facts = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
with_hrr = conn.execute("SELECT COUNT(*) FROM facts WHERE hrr_vector IS NOT NULL").fetchone()[0]
entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
links = conn.execute("SELECT COUNT(*) FROM fact_entities").fetchone()[0]
print(f"facts={facts}, hrr_vectors={with_hrr}, entities={entities}, links={links}")

# 2. numpy 检查
from plugins.memory.holographic import holographic as hrr
print(f"numpy_available={hrr._HAS_NUMPY}")

# 3. FTS5 检查
for q in ["WSL", "网络", "cron", "MiMo", "记忆"]:
    try:
        r = conn.execute("SELECT COUNT(*) FROM facts_fts WHERE facts_fts MATCH ?", (q,)).fetchone()[0]
        print(f"  FTS5 '{q}': {r}")
    except Exception as e:
        print(f"  FTS5 '{q}': ERROR {e}")

# 4. 缺失向量的事实
missing = conn.execute("SELECT fact_id, substr(content,1,40) FROM facts WHERE hrr_vector IS NULL").fetchall()
print(f"Facts without HRR vector: {len(missing)}")
for m in missing:
    print(f"  [{m[0]}] {m[1]}")

# 5. 无实体的事实
no_ent = conn.execute("""
    SELECT f.fact_id, substr(f.content,1,40)
    FROM facts f
    LEFT JOIN fact_entities fe ON fe.fact_id = f.fact_id
    WHERE fe.entity_id IS NULL
""").fetchall()
print(f"Facts without entities: {len(no_ent)}")

# 6. Bank 计数验证
banks = conn.execute("SELECT bank_name, fact_count FROM memory_banks").fetchall()
for b in banks:
    cat = b['bank_name'].replace('cat:', '')
    actual = conn.execute("SELECT COUNT(*) FROM facts WHERE category=?", (cat,)).fetchone()[0]
    status = "OK" if b['fact_count'] == actual else f"MISMATCH (bank={b['fact_count']}, actual={actual})"
    print(f"  {b['bank_name']}: {status}")

conn.close()
```

## 常见问题修复

### 修复1: 安装 numpy

```bash
cd ~/.hermes/hermes-agent && source .venv/bin/activate
uv pip install numpy
python -c "import numpy; print(numpy.__version__)"
```

### 修复2: 回填数据

```python
import sys
sys.path.insert(0, "/home/yingming/.hermes/hermes-agent")
from plugins.memory.holographic.store import MemoryStore

store = MemoryStore(db_path="/home/yingming/.hermes/memory_store.db")
result = store.backfill_all()
print(result)
# → {'facts_processed': N, 'entities_added': M, 'vectors_computed': N, 'banks_rebuilt': K}
```

`backfill_all()` 做三件事：
1. 重新提取所有事实的实体（用新的中文正则 + 已知术语表）
2. 重新计算所有 HRR 向量（需要 numpy）
3. 重建所有 memory bank 并清理孤儿 bank

### 修复3: 清理孤立实体

```python
store._conn.execute("""
    DELETE FROM entities WHERE entity_id NOT IN (
        SELECT DISTINCT entity_id FROM fact_entities
    )
""")
store._conn.commit()
```

## 文件清单

| 文件 | 功能 |
|------|------|
| `__init__.py` | HolographicMemoryProvider — 插件入口，注册 fact_store/fact_feedback 工具 |
| `store.py` | MemoryStore — SQLite 存储层，实体提取，HRR 向量计算 |
| `retrieval.py` | FactRetriever — 检索引擎（FTS5 + LIKE + HRR + Jaccard） |
| `holographic.py` | HRR 数学库 — 相位向量的 bind/unbind/bundle/similarity |

## 检索流水线详解

### search(query)
```
query → _build_fts_query() → FTS5 MATCH (前缀通配)
  ↓ 无结果
query → _tokenize_for_like() → LIKE '%token%' (子串匹配)
  ↓ 候选集
Jaccard(query_tokens, fact_tokens) → 重排序
  ↓
relevance × trust_score → 最终分数
  ↓
返回 top-N
```

### probe(entity)
```
entity → encode_atom() → bind(entity, ROLE_ENTITY) → probe_key
  ↓
每条事实: unbind(fact_vector, probe_key) → residual
  ↓
similarity(residual, content_vector) × trust_score → 分数
  ↓
返回 top-N（HRR 代数检索，非关键词匹配）
```

### reason([entity1, entity2])
```
每个 entity → bind(entity, ROLE_ENTITY) → probe_key
  ↓
每条事实: 对每个 probe_key 做 unbind → 取 min(similarity)
  ↓
AND 语义：所有 entity 都有结构关联才高分
```

### contradict()
```
所有事实两两比较:
  entity_overlap = |ents_A ∩ ents_B| / |ents_A ∪ ents_B|  (Jaccard)
  content_similarity = HRR cosine similarity
  contradiction_score = entity_overlap × (1 - content_similarity)
  ↓
返回 contradiction_score > threshold 的事实对
```

## _KNOWN_ENTITIES 维护

`store.py` 中的 `_KNOWN_ENTITIES` 集合包含已知技术术语/专有名词。
当用户频繁提到新术语时，应添加到此集合以改善实体提取。

添加原则：
- 技术工具名（如 "vLLM", "Ollama"）
- 金融标的（如 "沪深300", "纳斯达克"）
- 平台名（如 "小红书", "抖音"）
- 不添加通用词（如 "代码", "数据"）
