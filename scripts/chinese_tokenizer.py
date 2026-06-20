#!/usr/bin/env python3
"""
chinese_tokenizer.py - 中文分词器
版本: v1.0.0
功能: 正向最大匹配，同义词扩展，停用词过滤
"""

import sys
import os

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

# 停用词表
STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
    "它", "们", "那", "里", "为", "什么", "怎么", "如何", "为什么",
    "可以", "可能", "应该", "需要", "想要", "希望", "喜欢", "知道",
    "认为", "觉得", "感觉", "想要", "打算", "计划", "决定", "选择"
}

# 同义词表
SYNONYMS = {
    "记忆": ["memory", "存储", "保存", "记录"],
    "搜索": ["search", "查找", "查询", "检索"],
    "系统": ["system", "平台", "框架", "架构"],
    "工具": ["tool", "插件", "组件", "模块"],
    "数据": ["data", "信息", "内容", "资料"],
    "分析": ["analysis", "解析", "研究", "评估"],
    "优化": ["optimize", "改进", "提升", "增强"],
    "问题": ["problem", "issue", "bug", "故障"],
    "解决方案": ["solution", "fix", "修复", "解决"],
    "性能": ["performance", "效率", "速度", "响应"]
}

def load_dictionary(dict_path=None):
    """
    加载词典
    
    Args:
        dict_path: 词典文件路径
    
    Returns:
        词典集合
    """
    dictionary = set()
    
    # 默认词典
    default_words = [
        "记忆", "系统", "搜索", "工具", "数据", "分析", "优化",
        "问题", "解决方案", "性能", "缓存", "数据库", "索引",
        "查询", "排序", "过滤", "导出", "导入", "配置", "设置"
    ]
    dictionary.update(default_words)
    
    # 加载自定义词典
    if dict_path and os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    dictionary.add(word)
    
    return dictionary

def forward_maximum_matching(text, dictionary, max_word_length=4):
    """
    正向最大匹配分词
    
    Args:
        text: 待分词文本
        dictionary: 词典
        max_word_length: 最大词长
    
    Returns:
        分词结果列表
    """
    words = []
    i = 0
    
    while i < len(text):
        matched = False
        
        # 尝试从最大长度开始匹配
        for length in range(min(max_word_length, len(text) - i), 0, -1):
            word = text[i:i + length]
            
            if word in dictionary:
                words.append(word)
                i += length
                matched = True
                break
        
        # 如果没有匹配，单字切分
        if not matched:
            words.append(text[i])
            i += 1
    
    return words

def filter_stop_words(words):
    """
    过滤停用词
    
    Args:
        words: 分词结果
    
    Returns:
        过滤后的分词结果
    """
    return [word for word in words if word not in STOP_WORDS]

def expand_synonyms(words):
    """
    同义词扩展
    
    Args:
        words: 分词结果
    
    Returns:
        扩展后的分词结果
    """
    expanded = []
    
    for word in words:
        expanded.append(word)
        
        # 查找同义词
        for key, synonyms in SYNONYMS.items():
            if word == key or word in synonyms:
                # 添加同义词
                for synonym in synonyms:
                    if synonym != word and synonym not in expanded:
                        expanded.append(synonym)
                break
    
    return expanded

def tokenize(text, dict_path=None, use_synonyms=True, filter_stop=True):
    """
    中文分词
    
    Args:
        text: 待分词文本
        dict_path: 词典文件路径
        use_synonyms: 是否使用同义词扩展
        filter_stop: 是否过滤停用词
    
    Returns:
        分词结果列表
    """
    # 加载词典
    dictionary = load_dictionary(dict_path)
    
    # 正向最大匹配分词
    words = forward_maximum_matching(text, dictionary)
    
    # 过滤停用词
    if filter_stop:
        words = filter_stop_words(words)
    
    # 同义词扩展
    if use_synonyms:
        words = expand_synonyms(words)
    
    return words

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 chinese_tokenizer.py <text> [--no-synonyms] [--no-filter] [--dict PATH]")
        sys.exit(1)
    
    text = sys.argv[1]
    use_synonyms = True
    filter_stop = True
    dict_path = None
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--no-synonyms":
            use_synonyms = False
            i += 1
        elif sys.argv[i] == "--no-filter":
            filter_stop = False
            i += 1
        elif sys.argv[i] == "--dict" and i + 1 < len(sys.argv):
            dict_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # 分词
    words = tokenize(text, dict_path, use_synonyms, filter_stop)
    
    # 输出结果
    print(f"=== 中文分词 ===")
    print(f"原文: {text}")
    print(f"分词: {words}")
    print(f"词数: {len(words)}")

if __name__ == "__main__":
    main()
