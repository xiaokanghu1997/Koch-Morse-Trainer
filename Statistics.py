"""
Koch 统计数据管理模块
记录和管理练习统计数据

Author: xiaokanghu1997
Date: 2025-11-10
Version: 1.1.0
"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional
from Config import config


class StatisticsManager:
    """统计数据管理类"""
    
    def __init__(self):
        """初始化统计管理器"""
        self.stats_file = config.base_dir / "statistics.json"
        self.data = self.load_statistics()
    
    def load_statistics(self) -> dict:
        """
        从JSON文件加载统计数据
        
        Returns:
            统计数据字典
        """
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load statistics - {e}")
        
        # 返回默认数据结构
        return {
            "version": "1.1.0",
            "total_practice_time": 0,  # 总练习时长（秒）
            "total_practice_count": 0,  # 总练习次数
            "lessons": {},  # 各课程统计
            "daily_stats": {}  # 每日统计
        }
    
    def save_statistics(self):
        """保存统计数据到JSON文件"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save statistics - {e}")
    
    def add_practice_record(
        self, 
        lesson_name: str, 
        accuracy: float, 
        practice_time: float,
        text_index: int
    ):
        """
        添加一次练习记录
        
        Args:
            lesson_name: 课程名称，如 "01 - K, M"
            accuracy: 准确率（0-100）
            practice_time: 练习时长（秒）
            text_index: 练习文本索引
        """
        # 更新总计数据
        self.data["total_practice_time"] += practice_time
        self.data["total_practice_count"] += 1
        
        # 初始化课程数据（如果不存在）
        if lesson_name not in self.data["lessons"]:
            self.data["lessons"][lesson_name] = {
                "practice_count": 0,
                "accuracy_history": [],
                "total_accuracy": 0.0,
                "average_accuracy": 0.0,
                "best_accuracy": 0.0,
                "practice_time": 0.0
            }
        
        lesson_data = self.data["lessons"][lesson_name]
        
        # 添加历史记录
        record = {
            "timestamp": datetime.now().isoformat(),
            "accuracy": round(accuracy, 2),
            "practice_time": round(practice_time, 2),
            "text_index": text_index
        }
        lesson_data["accuracy_history"].append(record)
        
        # 更新课程统计
        lesson_data["practice_count"] += 1
        lesson_data["total_accuracy"] += accuracy
        lesson_data["average_accuracy"] = round(
            lesson_data["total_accuracy"] / lesson_data["practice_count"], 2
        )
        lesson_data["best_accuracy"] = max(
            lesson_data["best_accuracy"], accuracy
        )
        lesson_data["practice_time"] += practice_time
        
        # 更新每日统计
        today = date.today().isoformat()
        if today not in self.data["daily_stats"]:
            self.data["daily_stats"][today] = {
                "practice_time": 0.0,
                "practice_count": 0
            }
        
        self.data["daily_stats"][today]["practice_time"] += practice_time
        self.data["daily_stats"][today]["practice_count"] += 1
        
        # 保存数据
        self.save_statistics()
    
    def get_lesson_stats(self, lesson_name: str) -> Optional[dict]:
        """
        获取指定课程的统计数据
        
        Args:
            lesson_name: 课程名称
            
        Returns:
            课程统计数据字典，如果不存在返回None
        """
        return self.data["lessons"].get(lesson_name)
    
    def get_overall_stats(self) -> dict:
        """
        获取总体统计数据
        
        Returns:
            包含总体统计信息的字典
        """
        total_lessons = len(self.data["lessons"])
        completed_lessons = sum(
            1 for lesson in self.data["lessons"].values()
            if lesson.get("average_accuracy", 0) >= 90.0
        )
        
        # 计算总平均准确率
        if total_lessons > 0:
            total_avg = sum(
                lesson.get("average_accuracy", 0)
                for lesson in self.data["lessons"].values()
            ) / total_lessons
        else:
            total_avg = 0.0
        
        return {
            "total_practice_time": self.data["total_practice_time"],
            "total_practice_count": self.data["total_practice_count"],
            "total_lessons_practiced": total_lessons,
            "completed_lessons": completed_lessons,
            "average_accuracy": round(total_avg, 2)
        }
    
    def get_recent_history(self, lesson_name: str, count: int = 10) -> List[dict]:
        """
        获取最近的练习历史记录
        
        Args:
            lesson_name: 课程名称
            count: 返回记录数量
            
        Returns:
            最近的练习记录列表
        """
        lesson_data = self.get_lesson_stats(lesson_name)
        if not lesson_data:
            return []
        
        history = lesson_data.get("accuracy_history", [])
        return history[-count:]
    
    def get_daily_stats(self, days: int = 7) -> dict:
        """
        获取最近N天的每日统计
        
        Args:
            days: 天数
            
        Returns:
            每日统计数据字典
        """
        result = {}
        today = date.today()
        
        for i in range(days):
            target_date = today - datetime.timedelta(days=i)
            date_str = target_date.isoformat()
            
            if date_str in self.data["daily_stats"]:
                result[date_str] = self.data["daily_stats"][date_str]
            else:
                result[date_str] = {
                    "practice_time": 0.0,
                    "practice_count": 0
                }
        
        return result
    
    def format_time(self, seconds: float) -> str:
        """
        格式化时间显示
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间字符串，如 "1h 23m" 或 "45m 30s"
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        
        if minutes < 60:
            return f"{minutes}m {remaining_seconds}s"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        return f"{hours}h {remaining_minutes}m"


# 全局统计管理器实例
stats_manager = StatisticsManager()