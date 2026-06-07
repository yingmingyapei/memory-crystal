---
name: memory-crystal
description: Memory Crystal 记忆晶体 — Hermes Agent 结构化记忆系统操作指南。封装 fact_store + fact_feedback 的最佳实践、常用模板、pitfalls。
version: 1.0.0
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

Memory Crystal 是 Hermes Agent 的结构化记忆系统，由两个工具构成：

| 工具 | 功能 | 类比 |
|------|------|------|
| `fact_store` | 结构化存储 + 推理 | 晶体的切面 |
| `fact_feedback` | 反馈进化 | 晶体的光泽度 |

### 与传统 Memory 的区别

| 维度 | memory 工具 | Memory Crystal |
|------|------------|----------------|
| 存储结构 | 纯文本列表 | 结构化实体（类别/标签/信任分数） |
| 检索方式 | 关键词匹配 | 关键词 + 实体探查 + 关联追踪 |
| 推理能力 | 无 | 跨实体推理 + 矛盾检测 |
| 进化机制 | 静态 | 反馈驱动（信任分数训练） |
| 适用场景 | 短期/会话级 | 长期/跨任务/知识网络 |

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

**模板**：
```python
fact_store(action='search', query='[关键词1] [关键词2]')
```

**示例**：
```python
fact_store(action='search', query='cron 超时')
fact_store(action='search', query='MiMo 性能')
```

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
- [Wiki 文档](/mnt/c/Users/yingm/wiki/systems/hermes/2026-06-08-Memory-Crystal-记忆晶体系统.md)

## 口号

> **让知识结晶，让记忆永恒**  
> **Let Knowledge Crystallize, Let Memory Endure**

---

*Memory Crystal — 不是存储，是结晶。*
