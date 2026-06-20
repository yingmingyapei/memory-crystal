#!/usr/bin/env python3
"""
学习机制 - 从用户行为中学习
用于记忆系统主动检索

功能:
- 分析用户行为模式
- 优化检索算法
- 更新知识库
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


class LearningMechanism:
    """学习机制"""
    
    def __init__(self):
        self.fact_store_path = Path.home() / '.hermes' / 'memory_store.db'
        self.session_db_path = Path.home() / '.hermes' / 'sessions' / 'state.db'
        self.feedback_db_path = Path.home() / '.hermes' / 'feedback.db'
        self.learning_db_path = Path.home() / '.hermes' / 'learning.db'
        
        # 初始化学习数据库
        self._init_learning_db()
    
    def _init_learning_db(self):
        """初始化学习数据库"""
        try:
            conn = sqlite3.connect(str(self.learning_db_path))
            
            # 创建学习记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建用户行为表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_behavior (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action_type TEXT NOT NULL,
                    action_data TEXT,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_records(pattern_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_behavior_type ON user_behavior(action_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_behavior_user ON user_behavior(user_id)")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error initializing learning database: {e}")
    
    def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """从反馈中学习"""
        try:
            conn = sqlite3.connect(str(self.learning_db_path))
            
            # 提取模式
            pattern_type = feedback_data.get('type', 'unknown')
            pattern_data = json.dumps(feedback_data, ensure_ascii=False)
            
            # 检查是否已存在类似模式
            cursor = conn.execute("""
                SELECT id, confidence, usage_count, success_count
                FROM learning_records
                WHERE pattern_type = ?
                ORDER BY confidence DESC
                LIMIT 1
            """, (pattern_type,))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有模式
                record_id, confidence, usage_count, success_count = existing
                
                # 根据反馈调整置信度
                if feedback_data.get('value') == 'helpful':
                    new_confidence = min(1.0, confidence + 0.05)
                    new_success_count = success_count + 1
                else:
                    new_confidence = max(0.0, confidence - 0.05)
                    new_success_count = success_count
                
                new_usage_count = usage_count + 1
                
                conn.execute("""
                    UPDATE learning_records
                    SET confidence = ?, usage_count = ?, success_count = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_confidence, new_usage_count, new_success_count, record_id))
            else:
                # 创建新模式
                initial_confidence = 0.5
                if feedback_data.get('value') == 'helpful':
                    initial_success_count = 1
                else:
                    initial_success_count = 0
                
                conn.execute("""
                    INSERT INTO learning_records (pattern_type, pattern_data, confidence, usage_count, success_count)
                    VALUES (?, ?, ?, 1, ?)
                """, (pattern_type, pattern_data, initial_confidence, initial_success_count))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error learning from feedback: {e}")
            return False
    
    def learn_from_behavior(self, behavior_data: Dict[str, Any]) -> bool:
        """从用户行为中学习"""
        try:
            conn = sqlite3.connect(str(self.learning_db_path))
            
            # 记录用户行为
            conn.execute("""
                INSERT INTO user_behavior (user_id, action_type, action_data, context)
                VALUES (?, ?, ?, ?)
            """, (
                behavior_data.get('user_id', 'default'),
                behavior_data.get('action_type', 'unknown'),
                json.dumps(behavior_data.get('action_data', {}), ensure_ascii=False),
                behavior_data.get('context', '')
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error learning from behavior: {e}")
            return False
    
    def get_learned_patterns(self, pattern_type: str = None) -> List[Dict[str, Any]]:
        """获取学习到的模式"""
        try:
            conn = sqlite3.connect(str(self.learning_db_path))
            
            if pattern_type:
                cursor = conn.execute("""
                    SELECT pattern_type, pattern_data, confidence, usage_count, success_count
                    FROM learning_records
                    WHERE pattern_type = ?
                    ORDER BY confidence DESC
                """, (pattern_type,))
            else:
                cursor = conn.execute("""
                    SELECT pattern_type, pattern_data, confidence, usage_count, success_count
                    FROM learning_records
                    ORDER BY confidence DESC
                """)
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    'type': row[0],
                    'data': json.loads(row[1]),
                    'confidence': row[2],
                    'usage_count': row[3],
                    'success_count': row[4]
                })
            
            conn.close()
            return patterns
            
        except Exception as e:
            print(f"Error getting learned patterns: {e}")
            return []
    
    def get_user_behavior_statistics(self) -> Dict[str, Any]:
        """获取用户行为统计"""
        try:
            conn = sqlite3.connect(str(self.learning_db_path))
            
            # 总行为数
            cursor = conn.execute("SELECT COUNT(*) FROM user_behavior")
            total_behaviors = cursor.fetchone()[0]
            
            # 按类型统计
            cursor = conn.execute("""
                SELECT action_type, COUNT(*) 
                FROM user_behavior 
                GROUP BY action_type
            """)
            type_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 最近行为
            cursor = conn.execute("""
                SELECT user_id, action_type, action_data, created_at
                FROM user_behavior
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent_behaviors = []
            for row in cursor.fetchall():
                recent_behaviors.append({
                    'user_id': row[0],
                    'type': row[1],
                    'data': json.loads(row[2]) if row[2] else {},
                    'created_at': row[3]
                })
            
            conn.close()
            
            return {
                'total_behaviors': total_behaviors,
                'type_distribution': type_distribution,
                'recent_behaviors': recent_behaviors
            }
            
        except Exception as e:
            print(f"Error getting user behavior statistics: {e}")
            return {}
    
    def optimize_retrieval(self) -> Dict[str, Any]:
        """优化检索算法"""
        try:
            # 获取学习到的模式
            patterns = self.get_learned_patterns()
            
            # 分析模式
            optimization_suggestions = []
            
            for pattern in patterns:
                if pattern['confidence'] > 0.7 and pattern['usage_count'] > 5:
                    optimization_suggestions.append({
                        'pattern': pattern['type'],
                        'confidence': pattern['confidence'],
                        'suggestion': f"模式 '{pattern['type']}' 表现良好，建议增加权重"
                    })
                elif pattern['confidence'] < 0.3 and pattern['usage_count'] > 5:
                    optimization_suggestions.append({
                        'pattern': pattern['type'],
                        'confidence': pattern['confidence'],
                        'suggestion': f"模式 '{pattern['type']}' 表现不佳，建议减少权重"
                    })
            
            return {
                'total_patterns': len(patterns),
                'optimization_suggestions': optimization_suggestions
            }
            
        except Exception as e:
            print(f"Error optimizing retrieval: {e}")
            return {}


def learn_from_feedback(feedback_data: Dict[str, Any]) -> bool:
    """便捷函数：从反馈中学习"""
    mechanism = LearningMechanism()
    return mechanism.learn_from_feedback(feedback_data)


def learn_from_behavior(behavior_data: Dict[str, Any]) -> bool:
    """便捷函数：从用户行为中学习"""
    mechanism = LearningMechanism()
    return mechanism.learn_from_behavior(behavior_data)


def get_learned_patterns(pattern_type: str = None) -> List[Dict[str, Any]]:
    """便捷函数：获取学习到的模式"""
    mechanism = LearningMechanism()
    return mechanism.get_learned_patterns(pattern_type)


def get_user_behavior_statistics() -> Dict[str, Any]:
    """便捷函数：获取用户行为统计"""
    mechanism = LearningMechanism()
    return mechanism.get_user_behavior_statistics()


def optimize_retrieval() -> Dict[str, Any]:
    """便捷函数：优化检索算法"""
    mechanism = LearningMechanism()
    return mechanism.optimize_retrieval()


if __name__ == '__main__':
    # 测试
    print("=== 学习机制测试 ===\n")
    
    mechanism = LearningMechanism()
    
    # 测试从反馈中学习
    print("1. 从反馈中学习")
    success = mechanism.learn_from_feedback({
        'type': 'relevance',
        'value': 'helpful',
        'message': '如何配置 fact_store?'
    })
    print(f"   学习: {'成功' if success else '失败'}")
    
    # 测试从行为中学习
    print("\n2. 从行为中学习")
    success = mechanism.learn_from_behavior({
        'user_id': 'test_user',
        'action_type': 'search',
        'action_data': {'query': 'fact_store'},
        'context': '用户搜索 fact_store 配置'
    })
    print(f"   学习: {'成功' if success else '失败'}")
    
    # 测试获取学习到的模式
    print("\n3. 获取学习到的模式")
    patterns = mechanism.get_learned_patterns()
    print(f"   模式数量: {len(patterns)}")
    
    # 测试获取用户行为统计
    print("\n4. 获取用户行为统计")
    stats = mechanism.get_user_behavior_statistics()
    print(f"   总行为数: {stats.get('total_behaviors', 0)}")
    print(f"   类型分布: {stats.get('type_distribution', {})}")
    
    # 测试优化检索
    print("\n5. 优化检索")
    optimization = mechanism.optimize_retrieval()
    print(f"   总模式数: {optimization.get('total_patterns', 0)}")
    print(f"   优化建议: {len(optimization.get('optimization_suggestions', []))}")
