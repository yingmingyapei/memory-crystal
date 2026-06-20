#!/usr/bin/env python3
"""
search_filter.py - 搜索结果过滤
版本: v1.0.0
功能: 5种过滤器（min_score/max_age/category/tags/source）
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

DB_PATH = os.path.expanduser("~/.hermes/memory_store.db")

# 过滤器类型
FILTER_TYPES = {
    "min_score": "最小信任度",
    "max_age": "最大年龄（天）",
    "category": "类别",
    "tags": "标签",
    "source": "来源"
}

def get_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库不存在 {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def search_with_filters(query, filters=None, limit=10):
    """
    搜索并过滤结果
    
    Args:
        query: 搜索查询
        filters: 过滤器字典
        limit: 返回结果数量
    
    Returns:
        过滤后的搜索结果
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 构建查询
    sql = """
        SELECT fact_id, content, category, tags, trust_score, retrieval_count, created_at
        FROM facts 
        WHERE (content LIKE ? OR tags LIKE ?)
    """
    params = [f"%{query}%", f"%{query}%"]
    
    # 应用过滤器
    if filters:
        if "min_score" in filters:
            sql += " AND trust_score >= ?"
            params.append(float(filters["min_score"]))
        
        if "max_age" in filters:
            max_age_days = int(filters["max_age"])
            cutoff_date = (datetime.now() - timedelta(days=max_age_days)).strftime("%Y-%m-%d %H:%M:%S")
            sql += " AND created_at >= ?"
            params.append(cutoff_date)
        
        if "category" in filters:
            sql += " AND category = ?"
            params.append(filters["category"])
        
        if "tags" in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
    
    sql += " ORDER BY trust_score DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(sql, params)
    
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
    return results

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_filter.py <query> [--min-score SCORE] [--max-age DAYS] [--category CAT] [--tags TAGS] [--limit LIMIT]")
        print(f"过滤器: {', '.join(FILTER_TYPES.keys())}")
        sys.exit(1)
    
    query = sys.argv[1]
    filters = {}
    limit = 10
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--min-score" and i + 1 < len(sys.argv):
            filters["min_score"] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--max-age" and i + 1 < len(sys.argv):
            filters["max_age"] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--category" and i + 1 < len(sys.argv):
            filters["category"] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--tags" and i + 1 < len(sys.argv):
            filters["tags"] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    # 搜索并过滤
    results = search_with_filters(query, filters, limit)
    
    # 输出结果
    print(f"=== 搜索结果 (过滤) ===")
    print(f"查询: {query}")
    print(f"过滤器: {filters}")
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
