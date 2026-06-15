---
name: knowledge-retrieval
description: "Memory Crystal v2.1.0 主动检索模块 - 在用户提问或执行操作前，自动检索相关历史知识和会话记录"
version: 2.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [memory, retrieval, knowledge, fact-store, session-search, wiki, memory-crystal]
    category: hermes
    related_skills: [memory-crystal, llm-wiki, self-improvement]
---

# 记忆系统主动检索

在用户提问或执行操作前，自动检索相关历史知识和会话记录。

## 触发条件

使用此技能当：
- 用户提出问题时
- 用户要求执行操作时
- 需要查找历史知识时
- 需要查找历史会话时

## 核心功能

### 1. 消息分析
- 意图分类（question/action/query/general）
- 实体提取（股票/工具/配置）
- 关键词提取
- 紧急程度评估
- 主题识别

### 2. 知识检索
- fact_store 检索（结构化知识）
- session_search 检索（会话历史）
- llm-wiki 检索（可视化知识库）

### 3. 相关性评分
- 关键词匹配评分
- 实体匹配评分
- 信任分数评分
- 新鲜度评分

### 4. 响应生成
- 上下文构建
- 建议生成
- 动作生成

## 使用方法

### 方法 1: 直接调用工具

```python
import sys
from pathlib import Path

# 添加 scripts 目录到路径
scripts_dir = Path.home() / '.hermes' / 'scripts'
sys.path.insert(0, str(scripts_dir))

from knowledge_retrieval import retrieve_for_message

# 检索相关知识
result = retrieve_for_message("如何配置 fact_store?")

# 获取上下文
context = result['response']['context']

# 获取建议
suggestions = result['response']['suggestions']

# 获取动作
actions = result['response']['actions']
```

### 方法 2: 使用便捷函数

```python
import sys
from pathlib import Path

scripts_dir = Path.home() / '.hermes' / 'scripts'
sys.path.insert(0, str(scripts_dir))

from knowledge_retrieval import get_context_for_message, get_suggestions_for_message

# 只获取上下文
context = get_context_for_message("如何配置 fact_store?")

# 只获取建议
suggestions = get_suggestions_for_message("如何配置 fact_store?")
```

### 方法 3: 使用工具脚本

```bash
cd ~/.hermes/scripts
python3 knowledge_retrieve_tool.py
```

## 集成到工作流

### 在处理用户消息前调用

```python
# 1. 分析用户消息
analysis = analyze_message(user_message)

# 2. 检索相关知识
results = retrieve_knowledge(analysis)

# 3. 评分
scored_results = score_results(analysis, results)

# 4. 生成响应
response = generate_response(analysis, scored_results)

# 5. 使用上下文
if response['has_relevant_knowledge']:
    # 将上下文注入到对话中
    inject_context(response['context'])
```

## 文件位置

- 主模块: `~/.hermes/scripts/knowledge_retrieval.py`
- 消息分析器: `~/.hermes/scripts/message_analyzer.py`
- 知识检索器: `~/.hermes/scripts/knowledge_retriever.py`
- 相关性评分器: `~/.hermes/scripts/relevance_scorer.py`
- 响应生成器: `~/.hermes/scripts/response_generator.py`
- 工具脚本: `~/.hermes/scripts/knowledge_retrieve_tool.py`
- 会话标签提取器: `~/.hermes/scripts/session_tag_extractor.py`
- 会话关联发现器: `~/.hermes/scripts/session_relation_finder.py`
- 会话索引生成器: `~/.hermes/scripts/session_index_generator.py`
- Hermes 核心集成: `~/.hermes/scripts/hermes_integration.py`
- 反馈收集器: `~/.hermes/scripts/feedback_collector.py`
- 学习机制: `~/.hermes/scripts/learning_mechanism.py`
- 预测机制: `~/.hermes/scripts/prediction_mechanism.py`

## 数据源

### fact_store
- 路径: `~/.hermes/memory_store.db`
- 内容: 结构化知识（76 条记录）
- 搜索: FTS5 全文搜索

### session_search
- 路径: `~/.hermes/sessions/state.db`
- 内容: 会话历史
- 搜索: 标题匹配

### llm-wiki
- 路径: `/mnt/c/Users/yingm/wiki/`
- 内容: 可视化知识库（83 个页面）
- 搜索: index.md 匹配

## 测试

```bash
cd ~/.hermes/scripts
python3 knowledge_retrieval.py
```

## Pitfalls

### 1. 数据库不存在
**问题**: fact_store 或 session_search 数据库不存在  
**解决**: 检查数据库文件是否存在，不存在则创建

### 2. 表不存在
**问题**: sessions 表不存在  
**解决**: 运行初始化脚本创建表

### 3. 检索结果为空
**问题**: 没有找到相关知识  
**解决**: 检查关键词是否正确，尝试不同的搜索词

### 4. 性能问题
**问题**: 检索速度慢  
**解决**: 限制检索范围（最近 100 个会话，前 10 条知识）

### 5. 知识存储了但从未被检索（2026-06-15 诊断发现）
**问题**: fact_store 有 76 条记录，但 retrieval_count 全部为 0 — 100% 从未被检索过  
**根因**: 没有主动检索触发器，用户提问时不会自动搜索相关知识  
**诊断方法**: 
```python
import sqlite3
conn = sqlite3.connect('~/.hermes/memory_store.db')
cursor = conn.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count=0")
never_used = cursor.fetchone()[0]
print(f"从未检索: {never_used}")
```
**防御**: 
- 定期检查 retrieval_count 分布，在 cron job 中加入健康检查
- 如果大量记录 retrieval_count=0，说明检索触发器未生效
- 搜索速度优化无意义 — 如果根本没在搜索的话

### 6. 评估记忆系统不能只看存储侧（2026-06-15 用户纠正）
**问题**: 评估报告只关注了"搜索速度"，忽略了"搜索是否在发生"  
**用户原话**: "我要求的效果是无论我在哪个对话中提出问题或者是要求执行哪项操作，你都能及时做出正确的反应"  
**教训**: 评估任何知识/记忆系统时，必须同时检查：
1. **存储侧**: 数据是否完整、结构是否合理
2. **检索侧**: 检索是否在发生、触发率是多少
3. **应用侧**: 检索到的知识是否被正确应用
4. **反馈侧**: 用户反馈是否在优化系统

**正确评估框架**:
```
存储完整性 × 检索触发率 × 检索准确率 × 知识应用率 = 系统有效性
```

## 维护

### 更新检索计数
每次检索后，fact_store 的 retrieval_count 会自动更新。

### 清理旧数据
定期清理旧的会话数据和过时的知识。

### 优化评分算法
根据用户反馈优化相关性评分算法。
