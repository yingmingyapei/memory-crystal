#!/usr/bin/env python3
"""
响应生成器 - 基于检索结果生成响应
用于记忆系统主动检索
"""

from typing import Dict, Any, List


class ResponseGenerator:
    """基于检索结果生成响应"""
    
    def __init__(self):
        self.max_context_length = 2000  # 最大上下文长度
    
    def generate(self, analysis: Dict[str, Any], scored_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成响应"""
        # 构建上下文
        context = self._build_context(analysis, scored_results)
        
        # 生成建议
        suggestions = self._generate_suggestions(analysis, scored_results)
        
        # 生成动作
        actions = self._generate_actions(analysis, scored_results)
        
        response = {
            'context': context,
            'suggestions': suggestions,
            'actions': actions,
            'has_relevant_knowledge': bool(context)
        }
        
        return response
    
    def _build_context(self, analysis: Dict[str, Any], scored_results: Dict[str, Any]) -> str:
        """构建上下文"""
        context_parts = []
        
        # 添加 fact_store 结果
        facts = scored_results.get('facts', [])
        if facts:
            context_parts.append("## 相关知识")
            for fact in facts[:3]:  # 限制数量
                content = fact['content'][:100]
                if len(fact['content']) > 100:
                    content += '...'
                context_parts.append(f"- {content}")
        
        # 添加 session_search 结果
        sessions = scored_results.get('sessions', [])
        if sessions:
            context_parts.append("\n## 相关历史会话")
            for session in sessions[:2]:  # 限制数量
                title = session.get('title', 'Untitled')
                context_parts.append(f"- {title}")
        
        # 添加 wiki 结果
        wiki_pages = scored_results.get('wiki_pages', [])
        if wiki_pages:
            context_parts.append("\n## 相关 Wiki 页面")
            for page in wiki_pages[:2]:  # 限制数量
                page_name = page.get('page_name', '')
                summary = page.get('summary', '')
                context_parts.append(f"- [[{page_name}]] - {summary}")
        
        context = '\n'.join(context_parts)
        
        # 限制长度
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + '...'
        
        return context
    
    def _generate_suggestions(self, analysis: Dict[str, Any], scored_results: Dict[str, Any]) -> List[str]:
        """生成建议"""
        suggestions = []
        
        intent = analysis.get('intent', 'general')
        
        if intent == 'question':
            suggestions.append("基于历史知识回答问题")
            suggestions.append("提供相关 Wiki 页面链接")
        elif intent == 'action':
            suggestions.append("检查是否有相关技能")
            suggestions.append("查看历史会话中的类似操作")
        elif intent == 'query':
            suggestions.append("搜索 fact_store")
            suggestions.append("搜索 session_search")
            suggestions.append("搜索 llm-wiki")
        
        return suggestions
    
    def _generate_actions(self, analysis: Dict[str, Any], scored_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成动作"""
        actions = []
        
        # 基于检索结果生成动作
        facts = scored_results.get('facts', [])
        if facts:
            actions.append({
                'type': 'inject_context',
                'content': facts[0]['content'][:200],
                'source': 'fact_store'
            })
        
        sessions = scored_results.get('sessions', [])
        if sessions:
            actions.append({
                'type': 'suggest_session',
                'session_id': sessions[0].get('session_id', ''),
                'title': sessions[0].get('title', '')
            })
        
        wiki_pages = scored_results.get('wiki_pages', [])
        if wiki_pages:
            actions.append({
                'type': 'suggest_wiki',
                'page_name': wiki_pages[0].get('page_name', ''),
                'path': wiki_pages[0].get('path', '')
            })
        
        return actions


def generate_response(analysis: Dict[str, Any], scored_results: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：生成响应"""
    generator = ResponseGenerator()
    return generator.generate(analysis, scored_results)
