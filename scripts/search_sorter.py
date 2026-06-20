#!/usr/bin/env python3
"""
search_sorter.py - 搜索结果排序
版本: v1.0.0
功能: 5种排序方式（relevance/date/trust/frequency/alphabetical）
"""

import sys
import os
import sqlite3
from datetime import datetime

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

DB_PATH = os.path.expanduser("~/.hermes/memory_store.db")

# 排序方式
SORT_METHODS = {
    "relevance": "按相关性排序",
    "date": "按日期排序",
    "trust": "按信任度排序",
    "frequency": "按使用频率排序",
    "alphabetical": "按字母顺序排序"
}

def get_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库不存在 {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def sort_results(results, sort_by="relevance", reverse=True):
    """
    对搜索结果进行排序
    
    Args:
        results: 搜索结果列表
        sort_by: 排序方式
        reverse: 是否降序
    
    Returns:
        排序后的结果
    """
    if sort_by == "relevance":
        # 按相关性排序（使用trust_score作为相关性）
        return sorted(results, key=lambda x: x.get("trust_score", 0), reverse=reverse)
    elif sort_by == "date":
        # 按日期排序
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=reverse)
    elif sort_by == "trust":
        # 按信任度排序
        return sorted(results, key=lambda x: x.get("trust_score", 0), reverse=reverse)
    elif sort_by == "frequency":
        # 按使用频率排序
        return sorted(results, key=lambda x: x.get("retrieval_count", 0), reverse=reverse)
    elif sort_by == "alphabetical":
        # 按字母顺序排序
        return sorted(results, key=lambda x: x.get("content", ""), reverse=not reverse)
    else:
        print(f"警告: 未知排序方式 '{sort_by}'，使用默认排序")
        return results

def search_and_sort(query, sort_by="relevance", limit=10):
    """
    搜索并排序结果
    
    Args:
        query: 搜索查询
        sort_by: 排序方式
        limit: 返回结果数量
    
    Returns:
        排序后的搜索结果
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 执行搜索
    cursor.execute("""
        SELECT fact_id, content, category, tags, trust_score, retrieval_count, created_at
        FROM facts 
        WHERE content LIKE ? OR tags LIKE ?
        ORDER BY trust_score DESC
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", limit * 2))  # 获取更多结果用于排序
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "fact_id": row[0],
            "content": row[1],
            "category": row[2],
            "tags": row[3],
            "trust_score": row[4],
            "retrieval_count": row[5],
            "created_at": row[6]
        })
    
    conn.close()
    
    # 排序
    sorted_results = sort_results(results, sort_by)
    
    # 返回指定数量的结果
    return sorted_results[:limit]

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_sorter.py <query> [--sort SORT_METHOD] [--limit LIMIT]")
        print(f"排序方式: {', '.join(SORT_METHODS.keys())}")
        sys.exit(1)
    
    query = sys.argv[1]
    sort_by = "relevance"
    limit = 10
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--sort" and i + 1 < len(sys.argv):
            sort_by = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    # 检查排序方式
    if sort_by not in SORT_METHODS:
        print(f"错误: 未知排序方式 '{sort_by}'")
        print(f"可用排序方式: {', '.join(SORT_METHODS.keys())}")
        sys.exit(1)
    
    # 搜索并排序
    results = search_and_sort(query, sort_by, limit)
    
    # 输出结果
    print(f"=== 搜索结果 (排序: {SORT_METHODS[sort_by]}) ===")
    print(f"查询: {query}")
    print(f"结果数量: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. ID: {result['fact_id']}")
        print(f"   内容: {result['content'][:80]}...")
        print(f"   类别: {result['category']}")
        print(f"   标签: {result['tags']}")
        print(f"   信任度: {result['trust_score']}")
        print(f"   使用次数: {result['retrieval_count']}")
        print(f"   创建时间: {result['created_at']}")

if __name__ == "__main__":
    main()
