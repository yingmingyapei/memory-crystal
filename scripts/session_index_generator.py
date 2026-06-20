#!/usr/bin/env python3
"""
会话索引生成器 - 生成可视化会话索引
用于记忆系统主动检索

功能:
- 生成 session_index.md
- 生成 session_log.md
- 支持按主题/时间分区
- 支持标签索引
"""

import sqlite3
import re
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class SessionIndexGenerator:
    """会话索引生成器"""
    
    def __init__(self):
        self.session_db_path = Path.home() / '.hermes' / 'sessions' / 'state.db'
        self.wiki_path = Path('/mnt/c/Users/yingm/wiki')
        
        # 标签分类法
        self.tag_taxonomy = {
            '投资': ['股票', 'A股', 'ETF', '基金', '投资', '市场', '复盘'],
            '技术': ['代码', 'API', '数据库', '部署', '脚本', '工具'],
            'AI': ['LLM', 'Agent', '模型', '训练', '推理', 'Wiki'],
            '内容': ['写作', '文章', '视频', '头条', '内容'],
            '系统': ['配置', '调试', '错误', '修复', '维护']
        }
    
    def generate_index(self, output_path: str = None) -> str:
        """生成会话索引"""
        if not self.session_db_path.exists():
            return ""
        
        try:
            conn = sqlite3.connect(str(self.session_db_path))
            conn.row_factory = sqlite3.Row
            
            # 检查 sessions 表是否存在
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sessions'
            """)
            if not cursor.fetchone():
                conn.close()
                return ""
            
            # 获取所有会话
            cursor = conn.execute("""
                SELECT id, title, source, started_at, ended_at, message_count
                FROM sessions
                ORDER BY started_at DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row['id'],
                    'title': row['title'] or 'Untitled',
                    'source': row['source'],
                    'started_at': row['started_at'],
                    'ended_at': row['ended_at'],
                    'message_count': row['message_count']
                })
            
            conn.close()
            
            if not sessions:
                return ""
            
            # 生成索引内容
            index_content = self._build_index_content(sessions)
            
            # 保存到文件
            if output_path:
                output_file = Path(output_path)
            else:
                output_file = self.wiki_path / 'session_index.md'
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            return str(output_file)
            
        except Exception as e:
            print(f"Error generating index: {e}")
            return ""
    
    def _build_index_content(self, sessions: List[Dict[str, Any]]) -> str:
        """构建索引内容"""
        lines = []
        
        # 标题
        lines.append("# Session Index")
        lines.append("")
        lines.append("> 会话目录。按主题/时间分区，每条记录一行摘要。")
        lines.append(f"> Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Total sessions: {len(sessions)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 按主题分区
        topic_sessions = defaultdict(list)
        for session in sessions:
            topic = self._classify_session(session['title'])
            topic_sessions[topic].append(session)
        
        # 输出各主题
        for topic in ['投资', '技术', 'AI', '内容', '系统', 'general']:
            if topic in topic_sessions:
                topic_name = topic if topic != 'general' else '其他'
                lines.append(f"## {topic_name}")
                lines.append("")
                
                for session in topic_sessions[topic][:10]:  # 限制每个主题最多10个
                    title = session['title']
                    session_id = session['id']
                    started_at = self._format_timestamp(session['started_at'])
                    message_count = session['message_count']
                    
                    lines.append(f"- [[session:{session_id}]] - {title}")
                    lines.append(f"  - 时间: {started_at}")
                    lines.append(f"  - 消息数: {message_count}")
                    lines.append("")
        
        # 时间线
        lines.append("## 📅 时间线")
        lines.append("")
        
        # 按日期分组
        date_sessions = defaultdict(list)
        for session in sessions:
            date = self._format_date(session['started_at'])
            date_sessions[date].append(session)
        
        for date in sorted(date_sessions.keys(), reverse=True)[:7]:  # 最近7天
            lines.append(f"### {date}")
            for session in date_sessions[date][:5]:  # 每天最多5个
                time = self._format_time(session['started_at'])
                lines.append(f"- {time} - {session['title']}")
            lines.append("")
        
        # 标签索引
        lines.append("## 🏷️ 标签索引")
        lines.append("")
        
        tag_counts = defaultdict(int)
        for session in sessions:
            tags = self._extract_tags(session['title'])
            for tag in tags:
                tag_counts[tag] += 1
        
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"- `{tag}` ({count} 个会话)")
        
        lines.append("")
        
        return '\n'.join(lines)
    
    def _classify_session(self, title: str) -> str:
        """分类会话"""
        title_lower = title.lower()
        
        for topic, keywords in self.tag_taxonomy.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return topic
        
        return 'general'
    
    def _extract_tags(self, title: str) -> List[str]:
        """提取标签"""
        tags = []
        title_lower = title.lower()
        
        for topic, keywords in self.tag_taxonomy.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    tags.append(topic)
                    break
        
        return tags
    
    def _format_timestamp(self, timestamp: float) -> str:
        """格式化时间戳"""
        if not timestamp:
            return "Unknown"
        
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return "Unknown"
    
    def _format_date(self, timestamp: float) -> str:
        """格式化日期"""
        if not timestamp:
            return "Unknown"
        
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d')
        except:
            return "Unknown"
    
    def _format_time(self, timestamp: float) -> str:
        """格式化时间"""
        if not timestamp:
            return "Unknown"
        
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%H:%M')
        except:
            return "Unknown"
    
    def generate_log(self, output_path: str = None) -> str:
        """生成会话日志"""
        if not self.session_db_path.exists():
            return ""
        
        try:
            conn = sqlite3.connect(str(self.session_db_path))
            conn.row_factory = sqlite3.Row
            
            # 检查 sessions 表是否存在
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sessions'
            """)
            if not cursor.fetchone():
                conn.close()
                return ""
            
            # 获取所有会话
            cursor = conn.execute("""
                SELECT id, title, source, started_at, ended_at, message_count
                FROM sessions
                ORDER BY started_at DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row['id'],
                    'title': row['title'] or 'Untitled',
                    'source': row['source'],
                    'started_at': row['started_at'],
                    'ended_at': row['ended_at'],
                    'message_count': row['message_count']
                })
            
            conn.close()
            
            if not sessions:
                return ""
            
            # 生成日志内容
            log_content = self._build_log_content(sessions)
            
            # 保存到文件
            if output_path:
                output_file = Path(output_path)
            else:
                output_file = self.wiki_path / 'session_log.md'
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            return str(output_file)
            
        except Exception as e:
            print(f"Error generating log: {e}")
            return ""
    
    def _build_log_content(self, sessions: List[Dict[str, Any]]) -> str:
        """构建日志内容"""
        lines = []
        
        # 标题
        lines.append("# Session Log")
        lines.append("")
        lines.append("> 会话操作日志。按时间顺序记录。")
        lines.append("> Format: `## [YYYY-MM-DD HH:MM] action | session_id`")
        lines.append("> Actions: create, update, query, tag, relate, archive")
        lines.append("")
        
        # 按日期分组
        date_sessions = defaultdict(list)
        for session in sessions:
            date = self._format_date(session['started_at'])
            date_sessions[date].append(session)
        
        for date in sorted(date_sessions.keys(), reverse=True)[:7]:  # 最近7天
            for session in date_sessions[date]:
                time = self._format_time(session['started_at'])
                session_id = session['id']
                title = session['title']
                source = session['source']
                message_count = session['message_count']
                
                lines.append(f"## [{date} {time}] create | {session_id}")
                lines.append(f"- Title: {title}")
                lines.append(f"- Source: {source}")
                lines.append(f"- Messages: {message_count}")
                lines.append("")
        
        return '\n'.join(lines)


def generate_session_index(output_path: str = None) -> str:
    """便捷函数：生成会话索引"""
    generator = SessionIndexGenerator()
    return generator.generate_index(output_path)


def generate_session_log(output_path: str = None) -> str:
    """便捷函数：生成会话日志"""
    generator = SessionIndexGenerator()
    return generator.generate_log(output_path)


if __name__ == '__main__':
    # 测试
    print("=== 会话索引生成器测试 ===\n")
    
    generator = SessionIndexGenerator()
    
    # 测试生成索引
    print("1. 生成会话索引")
    index_path = generator.generate_index()
    if index_path:
        print(f"   索引已生成: {index_path}")
    else:
        print("   没有会话数据，跳过索引生成")
    
    # 测试生成日志
    print("\n2. 生成会话日志")
    log_path = generator.generate_log()
    if log_path:
        print(f"   日志已生成: {log_path}")
    else:
        print("   没有会话数据，跳过日志生成")
