#!/usr/bin/env python3
"""
parallel_search.py - 并行搜索
版本: v1.0.0
功能: ThreadPoolExecutor 并行搜索三源
"""

import sys
import os
import sqlite3
import concurrent.futures
from datetime import datetime

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

def search_facts(query, limit=10):
    """搜索fact_store"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT fact_id, content, category, tags, trust_score, retrieval_count, created_at
        FROM facts 
        WHERE content LIKE ? OR tags LIKE ?
        ORDER BY trust_score DESC
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "source": "fact_store",
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

def search_sessions(query, limit=10):
    """搜索会话历史（模拟）"""
    # 这里是模拟实现，实际应该调用session_search
    return [
        {
            "source": "sessions",
            "session_id": "session_1",
            "content": f"会话中提到 {query}",
            "timestamp": datetime.now().isoformat()
        }
    ][:limit]

def search_wiki(query, limit=10):
    """搜索wiki（模拟）"""
    # 这里是模拟实现，实际应该搜索wiki文件
    return [
        {
            "source": "wiki",
            "file": "wiki/memory.md",
            "content": f"wiki中关于 {query} 的内容",
            "timestamp": datetime.now().isoformat()
        }
    ][:limit]

def parallel_search(query, limit=10):
    """
    并行搜索三个数据源
    
    Args:
        query: 搜索查询
        limit: 每个源返回的结果数量
    
    Returns:
        合并的搜索结果
    """
    all_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 提交三个搜索任务
        future_facts = executor.submit(search_facts, query, limit)
        future_sessions = executor.submit(search_sessions, query, limit)
        future_wiki = executor.submit(search_wiki, query, limit)
        
        # 等待所有任务完成
        concurrent.futures.wait([future_facts, future_sessions, future_wiki])
        
        # 获取结果
        try:
            fact_results = future_facts.result()
            all_results.extend(fact_results)
        except Exception as e:
            print(f"搜索fact_store失败: {e}")
        
        try:
            session_results = future_sessions.result()
            all_results.extend(session_results)
        except Exception as e:
            print(f"搜索会话失败: {e}")
        
        try:
            wiki_results = future_wiki.result()
            all_results.extend(wiki_results)
        except Exception as e:
            print(f"搜索wiki失败: {e}")
    
    return all_results

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 parallel_search.py <query> [--limit LIMIT]")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = 10
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    # 并行搜索
    print(f"=== 并行搜索 ===")
    print(f"查询: {query}")
    print(f"搜索中...")
    
    start_time = datetime.now()
    results = parallel_search(query, limit)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds() * 1000  # 毫秒
    
    print(f"\n搜索完成!")
    print(f"耗时: {duration:.2f}ms")
    print(f"结果数量: {len(results)}")
    
    # 按来源分组
    sources = {}
    for result in results:
        source = result.get("source", "unknown")
        if source not in sources:
            sources[source] = []
        sources[source].append(result)
    
    # 输出结果
    for source, source_results in sources.items():
        print(f"\n--- {source} ({len(source_results)} 条) ---")
        for i, result in enumerate(source_results[:3], 1):  # 每个源只显示前3条
            print(f"{i}. {result.get('content', '')[:60]}...")

if __name__ == "__main__":
    main()
