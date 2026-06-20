#!/usr/bin/env python3
"""
search_history.py - 搜索历史
版本: v1.0.0
功能: 记录/查询/统计搜索历史，自动清理30天
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

HISTORY_DB_PATH = os.path.expanduser("~/.hermes/search_history.db")
AUTO_CLEANUP_DAYS = 30

def get_connection():
    """获取历史数据库连接"""
    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
    
    # 创建历史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            results_count INTEGER,
            search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration REAL
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query ON search_history(query)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_time ON search_history(search_time)")
    
    conn.commit()
    return conn

def record_search(query, results_count=None, duration=None):
    """
    记录搜索历史
    
    Args:
        query: 搜索查询
        results_count: 结果数量
        duration: 搜索耗时
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO search_history (query, results_count, duration)
        VALUES (?, ?, ?)
    """, (query, results_count, duration))
    
    conn.commit()
    conn.close()

def get_search_history(limit=20):
    """
    获取搜索历史
    
    Args:
        limit: 返回结果数量
    
    Returns:
        搜索历史列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT query, results_count, search_time, duration
        FROM search_history 
        ORDER BY search_time DESC 
        LIMIT ?
    """, (limit,))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            "query": row[0],
            "results_count": row[1],
            "search_time": row[2],
            "duration": row[3]
        })
    
    conn.close()
    return history

def get_search_stats():
    """
    获取搜索统计信息
    
    Returns:
        统计信息字典
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 总搜索次数
    cursor.execute("SELECT COUNT(*) FROM search_history")
    total_searches = cursor.fetchone()[0]
    
    # 唯一查询数
    cursor.execute("SELECT COUNT(DISTINCT query) FROM search_history")
    unique_queries = cursor.fetchone()[0]
    
    # 热门查询
    cursor.execute("""
        SELECT query, COUNT(*) as count 
        FROM search_history 
        GROUP BY query 
        ORDER BY count DESC 
        LIMIT 5
    """)
    top_queries = [{"query": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    # 平均搜索耗时
    cursor.execute("SELECT AVG(duration) FROM search_history WHERE duration IS NOT NULL")
    avg_duration = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_searches": total_searches,
        "unique_queries": unique_queries,
        "top_queries": top_queries,
        "avg_duration": avg_duration
    }

def cleanup_old_history(days=AUTO_CLEANUP_DAYS):
    """
    清理旧的搜索历史
    
    Args:
        days: 保留天数
    
    Returns:
        删除的记录数
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM search_history WHERE search_time < ?", (cutoff_date,))
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_count

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_history.py <command> [args...]")
        print("命令:")
        print("  record <query> [count] [duration]  记录搜索")
        print("  list [limit]                       查看历史")
        print("  stats                              统计信息")
        print("  cleanup [days]                     清理旧历史")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "record":
        if len(sys.argv) < 3:
            print("错误: record 需要查询参数")
            sys.exit(1)
        query = sys.argv[2]
        count = int(sys.argv[3]) if len(sys.argv) > 3 else None
        duration = float(sys.argv[4]) if len(sys.argv) > 4 else None
        record_search(query, count, duration)
        print(f"✅ 已记录搜索: {query}")
    
    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        history = get_search_history(limit)
        print(f"=== 搜索历史 (最近 {limit} 条) ===")
        for i, item in enumerate(history, 1):
            duration_str = f"{item['duration']:.2f}ms" if item['duration'] else "N/A"
            print(f"{i}. {item['query']} ({item['results_count']} 结果, {duration_str}) - {item['search_time']}")
    
    elif command == "stats":
        stats = get_search_stats()
        print(f"=== 搜索统计 ===")
        print(f"总搜索次数: {stats['total_searches']}")
        print(f"唯一查询数: {stats['unique_queries']}")
        print(f"平均耗时: {stats['avg_duration']:.2f}ms" if stats['avg_duration'] else "平均耗时: N/A")
        print(f"\n热门查询:")
        for i, item in enumerate(stats['top_queries'], 1):
            print(f"  {i}. {item['query']} ({item['count']} 次)")
    
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else AUTO_CLEANUP_DAYS
        deleted_count = cleanup_old_history(days)
        print(f"✅ 已清理 {deleted_count} 条 {days} 天前的搜索历史")
    
    else:
        print(f"错误: 未知命令 '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
