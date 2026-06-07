# 记忆选择性注入

借鉴 Claude Code 的 Memory Synthesis 机制：不全量注入所有记忆，而是选择最相关的 ≤N 条注入当前会话。

## 问题：全量注入的代价

```
当前做法：fact_store(action='list') → 全部注入 system prompt
├─ 60 条事实 × 平均 100 字 = 6000 字 ≈ 8000 tokens
├─ 大部分与当前任务无关
├─ 浪费 token，增加延迟
└─ 噪音干扰模型判断
```

## Claude Code 的做法

```
1. 子 agent 读取所有记忆文件
2. 对当前查询，提取 ≤7 条最相关事实
3. 返回 JSON：{relevant_facts: [...], cited_memories: [...]}
4. 只注入这 7 条到主 agent
```

## Memory Crystal 适配方案

### 方案1：fact_store search 替代全量注入

```python
# ❌ 当前做法：全量注入
fact_store(action='list')  # 返回所有事实

# ✅ 改进：按需检索
# 从用户消息中提取关键词
keywords = extract_keywords(user_message)

# 搜索最相关的事实
relevant = fact_store(action='search', query=keywords)

# 只使用 top-5 结果
top5 = relevant[:5]
```

### 方案2：实体探查 + 关联追踪

```python
# 识别用户消息中的实体
entities = extract_entities(user_message)  # e.g., ["WSL", "cron"]

# 对每个实体探查
for entity in entities:
    facts = fact_store(action='probe', entity=entity)

# 合并去重，取 top-N
```

### 方案3：跨实体推理（最精准）

```python
# 当任务涉及多个实体的交叉时
entities = ["WSL", "cron", "网络"]
result = fact_store(action='reason', entities=entities)
# → 返回同时涉及这三个实体的事实，最精准
```

## 注入策略选择

| 场景 | 策略 | 理由 |
|------|------|------|
| 简单查询 | search(关键词) | 快速，够用 |
| 涉及特定实体 | probe(实体名) | 精准，不遗漏 |
| 多实体交叉问题 | reason([实体列表]) | 最精准，跨实体推理 |
| 新会话启动 | search(项目关键词) | 选择性注入项目上下文 |
| 定期维护 | list（全量） | 需要全局视角 |

## 注入数量建议

| 任务类型 | 建议注入数 | 理由 |
|----------|-----------|------|
| 简单问答 | ≤3 | 噪音最小 |
| 一般任务 | ≤5 | 平衡精准和覆盖 |
| 复杂分析 | ≤7 | 需要更多上下文 |
| 全量巡检 | 全部 | 需要全局视角 |

## 实施建议

### 在 Phoenix Protocol 中的应用

```python
# 健康扫描时：全量注入（需要全局视角）
fact_store(action='list')

# 修复特定问题时：按需检索
fact_store(action='search', query='[故障关键词]')
```

### 在 agent-self-evolution 中的应用

```python
# 回看会话时：搜索相关教训
fact_store(action='search', query='[会话关键词]')

# 写日报时：全量扫描
fact_store(action='list')
```

## 关键原则

1. **搜索优于全量**：除非必须全局视角，否则用 search/probe/reason
2. **top-N 优于全部**：只注入最相关的 N 条，减少噪音
3. **实体感知优于关键词**：probe 比 search 更精准
4. **推理优于检索**：reason 能发现跨实体的隐含关联
