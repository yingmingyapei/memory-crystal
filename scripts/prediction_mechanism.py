#!/usr/bin/env python3
"""
预测机制 - 预测用户需求
用于记忆系统主动检索

功能:
- 预测用户意图
- 预测用户需求
- 提供主动建议
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class PredictionMechanism:
    """预测机制"""
    
    def __init__(self):
        self.session_db_path = Path.home() / '.hermes' / 'sessions' / 'state.db'
        self.learning_db_path = Path.home() / '.hermes' / 'learning.db'
        self.fact_store_path = Path.home() / '.hermes' / 'memory_store.db'
        
        # 预测模型参数
        self.history_weight = 0.4
        self.context_weight = 0.3
        self.pattern_weight = 0.3
    
    def predict_user_intent(self, current_message: str, session_history: List[str] = None) -> Dict[str, Any]:
        """预测用户意图"""
        try:
            # 1. 基于历史行为预测
            history_prediction = self._predict_from_history(current_message)
            
            # 2. 基于上下文预测
            context_prediction = self._predict_from_context(current_message, session_history)
            
            # 3. 基于模式预测
            pattern_prediction = self._predict_from_pattern(current_message)
            
            # 4. 综合预测
            final_prediction = self._combine_predictions(
                history_prediction,
                context_prediction,
                pattern_prediction
            )
            
            return final_prediction
            
        except Exception as e:
            print(f"Error predicting user intent: {e}")
            return {
                'intent': 'general',
                'confidence': 0.5,
                'suggestions': []
            }
    
    def _predict_from_history(self, message: str) -> Dict[str, Any]:
        """基于历史行为预测"""
        try:
            conn = sqlite3.connect(str(self.session_db_path))
            
            # 检查 sessions 表是否存在
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sessions'
            """)
            if not cursor.fetchone():
                conn.close()
                return {'intent': 'general', 'confidence': 0.5}
            
            # 获取最近会话
            cursor = conn.execute("""
                SELECT title, source, started_at
                FROM sessions
                ORDER BY started_at DESC
                LIMIT 10
            """)
            
            recent_sessions = []
            for row in cursor.fetchall():
                recent_sessions.append({
                    'title': row[0] or '',
                    'source': row[1],
                    'started_at': row[2]
                })
            
            conn.close()
            
            # 分析历史模式
            intent_counter = Counter()
            for session in recent_sessions:
                title = session['title'].lower()
                
                # 简单的意图识别
                if '配置' in title or '设置' in title:
                    intent_counter['config'] += 1
                elif '搜索' in title or '查找' in title:
                    intent_counter['search'] += 1
                elif '创建' in title or '新建' in title:
                    intent_counter['create'] += 1
                elif '修复' in title or '错误' in title:
                    intent_counter['fix'] += 1
                elif '查看' in title or '显示' in title:
                    intent_counter['view'] += 1
            
            if intent_counter:
                most_common = intent_counter.most_common(1)[0]
                return {
                    'intent': most_common[0],
                    'confidence': min(0.8, most_common[1] / len(recent_sessions))
                }
            
            return {'intent': 'general', 'confidence': 0.5}
            
        except Exception as e:
            print(f"Error predicting from history: {e}")
            return {'intent': 'general', 'confidence': 0.5}
    
    def _predict_from_context(self, message: str, session_history: List[str] = None) -> Dict[str, Any]:
        """基于上下文预测"""
        try:
            if not session_history:
                return {'intent': 'general', 'confidence': 0.5}
            
            # 分析会话历史
            intent_counter = Counter()
            
            for hist_message in session_history[-5:]:  # 最近5条消息
                hist_lower = hist_message.lower()
                
                if '配置' in hist_lower or '设置' in hist_lower:
                    intent_counter['config'] += 1
                elif '搜索' in hist_lower or '查找' in hist_lower:
                    intent_counter['search'] += 1
                elif '创建' in hist_lower or '新建' in hist_lower:
                    intent_counter['create'] += 1
                elif '修复' in hist_lower or '错误' in hist_lower:
                    intent_counter['fix'] += 1
                elif '查看' in hist_lower or '显示' in hist_lower:
                    intent_counter['view'] += 1
            
            if intent_counter:
                most_common = intent_counter.most_common(1)[0]
                return {
                    'intent': most_common[0],
                    'confidence': min(0.7, most_common[1] / len(session_history))
                }
            
            return {'intent': 'general', 'confidence': 0.5}
            
        except Exception as e:
            print(f"Error predicting from context: {e}")
            return {'intent': 'general', 'confidence': 0.5}
    
    def _predict_from_pattern(self, message: str) -> Dict[str, Any]:
        """基于模式预测"""
        try:
            conn = sqlite3.connect(str(self.learning_db_path))
            
            # 获取学习到的模式
            cursor = conn.execute("""
                SELECT pattern_type, confidence, usage_count
                FROM learning_records
                WHERE confidence > 0.6
                ORDER BY confidence DESC
                LIMIT 5
            """)
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    'type': row[0],
                    'confidence': row[1],
                    'usage_count': row[2]
                })
            
            conn.close()
            
            # 匹配模式
            message_lower = message.lower()
            
            for pattern in patterns:
                pattern_type = pattern['type']
                
                # 简单的模式匹配
                if pattern_type == 'config' and ('配置' in message_lower or '设置' in message_lower):
                    return {
                        'intent': 'config',
                        'confidence': pattern['confidence']
                    }
                elif pattern_type == 'search' and ('搜索' in message_lower or '查找' in message_lower):
                    return {
                        'intent': 'search',
                        'confidence': pattern['confidence']
                    }
                elif pattern_type == 'create' and ('创建' in message_lower or '新建' in message_lower):
                    return {
                        'intent': 'create',
                        'confidence': pattern['confidence']
                    }
                elif pattern_type == 'fix' and ('修复' in message_lower or '错误' in message_lower):
                    return {
                        'intent': 'fix',
                        'confidence': pattern['confidence']
                    }
            
            return {'intent': 'general', 'confidence': 0.5}
            
        except Exception as e:
            print(f"Error predicting from pattern: {e}")
            return {'intent': 'general', 'confidence': 0.5}
    
    def _combine_predictions(self, *predictions) -> Dict[str, Any]:
        """综合预测结果"""
        intent_scores = defaultdict(float)
        total_confidence = 0
        
        weights = [self.history_weight, self.context_weight, self.pattern_weight]
        
        for i, prediction in enumerate(predictions):
            intent = prediction.get('intent', 'general')
            confidence = prediction.get('confidence', 0.5)
            weight = weights[i] if i < len(weights) else 0.3
            
            intent_scores[intent] += confidence * weight
            total_confidence += weight
        
        # 归一化
        if total_confidence > 0:
            for intent in intent_scores:
                intent_scores[intent] /= total_confidence
        
        # 找到最高分的意图
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            return {
                'intent': best_intent[0],
                'confidence': best_intent[1],
                'all_intents': dict(intent_scores)
            }
        
        return {
            'intent': 'general',
            'confidence': 0.5,
            'all_intents': {}
        }
    
    def predict_user_needs(self, current_message: str, session_history: List[str] = None) -> List[Dict[str, Any]]:
        """预测用户需求"""
        try:
            # 预测意图
            intent_prediction = self.predict_user_intent(current_message, session_history)
            intent = intent_prediction.get('intent', 'general')
            
            # 基于意图预测需求
            needs = []
            
            if intent == 'config':
                needs.append({
                    'type': 'knowledge',
                    'description': '配置相关知识',
                    'confidence': 0.7
                })
                needs.append({
                    'type': 'tool',
                    'description': '配置工具',
                    'confidence': 0.6
                })
            elif intent == 'search':
                needs.append({
                    'type': 'knowledge',
                    'description': '搜索相关知识',
                    'confidence': 0.8
                })
                needs.append({
                    'type': 'session',
                    'description': '历史会话',
                    'confidence': 0.6
                })
            elif intent == 'create':
                needs.append({
                    'type': 'template',
                    'description': '创建模板',
                    'confidence': 0.7
                })
                needs.append({
                    'type': 'knowledge',
                    'description': '创建相关知识',
                    'confidence': 0.6
                })
            elif intent == 'fix':
                needs.append({
                    'type': 'knowledge',
                    'description': '修复相关知识',
                    'confidence': 0.8
                })
                needs.append({
                    'type': 'session',
                    'description': '类似问题历史',
                    'confidence': 0.7
                })
            else:
                needs.append({
                    'type': 'knowledge',
                    'description': '通用知识',
                    'confidence': 0.5
                })
            
            return needs
            
        except Exception as e:
            print(f"Error predicting user needs: {e}")
            return []
    
    def get_proactive_suggestions(self, current_message: str, session_history: List[str] = None) -> List[str]:
        """获取主动建议"""
        try:
            # 预测用户需求
            needs = self.predict_user_needs(current_message, session_history)
            
            suggestions = []
            
            for need in needs:
                if need['confidence'] > 0.6:
                    if need['type'] == 'knowledge':
                        suggestions.append("我可以帮你查找相关知识")
                    elif need['type'] == 'tool':
                        suggestions.append("我可以帮你找到合适的工具")
                    elif need['type'] == 'session':
                        suggestions.append("我可以帮你查找历史会话")
                    elif need['type'] == 'template':
                        suggestions.append("我可以帮你找到创建模板")
            
            return suggestions
            
        except Exception as e:
            print(f"Error getting proactive suggestions: {e}")
            return []


def predict_user_intent(current_message: str, session_history: List[str] = None) -> Dict[str, Any]:
    """便捷函数：预测用户意图"""
    mechanism = PredictionMechanism()
    return mechanism.predict_user_intent(current_message, session_history)


def predict_user_needs(current_message: str, session_history: List[str] = None) -> List[Dict[str, Any]]:
    """便捷函数：预测用户需求"""
    mechanism = PredictionMechanism()
    return mechanism.predict_user_needs(current_message, session_history)


def get_proactive_suggestions(current_message: str, session_history: List[str] = None) -> List[str]:
    """便捷函数：获取主动建议"""
    mechanism = PredictionMechanism()
    return mechanism.get_proactive_suggestions(current_message, session_history)


if __name__ == '__main__':
    # 测试
    print("=== 预测机制测试 ===\n")
    
    mechanism = PredictionMechanism()
    
    test_messages = [
        "如何配置 fact_store?",
        "帮我执行 A股复盘",
        "什么是 LLM Wiki?",
        "搜索历史会话",
        "创建一个新技能",
        "查看 MEMORY.md 配置",
        "修复 session_search 错误"
    ]
    
    for message in test_messages:
        print(f"消息: {message}")
        
        # 预测意图
        intent_prediction = mechanism.predict_user_intent(message)
        print(f"  预测意图: {intent_prediction['intent']}")
        print(f"  置信度: {intent_prediction['confidence']:.2f}")
        
        # 预测需求
        needs = mechanism.predict_user_needs(message)
        print(f"  预测需求: {[n['description'] for n in needs]}")
        
        # 获取主动建议
        suggestions = mechanism.get_proactive_suggestions(message)
        print(f"  主动建议: {suggestions}")
        
        print("-" * 50)
