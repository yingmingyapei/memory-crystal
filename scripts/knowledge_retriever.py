#!/usr/bin/env python3
"""
知识检索器 - 从多个数据源检索相关知识
用于记忆系统主动检索

优化版本 v1.1:
- 增加 FTS5 全文搜索
- 改进搜索算法
- 增加同义词扩展搜索
- 优化性能
"""

import sqlite3
import re
from typing import List, Dict, Any
from pathlib import Path


class KnowledgeRetriever:
    """从多个数据源检索相关知识"""
    
    def __init__(self):
        self.fact_store_path = Path.home() / '.hermes' / 'memory_store.db'
        self.session_db_path = Path.home() / '.hermes' / 'sessions' / 'state.db'
        self.wiki_path = Path('/mnt/c/Users/yingm/wiki')
        
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
    
    def retrieve(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """根据分析结果检索相关知识"""
        # 扩展关键词（包含同义词）
        expanded_keywords = self._expand_keywords(analysis)
        
        result = {
            'facts': self._search_facts(analysis, expanded_keywords),
            'sessions': self._search_sessions(analysis, expanded_keywords),
            'wiki_pages': self._search_wiki(analysis, expanded_keywords)
        }
        return result
    
    def _expand_keywords(self, analysis: Dict[str, Any]) -> List[str]:
        """扩展关键词（包含同义词）"""
        keywords = analysis.get('keywords', [])
        synonyms = analysis.get('synonyms', [])
        
        expanded = list(keywords)
        expanded.extend(synonyms)
        
        # 去重
        seen = set()
        unique = []
        for kw in expanded:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique.append(kw)
        
        return unique
    
    def _search_facts(self, analysis: Dict[str, Any], expanded_keywords: List[str]) -> List[Dict[str, Any]]:
        """搜索 fact_store - 支持 FTS5"""
        if not self.fact_store_path.exists():
            return []
        
        try:
            conn = sqlite3.connect(str(self.fact_store_path))
            conn.row_factory = sqlite3.Row
            
            # 构建搜索查询
            keywords = expanded_keywords[:10]  # 限制关键词数量
            entities = analysis.get('entities', [])
            
            if not keywords and not entities:
                return []
            
            results = []
            
            # 尝试 FTS5 搜索
            try:
                # 构建 FTS5 查询
                fts_query_parts = []
                for keyword in keywords[:5]:
                    # 转义特殊字符
                    escaped = keyword.replace('"', '""')
                    fts_query_parts.append(f'"{escaped}"')
                
                if fts_query_parts:
                    fts_query = ' OR '.join(fts_query_parts)
                    query = """
                        SELECT f.fact_id, f.content, f.category, f.tags, 
                               f.trust_score, f.retrieval_count,
                               rank
                        FROM facts_fts fts
                        JOIN facts f ON f.fact_id = fts.rowid
                        WHERE facts_fts MATCH ?
                        ORDER BY rank
                        LIMIT 10
                    """
                    cursor = conn.execute(query, (fts_query,))
                    for row in cursor.fetchall():
                        results.append({
                            'id': row['fact_id'],
                            'content': row['content'],
                            'category': row['category'],
                            'tags': row['tags'],
                            'trust_score': row['trust_score'],
                            'retrieval_count': row['retrieval_count'],
                            'source': 'fact_store',
                            'search_method': 'fts5'
                        })
            except Exception:
                # FTS5 搜索失败，回退到 LIKE 搜索
                pass
            
            # 如果 FTS5 没有结果，使用 LIKE 搜索
            if not results:
                query_parts = []
                params = []
                
                for keyword in keywords[:5]:
                    query_parts.append("content LIKE ?")
                    params.append(f'%{keyword}%')
                
                for entity in entities[:3]:
                    query_parts.append("content LIKE ?")
                    params.append(f'%{entity["value"]}%')
                
                if query_parts:
                    where_clause = ' OR '.join(query_parts)
                    query = f"""
                        SELECT fact_id, content, category, tags, trust_score, retrieval_count
                        FROM facts
                        WHERE {where_clause}
                        ORDER BY trust_score DESC, retrieval_count DESC
                        LIMIT 10
                    """
                    
                    cursor = conn.execute(query, params)
                    for row in cursor.fetchall():
                        results.append({
                            'id': row['fact_id'],
                            'content': row['content'],
                            'category': row['category'],
                            'tags': row['tags'],
                            'trust_score': row['trust_score'],
                            'retrieval_count': row['retrieval_count'],
                            'source': 'fact_store',
                            'search_method': 'like'
                        })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error searching facts: {e}")
            return []
    
    def _search_sessions(self, analysis: Dict[str, Any], expanded_keywords: List[str]) -> List[Dict[str, Any]]:
        """搜索 session_search - 支持 FTS5"""
        if not self.session_db_path.exists():
            return []
        
        try:
            conn = sqlite3.connect(str(self.session_db_path))
            conn.row_factory = sqlite3.Row
            
            # 检查 sessions 表是否存在
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sessions'
            """)
            if not cursor.fetchone():
                conn.close()
                return []
            
            # 构建搜索查询
            keywords = expanded_keywords[:10]
            if not keywords:
                return []
            
            results = []
            
            # 尝试 FTS5 搜索
            try:
                # 检查是否有 sessions_fts 表
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sessions_fts'
                """)
                if cursor.fetchone():
                    # 构建 FTS5 查询
                    fts_query_parts = []
                    for keyword in keywords[:5]:
                        escaped = keyword.replace('"', '""')
                        fts_query_parts.append(f'"{escaped}"')
                    
                    if fts_query_parts:
                        fts_query = ' OR '.join(fts_query_parts)
                        query = """
                            SELECT s.id, s.title, s.source, s.started_at, s.ended_at, s.message_count,
                                   rank
                            FROM sessions_fts fts
                            JOIN sessions s ON s.id = fts.rowid
                            WHERE sessions_fts MATCH ?
                            ORDER BY rank
                            LIMIT 5
                        """
                        cursor = conn.execute(query, (fts_query,))
                        for row in cursor.fetchall():
                            results.append({
                                'session_id': row['id'],
                                'title': row['title'] or 'Untitled',
                                'source': row['source'],
                                'started_at': row['started_at'],
                                'ended_at': row['ended_at'],
                                'message_count': row['message_count'],
                                'source_type': 'session_search',
                                'search_method': 'fts5'
                            })
            except Exception:
                # FTS5 搜索失败，回退到 LIKE 搜索
                pass
            
            # 如果 FTS5 没有结果，使用 LIKE 搜索
            if not results:
                query_parts = []
                params = []
                
                for keyword in keywords[:5]:
                    query_parts.append("title LIKE ?")
                    params.append(f'%{keyword}%')
                
                if query_parts:
                    where_clause = ' OR '.join(query_parts)
                    query = f"""
                        SELECT id, title, source, started_at, ended_at, message_count
                        FROM sessions
                        WHERE {where_clause}
                        ORDER BY started_at DESC
                        LIMIT 5
                    """
                    
                    cursor = conn.execute(query, params)
                    for row in cursor.fetchall():
                        results.append({
                            'session_id': row['id'],
                            'title': row['title'] or 'Untitled',
                            'source': row['source'],
                            'started_at': row['started_at'],
                            'ended_at': row['ended_at'],
                            'message_count': row['message_count'],
                            'source_type': 'session_search',
                            'search_method': 'like'
                        })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error searching sessions: {e}")
            return []
    
    def _search_wiki(self, analysis: Dict[str, Any], expanded_keywords: List[str]) -> List[Dict[str, Any]]:
        """搜索 llm-wiki - 改进版"""
        if not self.wiki_path.exists():
            return []
        
        try:
            # 读取 index.md
            index_path = self.wiki_path / 'index.md'
            if not index_path.exists():
                return []
            
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取关键词
            keywords = expanded_keywords[:10]
            if not keywords:
                return []
            
            # 搜索匹配的页面
            results = []
            seen_pages = set()
            
            lines = content.split('\n')
            for line in lines:
                if line.startswith('- [['):
                    # 提取页面名称和摘要
                    match = re.match(r'- \[\[(.*?)\]\] - (.*)', line)
                    if match:
                        page_name = match.group(1)
                        summary = match.group(2)
                        
                        # 去重
                        if page_name in seen_pages:
                            continue
                        
                        # 检查是否匹配关键词
                        matched = False
                        for keyword in keywords:
                            if (keyword.lower() in page_name.lower() or 
                                keyword.lower() in summary.lower()):
                                matched = True
                                break
                        
                        if matched:
                            seen_pages.add(page_name)
                            results.append({
                                'page_name': page_name,
                                'summary': summary,
                                'path': str(self.wiki_path / f'{page_name}.md'),
                                'source': 'llm-wiki',
                                'search_method': 'index'
                            })
            
            return results[:5]  # 限制结果数量
            
        except Exception as e:
            print(f"Error searching wiki: {e}")
            return []


def retrieve_knowledge(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：检索相关知识"""
    retriever = KnowledgeRetriever()
    return retriever.retrieve(analysis)


if __name__ == '__main__':
    # 测试
    from message_analyzer import analyze_message
    
    test_messages = [
        "如何配置 fact_store?",
        "帮我执行 A股复盘",
        "什么是 LLM Wiki?",
        "搜索历史会话"
    ]
    
    print("=== 知识检索器测试 v1.1 ===\n")
    
    retriever = KnowledgeRetriever()
    
    for message in test_messages:
        print(f"消息: {message}")
        analysis = analyze_message(message)
        results = retriever.retrieve(analysis)
        
        print(f"  fact_store: {len(results['facts'])} 条")
        print(f"  session_search: {len(results['sessions'])} 条")
        print(f"  llm-wiki: {len(results['wiki_pages'])} 条")
        
        if results['facts']:
            print(f"  首条知识: {results['facts'][0]['content'][:50]}...")
        
        print("-" * 50)
