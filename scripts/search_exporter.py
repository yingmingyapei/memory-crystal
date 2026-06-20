#!/usr/bin/env python3
"""
search_exporter.py - 搜索结果导出
版本: v1.0.0
功能: JSON/CSV/Markdown 格式导出
"""

import sys
import os
import sqlite3
import json
import csv
from datetime import datetime

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

DB_PATH = os.path.expanduser("~/.hermes/memory_store.db")

# 导出格式
EXPORT_FORMATS = {
    "json": "JSON格式",
    "csv": "CSV格式",
    "markdown": "Markdown格式"
}

def get_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库不存在 {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def search_facts(query, limit=10):
    """搜索fact"""
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

def export_json(results, output_file=None):
    """导出为JSON格式"""
    data = {
        "export_time": datetime.now().isoformat(),
        "total_count": len(results),
        "results": results
    }
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已导出到 {output_file}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))

def export_csv(results, output_file=None):
    """导出为CSV格式"""
    if not results:
        print("没有数据可导出")
        return
    
    fieldnames = ["fact_id", "content", "category", "tags", "trust_score", "retrieval_count", "created_at"]
    
    if output_file:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"✅ 已导出到 {output_file}")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def export_markdown(results, output_file=None):
    """导出为Markdown格式"""
    if not results:
        print("没有数据可导出")
        return
    
    lines = []
    lines.append("# 搜索结果导出")
    lines.append(f"\n导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"结果数量: {len(results)}")
    lines.append("\n## 结果列表")
    
    for i, result in enumerate(results, 1):
        lines.append(f"\n### {i}. ID: {result['fact_id']}")
        lines.append(f"- **内容**: {result['content']}")
        lines.append(f"- **类别**: {result['category']}")
        lines.append(f"- **标签**: {result['tags']}")
        lines.append(f"- **信任度**: {result['trust_score']}")
        lines.append(f"- **使用次数**: {result['retrieval_count']}")
        lines.append(f"- **创建时间**: {result['created_at']}")
    
    content = "\n".join(lines)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已导出到 {output_file}")
    else:
        print(content)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_exporter.py <query> [--format FORMAT] [--output FILE] [--limit LIMIT]")
        print(f"导出格式: {', '.join(EXPORT_FORMATS.keys())}")
        sys.exit(1)
    
    query = sys.argv[1]
    export_format = "json"
    output_file = None
    limit = 10
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--format" and i + 1 < len(sys.argv):
            export_format = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    # 检查导出格式
    if export_format not in EXPORT_FORMATS:
        print(f"错误: 未知导出格式 '{export_format}'")
        print(f"可用格式: {', '.join(EXPORT_FORMATS.keys())}")
        sys.exit(1)
    
    # 搜索
    results = search_facts(query, limit)
    
    # 导出
    if export_format == "json":
        export_json(results, output_file)
    elif export_format == "csv":
        export_csv(results, output_file)
    elif export_format == "markdown":
        export_markdown(results, output_file)

if __name__ == "__main__":
    main()
