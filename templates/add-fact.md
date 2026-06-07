# 添加事实模板

## 基本模板

```python
fact_store(
    action='add',
    content='[具体事实描述，包含条件、根因、解决方案]',
    category='[category]',
    tags='[tag1],[tag2],[tag3]'
)
```

## 按类别分类

### 用户偏好 (user_pref)

```python
fact_store(
    action='add',
    content='用户对自动化失败容忍度很低。失败 2 次后必须报告并提供替代方案。',
    category='user_pref',
    tags='automation,tolerance,preference'
)
```

### 项目相关 (project)

```python
fact_store(
    action='add',
    content='Memory Crystal 记忆晶体系统命名于 2026-06-08，由 fact_store + fact_feedback 构成。',
    category='project',
    tags='memory-crystal,naming,hermes'
)
```

### 工具/技术 (tool)

```python
fact_store(
    action='add',
    content='MiMo 输入超过 28K tokens 时 API 响应显著变慢。根因：服务器容量有限，KV-cache 处理能力不足。缓解：context_length=50000, compression.threshold=0.25。',
    category='tool',
    tags='mimo,xiaomi,performance,bottleneck'
)
```

### 通用知识 (general)

```python
fact_store(
    action='add',
    content='WSL 网络关键事实：Gateway 进程和 cron job 进程走不同网络路径。海外服务必须走代理 127.0.0.1:10808。cron job 超时 40% 根因是 WSL 网络。',
    category='general',
    tags='wsl,network,proxy,cron'
)
```

## 按场景分类

### 踩坑教训

```python
fact_store(
    action='add',
    content='[错误现象]。根因：[根因分析]。解决方案：[具体方案]。教训：[预防措施]。',
    category='general',
    tags='[工具名],lesson,[错误类型]'
)
```

### 环境配置

```python
fact_store(
    action='add',
    content='[配置项] = [值]。用途：[用途说明]。位置：[配置文件路径]。',
    category='tool',
    tags='[工具名],config,[配置类型]'
)
```

### 工作流程

```python
fact_store(
    action='add',
    content='[流程名称]：步骤1 → 步骤2 → 步骤3。关键点：[注意事项]。',
    category='general',
    tags='[领域],workflow,[流程类型]'
)
```

## 质量检查清单

存储前检查：

- [ ] 是否包含具体条件？（"输入超过 28K tokens"）
- [ ] 是否包含根因分析？（"服务器容量有限"）
- [ ] 是否包含解决方案？（"context_length=50000"）
- [ ] 是否设置了标签？（"mimo,performance"）
- [ ] 是否选择了正确的类别？
- [ ] 是否是长期有效的知识？（不是临时状态）
