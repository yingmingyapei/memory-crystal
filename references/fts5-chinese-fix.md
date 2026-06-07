# FTS5 中文搜索修复记录

**日期**: 2026-06-08
**状态**: 已修复（需重启 Hermes 生效）

## 问题描述

`fact_store(action='search', query='WSL')` 返回空，但 `fact_store(action='list')` 能看到包含 "WSL" 的事实。

## 根因分析

FTS5 的 `unicode61` 分词器对中英文混合文本的处理：

```
输入: "WSL网络关键事实：Gateway进程和cron job进程"
分词: ["WSL网络关键事实", "Gateway进程和cron", "job进程"]
       ^^^^^^^^^^^^^^^^
       "WSL" 和 "网络" 被合并成一个词

搜索 "WSL": 找不到单独的 "WSL" 词 → 返回空
搜索 "WSL*": 前缀匹配 "WSL网络" → 成功
搜索 "cron": 找到单独的 "cron" 词 → 成功（因为前后有空格）
```

**关键发现**：
- ✅ "cron" 搜索成功（英文单词，独立存在）
- ✅ "MiMo" 搜索成功（英文单词，独立存在）
- ✅ "WSL*" 前缀搜索成功
- ❌ "WSL" 搜索失败（被合并到 "WSL网络"）
- ❌ "网络" 搜索失败（被合并到 "WSL网络"）

## 修复方案

修改 `plugins/memory/holographic/retrieval.py` 的 `_fts_candidates` 方法：

```python
@staticmethod
def _build_fts_query(query: str) -> str:
    """Build FTS5 query with prefix matching for better Chinese support."""
    if not query:
        return ""
    
    words = query.strip().split()
    if not words:
        return ""
    
    fts_parts = []
    for word in words:
        if word:
            fts_parts.append(f"{word}*")
    
    if len(fts_parts) == 1:
        return fts_parts[0]
    else:
        return " OR ".join(fts_parts)
```

在 `_fts_candidates` 中使用：
```python
fts_query = self._build_fts_query(query)
where_clauses = ["facts_fts MATCH ?"]
params.append(fts_query)
```

## 修复后测试结果

```python
"WSL" → "WSL*": 1 条结果 ✅
"网络" → "网络*": 0 条结果 ⚠️（"网络" 被合并到 "WSL网络"，前缀匹配不到）
"cron" → "cron*": 3 条结果 ✅
"MiMo" → "MiMo*": 1 条结果 ✅
"性能" → "性能*": 1 条结果 ✅
"Memory" → "Memory*": 6 条结果 ✅
"Crystal" → "Crystal*": 4 条结果 ✅
"A股" → "A股*": 2 条结果 ✅
"热点刀锋" → "热点刀锋*": 2 条结果 ✅
```

## 已知限制

纯中文词（如"网络"）如果被合并到其他词中（如"WSL网络"），前缀匹配仍可能找不到。这种情况下用 `probe` 或 `list` 兜底。

## 涉及文件

- `plugins/memory/holographic/retrieval.py` — 添加 `_build_fts_query` 方法
- `plugins/memory/holographic/store.py` — FTS5 表定义和触发器（未修改）

## 教训

1. **先测试后文档**：创建完整文档前必须验证核心功能
2. **FTS5 中文限制**：unicode61 分词器对中英文混合文本有合并问题
3. **前缀匹配是 workaround**：不是根本解决方案，但能覆盖大部分场景
