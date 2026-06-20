#!/usr/bin/env python3
"""
knowledge_retrieve 工具
用于 Hermes 主动检索知识

工具描述:
    knowledge_retrieve: 主动检索相关知识（fact_store、session_search、llm-wiki）
    在用户提问或执行操作前，自动检索相关历史知识和会话记录。
    
    参数:
        message: 用户消息或查询内容
        
    返回:
        context: 相关知识上下文
        suggestions: 建议操作
        actions: 推荐动作
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
scripts_dir = Path.home() / '.hermes' / 'scripts'
sys.path.insert(0, str(scripts_dir))

from knowledge_retrieval import retrieve_for_message


def knowledge_retrieve(message: str) -> dict:
    """
    主动检索相关知识
    
    Args:
        message: 用户消息或查询内容
        
    Returns:
        dict: 包含上下文、建议、动作的结果
    """
    try:
        result = retrieve_for_message(message)
        
        # 提取关键信息
        response = result.get('response', {})
        analysis = result.get('analysis', {})
        results = result.get('results', {})
        
        # 构建返回结果
        return {
            'success': True,
            'context': response.get('context', ''),
            'suggestions': response.get('suggestions', []),
            'actions': response.get('actions', []),
            'has_relevant_knowledge': response.get('has_relevant_knowledge', False),
            'analysis': {
                'intent': analysis.get('intent', 'general'),
                'keywords': analysis.get('keywords', []),
                'entities': analysis.get('entities', []),
                'topic': analysis.get('topic', 'general'),
                'urgency': analysis.get('urgency', 'normal')
            },
            'results_summary': {
                'facts_count': len(results.get('facts', [])),
                'sessions_count': len(results.get('sessions', [])),
                'wiki_count': len(results.get('wiki_pages', []))
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'context': '',
            'suggestions': [],
            'actions': []
        }


if __name__ == '__main__':
    # 测试工具
    import json
    
    test_messages = [
        "如何配置 fact_store?",
        "帮我执行 A股复盘",
        "什么是 LLM Wiki?",
        "搜索历史会话"
    ]
    
    print("=== knowledge_retrieve 工具测试 ===\n")
    
    for message in test_messages:
        print(f"消息: {message}")
        result = knowledge_retrieve(message)
        
        print(f"成功: {result['success']}")
        print(f"意图: {result['analysis']['intent']}")
        print(f"关键词: {result['analysis']['keywords']}")
        print(f"主题: {result['analysis']['topic']}")
        print(f"有相关知识: {result['has_relevant_knowledge']}")
        
        if result['context']:
            print(f"上下文: {result['context'][:100]}...")
        
        print(f"建议: {result['suggestions']}")
        print(f"动作: {result['actions']}")
        
        print("-" * 50)
