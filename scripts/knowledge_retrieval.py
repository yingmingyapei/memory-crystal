#!/usr/bin/env python3
"""
记忆系统主动检索模块
整合消息分析、知识检索、相关性评分、响应生成

使用方法:
    from knowledge_retrieval import retrieve_for_message
    
    result = retrieve_for_message("如何配置 fact_store?")
    print(result['context'])
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
scripts_dir = Path.home() / '.hermes' / 'scripts'
sys.path.insert(0, str(scripts_dir))

from message_analyzer import MessageAnalyzer, analyze_message
from knowledge_retriever import KnowledgeRetriever, retrieve_knowledge
from relevance_scorer import RelevanceScorer, score_results
from response_generator import ResponseGenerator, generate_response


class KnowledgeRetrieval:
    """记忆系统主动检索"""
    
    def __init__(self):
        self.analyzer = MessageAnalyzer()
        self.retriever = KnowledgeRetriever()
        self.scorer = RelevanceScorer()
        self.generator = ResponseGenerator()
    
    def retrieve(self, message: str) -> dict:
        """主动检索：分析消息 -> 检索知识 -> 评分 -> 生成响应"""
        # 1. 分析消息
        analysis = self.analyzer.analyze(message)
        
        # 2. 检索知识
        results = self.retriever.retrieve(analysis)
        
        # 3. 评分
        scored_results = self.scorer.score(analysis, results)
        
        # 4. 生成响应
        response = self.generator.generate(analysis, scored_results)
        
        # 5. 更新检索计数
        self._update_retrieval_counts(scored_results.get('facts', []))
        
        return {
            'analysis': analysis,
            'results': results,
            'scored_results': scored_results,
            'response': response
        }
    
    def _update_retrieval_counts(self, facts: list):
        """更新 fact_store 的检索计数"""
        try:
            import sqlite3
            fact_store_path = Path.home() / '.hermes' / 'memory_store.db'
            
            if not fact_store_path.exists():
                return
            
            conn = sqlite3.connect(str(fact_store_path))
            
            for fact in facts:
                if fact.get('id'):
                    conn.execute("""
                        UPDATE facts 
                        SET retrieval_count = retrieval_count + 1
                        WHERE fact_id = ?
                    """, (fact['id'],))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating retrieval counts: {e}")


def retrieve_for_message(message: str) -> dict:
    """便捷函数：为主动检索设计"""
    retrieval = KnowledgeRetrieval()
    return retrieval.retrieve(message)


def get_context_for_message(message: str) -> str:
    """便捷函数：只获取上下文"""
    result = retrieve_for_message(message)
    return result['response'].get('context', '')


def get_suggestions_for_message(message: str) -> list:
    """便捷函数：只获取建议"""
    result = retrieve_for_message(message)
    return result['response'].get('suggestions', [])


if __name__ == '__main__':
    # 测试
    test_messages = [
        "如何配置 fact_store?",
        "帮我执行 A股复盘",
        "什么是 LLM Wiki?",
        "搜索历史会话"
    ]
    
    print("=== 记忆系统主动检索测试 ===\n")
    
    for message in test_messages:
        print(f"消息: {message}")
        result = retrieve_for_message(message)
        
        print(f"意图: {result['analysis']['intent']}")
        print(f"关键词: {result['analysis']['keywords']}")
        print(f"实体: {result['analysis']['entities']}")
        print(f"主题: {result['analysis']['topic']}")
        
        facts_count = len(result['results'].get('facts', []))
        sessions_count = len(result['results'].get('sessions', []))
        wiki_count = len(result['results'].get('wiki_pages', []))
        
        print(f"检索结果: facts={facts_count}, sessions={sessions_count}, wiki={wiki_count}")
        
        if result['response'].get('context'):
            print(f"上下文: {result['response']['context'][:100]}...")
        
        print("-" * 50)
