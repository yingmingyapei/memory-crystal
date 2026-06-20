#!/usr/bin/env python3
"""
fact_store CLI v1.0.0 - 命令行接口访问fact_store数据库
用法: python3 fact_store_cli.py <command> [args...]

命令:
  list [limit]            列出所有fact
  search <query>          搜索fact
  add <content> [--category CATEGORY] [--tags TAGS]  添加fact
  remove <fact_id>        删除fact
  stats                   统计信息
"""

import sys
import os
import sqlite3

DB_PATH = os.path.expanduser("~/.hermes/memory_store.db")

# 版本信息
__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库不存在 {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def list_facts(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fact_id, substr(content, 1, 80), category, tags, trust_score, created_at FROM facts ORDER BY fact_id DESC LIMIT ?", (limit,))
    facts = cursor.fetchall()
    conn.close()
    print(f"=== 最近 {len(facts)} 条fact ===")
    for fact in facts:
        print(f"ID {fact[0]}: {fact[1]}... [{fact[2]}] tags={fact[3]} trust={fact[4]} ({fact[5]})")

def search_facts(query):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fact_id, content, category, tags, trust_score FROM facts WHERE content LIKE ? OR tags LIKE ? ORDER BY trust_score DESC LIMIT 10", (f"%{query}%", f"%{query}%"))
    facts = cursor.fetchall()
    conn.close()
    print(f"=== 搜索 '{query}' 结果: {len(facts)} 条 ===")
    for fact in facts:
        print(f"ID {fact[0]}: {fact[1][:80]}... [{fact[2]}] tags={fact[3]} trust={fact[4]}")

def add_fact(content, category="general", tags=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO facts (content, category, tags, trust_score, retrieval_count, helpful_count, created_at, updated_at) VALUES (?, ?, ?, 0.5, 0, 0, datetime('now'), datetime('now'))", (content, category, tags))
    fact_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"✅ 已添加fact ID {fact_id}: {content[:50]}...")

def remove_fact(fact_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM facts WHERE fact_id = ?", (fact_id,))
    fact = cursor.fetchone()
    if not fact:
        print(f"错误: fact ID {fact_id} 不存在")
        conn.close()
        return
    cursor.execute("DELETE FROM facts WHERE fact_id = ?", (fact_id,))
    conn.commit()
    conn.close()
    print(f"✅ 已删除fact ID {fact_id}: {fact[0][:50]}...")

def show_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM facts")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT category, COUNT(*) FROM facts GROUP BY category")
    categories = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM facts WHERE trust_score < 0.3")
    low_trust = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count = 0")
    never_retrieved = cursor.fetchone()[0]
    conn.close()
    print("=== fact_store 统计信息 ===")
    print(f"总数: {total}")
    print(f"低信任 (<0.3): {low_trust}")
    print(f"从未检索: {never_retrieved}")
    print("\n按category分布:")
    for cat in categories:
        print(f"  {cat[0]}: {cat[1]}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    command = sys.argv[1]
    if command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        list_facts(limit)
    elif command == "search":
        if len(sys.argv) < 3:
            print("错误: search 需要查询参数")
            sys.exit(1)
        search_facts(sys.argv[2])
    elif command == "add":
        if len(sys.argv) < 3:
            print("错误: add 需要content参数")
            sys.exit(1)
        content = sys.argv[2]
        category = "general"
        tags = ""
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--category" and i + 1 < len(sys.argv):
                category = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--tags" and i + 1 < len(sys.argv):
                tags = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        add_fact(content, category, tags)
    elif command == "remove":
        if len(sys.argv) < 3:
            print("错误: remove 需要fact_id参数")
            sys.exit(1)
        remove_fact(int(sys.argv[2]))
    elif command == "stats":
        show_stats()
    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
