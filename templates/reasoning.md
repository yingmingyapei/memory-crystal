# 推理查询模板

## 跨实体推理 (reason)

### 基本用法

```python
# 同时查询多个实体的交集
fact_store(action='reason', entities=['[实体1]', '[实体2]', '[实体3]'])
```

### 推荐组合

#### 问题诊断

```python
# 诊断 cron 超时问题
fact_store(action='reason', entities=['cron', '超时', 'WSL'])
# → 可能发现：WSL 网络是 cron 超时的根因

# 诊断 API 连接问题
fact_store(action='reason', entities=['API', '代理', '连接'])
# → 可能发现：代理配置或网络路径问题
```

#### 性能优化

```python
# 分析 MiMo 性能瓶颈
fact_store(action='reason', entities=['MiMo', '性能', 'token'])
# → 可能发现：长 token 导致响应变慢

# 分析工具并发问题
fact_store(action='reason', entities=['工具', '并发', '限制'])
# → 可能发现：并发执行的安全限制
```

#### 配置查找

```python
# 查找代理配置
fact_store(action='reason', entities=['代理', '端口', '配置'])
# → 可能发现：V2rayN SOCKS5 端口 10808

# 查找数据源配置
fact_store(action='reason', entities=['数据源', 'A股', '优先级'])
# → 可能发现：问财 > 妙想 > QVeris > 财联社
```

#### 工作流程

```python
# 查找热点刀锋流程
fact_store(action='reason', entities=['热点刀锋', '数据源', '流程'])
# → 可能发现：六阶段流程 + 5个数据源

# 查找定时任务配置
fact_store(action='reason', entities=['cron', '定时任务', '配置'])
# → 可能发现：jobs.json 存储位置 + update 命令
```

## 关联追踪 (related)

### 基本用法

```python
# 查找与某实体关联的其他实体
fact_store(action='related', entity='[实体名称]')
```

### 推荐查询

```python
# 查找与 A股 相关的所有实体
fact_store(action='related', entity='A股')
# → 可能返回：数据源、技能、分析框架、定时任务等

# 查找与 WSL 相关的所有实体
fact_store(action='related', entity='WSL')
# → 可能返回：网络、代理、cron、Gateway 等

# 查找与 Hermes 相关的所有实体
fact_store(action='related', entity='Hermes')
# → 可能返回：技能、配置、定时任务、平台等
```

## 矛盾检测 (contract)

### 基本用法

```python
# 检查是否存在矛盾的事实
fact_store(action='contract')
```

### 处理矛盾

发现矛盾后：

1. **判断哪条更准确**
   ```python
   # 查看两条矛盾的事实
   fact_store(action='search', query='[相关关键词]')
   ```

2. **更新或删除过时事实**
   ```python
   # 更新事实
   fact_store(action='update', fact_id=[id], content='[新内容]')
   
   # 或删除过时事实
   fact_store(action='remove', fact_id=[id])
   ```

3. **标记错误事实**
   ```python
   fact_feedback(action='unhelpful', fact_id=[id])
   ```

## 推理模式

### 模式 1：问题 → 根因

```python
# 问题：cron job 超时
fact_store(action='reason', entities=['cron', '超时', '网络'])
# → 根因：WSL 网络路径不同
```

### 模式 2：工具 → 限制

```python
# 工具：MiMo
fact_store(action='reason', entities=['MiMo', '限制', 'token'])
# → 限制：输入>28K tokens 时响应变慢
```

### 模式 3：配置 → 位置

```python
# 配置：代理
fact_store(action='reason', entities=['代理', '端口', '配置'])
# → 位置：V2rayN SOCKS5 10808
```

### 模式 4：流程 → 步骤

```python
# 流程：热点刀锋
fact_store(action='reason', entities=['热点刀锋', '流程', '步骤'])
# → 步骤：六阶段（环境检查→数据采集→完整性校验→数据分析→写作→推送）
```

## 最佳实践

### 推理前

1. **明确目标**：想解决什么问题？
2. **选择实体**：哪些实体相关？
3. **预期结果**：希望发现什么？

### 推理后

1. **验证结果**：是否符合预期？
2. **反馈结果**：标记有用/过时
3. **记录发现**：如果发现新知识，存储为新事实

### 实体选择技巧

| 问题类型 | 推荐实体组合 |
|---------|-------------|
| 诊断问题 | [问题现象] + [可能原因] + [环境] |
| 查找配置 | [工具名] + [配置类型] + [位置] |
| 了解流程 | [流程名] + [步骤] + [工具] |
| 性能优化 | [工具名] + [性能指标] + [限制] |

---

*推理是 Memory Crystal 的核心能力 — 通过关联产生洞察。*
