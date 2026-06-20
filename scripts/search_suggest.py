#!/usr/bin/env python3
"""
search_suggest.py - 搜索建议
版本: v1.0.0
功能: 自动补全，热门搜索，相关搜索
"""

import sys
import os
import sqlite3
from collections import Counter

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

DB_PATH = os.path.expanduser("~/.hermes/memory_store.db")

def get_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库不存在 {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def get_auto_complete(partial_query, limit=5):
    """
    自动补全
    
    Args:
        partial_query: 部分查询
        limit: 返回结果数量
    
    Returns:
        补全建议列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 查询以partial_query开头的内容
    cursor.execute("""
        SELECT DISTINCT content FROM facts 
        WHERE content LIKE ?
        LIMIT ?
    """, (f"{partial_query}%", limit * 2))
    
    suggestions = []
    for row in cursor.fetchall():
        content = row[0]
        # 提取第一个词作为建议
        words = content.split()
        if words and words[0].startswith(partial_query):
            suggestions.append(words[0])
    
    conn.close()
    
    # 去重并限制数量
    unique_suggestions = list(set(suggestions))[:limit]
    return unique_suggestions

def get_popular_searches(limit=10):
    """
    获取热门搜索
    
    Args:
        limit: 返回结果数量
    
    Returns:
        热门搜索列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 查询使用频率最高的fact
    cursor.execute("""
        SELECT content, retrieval_count FROM facts 
        ORDER BY retrieval_count DESC 
        LIMIT ?
    """, (limit,))
    
    popular = []
    for row in cursor.fetchall():
        popular.append({
            "content": row[0][:50],
            "count": row[1]
        })
    
    conn.close()
    return popular

def get_related_searches(query, limit=5):
    """
    获取相关搜索
    
    Args:
        query: 查询词
        limit: 返回结果数量
    
    Returns:
        相关搜索列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 查询包含query的fact的标签
    cursor.execute("""
        SELECT tags FROM facts 
        WHERE content LIKE ? OR tags LIKE ?
    """, (f"%{query}%", f"%{query}%"))
    
    all_tags = []
    for row in cursor.fetchall():
        if row[0]:
            tags = [tag.strip() for tag in row[0].split(",")]
            all_tags.extend(tags)
    
    conn.close()
    
    # 统计最常出现的标签
    tag_counter = Counter(all_tags)
    related = [tag for tag, count in tag_counter.most_common(limit + 1) if tag != query]
    
    return related[:limit]

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_suggest.py <command> [args...]")
        print("命令:")
        print("  complete <partial>   自动补全")
        print("  popular [limit]      热门搜索")
        print("  related <query>      相关搜索")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "complete":
        if len(sys.argv) < 3:
            print("错误: complete 需要部分查询")
            sys.exit(1)
        partial = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        suggestions = get_auto_complete(partial, limit)
        print(f"=== 自动补全 ===")
        print(f"输入: {partial}")
        print(f"建议: {suggestions}")
    
    elif command == "popular":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        popular = get_popular_searches(limit)
        print(f"=== 热门搜索 ===")
        for i, item in enumerate(popular, 1):
            print(f"{i}. {item['content']} (使用 {item['count']} 次)")
    
    elif command == "related":
        if len(sys.argv) < 3:
            print("错误: related 需要查询词")
            sys.exit(1)
        query = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        related = get_related_searches(query, limit)
        print(f"=== 相关搜索 ===")
        print(f"查询: {query}")
        print(f"相关: {related}")
    
    else:
        print(f"错误: 未知命令 '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
