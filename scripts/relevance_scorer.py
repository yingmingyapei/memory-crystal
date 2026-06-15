#!/usr/bin/env python3
"""
相关性评分器 - 对检索结果进行相关性评分
用于记忆系统主动检索

优化版本 v1.1:
- 改进评分算法
- 增加时间衰减
- 增加实体匹配权重
- 优化性能
"""

from typing import List, Dict, Any
import time


class RelevanceScorer:
    """对检索结果进行相关性评分"""
    
    def __init__(self):
        # 评分权重
        self.weights = {
            'keyword_match': 0.35,
            'entity_match': 0.30,
            'trust_score': 0.15,
            'recency': 0.10,
            'retrieval_count': 0.10
        }
        
        # 时间衰减常数（天）
        self.time_decay_days = 30
    
    def score(self, analysis: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """对检索结果进行评分"""
        scored_results = {
            'facts': self._score_facts(analysis, results.get('facts', [])),
            'sessions': self._score_sessions(analysis, results.get('sessions', [])),
            'wiki_pages': self._score_wiki(analysis, results.get('wiki_pages', []))
        }
        return scored_results
    
    def _score_facts(self, analysis: Dict[str, Any], facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对 fact_store 结果评分"""
        scored = []
        keywords = analysis.get('keywords', [])
        entities = analysis.get('entities', [])
        
        for fact in facts:
            score = 0.0
            content = fact.get('content', '').lower()
            
            # 关键词匹配
            keyword_matches = 0
            for keyword in keywords:
                if keyword.lower() in content:
                    keyword_matches += 1
            if keywords:
                keyword_score = keyword_matches / len(keywords)
                score += keyword_score * self.weights['keyword_match']
            
            # 实体匹配
            entity_matches = 0
            for entity in entities:
                if entity['value'].lower() in content:
                    entity_matches += 1
            if entities:
                entity_score = entity_matches / len(entities)
                score += entity_score * self.weights['entity_match']
            
            # 信任分数
            trust_score = fact.get('trust_score', 0.5)
            score += trust_score * self.weights['trust_score']
            
            # 新鲜度（基于检索次数）
            retrieval_count = fact.get('retrieval_count', 0)
            if retrieval_count > 0:
                # 对数衰减
                import math
                recency_score = min(1.0, math.log(retrieval_count + 1) / 5)
                score += recency_score * self.weights['recency']
            
            # 检索频率
            if retrieval_count > 0:
                frequency_score = min(1.0, retrieval_count / 10)
                score += frequency_score * self.weights['retrieval_count']
            
            scored.append({
                **fact,
                'relevance_score': round(score, 3)
            })
        
        # 按分数排序
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored
    
    def _score_sessions(self, analysis: Dict[str, Any], sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对 session_search 结果评分"""
        scored = []
        keywords = analysis.get('keywords', [])
        
        current_time = time.time()
        
        for session in sessions:
            score = 0.0
            title = session.get('title', '') or ''
            title_lower = title.lower()
            
            # 关键词匹配
            keyword_matches = 0
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    keyword_matches += 1
            if keywords:
                keyword_score = keyword_matches / len(keywords)
                score += keyword_score * self.weights['keyword_match']
            
            # 时间衰减
            started_at = session.get('started_at', 0)
            if started_at:
                days_ago = (current_time - started_at) / (24 * 3600)
                # 指数衰减
                import math
                time_score = math.exp(-days_ago / self.time_decay_days)
                score += time_score * self.weights['recency']
            
            # 消息数量（会话越长，可能越有价值）
            message_count = session.get('message_count', 0)
            if message_count > 0:
                length_score = min(1.0, message_count / 100)
                score += length_score * 0.1
            
            scored.append({
                **session,
                'relevance_score': round(score, 3)
            })
        
        # 按分数排序
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored
    
    def _score_wiki(self, analysis: Dict[str, Any], wiki_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对 wiki 结果评分"""
        scored = []
        keywords = analysis.get('keywords', [])
        
        for page in wiki_pages:
            score = 0.0
            page_name = page.get('page_name', '') or ''
            summary = page.get('summary', '') or ''
            page_name_lower = page_name.lower()
            summary_lower = summary.lower()
            
            # 关键词匹配
            keyword_matches = 0
            for keyword in keywords:
                if keyword.lower() in page_name_lower or keyword.lower() in summary_lower:
                    keyword_matches += 1
            if keywords:
                keyword_score = keyword_matches / len(keywords)
                score += keyword_score * self.weights['keyword_match']
            
            # 页面名称匹配（权重更高）
            if keywords:
                name_matches = sum(1 for kw in keywords if kw.lower() in page_name_lower)
                name_score = name_matches / len(keywords)
                score += name_score * 0.2
            
            scored.append({
                **page,
                'relevance_score': round(score, 3)
            })
        
        # 按分数排序
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored


def score_results(analysis: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：对检索结果进行评分"""
    scorer = RelevanceScorer()
    return scorer.score(analysis, results)


if __name__ == '__main__':
    # 测试
    from message_analyzer import analyze_message
    from knowledge_retriever import retrieve_knowledge
    
    test_messages = [
        "如何配置 fact_store?",
        "帮我执行 A股复盘",
        "什么是 LLM Wiki?",
        "搜索历史会话"
    ]
    
    print("=== 相关性评分器测试 v1.1 ===\n")
    
    scorer = RelevanceScorer()
    
    for message in test_messages:
        print(f"消息: {message}")
        analysis = analyze_message(message)
        results = retrieve_knowledge(analysis)
        scored = scorer.score(analysis, results)
        
        print(f"  fact_store: {len(scored['facts'])} 条")
        if scored['facts']:
            top = scored['facts'][0]
            print(f"    最高分: {top['relevance_score']} - {top['content'][:50]}...")
        
        print(f"  session_search: {len(scored['sessions'])} 条")
        print(f"  llm-wiki: {len(scored['wiki_pages'])} 条")
        if scored['wiki_pages']:
            top = scored['wiki_pages'][0]
            print(f"    最高分: {top['relevance_score']} - {top['page_name']}")
        
        print("-" * 50)
