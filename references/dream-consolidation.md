# Dream 记忆整合 — 四阶段流程

借鉴 Claude Code 的 Dream Memory Consolidation 机制，适配 Hermes fact_store 架构。

## 触发时机

- 每日 22:00 由 Phoenix Protocol 深度进化任务触发
- 或用户说"记忆整合"/"memory consolidation"时手动触发

## Phase 1 — 定位 (Orient)

扫描现有记忆状态，建立基线：

```python
# 1. 列出所有事实
fact_store(action='list')

# 2. 检查矛盾
fact_store(action='contradict')

# 3. 统计健康指标
# - 总事实数
# - 平均 trust_score
# - 无标签事实数
# - 超过 30 天未更新的事实数
```

## Phase 2 — 采集 (Gather)

从多个信号源提取值得持久化的信息：

| 信号源 | 优先级 | 提取方式 |
|--------|--------|---------|
| 用户纠正 | 最高 | 本轮对话中的纠正 |
| 任务失败 | 高 | cron job 错误、工具调用失败 |
| 任务成功 | 高 | 验证通过的修复、成功的工作模式 |
| 新发现 | 中 | 环境变化、API 变更、新工具 |
| session_search | 中 | 历史会话中的教训 |

**关键原则**（借鉴 Claude Code）：
> 不只记录失败，也记录成功。如果只保存纠正，会避免过去的错误，但会偏离用户已验证过的方法，变得过于谨慎。

## Phase 3 — 整合 (Consolidate)

将采集到的信号整合到 fact_store：

### 3.1 合并重复

```python
# 搜索相似事实
fact_store(action='search', query='[关键词]')

# 如果发现多条描述同一事实：
# 1. 保留最完整、最新的一条
# 2. 标记旧的为 unhelpful
fact_feedback(action='unhelpful', fact_id=[旧ID])

# 3. 如果需要，创建一条合并后的新事实
fact_store(action='add', content='[合并后的完整描述]', ...)
```

### 3.2 更新过时

```python
# 检查事实中的日期/版本/URL 是否过时
# 如果发现过时信息：
# 1. 创建更新后的事实
fact_store(action='add', content='[更新后的描述]', ...)
# 2. 标记旧事实为 unhelpful
fact_feedback(action='unhelpful', fact_id=[旧ID])
```

### 3.3 转换相对日期

Claude Code 的关键洞察：
> 将相对日期（"昨天"、"上周"）转换为绝对日期，确保时间推移后仍可解读。

```python
# ❌ 错误："昨天修复了 cron 超时问题"
# ✅ 正确："2026-06-07 修复了 cron 超时问题"
```

### 3.4 补充标签

```python
# 检查无标签的事实，补充标签
fact_store(action='update', fact_id=[ID],
           tags='[补充的标签]')
```

## Phase 4 — 修剪+索引 (Prune & Index)

### 4.1 清理低信任事实

```python
# trust_score < 0.3 且创建 >30 天 → 删除
fact_store(action='remove', fact_id=[ID])
```

### 4.2 合并近似重复

```python
# 搜索内容高度相似的事实对
fact_store(action='contradict')
# contradiction_score > 0.7 且 content_similarity > 0.6 → 合并
```

### 4.3 生成整合报告

```
📊 记忆整合报告 [日期]

Phase 1 — 定位：
- 总事实数：N
- 平均信任分数：X.XX
- 矛盾对数：M

Phase 2 — 采集：
- 新信号：K 条（来自用户纠正/任务成功/新发现）

Phase 3 — 整合：
- 合并重复：X 条
- 更新过时：X 条
- 补充标签：X 条

Phase 4 — 修剪：
- 清理低信任：X 条
- 合并近似：X 条

整合后状态：
- 总事实数：N（变化 ±X）
- 平均信任分数：X.XX（变化 ±X.XX）
```

## 安全约束

- 不删除 trust_score ≥ 0.5 的事实
- 不删除最近 7 天内被标记 helpful 的事实
- 单次最多删除 10 条事实
- 单次最多合并 5 对重复事实
- 整合报告必须保存到参考文件
