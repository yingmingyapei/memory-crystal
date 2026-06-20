#!/usr/bin/env python3
"""
search_highlight.py - 搜索结果高亮
版本: v1.0.0
功能: 5种高亮样式，片段提取
"""

import sys
import os
import re

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

# 高亮样式
HIGHLIGHT_STYLES = {
    "bold": "粗体",
    "underline": "下划线",
    "color": "颜色",
    "bracket": "括号",
    "marker": "标记"
}

def highlight_text(text, query, style="bold"):
    """
    高亮文本中的查询词
    
    Args:
        text: 原始文本
        query: 查询词
        style: 高亮样式
    
    Returns:
        高亮后的文本
    """
    if not query or not text:
        return text
    
    # 转义正则表达式特殊字符
    escaped_query = re.escape(query)
    
    if style == "bold":
        # 粗体高亮
        return re.sub(f"({escaped_query})", r"**\1**", text, flags=re.IGNORECASE)
    elif style == "underline":
        # 下划线高亮
        return re.sub(f"({escaped_query})", r"__\1__", text, flags=re.IGNORECASE)
    elif style == "color":
        # 颜色高亮（ANSI）
        return re.sub(f"({escaped_query})", r"\033[1;31m\1\033[0m", text, flags=re.IGNORECASE)
    elif style == "bracket":
        # 括号高亮
        return re.sub(f"({escaped_query})", r"【\1】", text, flags=re.IGNORECASE)
    elif style == "marker":
        # 标记高亮
        return re.sub(f"({escaped_query})", r"▶\1◀", text, flags=re.IGNORECASE)
    else:
        return text

def extract_snippet(text, query, context_length=50):
    """
    提取包含查询词的文本片段
    
    Args:
        text: 原始文本
        query: 查询词
        context_length: 上下文长度
    
    Returns:
        提取的片段
    """
    if not query or not text:
        return text
    
    # 查找查询词位置
    match = re.search(re.escape(query), text, re.IGNORECASE)
    if not match:
        return text[:context_length * 2] + "..." if len(text) > context_length * 2 else text
    
    start = max(0, match.start() - context_length)
    end = min(len(text), match.end() + context_length)
    
    snippet = text[start:end]
    
    # 添加省略号
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    return snippet

def highlight_results(results, query, style="bold", snippet=True):
    """
    高亮搜索结果
    
    Args:
        results: 搜索结果列表
        query: 查询词
        style: 高亮样式
        snippet: 是否提取片段
    
    Returns:
        高亮后的结果
    """
    highlighted_results = []
    
    for result in results:
        highlighted_result = result.copy()
        
        # 高亮内容
        if snippet:
            content = extract_snippet(result["content"], query)
        else:
            content = result["content"]
        
        highlighted_result["content_highlighted"] = highlight_text(content, query, style)
        highlighted_results.append(highlighted_result)
    
    return highlighted_results

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 search_highlight.py <query> [--style STYLE] [--text TEXT]")
        print(f"高亮样式: {', '.join(HIGHLIGHT_STYLES.keys())}")
        sys.exit(1)
    
    query = sys.argv[1]
    style = "bold"
    text = None
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--style" and i + 1 < len(sys.argv):
            style = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--text" and i + 1 < len(sys.argv):
            text = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # 检查高亮样式
    if style not in HIGHLIGHT_STYLES:
        print(f"错误: 未知高亮样式 '{style}'")
        print(f"可用样式: {', '.join(HIGHLIGHT_STYLES.keys())}")
        sys.exit(1)
    
    # 测试高亮
    if text:
        highlighted = highlight_text(text, query, style)
        snippet = extract_snippet(text, query)
        
        print(f"=== 高亮测试 ===")
        print(f"查询: {query}")
        print(f"样式: {HIGHLIGHT_STYLES[style]}")
        print(f"\n原始文本:")
        print(text)
        print(f"\n高亮文本:")
        print(highlighted)
        print(f"\n提取片段:")
        print(snippet)
    else:
        # 示例文本
        example_text = "Memory Crystal 是 Hermes Agent 的新一代结构化记忆系统，由 fact_store 和 fact_feedback 两个工具构成。"
        highlighted = highlight_text(example_text, query, style)
        snippet = extract_snippet(example_text, query)
        
        print(f"=== 高亮示例 ===")
        print(f"查询: {query}")
        print(f"样式: {HIGHLIGHT_STYLES[style]}")
        print(f"\n原始文本:")
        print(example_text)
        print(f"\n高亮文本:")
        print(highlighted)
        print(f"\n提取片段:")
        print(snippet)

if __name__ == "__main__":
    main()
