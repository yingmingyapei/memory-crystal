# 实体探查模板

## 基本用法

```python
# 查询某个实体的所有相关事实
fact_store(action='probe', entity='[实体名称]')
```

## 常用实体

### 工具/技术

```python
fact_store(action='probe', entity='MiMo')
# → 返回所有提到 MiMo 的事实（性能、配置、限制等）

fact_store(action='probe', entity='opencli')
# → 返回所有提到 opencli 的事实（命令、daemon、浏览器等）

fact_store(action='probe', entity='WSL')
# → 返回所有提到 WSL 的事实（网络、代理、配置等）
```

### 系统/服务

```python
fact_store(action='probe', entity='cron')
# → 返回所有提到 cron 的事实（定时任务、超时、配置等）

fact_store(action='probe', entity='Gateway')
# → 返回所有提到 Gateway 的事实（平台、配置、故障等）

fact_store(action='probe', entity='Telegram')
# → 返回所有提到 Telegram 的事实（Bot、群组、配置等）
```

### 领域/主题

```python
fact_store(action='probe', entity='A股')
# → 返回所有提到 A股 的事实（数据源、分析框架、技能等）

fact_store(action='probe', entity='热点刀锋')
# → 返回所有提到热点刀锋的事实（版本、数据源、教训等）
```

## 实体命名规范

### 推荐命名

| 类型 | 示例 | 说明 |
|------|------|------|
| 工具名 | MiMo, opencli, curl_cffi | 保持原名 |
| 系统名 | WSL, Gateway, Telegram | 首字母大写 |
| 服务名 | cron, proxy, daemon | 小写 |
| 领域名 | A股, 热点刀锋, Memory Crystal | 保持原名 |

### 避免的命名

| ❌ 错误 | ✅ 正确 | 原因 |
|--------|--------|------|
| mimo | MiMo | 保持官方大小写 |
| wsl | WSL | 保持缩写大写 |
| cron job | cron | 保持核心词 |

## 结果解读

probe 返回的结果包含：

```python
{
    "facts": [
        {
            "fact_id": 41,
            "content": "MiMo 输入超过 28K tokens 时 API 响应显著变慢...",
            "category": "tool",
            "tags": "mimo,xiaomi,performance,bottleneck",
            "trust_score": 0.5,
            "retrieval_count": 5,
            "helpful_count": 2,
            "created_at": "2026-06-07 17:32:24",
            "updated_at": "2026-06-07 17:32:24"
        }
    ],
    "count": 1
}
```

**关键字段**：
- `content`: 事实内容
- `trust_score`: 信任分数（越高越可靠）
- `retrieval_count`: 被检索次数（高频 = 常用）
- `helpful_count`: 被标记有用次数

## 后续操作

探查后，可以：

1. **反馈**：标记事实有用/过时
   ```python
   fact_feedback(action='helpful', fact_id=41)
   ```

2. **关联查询**：查找相关实体
   ```python
   fact_store(action='related', entity='MiMo')
   ```

3. **推理查询**：跨实体推理
   ```python
   fact_store(action='reason', entities=['MiMo', '性能', 'cron'])
   ```
