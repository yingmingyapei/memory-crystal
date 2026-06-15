#!/usr/bin/env python3
"""
消息分析器 - 分析用户消息，提取关键信息
用于记忆系统主动检索

优化版本 v1.1:
- 改进中文分词算法
- 增加更多实体类型
- 优化关键词提取
- 增加同义词扩展
"""

import re
from typing import Dict, List, Any, Set


class MessageAnalyzer:
    """分析用户消息，提取关键信息"""
    
    def __init__(self):
        # 意图模式
        self.intent_patterns = {
            'question': [
                r'什么是', r'如何', r'怎么', r'为什么', r'哪里',
                r'what', r'how', r'why', r'where', r'when',
                r'？', r'\?', r'吗', r'呢', r'吧'
            ],
            'action': [
                r'执行', r'运行', r'创建', r'删除', r'修改',
                r'run', r'execute', r'create', r'delete', r'update',
                r'帮我', r'请', r'please', r'设置', r'配置',
                r'启动', r'停止', r'重启', r'部署', r'安装'
            ],
            'query': [
                r'查找', r'搜索', r'查询', r'显示', r'列出',
                r'search', r'find', r'query', r'show', r'list',
                r'查看', r'获取', r'读取', r'加载'
            ]
        }
        
        # 实体模式 - 扩展版
        self.entity_patterns = {
            'stock': [
                r'\d{6}',  # 股票代码
                r'[A-Z]{2}\d{6}',  # 带前缀的股票代码
                r'股票', r'基金', r'ETF', r'指数',
                r'A股', r'港股', r'美股', r'科创板'
            ],
            'tool': [
                r'fact_store', r'session_search', r'wiki',
                r'skill', r'cron', r'gateway', r'memory',
                r'terminal', r'browser', r'web_search',
                r'image_generate', r'send_message'
            ],
            'config': [
                r'配置', r'设置', r'config', r'setting',
                r'MEMORY.md', r'USER.md', r'\.env',
                r'config\.yaml', r'config\.json'
            ],
            'file': [
                r'\.py', r'\.js', r'\.ts', r'\.md',
                r'\.json', r'\.yaml', r'\.yml',
                r'\.sh', r'\.bash'
            ],
            'platform': [
                r'Telegram', r'Discord', r'Slack',
                r'微信', r'微博', r'头条', r'小红书',
                r'YouTube', r'Twitter', r'Reddit'
            ],
            'concept': [
                r'LLM', r'Agent', r'RAG', r'Wiki',
                r'记忆', r'知识', r'检索', r'搜索',
                r'主动检索', r'智能匹配', r'知识应用'
            ]
        }
        
        # 同义词映射
        self.synonyms = {
            '配置': ['设置', '设定', '调整'],
            '搜索': ['查找', '查询', '检索', '寻找'],
            '创建': ['新建', '建立', '生成'],
            '删除': ['移除', '清除', '去掉'],
            '修改': ['更改', '调整', '编辑'],
            '执行': ['运行', '启动', '触发'],
            '查看': ['显示', '列出', '查看'],
            'fact_store': ['事实存储', '知识库', '记忆库'],
            'session_search': ['会话搜索', '历史搜索', '对话搜索'],
            'wiki': ['知识库', '文档', '笔记']
        }
        
        # 停用词 - 扩展版
        self.stop_words = {
            # 中文停用词
            '的', '了', '在', '是', '我', '你', '他', '她', '它',
            '这', '那', '有', '和', '与', '或', '但', '而', '也',
            '就', '都', '要', '会', '能', '可以', '可能', '应该',
            '把', '被', '让', '给', '向', '从', '到', '对', '为',
            '着', '过', '地', '得', '呢', '吗', '吧', '啊', '呀',
            '哦', '嗯', '哈', '嘛', '啦', '噢', '呦',
            # 英文停用词
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us',
            'them', 'my', 'your', 'his', 'its', 'our', 'their',
            'and', 'or', 'but', 'if', 'then', 'else', 'when',
            'at', 'by', 'for', 'with', 'about', 'against',
            'between', 'through', 'during', 'before', 'after',
            'above', 'below', 'to', 'from', 'up', 'down', 'in',
            'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once'
        }
        
        # 重要关键词（不停用）
        self.important_keywords = {
            'fact_store', 'session_search', 'wiki', 'skill',
            'memory', 'config', '设置', '配置', '搜索',
            '创建', '删除', '修改', '执行', '查看'
        }
    
    def analyze(self, message: str) -> Dict[str, Any]:
        """分析用户消息"""
        result = {
            'raw_message': message,
            'intent': self._classify_intent(message),
            'entities': self._extract_entities(message),
            'keywords': self._extract_keywords(message),
            'urgency': self._assess_urgency(message),
            'topic': self._extract_topic(message),
            'synonyms': self._expand_synonyms(message)
        }
        return result
    
    def _classify_intent(self, message: str) -> str:
        """分类用户意图"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return intent
        return 'general'
    
    def _extract_entities(self, message: str) -> List[Dict[str, str]]:
        """提取实体"""
        entities = []
        seen = set()
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    # 去重
                    if match.lower() not in seen:
                        seen.add(match.lower())
                        entities.append({
                            'type': entity_type,
                            'value': match,
                            'pattern': pattern
                        })
        
        return entities
    
    def _extract_keywords(self, message: str) -> List[str]:
        """提取关键词 - 改进版"""
        # 移除标点符号
        clean = re.sub(r'[^\w\s]', ' ', message)
        
        # 分词（简单实现，按空格和中文字符分割）
        words = []
        
        # 英文单词
        english_words = re.findall(r'[a-zA-Z_]\w+', clean)
        words.extend(english_words)
        
        # 中文字符（连续的中文）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', clean)
        words.extend(chinese_chars)
        
        # 过滤停用词和短词
        keywords = []
        for w in words:
            w_lower = w.lower()
            # 保留重要关键词或长度>1的非停用词
            if w_lower in self.important_keywords or (len(w) > 1 and w_lower not in self.stop_words):
                keywords.append(w)
        
        # 去重，保持顺序
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)
        
        return unique_keywords[:15]  # 限制关键词数量
    
    def _assess_urgency(self, message: str) -> str:
        """评估紧急程度"""
        urgent_patterns = [
            r'紧急', r'立即', r'马上', r'ASAP', r'urgent',
            r'错误', r'失败', r'error', r'fail', r'bug',
            r'崩溃', r'crash', r'无法', r'不能', r'报错',
            r'异常', r'问题', r'故障', r'紧急修复'
        ]
        for pattern in urgent_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return 'high'
        return 'normal'
    
    def _extract_topic(self, message: str) -> str:
        """提取主题"""
        # 常见主题关键词
        topic_keywords = {
            '投资': ['股票', '基金', 'ETF', '投资', '市场', 'A股', '港股', '美股', '复盘', '行情'],
            '技术': ['代码', '编程', '开发', '部署', '配置', 'API', '脚本', '工具', '命令'],
            'AI': ['模型', '训练', '推理', 'LLM', 'Agent', 'RAG', 'Wiki', '记忆', '知识'],
            '内容': ['写作', '文章', '视频', '头条', '内容', '创作', '发布', '改写'],
            '系统': ['配置', '设置', '调试', '错误', '修复', '维护', '监控', '日志']
        }
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return topic
        
        return 'general'
    
    def _expand_synonyms(self, message: str) -> List[str]:
        """扩展同义词"""
        expanded = []
        
        for word, synonyms in self.synonyms.items():
            if word in message:
                expanded.extend(synonyms)
        
        return list(set(expanded))


def analyze_message(message: str) -> Dict[str, Any]:
    """便捷函数：分析用户消息"""
    analyzer = MessageAnalyzer()
    return analyzer.analyze(message)


if __name__ == '__main__':
    # 测试
    test_messages = [
        "如何配置 fact_store?",
        "帮我执行 A股复盘",
        "什么是 LLM Wiki?",
        "搜索历史会话",
        "创建一个新技能",
        "查看 MEMORY.md 配置",
        "修复 session_search 错误"
    ]
    
    print("=== 消息分析器测试 v1.1 ===\n")
    
    analyzer = MessageAnalyzer()
    
    for message in test_messages:
        print(f"消息: {message}")
        result = analyzer.analyze(message)
        
        print(f"  意图: {result['intent']}")
        print(f"  关键词: {result['keywords']}")
        print(f"  实体: {[e['value'] for e in result['entities']]}")
        print(f"  主题: {result['topic']}")
        print(f"  紧急: {result['urgency']}")
        if result['synonyms']:
            print(f"  同义词: {result['synonyms']}")
        print("-" * 50)
