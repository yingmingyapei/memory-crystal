# Memory Crystal 记忆晶体 v1.2.0

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║              ✦  M E M O R Y   C R Y S T A L  ✦               ║
    ║                     ─── 记 忆 晶 体 ───                       ║
    ║                         .  *  .                               ║
    ║                        . /|\\ .                                ║
    ║                       . / | \\ .                               ║
    ║                      . /  |  \\ .                              ║
    ║                     ◆─────◆─────◆                             ║
    ║                    /|    /|\\    |\\                             ║
    ║                   / |   / | \\   | \\                            ║
    ║                  /  |  /  |  \\  |  \\                           ║
    ║                 /   | /   |   \\ |   \\                          ║
    ║                ◆────◆────◆────◆────◆                          ║
    ║                 \\   | \\   |   / |   /                          ║
    ║                  \\  |  \\  |  /  |  /                           ║
    ║                   \\ |   \\ | /   | /                            ║
    ║                    \\|    \\|/    |/                             ║
    ║                     ◆─────◆─────◆                             ║
    ║          "让知识结晶，让记忆永恒"                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

**Memory Crystal** 是 Hermes Agent 的新一代结构化记忆系统，由 `fact_store` 和 `fact_feedback` 两个工具构成。

> **让知识结晶，让记忆永恒**  
> **Let Knowledge Crystallize, Let Memory Endure**

## 核心特性

- **结构化存储**：每条事实包含类别、标签、信任分数
- **实体探查**：查询某个实体的所有相关事实
- **关联追踪**：发现实体间的隐藏关联
- **跨实体推理**：多实体交集查询
- **矛盾检测**：自动发现知识冲突
- **反馈进化**：用得越多越准（信任分数训练）
- **HRR 向量**：1024 维相位向量支持语义检索（需 numpy）

## v1.2.0 新增特性

- **Dream 记忆整合**：四阶段整合流程（定位→采集→整合→修剪），定期清理过时/重复事实
- **自动记忆修剪**：过时删除（trust<0.3, >30天）+ 重复合并（similarity>0.8）+ 安全矩阵保护
- **成功反馈 + 双向记录**：不只记录失败教训，也记录成功模式（verified-fix / success-pattern）
- **记忆选择性注入**：search/probe/reason 按需检索替代全量 list 注入，节省 token

## 与传统 Memory 的区别

| 维度 | 传统 Memory | Memory Crystal |
|------|------------|----------------|
| 存储结构 | 纯文本列表 | 结构化实体（类别/标签/信任分数） |
| 检索方式 | 关键词匹配 | 向量相似度 + 实体探查 + 关联追踪 |
| 推理能力 | 无 | 跨实体推理 + 矛盾检测 |
| 进化机制 | 静态 | 反馈驱动 + Dream 整合 + 自动修剪 |
| 适用场景 | 短期/会话级 | 长期/跨任务/知识网络 |

## 快速开始

### 添加事实

```python
fact_store(
    action='add',
    content='MiMo 输入超过 28K tokens 时 API 响应显著变慢',
    category='tool',
    tags='mimo,xiaomi,performance'
)
```

### 查询事实

```python
# 关键词搜索（按需检索，推荐）
fact_store(action='search', query='MiMo 性能')

# 实体探查（精准查询某实体的所有事实）
fact_store(action='probe', entity='MiMo')

# 跨实体推理（多实体交集）
fact_store(action='reason', entities=['MiMo', '性能', 'cron'])
```

### 反馈进化

```python
# 标记有用（trust_score +0.1）
fact_feedback(action='helpful', fact_id=41)

# 标记过时（trust_score -0.1）
fact_feedback(action='unhelpful', fact_id=7)
```

## 文档

- [SKILL.md](SKILL.md) — 完整操作指南（v1.2.0）
- [架构详解](references/architecture.md) — 系统架构和数据模型
- [Dream 记忆整合](references/dream-consolidation.md) — 四阶段整合流程
- [自动修剪规则](references/auto-pruning-rules.md) — 过时删除+重复合并+安全矩阵
- [选择性注入](references/selective-injection.md) — 按需检索替代全量注入
- [FTS5 中文修复](references/fts5-chinese-fix.md) — 中文搜索问题修复记录
- [HRR 调试指南](references/holographic-debugging-guide.md) — 向量系统调试

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-06-08 | 初始发布：SKILL.md + 模板 |
| v1.1.0 | 2026-06-08 | +FTS5 中文修复 + HRR 调试指南 + 12 条 pitfalls |
| v1.2.0 | 2026-06-08 | +Dream 整合 + 自动修剪 + 成功反馈 + 选择性注入 |

## 作为 Hermes Skill 安装

```bash
# 从 GitHub 安装
hermes skill install github.com/yingmingyapei/memory-crystal

# 或手动复制
cp -r memory-crystal ~/.hermes/skills/hermes/
```

## 许可证

MIT License

---

*Memory Crystal — 不是存储，是结晶。*
