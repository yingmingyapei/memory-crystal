#!/usr/bin/env python3
"""
Hermes 核心集成模块
将主动检索功能集成到 Hermes 的消息处理流程中

功能:
- 在处理用户消息前自动检索相关知识
- 将检索结果注入到对话上下文
- 支持反馈收集和学习
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加 scripts 目录到路径
scripts_dir = Path.home() / '.hermes' / 'scripts'
sys.path.insert(0, str(scripts_dir))

from knowledge_retrieval import retrieve_for_message, get_context_for_message
from session_tag_extractor import extract_session_tags, extract_session_summary, categorize_session
from session_relation_finder import find_related_sessions, get_session_statistics


class HermesIntegration:
    """Hermes 核心集成"""
    
    def __init__(self):
        self.enabled = True
        self.max_context_length = 2000
        self.retrieval_history = []
    
    def process_user_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """处理用户消息，自动检索相关知识"""
        if not self.enabled:
            return {
                'context': '',
                'suggestions': [],
                'actions': [],
                'tags': [],
                'category': 'general'
            }
        
        try:
            # 1. 检索相关知识
            retrieval_result = retrieve_for_message(message)
            
            # 2. 提取标签
            tags = extract_session_tags(message)
            
            # 3. 分类会话
            category = categorize_session(message, tags=tags)
            
            # 4. 生成摘要
            summary = extract_session_summary(message)
            
            # 5. 查找相关会话
            related_sessions = find_related_sessions(
                session_id=session_id,
                title=message,
                tags=tags
            )
            
            # 6. 构建上下文
            context = self._build_context(retrieval_result, related_sessions)
            
            # 7. 记录检索历史
            self._record_retrieval(message, retrieval_result)
            
            return {
                'context': context,
                'suggestions': retrieval_result.get('response', {}).get('suggestions', []),
                'actions': retrieval_result.get('response', {}).get('actions', []),
                'tags': tags,
                'category': category,
                'summary': summary,
                'related_sessions': related_sessions,
                'has_relevant_knowledge': retrieval_result.get('response', {}).get('has_relevant_knowledge', False)
            }
            
        except Exception as e:
            print(f"Error processing user message: {e}")
            return {
                'context': '',
                'suggestions': [],
                'actions': [],
                'tags': [],
                'category': 'general',
                'error': str(e)
            }
    
    def _build_context(self, retrieval_result: Dict[str, Any], related_sessions: List[Dict[str, Any]]) -> str:
        """构建上下文"""
        context_parts = []
        
        # 添加检索结果上下文
        retrieval_context = retrieval_result.get('response', {}).get('context', '')
        if retrieval_context:
            context_parts.append(retrieval_context)
        
        # 添加相关会话
        if related_sessions:
            context_parts.append("\n## 相关历史会话")
            for session in related_sessions[:3]:  # 限制数量
                title = session.get('title', 'Untitled')
                similarity = session.get('similarity', 0)
                context_parts.append(f"- {title} (相似度: {similarity:.2f})")
        
        context = '\n'.join(context_parts)
        
        # 限制长度
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + '...'
        
        return context
    
    def _record_retrieval(self, message: str, result: Dict[str, Any]):
        """记录检索历史"""
        self.retrieval_history.append({
            'message': message,
            'result': result,
            'timestamp': __import__('time').time()
        })
        
        # 限制历史记录数量
        if len(self.retrieval_history) > 100:
            self.retrieval_history = self.retrieval_history[-100:]
    
    def get_retrieval_statistics(self) -> Dict[str, Any]:
        """获取检索统计信息"""
        if not self.retrieval_history:
            return {
                'total_retrievals': 0,
                'success_rate': 0,
                'average_context_length': 0
            }
        
        total = len(self.retrieval_history)
        successful = sum(1 for r in self.retrieval_history if r['result'].get('response', {}).get('has_relevant_knowledge', False))
        
        context_lengths = []
        for r in self.retrieval_history:
            context = r['result'].get('response', {}).get('context', '')
            context_lengths.append(len(context))
        
        return {
            'total_retrievals': total,
            'success_rate': successful / total if total > 0 else 0,
            'average_context_length': sum(context_lengths) / len(context_lengths) if context_lengths else 0
        }
    
    def enable(self):
        """启用主动检索"""
        self.enabled = True
    
    def disable(self):
        """禁用主动检索"""
        self.enabled = False


# 全局实例
_integration = None


def get_integration() -> HermesIntegration:
    """获取全局集成实例"""
    global _integration
    if _integration is None:
        _integration = HermesIntegration()
    return _integration


def process_user_message(message: str, session_id: str = None) -> Dict[str, Any]:
    """便捷函数：处理用户消息"""
    integration = get_integration()
    return integration.process_user_message(message, session_id)


def get_context_for_message(message: str) -> str:
    """便捷函数：获取上下文"""
    result = process_user_message(message)
    return result.get('context', '')


def get_suggestions_for_message(message: str) -> List[str]:
    """便捷函数：获取建议"""
    result = process_user_message(message)
    return result.get('suggestions', [])


def get_tags_for_message(message: str) -> List[str]:
    """便捷函数：获取标签"""
    result = process_user_message(message)
    return result.get('tags', [])


def get_category_for_message(message: str) -> str:
    """便捷函数：获取分类"""
    result = process_user_message(message)
    return result.get('category', 'general')


def get_retrieval_statistics() -> Dict[str, Any]:
    """便捷函数：获取检索统计信息"""
    integration = get_integration()
    return integration.get_retrieval_statistics()


if __name__ == '__main__':
    # 测试
    print("=== Hermes 核心集成测试 ===\n")
    
    integration = HermesIntegration()
    
    test_messages = [
        "如何配置 fact_store?",
        "帮我执行 A股复盘",
        "什么是 LLM Wiki?",
        "搜索历史会话",
        "创建一个新技能",
        "查看 MEMORY.md 配置",
        "修复 session_search 错误"
    ]
    
    for message in test_messages:
        print(f"消息: {message}")
        result = integration.process_user_message(message)
        
        print(f"  标签: {result['tags']}")
        print(f"  分类: {result['category']}")
        print(f"  摘要: {result['summary']}")
        print(f"  有相关知识: {result['has_relevant_knowledge']}")
        
        if result['context']:
            print(f"  上下文: {result['context'][:100]}...")
        
        print(f"  建议: {result['suggestions']}")
        print("-" * 50)
    
    # 获取统计信息
    stats = integration.get_retrieval_statistics()
    print(f"\n检索统计:")
    print(f"  总检索次数: {stats['total_retrievals']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  平均上下文长度: {stats['average_context_length']:.0f} 字符")
