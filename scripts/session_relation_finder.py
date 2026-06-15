#!/usr/bin/env python3
"""
会话关联发现器 - 自动发现会话之间的关联
用于记忆系统主动检索

功能:
- 基于标签相似度发现关联
- 基于标题相似度发现关联
- 基于内容相似度发现关联
- 基于时间 proximity 发现关联
"""

import sqlite3
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
from collections import Counter


class SessionRelationFinder:
    """会话关联发现器"""
    
    def __init__(self):
        self.session_db_path = Path.home() / '.hermes' / 'sessions' / 'state.db'
        
        # 相似度阈值
        self.similarity_threshold = 0.2
        self.max_related = 5
    
    def find_related_sessions(
        self,
        session_id: str = None,
        title: str = None,
        tags: List[str] = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """找到相关会话"""
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
            
            # 获取当前会话信息
            current_session = None
            if session_id:
                cursor = conn.execute("""
                    SELECT id, title, source, started_at, ended_at, message_count
                    FROM sessions
                    WHERE id = ?
                """, (session_id,))
                current_session = cursor.fetchone()
            
            # 如果没有当前会话，使用提供的信息
            if not current_session and not title:
                conn.close()
                return []
            
            # 查找相关会话
            related = []
            
            # 1. 基于标题相似度
            if title:
                cursor = conn.execute("""
                    SELECT id, title, source, started_at, ended_at, message_count
                    FROM sessions
                    WHERE id != ? AND title IS NOT NULL
                    ORDER BY started_at DESC
                    LIMIT 100
                """, (session_id or '',))
                
                for row in cursor.fetchall():
                    other_title = row['title'] or ''
                    similarity = self._calculate_title_similarity(title, other_title)
                    
                    if similarity > self.similarity_threshold:
                        related.append({
                            'session_id': row['id'],
                            'title': other_title,
                            'source': row['source'],
                            'started_at': row['started_at'],
                            'ended_at': row['ended_at'],
                            'message_count': row['message_count'],
                            'similarity': similarity,
                            'relation_type': 'title_similarity'
                        })
            
            # 2. 基于标签相似度
            if tags:
                cursor = conn.execute("""
                    SELECT id, title, source, started_at, ended_at, message_count
                    FROM sessions
                    WHERE id != ? AND title IS NOT NULL
                    ORDER BY started_at DESC
                    LIMIT 100
                """, (session_id or '',))
                
                for row in cursor.fetchall():
                    other_title = row['title'] or ''
                    # 简单的标签匹配
                    tag_matches = sum(1 for tag in tags if tag.lower() in other_title.lower())
                    
                    if tag_matches > 0:
                        similarity = tag_matches / len(tags) if tags else 0
                        
                        if similarity > self.similarity_threshold:
                            related.append({
                                'session_id': row['id'],
                                'title': other_title,
                                'source': row['source'],
                                'started_at': row['started_at'],
                                'ended_at': row['ended_at'],
                                'message_count': row['message_count'],
                                'similarity': similarity,
                                'relation_type': 'tag_similarity'
                            })
            
            # 3. 基于同一父会话
            if session_id:
                cursor = conn.execute("""
                    SELECT id, title, source, started_at, ended_at, message_count
                    FROM sessions
                    WHERE parent_session_id = (
                        SELECT parent_session_id 
                        FROM sessions 
                        WHERE id = ?
                    ) AND id != ?
                """, (session_id, session_id))
                
                for row in cursor.fetchall():
                    related.append({
                        'session_id': row['id'],
                        'title': row['title'] or 'Untitled',
                        'source': row['source'],
                        'started_at': row['started_at'],
                        'ended_at': row['ended_at'],
                        'message_count': row['message_count'],
                        'similarity': 0.8,
                        'relation_type': 'same_parent'
                    })
            
            # 去重并排序
            seen = set()
            unique_related = []
            for rel in related:
                if rel['session_id'] not in seen:
                    seen.add(rel['session_id'])
                    unique_related.append(rel)
            
            # 按相似度排序
            unique_related.sort(key=lambda x: x['similarity'], reverse=True)
            
            conn.close()
            
            # 限制结果数量
            max_results = limit or self.max_related
            return unique_related[:max_results]
            
        except Exception as e:
            print(f"Error finding related sessions: {e}")
            return []
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        if not title1 or not title2:
            return 0.0
        
        # 转换为小写
        t1 = title1.lower()
        t2 = title2.lower()
        
        # 提取关键词
        words1 = set(re.findall(r'[\w]+', t1))
        words2 = set(re.findall(r'[\w]+', t2))
        
        if not words1 or not words2:
            return 0.0
        
        # 计算 Jaccard 相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def find_sessions_by_keyword(
        self,
        keyword: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """根据关键词查找会话"""
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
            
            # 搜索会话
            cursor = conn.execute("""
                SELECT id, title, source, started_at, ended_at, message_count
                FROM sessions
                WHERE title LIKE ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (f'%{keyword}%', limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'session_id': row['id'],
                    'title': row['title'] or 'Untitled',
                    'source': row['source'],
                    'started_at': row['started_at'],
                    'ended_at': row['ended_at'],
                    'message_count': row['message_count']
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error finding sessions by keyword: {e}")
            return []
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        if not self.session_db_path.exists():
            return {}
        
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
                return {}
            
            # 统计信息
            cursor = conn.execute("SELECT COUNT(*) as total FROM sessions")
            total = cursor.fetchone()['total']
            
            cursor = conn.execute("SELECT COUNT(DISTINCT source) as sources FROM sessions")
            sources = cursor.fetchone()['sources']
            
            cursor = conn.execute("""
                SELECT source, COUNT(*) as count 
                FROM sessions 
                GROUP BY source 
                ORDER BY count DESC
            """)
            source_distribution = {row['source']: row['count'] for row in cursor.fetchall()}
            
            cursor = conn.execute("""
                SELECT MIN(started_at) as earliest, MAX(started_at) as latest
                FROM sessions
            """)
            time_range = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_sessions': total,
                'total_sources': sources,
                'source_distribution': source_distribution,
                'time_range': {
                    'earliest': time_range['earliest'],
                    'latest': time_range['latest']
                }
            }
            
        except Exception as e:
            print(f"Error getting session statistics: {e}")
            return {}


def find_related_sessions(
    session_id: str = None,
    title: str = None,
    tags: List[str] = None,
    limit: int = None
) -> List[Dict[str, Any]]:
    """便捷函数：查找相关会话"""
    finder = SessionRelationFinder()
    return finder.find_related_sessions(session_id, title, tags, limit)


def find_sessions_by_keyword(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """便捷函数：根据关键词查找会话"""
    finder = SessionRelationFinder()
    return finder.find_sessions_by_keyword(keyword, limit)


def get_session_statistics() -> Dict[str, Any]:
    """便捷函数：获取会话统计信息"""
    finder = SessionRelationFinder()
    return finder.get_session_statistics()


if __name__ == '__main__':
    # 测试
    print("=== 会话关联发现器测试 ===\n")
    
    finder = SessionRelationFinder()
    
    # 测试查找相关会话
    print("1. 查找相关会话 (基于标题)")
    related = finder.find_related_sessions(title="如何配置 fact_store?")
    print(f"   找到 {len(related)} 个相关会话")
    for rel in related[:3]:
        print(f"   - {rel['title']} (相似度: {rel['similarity']:.2f})")
    
    # 测试根据关键词查找
    print("\n2. 根据关键词查找会话")
    sessions = finder.find_sessions_by_keyword("fact_store")
    print(f"   找到 {len(sessions)} 个会话")
    for session in sessions[:3]:
        print(f"   - {session['title']}")
    
    # 测试获取统计信息
    print("\n3. 获取会话统计信息")
    stats = finder.get_session_statistics()
    print(f"   总会话数: {stats.get('total_sessions', 0)}")
    print(f"   来源数: {stats.get('total_sources', 0)}")
    print(f"   来源分布: {stats.get('source_distribution', {})}")
