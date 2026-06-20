#!/usr/bin/env python3
"""
反馈收集器 - 收集用户对检索结果的反馈
用于记忆系统主动检索

功能:
- 收集用户反馈
- 更新信任分数
- 优化检索算法
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class FeedbackCollector:
    """反馈收集器"""
    
    def __init__(self):
        self.fact_store_path = Path.home() / '.hermes' / 'memory_store.db'
        self.feedback_db_path = Path.home() / '.hermes' / 'feedback.db'
        
        # 初始化反馈数据库
        self._init_feedback_db()
    
    def _init_feedback_db(self):
        """初始化反馈数据库"""
        try:
            conn = sqlite3.connect(str(self.feedback_db_path))
            
            # 创建反馈表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    fact_id INTEGER,
                    session_id TEXT,
                    wiki_page TEXT,
                    feedback_type TEXT NOT NULL,
                    feedback_value TEXT,
                    relevance_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_message ON feedback(message)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_fact_id ON feedback(fact_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error initializing feedback database: {e}")
    
    def collect_feedback(
        self,
        message: str,
        fact_id: int = None,
        session_id: str = None,
        wiki_page: str = None,
        feedback_type: str = 'relevance',
        feedback_value: str = 'helpful',
        relevance_score: float = None
    ) -> bool:
        """收集反馈"""
        try:
            conn = sqlite3.connect(str(self.feedback_db_path))
            
            conn.execute("""
                INSERT INTO feedback (message, fact_id, session_id, wiki_page, 
                                     feedback_type, feedback_value, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message, fact_id, session_id, wiki_page, 
                  feedback_type, feedback_value, relevance_score))
            
            conn.commit()
            conn.close()
            
            # 更新 fact_store 的信任分数
            if fact_id and feedback_type == 'relevance':
                self._update_fact_trust_score(fact_id, feedback_value)
            
            return True
            
        except Exception as e:
            print(f"Error collecting feedback: {e}")
            return False
    
    def _update_fact_trust_score(self, fact_id: int, feedback_value: str):
        """更新 fact_store 的信任分数"""
        try:
            conn = sqlite3.connect(str(self.fact_store_path))
            
            # 获取当前信任分数
            cursor = conn.execute("SELECT trust_score FROM facts WHERE fact_id = ?", (fact_id,))
            row = cursor.fetchone()
            
            if row:
                current_score = row[0]
                
                # 根据反馈调整分数
                if feedback_value == 'helpful':
                    new_score = min(1.0, current_score + 0.05)
                elif feedback_value == 'unhelpful':
                    new_score = max(0.0, current_score - 0.10)
                else:
                    new_score = current_score
                
                # 更新分数
                conn.execute("""
                    UPDATE facts 
                    SET trust_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE fact_id = ?
                """, (new_score, fact_id))
                
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"Error updating fact trust score: {e}")
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        try:
            conn = sqlite3.connect(str(self.feedback_db_path))
            
            # 总反馈数
            cursor = conn.execute("SELECT COUNT(*) FROM feedback")
            total_feedback = cursor.fetchone()[0]
            
            # 按类型统计
            cursor = conn.execute("""
                SELECT feedback_type, COUNT(*) 
                FROM feedback 
                GROUP BY feedback_type
            """)
            type_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按值统计
            cursor = conn.execute("""
                SELECT feedback_value, COUNT(*) 
                FROM feedback 
                GROUP BY feedback_value
            """)
            value_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 最近反馈
            cursor = conn.execute("""
                SELECT message, feedback_type, feedback_value, created_at
                FROM feedback
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent_feedback = []
            for row in cursor.fetchall():
                recent_feedback.append({
                    'message': row[0],
                    'type': row[1],
                    'value': row[2],
                    'created_at': row[3]
                })
            
            conn.close()
            
            return {
                'total_feedback': total_feedback,
                'type_distribution': type_distribution,
                'value_distribution': value_distribution,
                'recent_feedback': recent_feedback
            }
            
        except Exception as e:
            print(f"Error getting feedback statistics: {e}")
            return {}
    
    def get_fact_feedback(self, fact_id: int) -> List[Dict[str, Any]]:
        """获取特定知识的反馈"""
        try:
            conn = sqlite3.connect(str(self.feedback_db_path))
            
            cursor = conn.execute("""
                SELECT message, feedback_type, feedback_value, created_at
                FROM feedback
                WHERE fact_id = ?
                ORDER BY created_at DESC
            """, (fact_id,))
            
            feedback = []
            for row in cursor.fetchall():
                feedback.append({
                    'message': row[0],
                    'type': row[1],
                    'value': row[2],
                    'created_at': row[3]
                })
            
            conn.close()
            return feedback
            
        except Exception as e:
            print(f"Error getting fact feedback: {e}")
            return []


def collect_feedback(
    message: str,
    fact_id: int = None,
    session_id: str = None,
    wiki_page: str = None,
    feedback_type: str = 'relevance',
    feedback_value: str = 'helpful',
    relevance_score: float = None
) -> bool:
    """便捷函数：收集反馈"""
    collector = FeedbackCollector()
    return collector.collect_feedback(
        message, fact_id, session_id, wiki_page,
        feedback_type, feedback_value, relevance_score
    )


def get_feedback_statistics() -> Dict[str, Any]:
    """便捷函数：获取反馈统计信息"""
    collector = FeedbackCollector()
    return collector.get_feedback_statistics()


if __name__ == '__main__':
    # 测试
    print("=== 反馈收集器测试 ===\n")
    
    collector = FeedbackCollector()
    
    # 测试收集反馈
    print("1. 收集反馈")
    success = collector.collect_feedback(
        message="如何配置 fact_store?",
        fact_id=1,
        feedback_type='relevance',
        feedback_value='helpful'
    )
    print(f"   收集反馈: {'成功' if success else '失败'}")
    
    # 测试获取统计信息
    print("\n2. 获取反馈统计信息")
    stats = collector.get_feedback_statistics()
    print(f"   总反馈数: {stats.get('total_feedback', 0)}")
    print(f"   类型分布: {stats.get('type_distribution', {})}")
    print(f"   值分布: {stats.get('value_distribution', {})}")
    
    # 测试获取特定知识的反馈
    print("\n3. 获取特定知识的反馈")
    feedback = collector.get_fact_feedback(1)
    print(f"   反馈数量: {len(feedback)}")
