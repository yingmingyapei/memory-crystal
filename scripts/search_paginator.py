#!/usr/bin/env python3
"""
search_paginator.py - 搜索结果分页
版本: v1.0.0
功能: 自动分页，分页元数据（当前页/总页数/总数）
"""

import sys
import os
import sqlite3

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

def search_with_pagination(query, page=1, page_size=10):
    """
    搜索并分页
    
    Args:
        query: 搜索查询
        page: 当前页码（从1开始）
        page_size: 每页数量
    
    Returns:
        包含分页元数据的结果字典
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取总数
    cursor.execute("""
        SELECT COUNT(*) FROM facts 
        WHERE content LIKE ? OR tags LIKE ?
    """, (f"%{query}%", f"%{query}%"))
    total_count = cursor.fetchone()[0]
    
    # 计算分页
    total_pages = (total_count + page_size - 1) // page_size
    offset = (page - 1) * page_size
    
    # 获取当前页数据
    cursor.execute("""
        SELECT fact_id, content, category, tags, trust_score, retrieval_count, created_at
        FROM facts 
        WHERE content LIKE ? OR tags LIKE ?
        ORDER BY trust_score DESC
        LIMIT ? OFFSET ?
    """, (f"%{query}%", f"%{query}%", page_size, offset))
    
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
    
    # 构建分页元数据
    pagination = {
        "current_page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "previous_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None
    }
    
    return {
        "results": results,
        "pagination": pagination
    }

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_paginator.py <query> [--page PAGE] [--size SIZE]")
        sys.exit(1)
    
    query = sys.argv[1]
    page = 1
    page_size = 10
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--page" and i + 1 < len(sys.argv):
            page = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--size" and i + 1 < len(sys.argv):
            page_size = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    # 搜索并分页
    result = search_with_pagination(query, page, page_size)
    
    # 输出结果
    pagination = result["pagination"]
    print(f"=== 搜索结果 (分页) ===")
    print(f"查询: {query}")
    print(f"当前页: {pagination['current_page']}/{pagination['total_pages']}")
    print(f"每页数量: {pagination['page_size']}")
    print(f"总数量: {pagination['total_count']}")
    
    for i, item in enumerate(result["results"], 1):
        print(f"\n{i}. ID: {item['fact_id']}")
        print(f"   内容: {item['content'][:80]}...")
        print(f"   类别: {item['category']}")
        print(f"   信任度: {item['trust_score']}")
    
    # 显示分页导航
    print(f"\n分页导航:")
    if pagination["has_previous"]:
        print(f"  上一页: {pagination['previous_page']}")
    if pagination["has_next"]:
        print(f"  下一页: {pagination['next_page']}")

if __name__ == "__main__":
    main()
