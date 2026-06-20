#!/usr/bin/env python3
"""
entity_extractor.py - 实体提取器
版本: v1.0.0
功能: 10种实体类型，实体关系发现
"""

import sys
import os
import re

__version__ = "1.0.0"
__author__ = "yingming"
__created__ = "2026-06-20"

# 实体类型
ENTITY_TYPES = {
    "PERSON": "人名",
    "ORG": "组织",
    "LOC": "地点",
    "DATE": "日期",
    "TIME": "时间",
    "MONEY": "金额",
    "PERCENT": "百分比",
    "EMAIL": "邮箱",
    "URL": "网址",
    "PHONE": "电话"
}

# 实体模式
ENTITY_PATTERNS = {
    "PERSON": [
        r"[\u4e00-\u9fa5]{2,4}(?:先生|女士|教授|博士|老师|总|经理|主任)",
        r"(?:我|你|他|她|它|我们|你们|他们)(?:叫|是|名字)",
    ],
    "ORG": [
        r"[\u4e00-\u9fa5]{2,10}(?:公司|集团|企业|机构|组织|大学|学院|研究所)",
        r"(?:华为|阿里巴巴|腾讯|百度|小米|字节跳动|美团|京东|网易|新浪)",
    ],
    "LOC": [
        r"[\u4e00-\u9fa5]{2,8}(?:省|市|区|县|镇|村|街|路|道)",
        r"(?:北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|重庆)",
    ],
    "DATE": [
        r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?",
        r"(?:今天|昨天|明天|前天|后天|本周|上周|下周|本月|上月|下月)",
    ],
    "TIME": [
        r"\d{1,2}:\d{2}(?::\d{2})?",
        r"(?:上午|下午|晚上|凌晨|中午)\d{1,2}点",
    ],
    "MONEY": [
        r"(?:￥|¥|RMB|\$|美元|欧元|英镑)\d+(?:\.\d+)?(?:万|亿)?",
        r"\d+(?:\.\d+)?(?:万|亿|元|美元|欧元|英镑)",
    ],
    "PERCENT": [
        r"\d+(?:\.\d+)?%",
        r"百分之\d+(?:\.\d+)?",
    ],
    "EMAIL": [
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    ],
    "URL": [
        r"https?://[^\s]+",
        r"www\.[^\s]+",
    ],
    "PHONE": [
        r"1[3-9]\d{9}",
        r"(?:\d{3,4}-)?\d{7,8}",
    ]
}

def extract_entities(text):
    """
    提取实体
    
    Args:
        text: 待提取文本
    
    Returns:
        实体字典，按类型分组
    """
    entities = {}
    
    for entity_type, patterns in ENTITY_PATTERNS.items():
        type_entities = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entity = match.group()
                if entity not in type_entities:
                    type_entities.append(entity)
        
        if type_entities:
            entities[entity_type] = type_entities
    
    return entities

def find_entity_relations(entities):
    """
    发现实体关系
    
    Args:
        entities: 实体字典
    
    Returns:
        实体关系列表
    """
    relations = []
    
    # 人名-组织关系
    if "PERSON" in entities and "ORG" in entities:
        for person in entities["PERSON"]:
            for org in entities["ORG"]:
                relations.append({
                    "type": "PERSON-ORG",
                    "entity1": person,
                    "entity2": org,
                    "relation": "属于"
                })
    
    # 人名-地点关系
    if "PERSON" in entities and "LOC" in entities:
        for person in entities["PERSON"]:
            for loc in entities["LOC"]:
                relations.append({
                    "type": "PERSON-LOC",
                    "entity1": person,
                    "entity2": loc,
                    "relation": "位于"
                })
    
    # 组织-地点关系
    if "ORG" in entities and "LOC" in entities:
        for org in entities["ORG"]:
            for loc in entities["LOC"]:
                relations.append({
                    "type": "ORG-LOC",
                    "entity1": org,
                    "entity2": loc,
                    "relation": "位于"
                })
    
    return relations

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 entity_extractor.py <text> [--type TYPE]")
        print(f"实体类型: {', '.join(ENTITY_TYPES.keys())}")
        sys.exit(1)
    
    text = sys.argv[1]
    filter_type = None
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--type" and i + 1 < len(sys.argv):
            filter_type = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # 提取实体
    entities = extract_entities(text)
    
    # 过滤类型
    if filter_type:
        if filter_type in entities:
            entities = {filter_type: entities[filter_type]}
        else:
            entities = {}
    
    # 输出结果
    print(f"=== 实体提取 ===")
    print(f"原文: {text}")
    print(f"\n提取的实体:")
    
    total_count = 0
    for entity_type, type_entities in entities.items():
        type_name = ENTITY_TYPES.get(entity_type, entity_type)
        print(f"\n{type_name} ({entity_type}):")
        for entity in type_entities:
            print(f"  - {entity}")
            total_count += 1
    
    print(f"\n总共提取: {total_count} 个实体")
    
    # 发现实体关系
    if not filter_type:
        relations = find_entity_relations(entities)
        if relations:
            print(f"\n实体关系:")
            for relation in relations:
                print(f"  {relation['entity1']} {relation['relation']} {relation['entity2']}")

if __name__ == "__main__":
    main()
