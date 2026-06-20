#!/usr/bin/env python3
"""
search_cache.py - 搜索缓存
版本: v1.0.0
功能: SQLite 缓存，自动过期(TTL 300s)，LRU 淘汰
"""

import sys
import os
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

CACHE_DB_PATH = os.path.expanduser("~/.hermes/search_cache.db")
DEFAULT_TTL = 300  # 5分钟
MAX_CACHE_SIZE = 1000

def get_connection():
    """获取缓存数据库连接"""
    conn = sqlite3.connect(CACHE_DB_PATH)
    cursor = conn.cursor()
    
    # 创建缓存表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT NOT NULL UNIQUE,
            query TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_hash ON search_cache(query_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON search_cache(expires_at)")
    
    conn.commit()
    return conn

def get_query_hash(query):
    """生成查询哈希"""
    return hashlib.md5(query.encode()).hexdigest()

def get_cached_results(query):
    """获取缓存的搜索结果"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query_hash = get_query_hash(query)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 查询缓存
    cursor.execute("""
        SELECT results, expires_at FROM search_cache 
        WHERE query_hash = ? AND expires_at > ?
    """, (query_hash, now))
    
    row = cursor.fetchone()
    
    if row:
        # 更新访问计数
        cursor.execute("""
            UPDATE search_cache 
            SET access_count = access_count + 1, last_accessed = ?
            WHERE query_hash = ?
        """, (now, query_hash))
        conn.commit()
        conn.close()
        
        return json.loads(row[0])
    
    conn.close()
    return None

def cache_results(query, results, ttl=DEFAULT_TTL):
    """缓存搜索结果"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query_hash = get_query_hash(query)
    now = datetime.now()
    expires_at = (now + timedelta(seconds=ttl)).strftime("%Y-%m-%d %H:%M:%S")
    
    # 检查是否已存在
    cursor.execute("SELECT cache_id FROM search_cache WHERE query_hash = ?", (query_hash,))
    existing = cursor.fetchone()
    
    if existing:
        # 更新现有缓存
        cursor.execute("""
            UPDATE search_cache 
            SET results = ?, expires_at = ?, access_count = 0, last_accessed = ?
            WHERE query_hash = ?
        """, (json.dumps(results), expires_at, now.strftime("%Y-%m-%d %H:%M:%S"), query_hash))
    else:
        # 插入新缓存
        cursor.execute("""
            INSERT INTO search_cache (query_hash, query, results, expires_at, last_accessed)
            VALUES (?, ?, ?, ?, ?)
        """, (query_hash, query, json.dumps(results), expires_at, now.strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    
    # 检查缓存大小，执行LRU淘汰
    cursor.execute("SELECT COUNT(*) FROM search_cache")
    count = cursor.fetchone()[0]
    
    if count > MAX_CACHE_SIZE:
        # 删除最久未访问的缓存
        cursor.execute("""
            DELETE FROM search_cache 
            WHERE cache_id IN (
                SELECT cache_id FROM search_cache 
                ORDER BY last_accessed ASC 
                LIMIT ?
            )
        """, (count - MAX_CACHE_SIZE,))
        conn.commit()
    
    conn.close()

def clear_expired_cache():
    """清理过期缓存"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM search_cache WHERE expires_at <= ?", (now,))
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_count

def get_cache_stats():
    """获取缓存统计信息"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 总缓存数
    cursor.execute("SELECT COUNT(*) FROM search_cache")
    total_count = cursor.fetchone()[0]
    
    # 有效缓存数
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT COUNT(*) FROM search_cache WHERE expires_at > ?", (now,))
    valid_count = cursor.fetchone()[0]
    
    # 过期缓存数
    expired_count = total_count - valid_count
    
    conn.close()
    
    return {
        "total_count": total_count,
        "valid_count": valid_count,
        "expired_count": expired_count
    }

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_cache.py <command> [args...]")
        print("命令:")
        print("  get <query>        获取缓存结果")
        print("  set <query> <ttl>  设置缓存")
        print("  clear              清理过期缓存")
        print("  stats              获取缓存统计")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "get":
        if len(sys.argv) < 3:
            print("错误: get 需要查询参数")
            sys.exit(1)
        query = sys.argv[2]
        results = get_cached_results(query)
        if results:
            print(f"✅ 缓存命中: {query}")
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 缓存未命中: {query}")
    
    elif command == "set":
        if len(sys.argv) < 4:
            print("错误: set 需要查询和结果参数")
            sys.exit(1)
        query = sys.argv[2]
        results = json.loads(sys.argv[3])
        ttl = int(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_TTL
        cache_results(query, results, ttl)
        print(f"✅ 已缓存: {query} (TTL: {ttl}s)")
    
    elif command == "clear":
        deleted_count = clear_expired_cache()
        print(f"✅ 已清理 {deleted_count} 个过期缓存")
    
    elif command == "stats":
        stats = get_cache_stats()
        print(f"=== 缓存统计 ===")
        print(f"总缓存数: {stats['total_count']}")
        print(f"有效缓存: {stats['valid_count']}")
        print(f"过期缓存: {stats['expired_count']}")
    
    else:
        print(f"错误: 未知命令 '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
