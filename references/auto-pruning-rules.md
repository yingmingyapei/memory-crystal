# 自动记忆修剪规则

借鉴 Claude Code 的 Dream Memory Pruning 机制，定义 Memory Crystal 的自动修剪策略。

## 修剪触发条件

| 条件 | 动作 | 安全等级 |
|------|------|---------|
| trust_score < 0.3 且创建 >30 天 | 删除 | 安全 |
| trust_score < 0.2 且创建 >7 天 | 删除 | 安全 |
| 两条事实 content_similarity > 0.8 | 合并（保留较新的） | 安全 |
| 两条事实 contradiction_score > 0.7 | 标记矛盾，人工确认 | 保守 |
| 事实内容 < 10 字且 trust_score < 0.5 | 增强或删除 | 保守 |

## 修剪规则详解

### Rule 1: 过时事实清理

```python
# 诊断
fact_store(action='list')
# 筛选：trust_score < 0.3 且 created_at > 30 天前

# 修复
fact_feedback(action='unhelpful', fact_id=[ID])  # 先标记
fact_store(action='remove', fact_id=[ID])        # 再删除
```

**例外**：
- 被标记 helpful 且 trust_score ≥ 0.5 的事实永不自动删除
- 最近 7 天内创建的事实不参与修剪
- 用户明确说"记住这个"的事实不参与修剪

### Rule 2: 重复合并

```python
# 诊断
fact_store(action='contradict')
# 筛选：content_similarity > 0.8 的事实对

# 修复
# 1. 保留内容更完整、更新的一条
# 2. 将另一条的关键信息合并到保留条目（如果需要）
# 3. 删除冗余条目
fact_store(action='remove', fact_id=[冗余ID])
```

### Rule 3: 近似去重

```python
# 诊断
fact_store(action='search', query='[关键词]')
# 检查返回结果中是否有描述同一事物但措辞不同的条目

# 修复
# 1. 创建一条综合性的新事实
fact_store(action='add', content='[综合描述]', ...)
# 2. 删除旧的近似条目
fact_feedback(action='unhelpful', fact_id=[旧ID1])
fact_feedback(action='unhelpful', fact_id=[旧ID2])
```

### Rule 4: 低质量增强

```python
# 诊断：内容过于笼统（<10字）
fact_store(action='list')
# 筛选：content 长度 < 10 且 trust_score < 0.5

# 修复选项
# A. 如果能补充细节 → 更新事实
fact_store(action='update', fact_id=[ID],
           content='[补充条件/根因/解决方案后的完整描述]')

# B. 如果无法补充 → 删除
fact_store(action='remove', fact_id=[ID])
```

### Rule 5: 成功模式强化

```python
# 诊断：被多次标记 helpful 的事实
# 筛选：helpful_count ≥ 3

# 修复：提升信任分数，确保不被误删
fact_feedback(action='helpful', fact_id=[ID])
```

## 修剪安全矩阵

| 操作 | trust ≥ 0.5 | trust 0.3-0.5 | trust < 0.3 |
|------|-------------|---------------|-------------|
| 创建 <7 天 | 🚫 不动 | 🚫 不动 | 🚫 不动 |
| 创建 7-30 天 | 🚫 不动 | ⚠️ 检查 | ✅ 可删 |
| 创建 >30 天 | 🚫 不动 | ✅ 可删 | ✅ 可删 |
| helpful_count ≥ 3 | 🚫 永不动 | 🚫 不动 | ⚠️ 检查 |

## 修剪报告格式

```
🧹 记忆修剪报告 [日期]

扫描：N 条事实
删除：X 条（过时/低信任）
合并：X 对（重复/近似）
增强：X 条（低质量→补充）
保留：X 条（仍然有效）

详情：
- fact_id=XX: "内容摘要..." → 删除（trust=0.2, 创建45天）
- fact_id=YY + fact_id=ZZ: 近似重复 → 合并为 fact_id=YY
```
