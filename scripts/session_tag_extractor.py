#!/usr/bin/env python3
"""
会话标签提取器 - 自动为会话提取标签
用于记忆系统主动检索

功能:
- 自动提取会话标签
- 支持多种标签类型
- 支持标签层级结构
"""

import re
import sqlite3
from typing import List, Dict, Any, Set
from pathlib import Path


class SessionTagExtractor:
    """会话标签提取器"""
    
    def __init__(self):
        # 标签分类法
        self.tag_taxonomy = {
            # 主题标签
            'topic': {
                '投资': ['股票', 'A股', 'ETF', '基金', '量化', '技术分析', '复盘', '行情'],
                '技术': ['Python', 'JavaScript', 'API', '数据库', '部署', '代码', '脚本', '工具'],
                'AI': ['LLM', 'Agent', 'RAG', '模型', '训练', '推理', 'Wiki', '记忆'],
                '内容': ['写作', '头条', '视频', '翻译', '创作', '发布', '改写'],
                '系统': ['配置', '调试', '优化', '监控', '日志', '错误', '修复']
            },
            
            # 情感标签
            'sentiment': {
                '问题': ['错误', '失败', 'bug', '异常', '报错', '故障'],
                '成功': ['完成', '解决', '成功', '修复', '通过'],
                '学习': ['学习', '理解', '分析', '研究', '探索']
            },
            
            # 优先级标签
            'priority': {
                '紧急': ['紧急', '立即', '马上', 'ASAP', 'urgent'],
                '重要': ['重要', '关键', '核心', '主要'],
                '普通': ['普通', '一般', '日常']
            },
            
            # 工具标签
            'tool': {
                'fact_store': ['fact_store', '知识库', '记忆库'],
                'session_search': ['session_search', '会话搜索', '历史搜索'],
                'wiki': ['wiki', 'Wiki', '知识库', '文档'],
                'skill': ['skill', '技能', '能力'],
                'cron': ['cron', '定时任务', '计划任务'],
                'gateway': ['gateway', '网关', '通道']
            }
        }
        
        # 实体模式
        self.entity_patterns = {
            'stock': [
                r'\d{6}',  # 股票代码
                r'[A-Z]{2}\d{6}',  # 带前缀的股票代码
                r'股票', r'基金', r'ETF', r'指数'
            ],
            'file': [
                r'\.py', r'\.js', r'\.ts', r'\.md',
                r'\.json', r'\.yaml', r'\.yml'
            ],
            'platform': [
                r'Telegram', r'Discord', r'Slack',
                r'微信', r'微博', r'头条', r'小红书',
                r'YouTube', r'Twitter', r'Reddit'
            ]
        }
    
    def extract_tags(self, title: str, content: str = "") -> List[str]:
        """提取会话标签"""
        tags = set()
        
        # 合并标题和内容
        text = f"{title} {content}".lower()
        
        # 1. 基于分类法提取标签
        for category, tag_groups in self.tag_taxonomy.items():
            for tag, keywords in tag_groups.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        tags.add(tag)
                        break
        
        # 2. 提取实体标签
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches[:2]:  # 限制每种实体类型最多2个
                    tags.add(f'{entity_type}:{match}')
        
        # 3. 提取工具调用标签
        tool_patterns = [
            r'"name":\s*"(\w+)"',
            r'function\.(\w+)',
            r'tool:(\w+)'
        ]
        for pattern in tool_patterns:
            matches = re.findall(pattern, content)
            for match in matches[:3]:  # 限制最多3个工具
                tags.add(f'tool:{match}')
        
        # 4. 限制标签数量
        tag_list = list(tags)[:10]  # 最多10个标签
        
        return tag_list
    
    def extract_summary(self, title: str, content: str = "", max_length: int = 200) -> str:
        """生成会话摘要"""
        # 优先使用标题
        if title and len(title) > 10:
            return title[:max_length]
        
        # 使用内容的前N个字符
        if content:
            if len(content) <= max_length:
                return content
            
            # 尝试在句号处截断
            truncated = content[:max_length]
            last_period = truncated.rfind('。')
            if last_period > max_length * 0.5:
                return truncated[:last_period + 1]
            
            return truncated + '...'
        
        return title or "Untitled"
    
    def categorize_session(self, title: str, content: str = "", tags: List[str] = None) -> str:
        """分类会话"""
        text = f"{title} {content}".lower()
        
        # 优先级: 投资 > 技术 > AI > 内容 > 系统 > 其他
        category_priority = ['投资', '技术', 'AI', '内容', '系统']
        
        # 基于标签分类
        if tags:
            for category in category_priority:
                if category in tags:
                    return category
        
        # 基于内容关键词判断
        category_keywords = {
            '投资': ['股票', 'A股', 'ETF', '基金', '投资', '市场', '复盘'],
            '技术': ['代码', 'API', '数据库', '部署', '脚本', '工具', '命令'],
            'AI': ['LLM', 'Agent', '模型', '训练', '推理', 'Wiki', '记忆'],
            '内容': ['写作', '文章', '视频', '头条', '内容', '创作'],
            '系统': ['配置', '调试', '错误', '修复', '维护', '监控']
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'general'


def extract_session_tags(title: str, content: str = "") -> List[str]:
    """便捷函数：提取会话标签"""
    extractor = SessionTagExtractor()
    return extractor.extract_tags(title, content)


def extract_session_summary(title: str, content: str = "", max_length: int = 200) -> str:
    """便捷函数：生成会话摘要"""
    extractor = SessionTagExtractor()
    return extractor.extract_summary(title, content, max_length)


def categorize_session(title: str, content: str = "", tags: List[str] = None) -> str:
    """便捷函数：分类会话"""
    extractor = SessionTagExtractor()
    return extractor.categorize_session(title, content, tags)


if __name__ == '__main__':
    # 测试
    test_sessions = [
        ("如何配置 fact_store?", ""),
        ("帮我执行 A股复盘", "今天A股市场表现不错，新能源板块涨幅居前"),
        ("什么是 LLM Wiki?", "LLM Wiki 是一种知识管理方法"),
        ("搜索历史会话", ""),
        ("创建一个新技能", "需要创建一个用于视频下载的技能"),
        ("查看 MEMORY.md 配置", "MEMORY.md 文件在哪里"),
        ("修复 session_search 错误", "session_search 数据库表不存在")
    ]
    
    print("=== 会话标签提取器测试 ===\n")
    
    extractor = SessionTagExtractor()
    
    for title, content in test_sessions:
        print(f"会话: {title}")
        
        tags = extractor.extract_tags(title, content)
        summary = extractor.extract_summary(title, content)
        category = extractor.categorize_session(title, content, tags)
        
        print(f"  标签: {tags}")
        print(f"  摘要: {summary}")
        print(f"  分类: {category}")
        print("-" * 50)
